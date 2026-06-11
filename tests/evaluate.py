import csv
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path，以便导入 engine 中的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.models import Rule
from engine.matchers import run_condition
from engine.scorer import score, decide

class FixedEngine:
    """只加载指定 JSON 规则文件的引擎，不扫描目录"""
    def __init__(self, rules_json_path):
        with open(rules_json_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        self.rules = []
        for item in rules_data:
            rule = Rule.from_dict(item)
            if rule.enabled:
                self.rules.append(rule)
        print(f"已加载 {len(self.rules)} 条规则（来自 {rules_json_path}）")

    def _rule_hits(self, content, rule):
        results = [run_condition(content, c) for c in rule.conditions]
        if rule.logic == "OR":
            return any(results)
        return all(results)

    def check(self, content, scale="standard"):
        hit_rules = [r for r in self.rules if self._rule_hits(content, r)]
        s = round(score(hit_rules), 4)
        result = decide(s, scale)
        hit_detail = [
            {"rule_id": r.rule_id, "name": r.name, "level": r.level.value}
            for r in hit_rules
        ]
        labels = sorted({label for r in hit_rules for label in r.action.labels})
        return {
            "decision": result["decision"],
            "risk_level": result["risk_level"],
            "score": s,
            "labels": labels,
            "hit_rules": hit_detail,
            "review_reason": result["review_reason"],
        }

def load_test_set(csv_path):
    texts, expected = [], []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row['text'])
            expected.append(row['expected'])
    return texts, expected

def evaluate(engine, test_csv, scale='standard'):
    texts, expected = load_test_set(test_csv)
    predicted = [engine.check(t, scale=scale)['decision'] for t in texts]

    tp = fp = fn = tn = 0
    for exp, pred in zip(expected, predicted):
        if exp == 'reject' and pred == 'reject':
            tp += 1
        elif exp == 'reject' and pred != 'reject':
            fn += 1
        elif exp != 'reject' and pred == 'reject':
            fp += 1
        elif exp != 'reject' and pred != 'reject':
            tn += 1

    precision = tp / (tp + fp) if (tp+fp) else 0
    recall = tp / (tp + fn) if (tp+fn) else 0
    f1 = 2 * precision * recall / (precision+recall) if (precision+recall) else 0

    print(f"尺度: {scale}")
    print(f"拦截精准率: {precision:.2f}, 召回率: {recall:.2f}, F1: {f1:.2f}")
    print(f"TP={tp}, FP={fp}, FN={fn}, TN={tn}")

    errors = [(t, e, p) for t, e, p in zip(texts, expected, predicted) if e != p]
    print(f"\n错误样本数: {len(errors)}")
    for err in errors:
        print(f"  文本: {err[0][:50]}... | 期望: {err[1]} | 预测: {err[2]}")
    return precision, recall

if __name__ == '__main__':
    # 固定 JSON 规则文件路径（请根据实际位置修改）
    RULES_JSON = os.path.join(os.path.dirname(__file__), '..', 'rules', 'advertising.json')
    # 测试集路径
    TEST_CSV = os.path.join(os.path.dirname(__file__), 'test_set.csv')

    if not os.path.exists(RULES_JSON):
        print(f"错误：找不到规则文件 {RULES_JSON}")
        sys.exit(1)
    if not os.path.exists(TEST_CSV):
        print(f"错误：找不到测试集文件 {TEST_CSV}")
        sys.exit(1)

    engine = FixedEngine(RULES_JSON)
    # evaluate(engine, TEST_CSV, scale='standard')
    # 可取消注释测试其他尺度
    evaluate(engine, TEST_CSV, scale='loose')
    # evaluate(engine, TEST_CSV, scale='strict')