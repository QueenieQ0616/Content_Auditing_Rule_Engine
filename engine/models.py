"""Rule data structures used by the moderation engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Level(str, Enum):
    """Risk level. L3 is highest, L1 is lowest."""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Logic(str, Enum):
    """How multiple conditions are combined."""

    AND = "AND"
    OR = "OR"


@dataclass
class Condition:
    type: str
    value: object
    match: str = "any"


@dataclass
class Action:
    labels: List[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class Rule:
    rule_id: str
    name: str
    level: Level
    weight: float
    conditions: List[Condition]
    action: Action
    domain: str = "bad_values"
    logic: Logic = Logic.AND
    enabled: bool = True

    @staticmethod
    def from_dict(d: dict) -> "Rule":
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
