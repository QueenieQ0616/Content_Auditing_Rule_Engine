"""FastAPI service for the merged content moderation app."""

import hashlib
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import Engine

app = FastAPI(
    title="广告识别规则引擎 API",
    description="合并 v1/v2 前后端与 engine 核心后的接口服务",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = Engine()
manual_queue: List[Dict] = []
review_history: List[Dict] = []
users: Dict[str, Dict] = {}
sessions: Dict[str, str] = {}


class ContentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    scale: str = Field(default="standard", pattern="^(loose|standard|strict)$")
    biz_type: str = "default"


class BatchReviewRequest(BaseModel):
    contents: List[str] = Field(..., min_length=1, max_length=500)
    scale: str = Field(default="standard", pattern="^(loose|standard|strict)$")
    biz_type: str = "default"


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_\-\u4e00-\u9fa5]+$")
    password: str = Field(..., min_length=6, max_length=64)


class ManualReviewRequest(BaseModel):
    task_id: str
    decision: str = Field(..., pattern="^(pass|review|reject)$")
    reviewer: str = Field(..., min_length=1)
    comment: Optional[str] = ""


def generate_id(prefix: str) -> str:
    return f"{prefix}{int(time.time() * 1000)}"


def current_time() -> str:
    return datetime.now().isoformat()


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def public_user(username: str) -> Dict:
    user = users[username]
    return {
        "username": username,
        "created_at": user["created_at"],
        "role": user.get("role", "user"),
    }


def current_user_from_token(authorization: Optional[str]) -> Dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    token = authorization.replace("Bearer ", "", 1).strip()
    username = sessions.get(token)
    if not username or username not in users:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return public_user(username)


def public_rules() -> List[Dict]:
    rules = []
    for rule in engine.rules:
        keywords = []
        for condition in rule.conditions:
            if condition.type == "keyword":
                value = condition.value
                keywords.extend(value if isinstance(value, list) else [value])
        risk_level = {"L1": "low", "L2": "medium", "L3": "high"}[rule.level.value]
        rules.append(
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "level": rule.level.value,
                "risk_level": risk_level,
                "label": "、".join(rule.action.labels),
                "keywords": keywords,
            }
        )
    return rules


def create_review_record(content: str, scale: str, biz_type: str = "default", batch_id: Optional[str] = None, index: Optional[int] = None) -> Dict:
    result = engine.check(content, scale)
    request_id = generate_id("REQ")
    timestamp = current_time()

    response = {
        "request_id": request_id,
        "content": content,
        "scale": scale,
        "biz_type": biz_type,
        "timestamp": timestamp,
        **result,
    }
    if batch_id is not None:
        response["batch_id"] = batch_id
        response["batch_index"] = index

    review_history.append(response)

    if result["decision"] == "review":
        manual_queue.append(
            {
                "task_id": generate_id("TASK"),
                "content": content,
                "machine_decision": result["decision"],
                "machine_score": result["score"],
                "hit_rules": result["hit_rules"],
                "hit_positions": result.get("hit_positions", []),
                "adversarial_hits": result.get("adversarial_hits", []),
                "score_detail": result.get("score_detail", {}),
                "decision_detail": result.get("decision_detail", {}),
                "trace": result.get("trace", {}),
                "status": "pending",
                "created_at": timestamp,
                "reviewed_at": None,
                "reviewer": None,
                "review_decision": None,
                "review_comment": None,
                "batch_id": batch_id,
            }
        )

    return response


@app.post("/api/v1/auth/register")
async def register(request: AuthRequest):
    username = request.username.strip()
    if username in users:
        raise HTTPException(status_code=400, detail="用户名已存在")

    salt = secrets.token_hex(16)
    users[username] = {
        "password_hash": hash_password(request.password, salt),
        "salt": salt,
        "created_at": current_time(),
        "role": "user",
    }
    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return {
        "token": token,
        "user": public_user(username),
    }


@app.post("/api/v1/auth/login")
async def login(request: AuthRequest):
    username = request.username.strip()
    user = users.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    password_hash = hash_password(request.password, user["salt"])
    if not secrets.compare_digest(password_hash, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = secrets.token_urlsafe(32)
    sessions[token] = username
    return {
        "token": token,
        "user": public_user(username),
    }


@app.get("/api/v1/auth/me")
async def get_current_user(authorization: Optional[str] = Header(default=None)):
    return {"user": current_user_from_token(authorization)}


@app.post("/api/v1/auth/logout")
async def logout(authorization: Optional[str] = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "", 1).strip()
        sessions.pop(token, None)
    return {"message": "已退出登录"}


@app.post("/api/v1/review")
async def review_content(request: ContentRequest):
    return create_review_record(request.content, request.scale, request.biz_type)


@app.post("/api/v1/review/batch")
async def batch_review_content(request: BatchReviewRequest):
    contents = [content.strip() for content in request.contents if content and content.strip()]
    if not contents:
        raise HTTPException(status_code=400, detail="批量内容不能为空")

    batch_id = generate_id("BATCH")
    items = [
        create_review_record(content, request.scale, request.biz_type, batch_id=batch_id, index=index + 1)
        for index, content in enumerate(contents)
    ]

    return {
        "batch_id": batch_id,
        "total": len(items),
        "summary": {
            "pass_count": sum(1 for item in items if item["decision"] == "pass"),
            "review_count": sum(1 for item in items if item["decision"] == "review"),
            "reject_count": sum(1 for item in items if item["decision"] == "reject"),
        },
        "items": items,
    }


@app.post("/api/v1/trace")
async def trace_content(request: ContentRequest):
    """仅用于展示规则和关键词命中过程，不写入审核历史和人工队列。"""
    result = engine.check(request.content, request.scale)
    return {
        "content": request.content,
        "scale": request.scale,
        "timestamp": current_time(),
        **result,
    }


@app.get("/api/v1/review/history")
async def get_review_history(limit: int = 50, offset: int = 0):
    return {"total": len(review_history), "items": review_history[offset : offset + limit]}


@app.get("/api/v1/rules")
async def get_rules():
    return {"rules": public_rules()}


@app.get("/api/v1/manual/tasks")
async def get_manual_tasks(status: Optional[str] = "pending"):
    tasks = manual_queue if status == "all" else [t for t in manual_queue if t["status"] == status]
    return {"total": len(tasks), "tasks": tasks}


@app.get("/api/v1/manual/tasks/{task_id}")
async def get_manual_task_detail(task_id: str):
    task = next((t for t in manual_queue if t["task_id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@app.post("/api/v1/manual/review")
async def manual_review(request: ManualReviewRequest):
    task = next((t for t in manual_queue if t["task_id"] == request.task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] != "pending":
        raise HTTPException(status_code=400, detail="任务已被处理")

    if request.decision == "pass":
        task["status"] = "approved"
    elif request.decision == "reject":
        task["status"] = "rejected"
    else:
        task["status"] = "pending"
    task["reviewed_at"] = current_time()
    task["reviewer"] = request.reviewer
    task["review_decision"] = request.decision
    task["review_comment"] = request.comment
    return {
        "task_id": request.task_id,
        "status": task["status"],
        "decision": request.decision,
        "reviewer": request.reviewer,
        "reviewed_at": task["reviewed_at"],
    }


@app.get("/api/v1/stats")
async def get_statistics():
    total = len(review_history)
    pass_count = sum(1 for r in review_history if r["decision"] == "pass")
    review_count = sum(1 for r in review_history if r["decision"] == "review")
    reject_count = sum(1 for r in review_history if r["decision"] == "reject")
    pending_manual = sum(1 for t in manual_queue if t["status"] == "pending")
    return {
        "total_reviews": total,
        "pass_count": pass_count,
        "review_count": review_count,
        "reject_count": reject_count,
        "pending_manual": pending_manual,
        "pass_rate": round(pass_count / total, 3) if total else 0,
        "reject_rate": round(reject_count / total, 3) if total else 0,
    }


@app.delete("/api/v1/data/reset")
async def reset_data():
    cleared_reviews = len(review_history)
    cleared_manual_tasks = len(manual_queue)
    review_history.clear()
    manual_queue.clear()
    return {
        "message": "数据已清空",
        "cleared_reviews": cleared_reviews,
        "cleared_manual_tasks": cleared_manual_tasks,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": current_time()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
