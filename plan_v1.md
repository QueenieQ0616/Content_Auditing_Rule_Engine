# Plan V1: 单条审核数据链路复现

## 1. 背景

当前项目已经实现了基础的内容审核能力：

```text
输入文本 -> 规则匹配 -> 风险打分 -> 三态判定 -> 返回结果
```

但是当前展示效果仍然偏简单，用户只能看到最终结果，例如：

```text
decision = reject
score = 0.95
hit_rules = BV_001, BV_002
```

这会让系统看起来像一个简单的关键词匹配 demo，缺少“为什么这么判定”的解释过程。

因此计划新增一个功能：

```text
单条审核数据链路复现 / Audit Trace / 审核过程追踪
```

目标是让每一条审核数据都可以复现完整处理过程，包括输入、关键词扫描、规则匹配、风险打分、阈值判定和最终处理结果。

## 2. 功能目标

用户提交一条文本后，系统不只返回最终审核结果，还要返回完整审核链路。

示例输入：

```text
限时特惠，全网最低价，特价包邮，加微信下单
```

期望展示：

```text
审核结果：拦截
风险分数：0.95
风险等级：高危

审核链路：
1. 接收输入
   文本长度 21，审核尺度 standard

2. 文本预处理
   去除首尾空白，保留原文

3. 关键词扫描
   命中关键词：限时特惠、全网最低价、特价包邮、加微信

4. 规则匹配
   命中 BV_001 硬广推销-联系方式
   命中 BV_002 硬广推销-价格诱导

5. 风险打分
   最高规则权重 0.90
   额外命中规则 1 条，加分 0.05
   最终分数 0.95

6. 三态判定
   standard 模式 high 阈值为 0.70
   0.95 >= 0.70，因此判定为 reject

7. 处理结果
   直接拦截，不进入人工审核
```

## 3. 设计原则

### 3.1 先做轻量版本

不优先引入数据库，不大改架构。

第一版只在当前 API 返回结果中增加 trace 信息，让前端可以展示审核过程。

### 3.2 保持兼容

保留当前已有字段：

```text
decision
risk_level
score
labels
hit_rules
review_reason
```

新增字段不破坏现有前端逻辑。

### 3.3 强调可解释性

每一步都要回答：

```text
系统做了什么？
命中了什么？
为什么得到这个分数？
为什么最终是 pass / review / reject？
```

## 4. 后端设计

主要改动文件：

```text
engine/engine.py
engine/scorer.py
backend/main.py
```

其中 `backend/main.py` 原则上少改，因为后端主要透传 `Engine.check()` 的结果。

### 4.1 Engine.check 增加 trace 输出

当前返回结构：

```json
{
  "decision": "reject",
  "risk_level": "high",
  "score": 0.95,
  "labels": ["硬广推销"],
  "hit_rules": [],
  "review_reason": "..."
}
```

计划扩展为：

```json
{
  "decision": "reject",
  "risk_level": "high",
  "score": 0.95,
  "labels": ["硬广推销"],
  "hit_rules": [],
  "review_reason": "...",
  "trace": {
    "trace_id": "TRACE_001",
    "stages": []
  }
}
```

### 4.2 trace stage 结构

每一个处理步骤使用统一结构：

```json
{
  "stage": "keyword_scan",
  "title": "关键词扫描",
  "status": "success",
  "detail": "命中 4 个关键词",
  "data": {
    "hit_keywords": ["限时特惠", "全网最低价", "特价包邮", "加微信"]
  }
}
```

字段说明：

```text
stage   机器可读的阶段标识
title   页面展示标题
status  阶段状态，success / warning / danger / info
detail  人类可读的说明
data    结构化扩展数据
```

### 4.3 推荐 stage 列表

第一版建议包含：

```text
input_received   接收输入
preprocess       文本预处理
keyword_scan     关键词扫描
rule_match       规则匹配
score            风险打分
decision         三态判定
final_action     最终处理
```

## 5. 命中词位置设计

为了后续做前端高亮，建议返回命中词位置。

新增字段：

```json
"hit_positions": [
  {
    "keyword": "加微信",
    "start": 15,
    "end": 18,
    "rule_ids": ["BV_001"]
  }
]
```

### 5.1 实现方案 A：轻量实现

不改 `keyword_index.py`。

在 `Engine.check()` 中根据 `hit_words` 再用 `content.find()` 查找位置。

优点：

```text
改动小
实现快
适合当前项目规模
```

缺点：

```text
性能不是最优
重复扫描文本
```

### 5.2 实现方案 B：索引层返回位置

修改 `keyword_index.search()`，让它返回：

```python
{
    "words": set(...),
    "positions": [...]
}
```

优点：

```text
结构更清晰
性能更好
```

缺点：

```text
调用链改动更大
```

第一版推荐使用方案 A。

## 6. 打分细节设计

当前 `score(hit_rules)` 只返回最终分数。

计划新增：

```python
score_with_detail(hit_rules)
```

返回：

```json
{
  "score": 0.95,
  "base_weight": 0.9,
  "base_rule_id": "BV_001",
  "extra_hit_count": 1,
  "extra_bonus": 0.05,
  "formula": "min(1.0, 0.9 + 0.05 * 1)"
}
```

原来的 `score()` 可以保留，避免破坏旧逻辑。

## 7. 判定细节设计

当前 `decide(score, scale)` 返回：

```json
{
  "decision": "reject",
  "risk_level": "high",
  "review_reason": "分数达到拦截阈值"
}
```

计划扩展为：

```json
{
  "decision": "reject",
  "risk_level": "high",
  "review_reason": "分数达到拦截阈值",
  "decision_detail": {
    "scale": "standard",
    "low": 0.35,
    "high": 0.7,
    "reason": "0.95 >= 0.7，判定为 reject"
  }
}
```

这样前端可以明确展示判定依据。

## 8. API 返回结构草案

完整返回示例：

```json
{
  "request_id": "REQ_001",
  "content": "限时特惠，全网最低价，特价包邮，加微信下单",
  "decision": "reject",
  "risk_level": "high",
  "score": 0.95,
  "scale": "standard",
  "labels": ["硬广推销"],
  "hit_rules": [
    {
      "rule_id": "BV_001",
      "name": "硬广推销-联系方式",
      "level": "L3",
      "weight": 0.9,
      "labels": ["硬广推销"]
    }
  ],
  "hit_positions": [
    {
      "keyword": "加微信",
      "start": 15,
      "end": 18,
      "rule_ids": ["BV_001"]
    }
  ],
  "score_detail": {
    "base_weight": 0.9,
    "base_rule_id": "BV_001",
    "extra_hit_count": 1,
    "extra_bonus": 0.05,
    "final_score": 0.95
  },
  "decision_detail": {
    "scale": "standard",
    "low": 0.35,
    "high": 0.7,
    "reason": "0.95 >= 0.7，判定为 reject"
  },
  "trace": {
    "trace_id": "TRACE_001",
    "stages": [
      {
        "stage": "input_received",
        "title": "接收输入",
        "status": "info",
        "detail": "收到待审核文本，长度 21，审核尺度 standard"
      },
      {
        "stage": "keyword_scan",
        "title": "关键词扫描",
        "status": "success",
        "detail": "命中 4 个关键词",
        "data": {
          "hit_keywords": ["限时特惠", "全网最低价", "特价包邮", "加微信"]
        }
      },
      {
        "stage": "rule_match",
        "title": "规则匹配",
        "status": "warning",
        "detail": "命中 2 条规则",
        "data": {
          "hit_rules": ["BV_001", "BV_002"]
        }
      },
      {
        "stage": "score",
        "title": "风险打分",
        "status": "warning",
        "detail": "最高权重 0.9，额外命中 1 条，最终分数 0.95"
      },
      {
        "stage": "decision",
        "title": "三态判定",
        "status": "danger",
        "detail": "standard 模式 high 阈值 0.7，分数 0.95 >= 0.7，判定 reject"
      }
    ]
  }
}
```

## 9. 前端设计

主要改动：

```text
frontend/src/views/ReviewPage.vue
```

### 9.1 新增审核过程复现卡片

在识别结果下方新增：

```text
审核过程复现
```

推荐使用 Element Plus：

```text
el-timeline
el-timeline-item
```

展示效果：

```text
接收输入
文本预处理
关键词扫描
规则匹配
风险打分
三态判定
最终处理
```

### 9.2 命中词高亮

如果实现 `hit_positions`，则在结果区域展示原文，并对命中词高亮。

示例：

```text
限时特惠，全网最低价，特价包邮，加微信下单
```

其中命中的词用红色背景或标签样式突出。

## 10. 分阶段实现计划

### 阶段一：后端返回 trace

目标：

```text
API 返回 trace.stages
前端可以展示审核过程时间线
```

改动文件：

```text
engine/engine.py
engine/scorer.py
frontend/src/views/ReviewPage.vue
```

交付效果：

```text
用户提交一条内容后，可以看到完整审核步骤。
```

### 阶段二：命中词位置和高亮

目标：

```text
API 返回 hit_positions
前端高亮原文中的命中词
```

改动文件：

```text
engine/engine.py
frontend/src/views/ReviewPage.vue
```

交付效果：

```text
用户可以直观看到哪些词触发了规则。
```

### 阶段三：人工审核 trace 闭环

目标：

```text
如果 decision = review，人工审核后追加人工处理记录。
```

新增 trace stage：

```text
manual_review
```

展示内容：

```text
审核人
审核时间
人工结论
审核意见
机器结果和人工结果是否一致
```

### 阶段四：审核历史详情

目标：

```text
支持根据 request_id 查看某条历史审核的完整 trace。
```

可新增接口：

```text
GET /api/v1/review/history/{request_id}
```

前端可在历史记录中点击查看详情。

## 11. 最小可交付版本

如果时间有限，第一版只做：

```text
1. trace.stages
2. score_detail
3. decision_detail
4. 前端时间线展示
```

暂不做：

```text
数据库
规则管理后台
人工审核 trace 闭环
历史详情页
```

这样可以用较小改动获得明显展示效果。

## 12. 答辩表达

可以这样介绍：

```text
我们不仅实现了规则命中和三态判定，还加入了单条审核数据的过程追踪。
每次审核都会生成一条 trace，记录输入接收、关键词扫描、规则匹配、风险打分、阈值判定和最终处理结果。
这样系统具备可解释性和可追溯性，方便人工复核、规则调试和后续审计。
```

这个功能可以把项目从“关键词匹配 demo”提升为“可解释、可追踪的规则审核引擎”。

## 13. 对抗样本与规则绕过防护

### 13.1 问题背景

当前规则引擎主要依赖连续关键词匹配。例如：

```text
加我微信
```

可以命中广告规则。

但是如果用户故意插入无关字符：

```text
床加前我明微月信光
```

人可以看出其中隐藏了：

```text
加 我 微 信
```

但普通关键词匹配无法命中连续的 `加我微信` 或 `微信`，因此可能被错误放行。

这类问题属于：

```text
对抗样本
规则绕过
文本扰动攻击
```

它说明当前规则系统存在一个边界：

```text
只支持连续关键词匹配，对插字、空格、符号、谐音、变体词等绕过方式不敏感。
```

### 13.2 优化目标

在不大幅增加误杀率的前提下，增强系统对常见文本扰动的识别能力。

目标包括：

```text
1. 识别空格、标点、符号插入造成的绕过
2. 识别少量无关字符插入造成的绕过
3. 将对抗检测过程记录进 trace
4. 对疑似对抗样本给出更可解释的审核结论
```

### 13.3 文本归一化

第一层防护是文本归一化。

在规则匹配前生成一个 `normalized_content`，用于辅助匹配。

可处理：

```text
去除空格
去除常见标点
全角转半角
英文转小写
连续符号压缩
繁简转换，可选
```

示例：

```text
原文：加 我 微 信
归一化：加我微信

原文：加-我-微-信
归一化：加我微信

原文：V X 号
归一化：vx号
```

这样可以覆盖基础扰动场景。

### 13.4 间隔容忍匹配

对于如下样本：

```text
床加前我明微月信光
```

仅靠去空格和去标点不够，因为关键词字符之间插入的是正常汉字。

因此可以对高危关键词启用“间隔容忍匹配”。

例如关键词：

```text
加我微信
```

允许每两个关键词字符之间最多插入 2 个字符，可转换为类似规则：

```text
加.{0,2}我.{0,2}微.{0,2}信
```

这样就能命中：

```text
床加前我明微月信光
```

其中匹配片段为：

```text
加前我明微月信
```

### 13.5 规则配置建议

不建议对所有规则都启用间隔匹配，否则容易误杀。

建议只对高危规则或高危关键词启用，例如：

```text
加微信
加我微信
微信号
VX号
私聊
下单
扫码加
```

规则 JSON 可以扩展为：

```json
{
  "type": "keyword",
  "value": ["加我微信"],
  "match": "any",
  "fuzzy": {
    "enabled": true,
    "max_gap": 2
  }
}
```

字段说明：

```text
fuzzy.enabled  是否启用扰动匹配
fuzzy.max_gap  关键词字符之间允许插入的最大字符数
```

第一版如果不想改规则格式，也可以先在代码中对 L3 高危规则启用默认间隔匹配。

### 13.6 trace 展示设计

对抗检测应该进入审核链路复现。

新增 trace stage：

```text
adversarial_check  对抗扰动检测
```

示例：

```json
{
  "stage": "adversarial_check",
  "title": "对抗扰动检测",
  "status": "warning",
  "detail": "发现疑似插字绕过：关键词 加我微信，最大间隔 1",
  "data": {
    "keyword": "加我微信",
    "matched_text": "加前我明微月信",
    "max_gap": 1,
    "rule_ids": ["BV_001"]
  }
}
```

这样前端可以展示：

```text
对抗扰动检测：
发现疑似插字绕过
关键词：加我微信
匹配片段：加前我明微月信
关联规则：BV_001
```

### 13.7 判定策略

对抗匹配不能一律直接拦截，需要控制误杀。

建议策略：

```text
1. L3 高危规则 + 对抗命中，可以 reject 或 review
2. L2 规则 + 对抗命中，优先 review
3. L1 规则一般不启用对抗匹配
4. max_gap 建议从 1 或 2 开始，不要过大
5. 关键词长度至少 3 或 4，避免短词误伤
```

可以在打分时增加对抗命中的说明：

```json
{
  "score_detail": {
    "base_weight": 0.9,
    "adversarial_bonus": 0.1,
    "final_score": 1.0
  }
}
```

也可以保守一些：

```text
对抗命中不直接加分，只作为 review_reason 和 trace 解释依据。
```

### 13.8 最小实现版本

第一版可以只做：

```text
1. 文本归一化
2. 对 L3 keyword 规则做 max_gap = 2 的间隔匹配
3. 返回 adversarial_hits
4. 在 trace 中展示 adversarial_check
```

暂不做：

```text
谐音识别
拼音识别
机器学习模型识别
复杂语义绕过检测
```

### 13.9 示例效果

输入：

```text
床加前我明微月信光
```

期望结果：

```text
decision = review 或 reject
risk_level = high
命中规则 = 硬广推销-联系方式
trace 中出现 对抗扰动检测
```

展示说明：

```text
系统识别到该文本疑似通过插入无关字符绕过关键词规则。
原始高危关键词为“加我微信”，文本中出现了间隔匹配片段“加前我明微月信”。
因此系统将该内容判定为高风险，并进入拦截或人工审核流程。
```

### 13.10 答辩表达

可以这样介绍：

```text
我们进一步考虑了规则系统在真实场景中的对抗绕过问题。
例如“加我微信”可以直接命中规则，但用户可能通过插入无关字符写成“床加前我明微月信光”来绕过连续关键词匹配。
为此我们设计了文本归一化和间隔容忍匹配机制，并将对抗检测过程写入 trace。
这样系统不仅能给出最终结果，还能解释为什么认为这是一条疑似绕过的广告内容。
```
