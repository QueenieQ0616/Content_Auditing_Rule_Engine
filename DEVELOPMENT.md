# 开发文档

本文档面向继续开发或接入本项目的人，说明项目结构、核心流程、规则引擎实现、API 调用方式和后续扩展方向。

## 1. 项目概览

本项目是一个基于规则引擎的广告内容审核系统，主要能力是识别文本中的硬广、软广、引流、疑似广告等风险内容，并输出三态审核结果：

```text
pass    放行
review  转人工审核
reject  拦截
```

当前主工程由三部分组成：

```text
frontend  前端审核后台
backend   FastAPI 接口服务
engine    规则引擎核心
```

整体调用链路：

```text
用户输入文本
  -> frontend 提交请求
  -> backend 接收 API 请求
  -> engine 加载规则并匹配文本
  -> scorer 计算分数并判定结果
  -> backend 返回结构化结果
  -> frontend 展示审核结果
```

## 2. 目录结构

```text
engine_skeleton/
├── backend/
│   ├── main.py              # FastAPI 后端入口
│   └── requirements.txt     # 后端依赖
├── engine/
│   ├── __init__.py
│   ├── engine.py            # Engine.check 主流程
│   ├── keyword_index.py     # 关键词索引，支持 pyahocorasick
│   ├── matchers.py          # 条件匹配器
│   ├── models.py            # 规则数据结构
│   ├── rule_store.py        # 规则加载器
│   ├── scorer.py            # 打分和三态判定
│   └── rules/               # 规则 JSON 文件
├── frontend/
│   ├── src/
│   │   ├── api/             # 前端接口封装
│   │   ├── router/          # 页面路由
│   │   └── views/           # 页面组件
│   ├── package.json
│   └── vite.config.js
├── requirements.txt         # 根目录后端依赖
├── v1/                      # 历史版本，保留参考
└── v2/                      # 历史版本，保留参考
```

当前实际运行的是根目录下的 `backend/`、`frontend/` 和 `engine/`。`v1/`、`v2/` 只作为历史版本参考。

## 3. 本地开发环境

### 3.1 后端环境

推荐使用独立 conda 环境：

```powershell
conda create -n care python=3.12 -y
conda activate D:\conda-envs\care
```

安装依赖：

```powershell
cd D:\engine_skeleton
python -m pip install -r requirements.txt
```

启动后端：

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

接口文档：

```text
http://127.0.0.1:8010/docs
```

### 3.2 前端环境

另开一个 PowerShell：

```powershell
cd D:\engine_skeleton\frontend
npm install
npm.cmd run dev -- --host 127.0.0.1
```

前端访问地址：

```text
http://127.0.0.1:3000
```

前端开发代理配置在 `frontend/vite.config.js`：

```js
proxy: {
  '/api': {
    target: 'http://localhost:8010',
    changeOrigin: true
  }
}
```

如果后端端口变化，需要同步修改 `target`。

## 4. 后端实现说明

后端入口：

```text
backend/main.py
```

启动时会初始化规则引擎：

```python
engine = Engine()
```

核心接口：

```python
@app.post("/api/v1/review")
async def review_content(request: ContentRequest):
    result = engine.check(request.content, request.scale)
```

后端主要职责：

```text
1. 接收前端或外部系统请求
2. 调用 engine.check(content, scale)
3. 包装返回结果
4. 维护运行时审核历史 review_history
5. 维护运行时人工审核队列 manual_queue
6. 提供统计、规则查询、人工审核接口
```

当前 `review_history` 和 `manual_queue` 都是内存列表，服务重启后会清空。后续如果要做生产化，应接入数据库。

## 5. 规则引擎实现说明

规则引擎入口：

```text
engine/engine.py
```

核心方法：

```python
Engine.check(content: str, scale: str = "standard") -> dict
```

执行流程：

```text
1. Engine 初始化时从 engine/rules/ 加载规则
2. 收集所有 keyword 条件中的关键词
3. 构建 KeywordIndex
4. check() 调用时先扫描文本，得到 hit_words
5. 遍历所有规则，判断每条规则是否命中
6. 收集 hit_rules
7. scorer.score(hit_rules) 计算风险分数
8. scorer.decide(score, scale) 输出三态判定
9. 返回 decision、risk_level、score、labels、hit_rules、review_reason
```

### 5.1 规则加载

规则加载逻辑在：

```text
engine/rule_store.py
```

它读取：

```text
engine/rules/*.json
```

并将 JSON 数据转换成 `Rule` 对象。

### 5.2 规则模型

规则数据结构定义在：

```text
engine/models.py
```

主要模型：

```text
Rule       一条完整规则
Condition  单个匹配条件
Action     命中后的标签和分数信息
Level      L1 / L2 / L3
Logic      AND / OR
```

### 5.3 匹配器

匹配器定义在：

```text
engine/matchers.py
```

当前支持：

```text
keyword  关键词匹配
regex    正则匹配
length   文本长度匹配
model    模型匹配预留，目前恒为 False
```

### 5.4 关键词索引

关键词索引在：

```text
engine/keyword_index.py
```

如果安装了 `pyahocorasick`，会优先使用 AC 自动机进行多关键词匹配。否则退回普通字符串匹配。

### 5.5 打分与判定

打分和判定逻辑在：

```text
engine/scorer.py
```

当前打分公式：

```text
score = min(1.0, 最高命中规则权重 + 0.05 * 额外命中规则数)
```

三档审核尺度：

```python
SCALES = {
    "loose": {"low": 0.5, "high": 0.8},
    "standard": {"low": 0.35, "high": 0.7},
    "strict": {"low": 0.2, "high": 0.5},
}
```

判定规则：

```text
score < low          -> pass
low <= score < high  -> review
score >= high        -> reject
```

## 6. 规则文件格式

规则文件放在：

```text
engine/rules/
```

支持单个 JSON 文件中保存数组形式的规则列表。

示例：

```json
{
  "rule_id": "BV_001",
  "name": "硬广推销-联系方式",
  "level": "L3",
  "weight": 0.9,
  "logic": "OR",
  "enabled": true,
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

字段说明：

```text
rule_id     规则唯一 ID
name        规则名称
level       风险等级，L1 / L2 / L3
weight      规则权重，用于计算风险分数
logic       条件组合方式，AND / OR
enabled     是否启用
conditions  匹配条件列表
action      命中后的标签和分数信息
```

新增或修改规则后，需要重启后端服务。

## 7. API 调用说明

### 7.1 内容审核

接口：

```text
POST /api/v1/review
```

完整本地地址：

```text
http://127.0.0.1:8010/api/v1/review
```

请求体：

```json
{
  "content": "限时特惠，全网最低价，特价包邮，加微信下单",
  "scale": "standard",
  "biz_type": "default"
}
```

返回体：

```json
{
  "request_id": "REQ1781161554292",
  "content": "限时特惠，全网最低价，特价包邮，加微信下单",
  "scale": "standard",
  "timestamp": "2026-06-11T15:05:54.292789",
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
  "review_reason": "分数达到拦截阈值，命中规则：硬广推销-联系方式"
}
```

### 7.2 PowerShell 调用示例

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8010/api/v1/review" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"content":"限时特惠，全网最低价，加微信下单","scale":"standard","biz_type":"default"}'
```

### 7.3 Python 调用示例

```python
import requests

url = "http://127.0.0.1:8010/api/v1/review"
payload = {
    "content": "强烈推荐这款产品，亲测好用，安利给大家",
    "scale": "standard",
    "biz_type": "default",
}

resp = requests.post(url, json=payload)
print(resp.json())
```

### 7.4 其他接口

```text
GET    /api/v1/review/history   获取审核历史
GET    /api/v1/rules            获取规则列表
GET    /api/v1/manual/tasks     获取人工审核任务
POST   /api/v1/manual/review    提交人工审核结果
GET    /api/v1/stats            获取统计数据
DELETE /api/v1/data/reset       清空运行时数据
GET    /health                  健康检查
```

## 8. 前端实现说明

前端使用 Vue 3 + Element Plus + Vite。

主要文件：

```text
frontend/src/App.vue
frontend/src/main.js
frontend/src/router/index.js
frontend/src/api/index.js
frontend/src/views/ReviewPage.vue
frontend/src/views/ManualQueue.vue
frontend/src/views/StatsPage.vue
```

页面说明：

```text
ReviewPage.vue   内容审核页面
ManualQueue.vue  人工审核队列页面
StatsPage.vue    统计看板页面
```

接口封装：

```text
frontend/src/api/index.js
```

示例：

```js
export const reviewContent = (data) => api.post('/review', data)
export const getManualTasks = (status = 'pending') => api.get('/manual/tasks', { params: { status } })
export const getStatistics = () => api.get('/stats')
```

## 9. 开发注意事项

### 9.1 不要提交运行缓存

不要提交：

```text
__pycache__/
*.pyc
node_modules/
dist/
*-server.log
```

这些已在 `.gitignore` 中配置。

### 9.2 规则修改后要重启后端

当前规则只在后端启动时加载。修改 `engine/rules/*.json` 后，需要重启后端。

### 9.3 前后端端口要一致

如果后端不是 `8010`，需要修改：

```text
frontend/vite.config.js
```

确保 `target` 指向正确的后端地址。

### 9.4 运行时数据不会持久化

当前审核历史和人工审核队列存在内存中。后端重启后会清空。

## 10. 后续优化方向

推荐优先优化：

```text
1. 数据库持久化
2. 规则热加载
3. 规则管理后台
4. 命中词位置返回和前端高亮
5. 测试集评估脚本
6. 统计图表增强
7. 文本归一化，处理空格、符号、谐音、变体词
8. Docker 部署
```

其中最适合当前阶段做的是：

```text
规则热加载
命中词高亮
测试集评估
```

这三项改动范围相对可控，同时展示效果比较明显。
