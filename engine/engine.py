"""Core moderation engine."""

import re
import time
import unicodedata
from pathlib import Path
from typing import List

from .keyword_index import keyword_index
from .matchers import run_condition
from .models import Logic, Rule
from .rule_store import load_rules
from .scorer import decide, score_with_detail


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
        words.extend(self._normalized_content(word) for word in list(words))
        keyword_index.build(words)

    def _rule_hits(self, content: str, rule: Rule, hit_words: set[str]) -> bool:
        matches = [
            run_condition(content, condition, hit_words=hit_words)
            for condition in rule.conditions
        ]
        if rule.logic == Logic.OR:
            return any(matches)
        return all(matches)

    def _normalized_with_map(self, content: str) -> tuple[str, List[int]]:
        normalized_chars: List[str] = []
        index_map: List[int] = []

        for original_index, char in enumerate(content):
            for normalized_char in unicodedata.normalize("NFKC", char).lower():
                category = unicodedata.category(normalized_char)
                if category.startswith(("P", "S", "Z", "C")):
                    continue
                normalized_chars.append(normalized_char)
                index_map.append(original_index)

        return "".join(normalized_chars), index_map

    def _normalized_content(self, content: str) -> str:
        normalized_content, _ = self._normalized_with_map(content)
        return normalized_content

    def _keyword_values(self, rule: Rule) -> List[str]:
        words: List[str] = []
        for condition in rule.conditions:
            if condition.type != "keyword":
                continue
            value = condition.value
            if isinstance(value, list):
                words.extend(str(word) for word in value)
            else:
                words.append(str(value))
        return [word for word in words if word]

    def _matched_keywords(self, rule: Rule, hit_words: set[str]) -> List[str]:
        return [word for word in self._keyword_values(rule) if word in hit_words]

    def _find_keyword_positions(self, content: str, keyword_to_rules: dict) -> List[dict]:
        positions = []
        for keyword, rule_ids in keyword_to_rules.items():
            start = 0
            while True:
                idx = content.find(keyword, start)
                if idx == -1:
                    break
                positions.append(
                    {
                        "keyword": keyword,
                        "start": idx,
                        "end": idx + len(keyword),
                        "rule_ids": sorted(rule_ids),
                        "match_type": "exact",
                    }
                )
                start = idx + 1
        return sorted(positions, key=lambda item: (item["start"], item["end"]))

    def _gap_pattern(self, keyword: str, max_gap: int) -> str:
        chars = [re.escape(char) for char in keyword]
        if not chars:
            return ""
        return chars[0] + "".join(f".{{0,{max_gap}}}{char}" for char in chars[1:])

    def _adversarial_hits(self, content: str, hit_rules: List[Rule], max_gap: int = 2) -> List[dict]:
        normal_rule_keys = {(rule.rule_id, rule.name) for rule in hit_rules}
        hits = []
        normalized_content, index_map = self._normalized_with_map(content)

        for rule in self.rules:
            if (rule.rule_id, rule.name) in normal_rule_keys or rule.level.value != "L3":
                continue

            for keyword in self._keyword_values(rule):
                normalized_keyword = self._normalized_content(keyword)
                if len(normalized_keyword) < 3:
                    continue

                pattern = self._gap_pattern(normalized_keyword, max_gap)
                match = re.search(pattern, normalized_content, flags=re.IGNORECASE)
                if not match:
                    continue

                original_start = index_map[match.start()]
                original_end = index_map[match.end() - 1] + 1

                hits.append(
                    {
                        "keyword": keyword,
                        "normalized_keyword": normalized_keyword,
                        "matched_text": content[original_start:original_end],
                        "normalized_matched_text": match.group(0),
                        "start": original_start,
                        "end": original_end,
                        "max_gap": max_gap,
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "level": rule.level.value,
                    }
                )
                break

        return hits

    def check(self, content: str, scale: str = "standard") -> dict:
        cleaned_content = content.strip()
        normalized_content = self._normalized_content(cleaned_content)
        hit_words = keyword_index.search(cleaned_content) | keyword_index.search(normalized_content)

        hit_rules = [rule for rule in self.rules if self._rule_hits(cleaned_content, rule, hit_words)]
        adversarial_hits = self._adversarial_hits(cleaned_content, hit_rules)

        if adversarial_hits:
            existing_rule_keys = {(rule.rule_id, rule.name) for rule in hit_rules}
            adversarial_rule_keys = {
                (hit["rule_id"], hit["rule_name"]) for hit in adversarial_hits
            }
            hit_rules.extend(
                rule
                for rule in self.rules
                if (rule.rule_id, rule.name) in adversarial_rule_keys
                and (rule.rule_id, rule.name) not in existing_rule_keys
            )

        score_detail = score_with_detail(hit_rules)
        s = score_detail["score"]
        decision = decide(s, scale)

        labels = []
        keyword_to_rules = {}
        for rule in hit_rules:
            for label in rule.action.labels:
                if label not in labels:
                    labels.append(label)
            for keyword in self._matched_keywords(rule, hit_words):
                keyword_to_rules.setdefault(keyword, set()).add(rule.rule_id)

        hit_positions = self._find_keyword_positions(cleaned_content, keyword_to_rules)
        hit_positions.extend(
            {
                "keyword": hit["keyword"],
                "start": hit["start"],
                "end": hit["end"],
                "rule_ids": [hit["rule_id"]],
                "match_type": "adversarial_gap",
                "matched_text": hit["matched_text"],
                "max_gap": hit["max_gap"],
            }
            for hit in adversarial_hits
        )
        hit_positions = sorted(hit_positions, key=lambda item: (item["start"], item["end"]))

        hit_rule_items = [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "level": rule.level.value,
                "weight": rule.weight,
                "labels": rule.action.labels,
                "matched_keywords": self._matched_keywords(rule, hit_words),
            }
            for rule in hit_rules
        ]

        if hit_rules:
            names = "、".join(rule.name for rule in hit_rules)
            review_reason = f"{decision['review_reason']}，命中规则：{names}"
        else:
            review_reason = decision["review_reason"]

        trace = {
            "trace_id": f"TRACE{int(time.time() * 1000)}",
            "stages": [
                {
                    "stage": "input_received",
                    "title": "接收输入",
                    "status": "info",
                    "detail": f"收到待审核文本，长度 {len(content)}，审核尺度 {scale}",
                    "data": {"content_length": len(content), "scale": scale},
                },
                {
                    "stage": "preprocess",
                    "title": "文本预处理",
                    "status": "info",
                    "detail": "完成首尾空白清理、全半角归一、空白和符号移除",
                    "data": {
                        "cleaned_content": cleaned_content,
                        "normalized_content": normalized_content,
                    },
                },
                {
                    "stage": "keyword_scan",
                    "title": "关键词扫描",
                    "status": "success" if hit_words else "info",
                    "detail": f"命中 {len(hit_words)} 个关键词",
                    "data": {"hit_keywords": sorted(hit_words)},
                },
                {
                    "stage": "adversarial_check",
                    "title": "对抗扰动检测",
                    "status": "warning" if adversarial_hits else "success",
                    "detail": (
                        f"发现 {len(adversarial_hits)} 个疑似插字绕过"
                        if adversarial_hits
                        else "未发现疑似插字绕过"
                    ),
                    "data": {"adversarial_hits": adversarial_hits},
                },
                {
                    "stage": "rule_match",
                    "title": "规则匹配",
                    "status": "warning" if hit_rules else "success",
                    "detail": f"命中 {len(hit_rules)} 条规则",
                    "data": {"hit_rules": hit_rule_items},
                },
                {
                    "stage": "score",
                    "title": "风险打分",
                    "status": "warning" if s > 0 else "success",
                    "detail": (
                        f"基础权重 {score_detail['base_weight']}，"
                        f"额外命中 {score_detail['extra_hit_count']} 条，"
                        f"最终分数 {score_detail['score']}"
                    ),
                    "data": score_detail,
                },
                {
                    "stage": "decision",
                    "title": "三态判定",
                    "status": decision["decision"],
                    "detail": decision["decision_detail"]["reason"],
                    "data": decision["decision_detail"],
                },
                {
                    "stage": "final_action",
                    "title": "最终处理",
                    "status": decision["decision"],
                    "detail": {
                        "pass": "内容放行",
                        "review": "进入人工审核队列",
                        "reject": "内容拦截",
                    }[decision["decision"]],
                    "data": {"decision": decision["decision"]},
                },
            ],
        }

        return {
            "decision": decision["decision"],
            "risk_level": decision["risk_level"],
            "score": s,
            "labels": labels,
            "hit_rules": hit_rule_items,
            "hit_positions": hit_positions,
            "adversarial_hits": adversarial_hits,
            "score_detail": score_detail,
            "decision_detail": decision["decision_detail"],
            "trace": trace,
            "review_reason": review_reason,
        }
