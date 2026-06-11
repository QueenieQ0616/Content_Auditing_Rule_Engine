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
    "今天高数课讲了微分方程，有点难",                          # 干净 -> pass
    "这款面膜真的超好用，推荐给大家",                  # 命中 BV_001 L2 -> review
    "微信--Ch5888sy 只要本科学历，你就来拿钱",                        # 命中 BV_003 L3 -> reject
    "想赚钱的可以加我，资料免费领",                              # 命中三条 -> 看分数
    "导员让转发的，还没进群的学弟学妹抓紧进一下务必进群，需要统计人数"
]

print(f"已加载规则数: {len(eng.rules)}\n")
for s in samples:
    r = eng.check(s, scale="standard")
    print(f"输入: {s}")
    print(f"  -> 判定={r['decision']} 分数={r['score']} 标签={r['labels']} "
          f"命中={[h['rule_id'] for h in r['hit_rules']]}")
    print()
