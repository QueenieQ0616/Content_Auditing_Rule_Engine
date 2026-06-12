"""Rule loader for JSON rules."""

import json
import os
from typing import List

from .models import Rule


def load_rules(rules_dir: str) -> List[Rule]:
    rules: List[Rule] = []
    if not os.path.isdir(rules_dir):
        return rules

    for filename in sorted(os.listdir(rules_dir)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(rules_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get("rules", [])
        for item in items:
            rule = Rule.from_dict(item)
            if rule.enabled:
                rules.append(rule)
    return rules
