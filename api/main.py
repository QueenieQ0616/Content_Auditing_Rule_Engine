"""
API 层（FastAPI）。这部分是 C 的活，A 先写一版能跑的，作为接口约定的示范。

启动: uvicorn api.main:app --reload
文档: 启动后访问 http://127.0.0.1:8000/docs （自动生成的接口文档，可直接测试）
"""
import os
import uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field

from engine import Engine

# 启动时加载引擎（规则进内存）
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "rules")
engine = Engine(RULES_DIR)

app = FastAPI(title="内容审核规则引擎", version="0.1.0")


class CheckRequest(BaseModel):
    """检测请求体 —— 接口输入约定。"""
    content: str = Field(..., description="待检测文本")
    scale: str = Field("standard", description="处理尺度: loose / standard / strict")
    tenant_id: str = Field("default", description="公司/租户")
    biz_id: str = Field("default", description="业务线")
    modality: str = Field("text", description="模态，本期仅 text")


class CheckResponse(BaseModel):
    """检测响应体 —— 接口输出约定。"""
    request_id: str
    decision: str          # pass / review / reject
    risk_level: str        # low / medium / high
    score: float
    labels: list
    hit_rules: list
    review_reason: str


@app.post("/v1/engine/check", response_model=CheckResponse)
def check(req: CheckRequest):
    result = engine.check(req.content, scale=req.scale)
    return CheckResponse(request_id="req_" + uuid.uuid4().hex[:12], **result)


@app.get("/health")
def health():
    return {"status": "ok", "rules_loaded": len(engine.rules)}
