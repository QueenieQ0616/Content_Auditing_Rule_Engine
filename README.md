# 引擎骨架（W1 版本）

A 搭的第一周骨架。已跑通：输入文本 → 词库/正则匹配 → 分级打分 → 三态判定。
B 和 C 照着下面两个「约定」就能并行开工。

## 怎么跑

```bash
pip install -r requirements.txt

# 方式一：不起服务，直接测引擎
python tests/test_engine.py

# 方式二：起 API 服务
uvicorn api.main:app --reload
# 然后浏览器打开 http://127.0.0.1:8000/docs 直接点着测
```

## 目录

```
engine/
  models.py      # 规则数据结构  ← B 的「规则格式约定」在这
  matchers.py    # 匹配器(keyword/regex/length/model)
  scorer.py      # 打分 + 三态判定 + 三档尺度阈值
  rule_store.py  # 规则加载(热更新待做)
  engine.py      # 核心主流程  ← C 的「引擎输入输出约定」在这
api/
  main.py        # FastAPI 接口层  ← C 接着往下做
rules/
  advertisement.json # 示例规则  ← B 照这个格式写
tests/
  test_engine.py
```

## 约定一：规则格式（给 B）

规则写在 `rules/*.json`，一条规则长这样：

```json
{
  "rule_id": "BV_001",
  "name": "示例-营销推广导向",
  "level": "L2",                          // 危害等级 L1/L2/L3
  "weight": 0.6,                          // 权重，建议 L1≈0.3 L2≈0.6 L3≈0.9
  "logic": "OR",                          // AND=都命中 / OR=任一命中
  "conditions": [
    { "type": "keyword", "match": "any", "value": ["词A", "词B"] },
    { "type": "regex", "value": "正则" }
  ],
  "action": { "labels": ["营销推广"], "score": 0.6 }
}
```

B 主要就是往里加规则、扩充 `keyword` 的词表。词库可从 Sensitive-lexicon 拿来补充。

## 约定二：引擎输入输出（给 C）

引擎只有一个入口 `Engine.check(content, scale)`，返回：

```json
{
  "decision": "review",          // pass/review/reject 三态
  "risk_level": "medium",        // low/medium/high
  "score": 0.6,
  "labels": ["营销推广"],
  "hit_rules": [{"rule_id":"BV_001","name":"...","level":"L2"}],
  "review_reason": "分数处于人工审核区间"
}
```

C 的 API 直接把这个结构包成 HTTP 响应即可（`api/main.py` 已示范）。

## 还没做的（A 后续）

- [ ] 词库匹配换成 AC 自动机（pyahocorasick），现在是朴素 in 判断
- [ ] 规则热更新（改规则不重启）
- [ ] 多租户/业务的规则集筛选（现在所有规则都跑）
- [ ] 短路优化（命中高危即停）
```
