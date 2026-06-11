"""FastAPI service for the merged content moderation app."""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
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


class ContentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    scale: str = Field(default="standard", pattern="^(loose|standard|strict)$")
    biz_type: str = "default"


class ManualReviewRequest(BaseModel):
    task_id: str
    decision: str = Field(..., pattern="^(pass|review|reject)$")
    reviewer: str = Field(..., min_length=1)
    comment: Optional[str] = ""


def generate_id(prefix: str) -> str:
    return f"{prefix}{int(time.time() * 1000)}"


def current_time() -> str:
    return datetime.now().isoformat()


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


@app.post("/api/v1/review")
async def review_content(request: ContentRequest):
    result = engine.check(request.content, request.scale)
    request_id = generate_id("REQ")
    timestamp = current_time()

    response = {
        "request_id": request_id,
        "content": request.content,
        "scale": request.scale,
        "timestamp": timestamp,
        **result,
    }
    review_history.append(response)

    if result["decision"] == "review":
        manual_queue.append(
            {
                "task_id": generate_id("TASK"),
                "content": request.content,
                "machine_decision": result["decision"],
                "machine_score": result["score"],
                "hit_rules": result["hit_rules"],
                "status": "pending",
                "created_at": timestamp,
                "reviewed_at": None,
                "reviewer": None,
                "review_decision": None,
                "review_comment": None,
            }
        )

    return response


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


@app.post("/api/v1/manual/review")
async def manual_review(request: ManualReviewRequest):
    task = next((t for t in manual_queue if t["task_id"] == request.task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] != "pending":
        raise HTTPException(status_code=400, detail="任务已被处理")

    task["status"] = "approved" if request.decision == "pass" else "rejected"
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
