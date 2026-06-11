# 广告识别规则引擎

这是把 `v1`、`v2` 和 `engine` 合并后的可运行版本：

- `engine/`：规则引擎核心，负责加载规则、关键词索引、匹配、打分和三态判定。
- `backend/`：FastAPI 接口服务，调用 `Engine.check(content, scale)`。
- `frontend/`：Vue 3 + Element Plus 管理界面。
- `v1/`、`v2/`：原始版本保留为参考。

## 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端默认运行在 `http://localhost:8000`，接口文档为 `http://localhost:8000/docs`。

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:3000`，并将 `/api` 代理到后端。

## API

合并版统一使用 `/api/v1`：

- `POST /api/v1/review`：提交内容识别。
- `GET /api/v1/review/history`：查看识别历史。
- `GET /api/v1/rules`：查看规则库。
- `GET /api/v1/manual/tasks`：查看人工审核任务。
- `POST /api/v1/manual/review`：提交人工审核结果。
- `GET /api/v1/stats`：查看统计数据。
- `GET /health`：健康检查。

## 引擎输出

```json
{
  "decision": "pass | review | reject",
  "risk_level": "low | medium | high",
  "score": 0.6,
  "labels": ["软广植入"],
  "hit_rules": [{ "rule_id": "BV_003", "name": "软广植入-产品推荐", "level": "L2" }],
  "review_reason": "分数处于人工审核区间，命中规则：软广植入-产品推荐"
}
```
