"""
打分与三态判定。

打分逻辑（第四章 4.3）：取命中规则的最高权重 + 命中数微调
  score = min(1.0, 最高权重 + 0.05 * 额外命中数)

三态判定（第四章 4.4）：双阈值
  score < low            -> pass   放行
  low <= score < high    -> review 转人工
  score >= high          -> reject 拦截

三档尺度（第四章 4.5）：不同尺度用不同的 (low, high) 阈值组合。
"""
from typing import List

# 三档尺度对应的双阈值。可按评估结果调整。
SCALES = {
    "loose":    {"low": 0.35, "high": 0.7},   # 宽松：只拦最严重的
    "standard": {"low": 0.3, "high": 0.61},  # 标准：平衡
    "strict":   {"low": 0.05, "high": 0.5},   # 严格：宁可错杀
}


def score(hit_rules: List) -> float:
    """根据命中的规则列表算出风险分数。"""
    if not hit_rules:
        return 0.0
    max_weight = max(r.weight for r in hit_rules)
    extra = len(hit_rules) - 1  # 除最高那条外的额外命中数
    return min(1.0, max_weight + 0.05 * extra)


def decide(s: float, scale: str = "standard") -> dict:
    """把分数映射成三态判定。"""
    th = SCALES.get(scale, SCALES["standard"])
    if s < th["low"]:
        decision, risk = "pass", "low"
        reason = "未命中或分数低于放行阈值"
    elif s < th["high"]:
        decision, risk = "review", "medium"
        reason = "分数处于人工审核区间"
    else:
        decision, risk = "reject", "high"
        reason = "分数达到拦截阈值"
    return {"decision": decision, "risk_level": risk, "review_reason": reason}
