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
    "限时优惠，全场五折",                              # L1 营销 -> 看分数
    "有需要的加微信 abc12345 详聊",                    # L3 微信引流 -> reject
    "诚招代理，扫码加入，全网最低价",                  # 多命中 -> 看分数
    "联系电话 13800138000",                            # L2 手机号 -> review
]

print(f"已加载规则数: {len(eng.rules)}\n")
for s in samples:
    r = eng.check(s, scale="standard")
    print(f"输入: {s}")
    print(f"  -> 判定={r['decision']} 分数={r['score']} 标签={r['labels']} "
          f"命中={[h['rule_id'] for h in r['hit_rules']]}")
    print()
