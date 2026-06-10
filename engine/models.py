"""
规则数据结构定义 —— 这是给 B 的「规则格式约定」。
B 写规则、攒词库时，规则 JSON 必须符合这里定义的结构。

一条规则 = 条件(conditions) + 逻辑(logic) + 动作(action)
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Level(str, Enum):
    """危害等级。L3 最严重，L1 最轻。"""
    L1 = "L1"  # 低危：擦边、疑似
    L2 = "L2"  # 中危：需结合上下文
    L3 = "L3"  # 高危：明确严重


class Logic(str, Enum):
    """多个条件之间的组合方式。"""
    AND = "AND"  # 所有条件都命中，规则才命中
    OR = "OR"    # 任一条件命中即命中


@dataclass
class Condition:
    """
    单个判断条件。
    type 决定用哪种匹配器来判断：
      - keyword : 词库/关键词匹配（B 提供词表）
      - regex   : 正则匹配
      - length  : 长度/数量特征
      - model   : 模型打分（预留，本期不实现）
    """
    type: str                          # keyword / regex / length / model
    value: object                      # keyword: List[str]; regex: str; length: int
    match: str = "any"                 # keyword 专用：any=命中任一即可, all=全部命中


@dataclass
class Action:
    """规则命中后产生的结果。"""
    labels: List[str] = field(default_factory=list)  # 风险标签，如 ["低俗审丑"]
    score: float = 0.0                                # 该规则的分数贡献（一般等于 weight）


@dataclass
class Rule:
    """一条完整的规则。对应 rules/*.json 里的一个对象。"""
    rule_id: str
    name: str
    level: Level
    weight: float                      # 权重，用于打分，建议与 level 对应
    conditions: List[Condition]
    action: Action
    domain: str = "bad_values"         # 产域，本期固定不良价值观
    logic: Logic = Logic.AND
    enabled: bool = True

    @staticmethod
    def from_dict(d: dict) -> "Rule":
        """从 JSON 字典构造 Rule 对象。"""
        return Rule(
            rule_id=d["rule_id"],
            name=d["name"],
            level=Level(d.get("level", "L1")),
            weight=float(d.get("weight", 0.3)),
            conditions=[Condition(**c) for c in d["conditions"]],
            action=Action(**d.get("action", {})),
            domain=d.get("domain", "bad_values"),
            logic=Logic(d.get("logic", "AND")),
            enabled=d.get("enabled", True),
        )
