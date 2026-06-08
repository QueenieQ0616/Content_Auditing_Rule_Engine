"""
引擎核心 —— 串起匹配、打分、判定的主流程。

这里的 Engine.check() 就是给 C 的「引擎输入输出约定」：
  输入: content(str), scale(str)
  输出: dict，字段见下方 check() 的返回值。
C 写 API 时，照着这个输入输出来包就行。
"""
from typing import List

from .models import Rule, Logic
from .matchers import run_condition
from .scorer import score, decide
from .rule_store import load_rules


class Engine:
    def __init__(self, rules_dir: str):
        # 启动时把规则加载进内存
        self.rules: List[Rule] = load_rules(rules_dir)

    def _rule_hits(self, content: str, rule: Rule) -> bool:
        """判断单条规则是否命中：跑各条件，再按 AND/OR 组合。"""
        results = [run_condition(content, c) for c in rule.conditions]
        if rule.logic == Logic.OR:
            return any(results)
        return all(results)  # AND

    def check(self, content: str, scale: str = "standard") -> dict:
        """
        检测主流程。这是引擎对外的唯一入口。

        返回结构（C 的 API 直接照搬）:
        {
          "decision": "pass" | "review" | "reject",
          "risk_level": "low" | "medium" | "high",
          "score": 0.0~1.0,
          "labels": [...],
          "hit_rules": [{"rule_id","name","level"}...],
          "review_reason": "..."
        }
        """
        # 1. 找出所有命中的规则
        hit_rules = [r for r in self.rules if self._rule_hits(content, r)]

        # 2. 打分
        s = round(score(hit_rules), 4)

        # 3. 三态判定
        result = decide(s, scale)

        # 4. 合并标签 + 命中明细
        labels = sorted({label for r in hit_rules for label in r.action.labels})
        hit_detail = [
            {"rule_id": r.rule_id, "name": r.name, "level": r.level.value}
            for r in hit_rules
        ]

        return {
            "decision": result["decision"],
            "risk_level": result["risk_level"],
            "score": s,
            "labels": labels,
            "hit_rules": hit_detail,
            "review_reason": result["review_reason"],
        }
