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


def score_with_detail(hit_rules: List[object]) -> dict:
    """Return the final score plus the explanation data used to calculate it."""
    if not hit_rules:
        return {
            "score": 0.0,
            "base_weight": 0.0,
            "base_rule_id": None,
            "extra_hit_count": 0,
            "extra_bonus": 0.0,
            "formula": "no hit rules",
        }

    base_rule = max(hit_rules, key=lambda rule: rule.weight)
    extra_hit_count = max(0, len(hit_rules) - 1)
    extra_bonus = round(0.05 * extra_hit_count, 3)
    final_score = round(min(1.0, base_rule.weight + extra_bonus), 3)
    return {
        "score": final_score,
        "base_weight": round(base_rule.weight, 3),
        "base_rule_id": base_rule.rule_id,
        "extra_hit_count": extra_hit_count,
        "extra_bonus": extra_bonus,
        "formula": f"min(1.0, {round(base_rule.weight, 3)} + 0.05 * {extra_hit_count})",
    }


def decide(s: float, scale: str = "standard") -> dict:
    thresholds = SCALES.get(scale, SCALES["standard"])
    low = thresholds["low"]
    high = thresholds["high"]
    if s < thresholds["low"]:
        return {
            "decision": "pass",
            "risk_level": "low",
            "review_reason": "未命中规则或分数低于放行阈值",
            "decision_detail": {
                "scale": scale,
                "low": low,
                "high": high,
                "reason": f"{s} < {low}, decision = pass",
            },
        }
    if s < thresholds["high"]:
        return {
            "decision": "review",
            "risk_level": "medium",
            "review_reason": "分数处于人工审核区间",
            "decision_detail": {
                "scale": scale,
                "low": low,
                "high": high,
                "reason": f"{low} <= {s} < {high}, decision = review",
            },
        }
    return {
        "decision": "reject",
        "risk_level": "high",
        "review_reason": "分数达到拦截阈值",
        "decision_detail": {
            "scale": scale,
            "low": low,
            "high": high,
            "reason": f"{s} >= {high}, decision = reject",
        },
    }
