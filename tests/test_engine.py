"""
不启服务，直接测引擎核心。跑: python tests/test_engine.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import Engine

RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "rules")
eng = Engine(RULES_DIR)

samples = [
    "今天天气真好，出去散步",                          # 干净 -> pass
    "我觉得女生还是干得好不如嫁得好",                  # 命中 BV_001 L2 -> review
    "这种暴力歧视的言论真恶心",                        # 命中 BV_003 L3 -> reject
    "又拜金又审丑的内容",                              # 命中两条 -> 看分数
]

print(f"已加载规则数: {len(eng.rules)}\n")
for s in samples:
    r = eng.check(s, scale="standard")
    print(f"输入: {s}")
    print(f"  -> 判定={r['decision']} 分数={r['score']} 标签={r['labels']} "
          f"命中={[h['rule_id'] for h in r['hit_rules']]}")
    print()
