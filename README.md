# Content Auditing Rule Engine

广告内容审核规则引擎。当前工程已经把原来的 `rules_and_test`、`v2` 和 `engine` 部分合并成一个可本地运行的完整项目。

## 项目结构

```text
engine_skeleton/
├── backend/              # FastAPI 后端服务
│   └── main.py
├── engine/               # 规则引擎核心
│   ├── engine.py         # Engine.check(content, scale)
│   ├── keyword_index.py  # 关键词索引，优先使用 AC 自动机
│   ├── matchers.py       # keyword / regex / length 匹配器
│   ├── models.py         # 规则数据结构
│   ├── rule_store.py     # 规则加载
│   ├── scorer.py         # 打分与三态判定
│   └── rules/            # 规则 JSON 文件
├── frontend/             # Vue 3 + Element Plus 前端
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── requirements.txt      # 后端 Python 依赖

```

## 环境准备

推荐使用单独的 conda 环境，不建议直接污染 `base`。
如果你已经有环境，直接激活即可：
安装后端依赖：

```powershell
cd engine_skeleton
python -m pip install -r requirements.txt
```

## 启动后端

本人在本地运行时后端使用 `8010` 端口：

```powershell
cd D:\engine_skeleton
conda activate D:\conda-envs\care
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

启动成功后访问：

```text
http://127.0.0.1:8010/docs
```

这里是 FastAPI 自动生成的接口文档，可以直接测试接口。

## 启动前端

另开一个 PowerShell：

```powershell
cd D:\engine_skeleton\frontend
npm install
npm.cmd run dev -- --host 127.0.0.1
```

前端启动后访问：

```text
http://127.0.0.1:3000
```

注意：前端代理配置在 `frontend/vite.config.js`，当前已经指向后端：

```js
target: 'http://localhost:8010'
```

如果你后端换了端口，需要同步修改这里。

## 核心接口

### 内容审核

```text
POST /api/v1/review
```

请求示例：

```json
{
  "content": "限时特惠，全网最低价，特价包邮，加微信下单",
  "scale": "standard",
  "biz_type": "default"
}
```

返回示例：

```json
{
  "request_id": "REQ1781161554292",
  "content": "限时特惠，全网最低价，特价包邮，加微信下单",
  "decision": "reject",
  "risk_level": "high",
  "score": 0.95,
  "labels": ["硬广推销"],
  "hit_rules": [
    {
      "rule_id": "BV_001",
      "name": "硬广推销-联系方式",
      "level": "L3"
    }
  ],
  "review_reason": "分数达到拦截阈值，命中规则：硬广推销-联系方式",
  "scale": "standard",
  "timestamp": "2026-06-11T15:05:54.292789"
}
```

### 其他接口

```text
GET    /api/v1/review/history
GET    /api/v1/rules
GET    /api/v1/manual/tasks
POST   /api/v1/manual/review
GET    /api/v1/stats
DELETE /api/v1/data/reset
GET    /health
```

## 判定结果说明

`decision` 有三种：

```text
pass    放行
review  转人工审核
reject  拦截
```

`risk_level` 有三种：

```text
low     低风险
medium  中风险
high    高风险
```

`scale` 有三种：

```text
loose     宽松
standard  标准
strict    严格
```

越严格越容易进入 `review` 或 `reject`。

## 规则文件

规则文件放在：

```text
engine/rules/
```

后端启动时会读取该目录下的 `.json` 文件。新增规则后，重启后端即可生效。

规则大致结构：

```json
{
  "rule_id": "BV_001",
  "name": "硬广推销-联系方式",
  "level": "L3",
  "weight": 0.9,
  "logic": "OR",
  "conditions": [
    {
      "type": "keyword",
      "value": ["加微信", "加VX", "微信号"]
    }
  ],
  "action": {
    "labels": ["硬广推销"],
    "score": 0.9
  }
}
```

## 常见问题

### 8000 端口被占用或无权限

可以直接使用 `8010`：

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

如果前端无法访问后端，检查 `frontend/vite.config.js` 的代理端口是否一致。

### npm install 找不到 package.json

说明你在根目录执行了 `npm install`。前端依赖要在 `frontend` 目录安装：

```powershell
cd D:\engine_skeleton\frontend
npm install
```

### PowerShell 不允许运行 npm.ps1

使用 `npm.cmd`：

```powershell
npm.cmd run dev -- --host 127.0.0.1
```

### 修改规则后没有生效

规则是在后端启动时加载的。修改 `engine/rules/*.json` 后，需要重启后端。
