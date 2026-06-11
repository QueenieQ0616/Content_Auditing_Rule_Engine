"""Scoring and three-state decision logic."""

from typing import List

SCALES = {
    "loose": {"low": 0.5, "high": 0.8},
    "standard": {"low": 0.35, "high": 0.7},
    "strict": {"low": 0.2, "high": 0.5},
}


def score(hit_rules: List[object]) -> float:
    if not hit_rules:
        return 0.0
    max_weight = max(rule.weight for rule in hit_rules)
    return round(min(1.0, max_weight + 0.05 * (len(hit_rules) - 1)), 3)


def decide(s: float, scale: str = "standard") -> dict:
    thresholds = SCALES.get(scale, SCALES["standard"])
    if s < thresholds["low"]:
        return {
            "decision": "pass",
            "risk_level": "low",
            "review_reason": "未命中规则或分数低于放行阈值",
        }
    if s < thresholds["high"]:
        return {
            "decision": "review",
            "risk_level": "medium",
            "review_reason": "分数处于人工审核区间",
        }
    return {
        "decision": "reject",
        "risk_level": "high",
        "review_reason": "分数达到拦截阈值",
    }
