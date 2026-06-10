"""
内容审核规则引擎 - FastAPI 后端
C部分：接口与前端 - 后端 API 服务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import uvicorn
import json
import time
from datetime import datetime

app = FastAPI(
    title="广告识别规则引擎 API",
    description="广告内容识别 - 规则引擎接口服务",
    version="1.0.0"
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 数据模型 ============

class ReviewResult(str, Enum):
    """三态审核结果"""
    PASS = "pass"           # 放行
    MANUAL = "manual"       # 转人工
    BLOCK = "block"         # 拦截

class RiskLevel(str, Enum):
    """危害等级"""
    L1 = "L1"   # 低危
    L2 = "L2"   # 中危
    L3 = "L3"   # 高危

class Scale(str, Enum):
    """处理尺度"""
    LOOSE = "loose"     # 宽松
    STANDARD = "standard"  # 标准
    STRICT = "strict"   # 严格

class ContentRequest(BaseModel):
    """内容审核请求"""
    content: str = Field(..., min_length=1, max_length=10000, description="待审核内容")
    scale: Scale = Field(default=Scale.STANDARD, description="处理尺度")
    biz_type: str = Field(default="default", description="业务类型")

class HitRule(BaseModel):
    """命中规则"""
    rule_id: str
    rule_name: str
    risk_level: RiskLevel
    keywords: List[str]
    position: List[Dict[str, int]]  # 命中位置

class ReviewResponse(BaseModel):
    """内容审核响应"""
    request_id: str
    content: str
    result: ReviewResult
    score: float = Field(..., ge=0, le=1)
    scale: Scale
    hit_rules: List[HitRule]
    reason: str
    timestamp: str

class ManualTask(BaseModel):
    """人工审核任务"""
    task_id: str
    content: str
    machine_result: ReviewResult
    machine_score: float
    hit_rules: List[HitRule]
    status: str  # pending / approved / rejected
    created_at: str
    reviewed_at: Optional[str] = None
    reviewer: Optional[str] = None
    review_result: Optional[ReviewResult] = None
    review_comment: Optional[str] = None

class ManualReviewRequest(BaseModel):
    """人工审核请求"""
    task_id: str
    result: ReviewResult
    reviewer: str
    comment: Optional[str] = ""

# ============ 模拟数据存储 ============

# 模拟规则库 —— 广告识别
RULES_DB = [
    {
        "rule_id": "R001",
        "rule_name": "硬广推销-联系方式",
        "risk_level": "L3",
        "keywords": ["加微信", "加VX", "加V", "扫码加", "微信号", "VX号", "加我微信"],
        "pattern": None
    },
    {
        "rule_id": "R002",
        "rule_name": "硬广推销-价格诱导",
        "risk_level": "L3",
        "keywords": ["限时特惠", "亏本甩卖", "清仓大甩卖", "全网最低价", "跳楼价", "特价包邮"],
        "pattern": None
    },
    {
        "rule_id": "R003",
        "rule_name": "软广植入-产品推荐",
        "risk_level": "L2",
        "keywords": ["强烈推荐", "亲测好用", "回购无数次", "必备好物", "种草", "安利给大家"],
        "pattern": None
    },
    {
        "rule_id": "R004",
        "rule_name": "软广植入-效果夸大",
        "risk_level": "L2",
        "keywords": ["效果惊人", "三天见效", "一用就灵", "用了都说好", "好评如潮", "销量冠军"],
        "pattern": None
    },
    {
        "rule_id": "R005",
        "rule_name": "引流营销-直播间引流",
        "risk_level": "L2",
        "keywords": ["直播间下单", "进直播间", "来我直播间", "直播专属", "直播间福利", "开播提醒"],
        "pattern": None
    },
    {
        "rule_id": "R006",
        "rule_name": "疑似广告-模糊营销",
        "risk_level": "L1",
        "keywords": ["私信了解", "详情私聊", "感兴趣私", "评论区见", "戳链接", "点击下方"],
        "pattern": None
    }
]

# 人工审核队列
manual_queue: List[ManualTask] = []

# 审核历史
review_history: List[Dict] = []

# ============ 核心引擎（模拟） ============

def generate_request_id() -> str:
    """生成请求ID"""
    return f"REQ{int(time.time() * 1000)}"

def match_content(content: str) -> List[HitRule]:
    """
    模拟内容匹配
    实际项目中这里会调用 AC 自动机和规则引擎
    """
    hit_rules = []
    
    for rule in RULES_DB:
        matched_keywords = []
        positions = []
        
        for keyword in rule["keywords"]:
            if keyword in content:
                matched_keywords.append(keyword)
                # 记录位置
                start = 0
                while True:
                    idx = content.find(keyword, start)
                    if idx == -1:
                        break
                    positions.append({"start": idx, "end": idx + len(keyword)})
                    start = idx + 1
        
        if matched_keywords:
            hit_rules.append(HitRule(
                rule_id=rule["rule_id"],
                rule_name=rule["rule_name"],
                risk_level=RiskLevel(rule["risk_level"]),
                keywords=matched_keywords,
                position=positions
            ))
    
    return hit_rules

def calculate_score(hit_rules: List[HitRule]) -> float:
    """
    计算危害分数
    基于最高等级和命中数量
    """
    if not hit_rules:
        return 0.0
    
    # 等级权重
    level_weights = {"L1": 0.3, "L2": 0.6, "L3": 1.0}
    
    max_score = 0.0
    for rule in hit_rules:
        weight = level_weights.get(rule.risk_level.value, 0.1)
        keyword_count = len(rule.keywords)
        rule_score = min(weight * (1 + (keyword_count - 1) * 0.2), 1.0)
        max_score = max(max_score, rule_score)
    
    return round(min(max_score, 1.0), 3)

def determine_result(score: float, scale: Scale) -> ReviewResult:
    """
    三态判定
    根据分数和尺度决定结果
    """
    # 阈值配置
    thresholds = {
        Scale.LOOSE: {"block": 0.8, "manual": 0.5},
        Scale.STANDARD: {"block": 0.7, "manual": 0.4},
        Scale.STRICT: {"block": 0.6, "manual": 0.3}
    }
    
    threshold = thresholds.get(scale, thresholds[Scale.STANDARD])
    
    if score >= threshold["block"]:
        return ReviewResult.BLOCK
    elif score >= threshold["manual"]:
        return ReviewResult.MANUAL
    else:
        return ReviewResult.PASS

def get_result_reason(result: ReviewResult, hit_rules: List[HitRule]) -> str:
    """生成审核原因说明"""
    if result == ReviewResult.PASS:
        return "内容未命中任何规则，予以放行"
    
    rule_names = [r.rule_name for r in hit_rules]
    if result == ReviewResult.BLOCK:
        return f"命中高危规则：{', '.join(rule_names)}，予以拦截"
    else:
        return f"命中规则：{', '.join(rule_names)}，需人工复核"

# ============ API 路由 ============

@app.post("/api/v1/review", response_model=ReviewResponse, tags=["内容审核"])
async def review_content(request: ContentRequest, background_tasks: BackgroundTasks):
    """
    内容审核接口
    
    - 接收待审核内容
    - 返回三态结果（放行/转人工/拦截）
    - 命中规则详情
    """
    request_id = generate_request_id()
    
    # 1. 内容匹配
    hit_rules = match_content(request.content)
    
    # 2. 计算分数
    score = calculate_score(hit_rules)
    
    # 3. 三态判定
    result = determine_result(score, request.scale)
    
    # 4. 生成原因
    reason = get_result_reason(result, hit_rules)
    
    # 5. 如果是转人工，加入队列
    if result == ReviewResult.MANUAL:
        task = ManualTask(
            task_id=f"TASK{int(time.time() * 1000)}",
            content=request.content,
            machine_result=result,
            machine_score=score,
            hit_rules=hit_rules,
            status="pending",
            created_at=datetime.now().isoformat()
        )
        manual_queue.append(task)
    
    # 6. 记录历史
    review_record = {
        "request_id": request_id,
        "content": request.content,
        "result": result.value,
        "score": score,
        "scale": request.scale.value,
        "hit_rules": [rule.dict() for rule in hit_rules],
        "timestamp": datetime.now().isoformat()
    }
    review_history.append(review_record)
    
    return ReviewResponse(
        request_id=request_id,
        content=request.content,
        result=result,
        score=score,
        scale=request.scale,
        hit_rules=hit_rules,
        reason=reason,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/v1/review/history", tags=["内容审核"])
async def get_review_history(limit: int = 50, offset: int = 0):
    """获取审核历史"""
    return {
        "total": len(review_history),
        "items": review_history[offset:offset + limit]
    }

@app.get("/api/v1/rules", tags=["规则管理"])
async def get_rules():
    """获取规则列表"""
    return {"rules": RULES_DB}

@app.get("/api/v1/manual/tasks", tags=["人工审核"])
async def get_manual_tasks(status: Optional[str] = "pending"):
    """
    获取人工审核任务列表
    
    - status: pending / approved / rejected / all
    """
    if status == "all":
        tasks = manual_queue
    else:
        tasks = [t for t in manual_queue if t.status == status]
    
    return {
        "total": len(tasks),
        "tasks": [t.dict() for t in tasks]
    }

@app.post("/api/v1/manual/review", tags=["人工审核"])
async def manual_review(request: ManualReviewRequest):
    """
    人工审核处理
    
    - 对转人工的任务进行最终判定
    """
    task = None
    for t in manual_queue:
        if t.task_id == request.task_id:
            task = t
            break
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="任务已被处理")
    
    # 更新任务状态
    task.status = "approved" if request.result == ReviewResult.PASS else "rejected"
    task.reviewed_at = datetime.now().isoformat()
    task.reviewer = request.reviewer
    task.review_result = request.result
    task.review_comment = request.comment
    
    return {
        "task_id": request.task_id,
        "status": task.status,
        "result": request.result.value,
        "reviewer": request.reviewer,
        "reviewed_at": task.reviewed_at
    }

@app.get("/api/v1/stats", tags=["统计"])
async def get_statistics():
    """获取审核统计信息"""
    total = len(review_history)
    pass_count = sum(1 for r in review_history if r["result"] == "pass")
    manual_count = sum(1 for r in review_history if r["result"] == "manual")
    block_count = sum(1 for r in review_history if r["result"] == "block")
    
    pending_manual = sum(1 for t in manual_queue if t.status == "pending")
    
    return {
        "total_reviews": total,
        "pass_count": pass_count,
        "manual_count": manual_count,
        "block_count": block_count,
        "pending_manual": pending_manual,
        "pass_rate": round(pass_count / total, 3) if total > 0 else 0,
        "block_rate": round(block_count / total, 3) if total > 0 else 0
    }

@app.delete("/api/v1/data/reset", tags=["数据管理"])
async def reset_data():
    """清空所有运行时数据（审核历史、人工审核队列）"""
    cleared_history = len(review_history)
    cleared_tasks = len(manual_queue)
    review_history.clear()
    manual_queue.clear()
    return {
        "message": "数据已清空",
        "cleared_reviews": cleared_history,
        "cleared_manual_tasks": cleared_tasks
    }

@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============ 启动入口 ============

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
