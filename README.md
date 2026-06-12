# Content Auditing Rule Engine

广告识别规则引擎是一个前后端分离的内容审核演示系统，核心目标是识别文本中的硬广、软广、引流营销和疑似广告内容，并给出放行、转人工或拦截三态结果。项目同时提供人工审核、批量审核、命中过程可视化、账号注册登录和统计看板，适合用于规则引擎课程设计、原型展示和审核流程演示。

## 当前功能

- 文本广告识别：输入单条文本后返回 `pass`、`review`、`reject` 三态结果。
- 审核尺度选择：支持 `loose`、`standard`、`strict` 三种尺度。
- 规则命中解释：返回风险分数、风险等级、命中标签、命中规则、审核原因。
- 对抗样本识别：支持符号拆分和少量插字规避识别，例如 `强/烈/推/荐`、`床加前微明信月下光单`。
- 批量审核：支持粘贴多行文本或导入 `.txt` / `.csv` 文件，批量生成审核结果。
- 人工审核队列：`review` 结果会进入队列，审核员可以单独查看详情并提交人工判定。
- 单任务详情审核：完整展示长文本内容，并支持上一个 / 下一个任务切换。
- 命中过程展示：从审核历史中选择一条记录，以流程图形式展示输入、预处理、关键词扫描、规则匹配、打分和决策过程。
- 账号管理：支持注册、登录、登录态保存、退出登录和前端路由访问控制。
- 统计看板：展示审核总量、放行数、转人工数、拦截数和规则库信息。

## 项目结构

```text
content-moderation-engine/
├── backend/
│   └── main.py                 # FastAPI 后端服务
├── engine/
│   ├── engine.py               # Engine.check(content, scale)
│   ├── keyword_index.py        # 关键词索引与模糊命中
│   ├── matchers.py             # keyword / regex / length / model 匹配器
│   ├── models.py               # 规则数据结构
│   ├── rule_store.py           # 规则加载
│   ├── scorer.py               # 风险打分与三态判定
│   └── rules/                  # JSON 规则文件
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API 封装
│   │   ├── router/             # Vue Router
│   │   ├── views/              # 页面组件
│   │   ├── App.vue             # 主布局
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── test_texts_adversarial.csv
│   └── test_texts_adversarial.txt
├── tests/
│   ├── evaluate.py
│   ├── test_engine.py
│   └── test_set.csv
├── requirements.txt
└── README.md
```

## 环境准备

后端依赖使用 Python 安装：

```powershell
cd D:\project\content-moderation-engine
python -m pip install -r requirements.txt
```

前端依赖在 `frontend` 目录安装：

```powershell
cd D:\project\content-moderation-engine\frontend
npm install
```

## 启动项目

先启动后端服务：

```powershell
cd D:\project\content-moderation-engine
python backend/main.py
```

默认后端端口是 `8000`。启动成功后可以访问：

```text
http://localhost:8000/docs
http://localhost:8000/health
```

再启动前端服务：

```powershell
cd D:\project\content-moderation-engine\frontend
npm run dev
```

默认前端地址是：

```text
http://localhost:3000
```

前端代理配置位于 `frontend/vite.config.js`，当前指向：

```js
target: 'http://localhost:8000'
```

如果后端端口改变，需要同步修改该配置并重启前端服务。

## 首次使用

访问前端后会先进入登录页。当前账号系统使用内存存储，首次启动后需要注册一个账号。注册成功后会自动登录，并进入主系统。

当前账号体系适合本地演示：

- 用户数据保存在后端内存中。
- 后端重启后账号和登录会话会丢失。
- 密码不会明文存储，后端使用盐值和 SHA256 保存哈希。

如果需要用于正式场景，应接入数据库、完善密码策略、增加权限角色和审计日志。

## 页面说明

| 页面 | 路径 | 说明 |
|---|---|---|
| 登录注册 | `/login` | 注册账号、登录账号 |
| 内容审核 | `/` | 单条文本审核 |
| 批量审核 | `/batch` | 多条内容批量导入审核 |
| 人工队列 | `/manual` | 查看待人工处理任务 |
| 人工审核详情 | `/manual/:taskId` | 单条任务详情审核，支持上下切换 |
| 命中过程 | `/trace` | 从审核历史选择记录，展示流程图 |
| 统计看板 | `/stats` | 查看审核统计和规则库信息 |

## 核心接口

### 账号管理

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

注册或登录请求示例：

```json
{
  "username": "tester",
  "password": "123456"
}
```

返回示例：

```json
{
  "token": "token-string",
  "user": {
    "username": "tester",
    "created_at": "2026-06-12T10:00:00",
    "role": "user"
  }
}
```

### 单条审核

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

返回中的关键字段：

| 字段 | 说明 |
|---|---|
| `decision` | 三态结果：`pass`、`review`、`reject` |
| `risk_level` | 风险等级：`low`、`medium`、`high` |
| `score` | 风险分数，范围 `0` 到 `1` |
| `labels` | 命中标签 |
| `hit_rules` | 命中规则 |
| `hit_positions` | 关键词命中位置 |
| `adversarial_hits` | 对抗规避命中记录 |
| `score_detail` | 打分细节 |
| `decision_detail` | 阈值判定细节 |
| `trace` | 审核全过程数据 |
| `review_reason` | 审核原因 |

### 批量审核

```text
POST /api/v1/review/batch
```

请求示例：

```json
{
  "contents": [
    "今天天气很好，适合出去散步。",
    "加微信领取限时福利，直播间下单更优惠。",
    "强/烈/推/荐这款产品。"
  ],
  "scale": "standard",
  "biz_type": "default"
}
```

批量审核返回 `batch_id`、汇总统计和每条内容的审核结果。每条内容也会写入审核历史，因此可以在“命中过程”页面选择并查看流程图。

### 命中过程

```text
POST /api/v1/trace
GET  /api/v1/review/history
```

`/trace` 接口用于单独分析一段文本但不写入历史；前端“命中过程”页面主要使用 `/review/history`，直接展示已经审核过的记录。

### 人工审核

```text
GET  /api/v1/manual/tasks
GET  /api/v1/manual/tasks/{task_id}
POST /api/v1/manual/review
```

人工审核提交示例：

```json
{
  "task_id": "TASK1780000000000",
  "decision": "pass",
  "reviewer": "auditor",
  "comment": "人工确认可放行"
}
```

## 三态审核尺度

系统先根据命中规则计算风险分数，再按不同尺度使用不同阈值：

```python
SCALES = {
    "loose": {"low": 0.5, "high": 0.8},
    "standard": {"low": 0.35, "high": 0.7},
    "strict": {"low": 0.2, "high": 0.5},
}
```

判断逻辑：

| 结果 | 条件 | 含义 |
|---|---|---|
| `pass` | `score < low` | 放行 |
| `review` | `low <= score < high` | 转人工审核 |
| `reject` | `score >= high` | 拦截 |

`strict` 更容易转人工或拦截，`loose` 更容易放行，`standard` 适合作为默认策略。

## 规则与关键词

规则文件位于：

```text
engine/rules/
```

规则示例：

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

后端启动时加载规则。修改规则文件后，需要重启后端。

关键词匹配优先使用 Aho-Corasick 自动机。如果环境中没有 `pyahocorasick`，系统会退化为普通关键词包含匹配。项目还增加了文本归一化和模糊关键词匹配，用来识别常见规避写法：

| 规避方式 | 示例 | 可识别目标 |
|---|---|---|
| 符号拆分 | `强/烈/推/荐` | `强烈推荐` |
| 空格拆分 | `亲 测 好 用` | `亲测好用` |
| 插入少量无关字 | `床加前微明信月下光单` | `加微信` |

## 测试文本集

项目提供两个测试数据文件：

```text
data/test_texts_adversarial.csv
data/test_texts_adversarial.txt
```

`test_texts_adversarial.txt` 可以直接在前端“批量审核”页面导入。`test_texts_adversarial.csv` 包含样本类型、预期结果和说明，适合人工评估或后续自动化测试。

样本覆盖：

- 正常内容
- 硬广推销
- 软广植入
- 引流营销
- 疑似广告
- 符号拆分对抗样本
- 空格拆分对抗样本
- 插字规避对抗样本
- 混合规避样本

## 常见问题

### 前端一直报 Vite proxy error

通常是后端没有启动，或 `frontend/vite.config.js` 的代理端口和后端端口不一致。当前项目默认后端端口为 `8000`。

### 注册的账号重启后消失

当前账号系统使用内存存储。后端重启后，账号、Token、审核历史和人工队列都会清空。正式使用前需要接入数据库。

### 修改规则后没有生效

规则是在后端启动时加载的。修改 `engine/rules/*.json` 后，需要重启后端。

### npm run build 提示 chunk size 较大

这是 Vite 的打包体积提示，不影响运行。后续可以通过路由懒加载或手动分包优化。

## 后续可完善方向

- 接入数据库，持久化账号、审核历史、人工队列和规则配置。
- 增加管理员角色、权限控制和操作日志。
- 提供规则管理页面，支持在线新增、编辑和停用规则。
- 增加模型识别能力，用于识别更隐晦的软广和语义变体。
- 支持图片 OCR、视频标题、评论批量导入等更多审核来源。
- 增加自动化评估脚本，输出准确率、召回率和误判样本分析。
