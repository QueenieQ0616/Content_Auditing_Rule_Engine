"""
规则加载器。负责从 rules/*.json 把规则读进内存。

本骨架先做最简单的「读文件 -> 转成 Rule 对象」。
TODO(A, W5): 加热更新——重新加载并原子替换内存里的规则集，不重启服务。
"""
import json
import os
from typing import List

from .models import Rule


def load_rules(rules_dir: str) -> List[Rule]:
    """读取目录下所有 .json 规则文件，返回 enabled 的规则列表。"""
    rules = []
    for fname in os.listdir(rules_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(rules_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            rule = Rule.from_dict(item)
            if rule.enabled:
                rules.append(rule)
    return rules
