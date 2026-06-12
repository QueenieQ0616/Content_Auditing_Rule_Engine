# 开发文档

本文档面向继续开发、调试或接入本项目的同学。内容包括项目结构、开发环境准备、启动方式、核心模块说明、规则格式、API 调用、测试与常见问题。

## 1. 项目概览

本项目是一个基于规则引擎的内容审核系统，主要用于识别文本中的广告、软广、引流、疑似营销和对抗绕过内容。

当前主流程：

```text
用户输入文本
  -> 前端提交审核请求
  -> 后端 FastAPI 接收请求
  -> engine 加载规则并执行匹配
  -> scorer 计算风险分数
  -> 输出 pass / review / reject
  -> 前端展示结果、命中规则、命中词高亮和审核链路
```

三态结果：

```text
pass    放行
review  转人工审核
reject  拦截
```

## 2. 目录结构

```text
project-root/
├── api/                    # 其他 API 入口或历史接口
├── backend/                # 当前 FastAPI 后端服务
│   └── main.py
├── data/                   # 测试数据、对抗样本数据
├── engine/                 # 规则引擎核心
│   ├── engine.py           # Engine.check 主流程
│   ├── keyword_index.py    # 关键词索引
│   ├── matchers.py         # keyword / regex / length / model 匹配器
│   ├── models.py           # 规则数据结构
│   ├── rule_store.py       # 规则加载
│   ├── scorer.py           # 打分与三态判定
│   └── rules/              # 规则 JSON 文件
├── frontend/               # Vue 3 + Element Plus 前端
│   ├── src/
│   │   ├── api/
│   │   ├── router/
│   │   └── views/
│   ├── package.json
│   └── vite.config.js
├── tests/                  # 测试脚本和评估脚本
├── requirements.txt        # Python 后端依赖
├── README.md
├── DEVELOPMENT.md
└── plan_v1.md
```

后续开发主要关注：

```text
backend/
engine/
frontend/
tests/
data/
```

## 3. 通用开发环境

### 3.1 基础要求

建议版本：

```text
Python 3.10+
Node.js 18+
npm 9+
Git
```

如果使用 conda，建议使用独立环境，不建议直接在 `base` 环境开发。

### 3.2 获取代码

```bash
git clone <repo-url>
cd <project-root>
git checkout feature
```

如果已经有本地仓库：

```bash
git fetch origin
git checkout feature
git pull origin feature
```

## 4. 后端开发环境

后端使用 Python + FastAPI。

### 4.1 创建 Python 环境

任选一种方式。

conda：

```bash
conda create -n content-audit python=3.12 -y
conda activate content-audit
```

venv：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 4.2 安装依赖

在项目根目录执行：

```bash
python -m pip install -r requirements.txt
```

如果 `pyahocorasick` 安装失败，可以先只安装核心依赖运行项目：

```bash
python -m pip install fastapi pydantic "uvicorn[standard]"
```

没有 `pyahocorasick` 时，系统会退回普通字符串匹配，功能可用但性能略低。

### 4.3 启动后端

默认建议使用 `8000` 端口：

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

开发时可以加热重载：

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

如果 `8000` 被占用，可以换端口，例如：

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010
```

换端口后，需要同步修改前端代理配置。

## 5. 前端开发环境

前端使用 Vue 3 + Vite + Element Plus。

### 5.1 安装依赖

进入前端目录：

```bash
cd frontend
npm install
```

注意：不要在项目根目录执行 `npm install`，因为前端的 `package.json` 在 `frontend/` 目录。

### 5.2 启动前端

```bash
npm run dev -- --host 127.0.0.1
```

Windows PowerShell 如果遇到 `npm.ps1` 执行策略问题，可以使用：

```powershell
npm.cmd run dev -- --host 127.0.0.1
```

前端默认地址：

```text
http://127.0.0.1:3000
```

### 5.3 前后端代理

前端代理配置在：

```text
frontend/vite.config.js
```

默认配置：

```js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

如果后端启动在 `8010`，则需要改成：

```js
target: 'http://localhost:8010'
```

## 6. 一次完整本地启动流程

终端 1：启动后端。

```bash
cd <project-root>
conda activate content-audit
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

终端 2：启动前端。

```bash
cd <project-root>/frontend
npm install
npm run dev -- --host 127.0.0.1
```

浏览器访问：

```text
http://127.0.0.1:3000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 7. 核心后端接口

### 7.1 内容审核

```text
POST /api/v1/review
```

请求示例：

```json
{
  "content": "限时特惠，全网最低价，加微信下单",
  "scale": "standard",
  "biz_type": "default"
}
```

返回中重点字段：

```text
decision          pass / review / reject
risk_level        low / medium / high
score             风险分数
labels            标签
hit_rules         命中规则
hit_positions     命中词位置
adversarial_hits  对抗绕过命中
score_detail      打分细节
decision_detail   判定细节
trace             审核链路复现
```

### 7.2 其他接口

```text
GET    /api/v1/review/history
GET    /api/v1/rules
GET    /api/v1/manual/tasks
POST   /api/v1/manual/review
GET    /api/v1/stats
DELETE /api/v1/data/reset
GET    /health
```

## 8. 规则引擎说明

规则引擎入口：

```text
engine/engine.py
```

核心方法：

```python
Engine.check(content: str, scale: str = "standard") -> dict
```

主要流程：

```text
1. 从 engine/rules/ 加载规则
2. 收集 keyword 条件并构建关键词索引
3. 对输入文本做归一化
4. 执行关键词、正则、长度等条件匹配
5. 对 L3 高危关键词执行轻量对抗绕过检测
6. 计算风险分数
7. 根据 scale 阈值输出 pass / review / reject
8. 返回 trace、hit_positions、score_detail 等解释字段
```

### 8.1 支持的 matcher

```text
keyword  关键词匹配
regex    正则匹配
length   长度匹配
model    模型接口预留，当前未真正接入模型
```

### 8.2 对抗绕过检测

当前轻量实现支持识别插字、空格、换行、标点等扰动。

例如：

```text
加我微信
床加前我明微月信光
床
加
前
我
明
微
月
信
光
```

后两种会通过间隔容忍匹配识别为疑似 `加我微信` 绕过。

当前策略：

```text
只对 L3 高危规则启用
关键词长度小于 3 不启用
默认 max_gap = 2
结果写入 adversarial_hits 和 trace
```

后续可优化为规则 JSON 配置：

```json
{
  "type": "keyword",
  "value": ["加我微信"],
  "fuzzy": {
    "enabled": true,
    "max_gap": 2
  }
}
```

## 9. 规则文件格式

规则文件目录：

```text
engine/rules/
```

规则示例：

```json
{
  "rule_id": "BV_001",
  "name": "硬广推销-联系方式",
  "domain": "advertising",
  "level": "L3",
  "weight": 0.9,
  "enabled": true,
  "logic": "OR",
  "conditions": [
    {
      "type": "keyword",
      "match": "any",
      "value": ["加微信", "加我微信", "微信号"]
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
rule_id     规则 ID
name        规则名称
domain      规则领域
level       L1 / L2 / L3
weight      风险权重
enabled     是否启用
logic       AND / OR
conditions  条件列表
action      命中后的标签和分数
```

修改规则后，需要重启后端服务。

## 10. 前端页面说明

主要页面位于：

```text
frontend/src/views/
```

当前常见页面：

```text
LoginPage.vue          登录页
ReviewPage.vue         单条内容审核
BatchReviewPage.vue    批量审核
ManualQueue.vue        人工审核队列
ManualTaskDetail.vue   人工审核详情
TracePage.vue          命中过程展示
StatsPage.vue          统计看板
```

接口封装：

```text
frontend/src/api/index.js
```

路由配置：

```text
frontend/src/router/index.js
```

## 11. 测试与验证

### 11.1 后端快速验证

后端启动后，在浏览器打开：

```text
http://127.0.0.1:8000/docs
```

测试 `POST /api/v1/review`。

也可以用 PowerShell：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/review" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"content":"床加前我明微月信光","scale":"standard","biz_type":"default"}'
```

### 11.2 Python 测试

项目包含测试脚本：

```text
tests/test_engine.py
tests/evaluate.py
```

可以按需要运行：

```bash
python tests/test_engine.py
python tests/evaluate.py
```

### 11.3 前端构建

```bash
cd frontend
npm run build
```

如果在受限环境中出现 `esbuild spawn EPERM`，通常是本机权限或安全策略问题，不一定是代码问题。

## 12. 常见问题

### 12.1 No module named uvicorn

当前 Python 环境没有安装依赖：

```bash
python -m pip install -r requirements.txt
```

### 12.2 端口被占用

Windows 查看端口：

```powershell
netstat -ano | findstr :8000
```

结束进程：

```powershell
taskkill /PID <pid> /F
```

也可以换端口启动后端，并同步修改 `frontend/vite.config.js`。

### 12.3 npm install 找不到 package.json

请确认在前端目录执行：

```bash
cd frontend
npm install
```

### 12.4 前端请求后端失败

检查三件事：

```text
1. 后端是否启动
2. 后端端口是否和 vite.config.js 中 target 一致
3. 前端请求路径是否以 /api 开头
```

## 13. 开发注意事项

不要提交运行缓存：

```text
__pycache__/
*.pyc
node_modules/
dist/
*.log
```

建议提交前检查：

```bash
git status
git diff --stat
```

如果新增依赖：

```text
Python 依赖写入 requirements.txt
前端依赖通过 package.json / package-lock.json 管理
```

## 14. 后续优化方向

建议优先级：

```text
1. 规则热加载
2. 规则管理后台
3. 数据库存储审核历史和人工队列
4. 对抗检测策略配置化
5. model matcher 接入大语言模型或本地分类模型
6. 批量评估准确率、召回率、误杀率、漏放率
7. Docker / docker-compose 部署
```

其中 `model` matcher 已在 `engine/matchers.py` 中预留，但当前还没有实际调用模型 API。
