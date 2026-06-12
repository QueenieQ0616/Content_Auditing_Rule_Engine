# 广告识别规则引擎 API 文档

## 文档信息

| 项目 | 内容 |
|---|---|
| 服务名称 | 广告识别规则引擎 API |
| 当前版本 | `2.0.0` |
| 后端框架 | FastAPI |
| 默认服务地址 | `http://localhost:8000` |
| API 前缀 | `/api/v1` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

## 接口约定

所有业务接口默认使用 JSON 请求体和 JSON 响应体。

```http
Content-Type: application/json
```

登录后访问需要身份信息的接口时，客户端通过请求头传递 Token：

```http
Authorization: Bearer <token>
```

当前版本中，账号、登录会话、审核历史和人工审核队列均保存在后端内存中。后端服务重启后，这些运行时数据会清空。

## 通用错误格式

FastAPI 默认错误响应格式如下：

```json
{
  "detail": "错误说明"
}
```

常见状态码：

| 状态码 | 含义 | 常见场景 |
|---|---|---|
| `200` | 请求成功 | 查询、登录、审核成功 |
| `400` | 请求参数或业务状态错误 | 用户名已存在、任务已处理、批量内容为空 |
| `401` | 未认证或认证失败 | 登录失败、Token 无效 |
| `404` | 资源不存在 | 人工审核任务不存在 |
| `422` | 请求体校验失败 | 字段缺失、枚举值不合法、长度不符合要求 |

## 核心枚举

### 审核结果

| 值 | 含义 |
|---|---|
| `pass` | 放行 |
| `review` | 转人工审核 |
| `reject` | 拦截 |

### 审核尺度

| 值 | 含义 |
|---|---|
| `loose` | 宽松 |
| `standard` | 标准 |
| `strict` | 严格 |

### 风险等级

| 值 | 含义 |
|---|---|
| `low` | 低风险 |
| `medium` | 中风险 |
| `high` | 高风险 |

## 数据模型

### AuthRequest

账号注册和登录请求体。

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| `username` | string | 是 | 3 到 32 位；支持中文、字母、数字、下划线、短横线 | 用户名 |
| `password` | string | 是 | 6 到 64 位 | 密码 |

示例：

```json
{
  "username": "tester",
  "password": "123456"
}
```

### ContentRequest

单条审核和命中过程分析请求体。

| 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|---|---|---|---|---|---|
| `content` | string | 是 | 无 | 1 到 10000 字符 | 待审核文本 |
| `scale` | string | 否 | `standard` | `loose`、`standard`、`strict` | 审核尺度 |
| `biz_type` | string | 否 | `default` | 无 | 业务类型 |

示例：

```json
{
  "content": "限时特惠，全网最低价，特价包邮，加微信下单。",
  "scale": "standard",
  "biz_type": "default"
}
```

### BatchReviewRequest

批量审核请求体。

| 字段 | 类型 | 必填 | 默认值 | 约束 | 说明 |
|---|---|---|---|---|---|
| `contents` | string[] | 是 | 无 | 1 到 500 条 | 待审核文本列表 |
| `scale` | string | 否 | `standard` | `loose`、`standard`、`strict` | 审核尺度 |
| `biz_type` | string | 否 | `default` | 无 | 业务类型 |

示例：

```json
{
  "contents": [
    "今天天气很好，适合出去散步。",
    "加微信领取限时福利，直播间下单更优惠。"
  ],
  "scale": "standard",
  "biz_type": "default"
}
```

### ManualReviewRequest

人工审核提交请求体。

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| `task_id` | string | 是 | 无 | 人工审核任务 ID |
| `decision` | string | 是 | `pass`、`review`、`reject` | 人工判定结果 |
| `reviewer` | string | 是 | 最少 1 字符 | 审核员名称 |
| `comment` | string | 否 | 无 | 审核意见 |

示例：

```json
{
  "task_id": "TASK1780000000000",
  "decision": "pass",
  "reviewer": "auditor",
  "comment": "人工确认可放行"
}
```

### ReviewResult

单条审核结果核心字段。

| 字段 | 类型 | 说明 |
|---|---|---|
| `request_id` | string | 请求 ID |
| `content` | string | 原始待审核内容 |
| `scale` | string | 审核尺度 |
| `biz_type` | string | 业务类型 |
| `timestamp` | string | 审核时间 |
| `decision` | string | 三态审核结果 |
| `risk_level` | string | 风险等级 |
| `score` | number | 风险分数，范围 `0` 到 `1` |
| `labels` | string[] | 命中标签 |
| `hit_rules` | object[] | 命中规则列表 |
| `hit_positions` | object[] | 关键词命中位置 |
| `adversarial_hits` | object[] | 对抗规避命中记录 |
| `score_detail` | object | 打分细节 |
| `decision_detail` | object | 阈值判定细节 |
| `trace` | object | 规则命中全过程 |
| `review_reason` | string | 审核原因 |
| `batch_id` | string | 批次 ID，仅批量审核返回 |
| `batch_index` | number | 批次内序号，仅批量审核返回 |

## 健康检查

### GET /health

检查后端服务是否正常运行。

#### 请求参数

无。

#### 响应示例

```json
{
  "status": "healthy",
  "timestamp": "2026-06-12T10:00:00.000000"
}
```

## 账号管理

### POST /api/v1/auth/register

注册账号。注册成功后会直接返回 Token 和用户信息。

#### 请求体

`AuthRequest`

#### 响应示例

```json
{
  "token": "V9g1p7...",
  "user": {
    "username": "tester",
    "created_at": "2026-06-12T10:00:00.000000",
    "role": "user"
  }
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `400` | 用户名已存在 |
| `422` | 用户名或密码不符合格式 |

### POST /api/v1/auth/login

登录账号。登录成功后返回 Token 和用户信息。

#### 请求体

`AuthRequest`

#### 响应示例

```json
{
  "token": "V9g1p7...",
  "user": {
    "username": "tester",
    "created_at": "2026-06-12T10:00:00.000000",
    "role": "user"
  }
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `401` | 用户名或密码错误 |
| `422` | 请求体格式不合法 |

### GET /api/v1/auth/me

获取当前登录用户信息。

#### 请求头

```http
Authorization: Bearer <token>
```

#### 响应示例

```json
{
  "user": {
    "username": "tester",
    "created_at": "2026-06-12T10:00:00.000000",
    "role": "user"
  }
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `401` | 未登录或登录已过期 |

### POST /api/v1/auth/logout

退出登录。服务端会删除当前 Token 对应的会话。

#### 请求头

```http
Authorization: Bearer <token>
```

#### 响应示例

```json
{
  "message": "已退出登录"
}
```

## 内容审核

### POST /api/v1/review

对单条文本执行广告识别。该接口会写入审核历史；如果结果为 `review`，会同时写入人工审核队列。

#### 请求体

`ContentRequest`

#### 响应示例

```json
{
  "request_id": "REQ1780000000000",
  "content": "限时特惠，全网最低价，特价包邮，加微信下单。",
  "scale": "standard",
  "biz_type": "default",
  "timestamp": "2026-06-12T10:00:00.000000",
  "decision": "reject",
  "risk_level": "high",
  "score": 0.9,
  "labels": ["硬广推销"],
  "hit_rules": [
    {
      "rule_id": "BV_001",
      "name": "硬广推销-联系方式",
      "level": "L3"
    }
  ],
  "hit_positions": [],
  "adversarial_hits": [],
  "score_detail": {},
  "decision_detail": {},
  "trace": {},
  "review_reason": "命中高危广告规则，建议拦截"
}
```

实际响应中的 `hit_positions`、`score_detail`、`decision_detail` 和 `trace` 会根据引擎命中情况返回具体内容。

#### 错误码

| 状态码 | 说明 |
|---|---|
| `422` | `content` 为空、超长，或 `scale` 不合法 |

### POST /api/v1/review/batch

批量审核多条文本。每条内容都会写入审核历史；结果为 `review` 的内容会进入人工审核队列。

#### 请求体

`BatchReviewRequest`

#### 响应示例

```json
{
  "batch_id": "BATCH1780000000000",
  "total": 2,
  "summary": {
    "pass_count": 1,
    "review_count": 0,
    "reject_count": 1
  },
  "items": [
    {
      "request_id": "REQ1780000000001",
      "content": "今天天气很好，适合出去散步。",
      "scale": "standard",
      "biz_type": "default",
      "timestamp": "2026-06-12T10:00:00.000000",
      "decision": "pass",
      "risk_level": "low",
      "score": 0,
      "labels": [],
      "hit_rules": [],
      "review_reason": "未命中广告规则，予以放行",
      "batch_id": "BATCH1780000000000",
      "batch_index": 1
    }
  ]
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `400` | 批量内容不能为空 |
| `422` | `contents` 超过 500 条，或 `scale` 不合法 |

### POST /api/v1/trace

分析单条文本的命中过程。该接口不会写入审核历史，也不会写入人工审核队列。

#### 请求体

`ContentRequest`

#### 响应示例

```json
{
  "content": "强/烈/推/荐这款产品，亲/测/好/用。",
  "scale": "standard",
  "timestamp": "2026-06-12T10:00:00.000000",
  "decision": "review",
  "risk_level": "medium",
  "score": 0.6,
  "labels": ["软广植入"],
  "hit_rules": [
    {
      "rule_id": "BV_003",
      "name": "软广植入-产品推荐",
      "level": "L2"
    }
  ],
  "hit_positions": [],
  "adversarial_hits": [],
  "score_detail": {},
  "decision_detail": {},
  "trace": {
    "stages": []
  },
  "review_reason": "分数处于人工审核区间"
}
```

### GET /api/v1/review/history

获取审核历史。

#### Query 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `limit` | number | 否 | `50` | 返回条数 |
| `offset` | number | 否 | `0` | 起始偏移 |

#### 请求示例

```http
GET /api/v1/review/history?limit=20&offset=0
```

#### 响应示例

```json
{
  "total": 2,
  "items": [
    {
      "request_id": "REQ1780000000000",
      "content": "加微信下单。",
      "decision": "reject",
      "risk_level": "high",
      "score": 0.9,
      "labels": ["硬广推销"],
      "hit_rules": [],
      "timestamp": "2026-06-12T10:00:00.000000"
    }
  ]
}
```

## 规则管理

### GET /api/v1/rules

获取当前公开规则列表。该接口返回规则 ID、规则名称、规则等级、风险等级、标签和关键词。

#### 响应示例

```json
{
  "rules": [
    {
      "rule_id": "BV_001",
      "name": "硬广推销-联系方式",
      "level": "L3",
      "risk_level": "high",
      "label": "硬广推销",
      "keywords": ["加微信", "加VX", "微信号"]
    }
  ]
}
```

## 人工审核

### GET /api/v1/manual/tasks

获取人工审核任务列表。

#### Query 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `status` | string | 否 | `pending` | `pending`、`approved`、`rejected`、`all` |

#### 请求示例

```http
GET /api/v1/manual/tasks?status=pending
```

#### 响应示例

```json
{
  "total": 1,
  "tasks": [
    {
      "task_id": "TASK1780000000000",
      "content": "强烈推荐这款面霜，亲测好用。",
      "machine_decision": "review",
      "machine_score": 0.6,
      "hit_rules": [
        {
          "rule_id": "BV_003",
          "name": "软广植入-产品推荐",
          "level": "L2"
        }
      ],
      "status": "pending",
      "created_at": "2026-06-12T10:00:00.000000",
      "reviewed_at": null,
      "reviewer": null,
      "review_decision": null,
      "review_comment": null
    }
  ]
}
```

### GET /api/v1/manual/tasks/{task_id}

获取单个人工审核任务详情。

#### Path 参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | 是 | 人工审核任务 ID |

#### 响应示例

```json
{
  "task_id": "TASK1780000000000",
  "content": "强烈推荐这款面霜，亲测好用。",
  "machine_decision": "review",
  "machine_score": 0.6,
  "hit_rules": [],
  "hit_positions": [],
  "adversarial_hits": [],
  "score_detail": {},
  "decision_detail": {},
  "trace": {},
  "status": "pending",
  "created_at": "2026-06-12T10:00:00.000000",
  "reviewed_at": null,
  "reviewer": null,
  "review_decision": null,
  "review_comment": null,
  "batch_id": null
}
```

#### 错误码

| 状态码 | 说明 |
|---|---|
| `404` | 任务不存在 |

### POST /api/v1/manual/review

提交人工审核结果。

#### 请求体

`ManualReviewRequest`

#### 响应示例

```json
{
  "task_id": "TASK1780000000000",
  "status": "approved",
  "decision": "pass",
  "reviewer": "auditor",
  "reviewed_at": "2026-06-12T10:05:00.000000"
}
```

#### 状态变化

| `decision` | 任务状态变化 |
|---|---|
| `pass` | `approved` |
| `reject` | `rejected` |
| `review` | 保持 `pending` |

#### 错误码

| 状态码 | 说明 |
|---|---|
| `400` | 任务已被处理 |
| `404` | 任务不存在 |
| `422` | 请求体格式不合法 |

## 统计与数据管理

### GET /api/v1/stats

获取审核统计。

#### 响应示例

```json
{
  "total_reviews": 100,
  "pass_count": 40,
  "review_count": 35,
  "reject_count": 25,
  "pending_manual": 12,
  "pass_rate": 0.4,
  "reject_rate": 0.25
}
```

### DELETE /api/v1/data/reset

清空运行时审核历史和人工审核队列。该接口不会清空账号和登录会话。

#### 响应示例

```json
{
  "message": "数据已清空",
  "cleared_reviews": 100,
  "cleared_manual_tasks": 12
}
```

## 调用示例

### 注册并审核

```powershell
$body = @{
  username = "tester"
  password = "123456"
} | ConvertTo-Json

$auth = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body $body

$token = $auth.token

$reviewBody = @{
  content = "限时特惠，全网最低价，特价包邮，加微信下单。"
  scale = "standard"
  biz_type = "default"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/review" `
  -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $token" } `
  -Body $reviewBody
```

### 批量审核

```powershell
$body = @{
  contents = @(
    "今天天气很好，适合出去散步。"
    "加微信领取限时福利，直播间下单更优惠。"
  )
  scale = "standard"
  biz_type = "default"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/review/batch" `
  -ContentType "application/json" `
  -Body $body
```

## 说明

当前接口服务以演示和课程项目为主，后端未对所有业务接口强制校验 Token，主要由前端路由控制页面访问。若后续用于正式环境，建议补充后端鉴权依赖，将审核、规则、人工审核、统计和数据清空接口全部纳入权限控制，并将用户、审核记录、人工任务和规则配置持久化到数据库。
