"""Core moderation engine."""

from pathlib import Path
from typing import List

from .keyword_index import keyword_index
from .matchers import run_condition
from .models import Logic, Rule
from .rule_store import load_rules
from .scorer import decide, score


class Engine:
    def __init__(self, rules_dir: str | None = None) -> None:
        if rules_dir is None:
            rules_dir = str(Path(__file__).with_name("rules"))
        self.rules = load_rules(rules_dir)
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        words: List[str] = []
        for rule in self.rules:
            for condition in rule.conditions:
                if condition.type == "keyword":
                    value = condition.value
                    if isinstance(value, list):
                        words.extend(str(word) for word in value)
                    else:
                        words.append(str(value))
        keyword_index.build(words)

    def _rule_hits(self, content: str, rule: Rule, hit_words: set[str]) -> bool:
        matches = [
            run_condition(content, condition, hit_words=hit_words)
            for condition in rule.conditions
        ]
        if rule.logic == Logic.OR:
            return any(matches)
        return all(matches)

    def check(self, content: str, scale: str = "standard") -> dict:
        hit_words = keyword_index.search(content)
        hit_rules = [
            rule for rule in self.rules if self._rule_hits(content, rule, hit_words)
        ]
        s = score(hit_rules)
        decision = decide(s, scale)

        labels = []
        for rule in hit_rules:
            for label in rule.action.labels:
                if label not in labels:
                    labels.append(label)

        hit_rule_items = [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "level": rule.level.value,
            }
            for rule in hit_rules
        ]

        if hit_rules:
            names = "、".join(rule.name for rule in hit_rules)
            review_reason = f"{decision['review_reason']}，命中规则：{names}"
        else:
            review_reason = decision["review_reason"]

        return {
            "decision": decision["decision"],
            "risk_level": decision["risk_level"],
            "score": s,
            "labels": labels,
            "hit_rules": hit_rule_items,
            "review_reason": review_reason,
        }
