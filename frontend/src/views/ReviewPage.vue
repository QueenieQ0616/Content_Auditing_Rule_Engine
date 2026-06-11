<template>
  <div class="review-page">
    <el-card class="panel">
      <template #header>
        <div class="card-header">
          <span>广告识别</span>
          <el-tag type="info">文本</el-tag>
        </div>
      </template>

      <el-form :model="form" label-position="top">
        <el-form-item label="待识别内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入需要识别的内容..."
            maxlength="10000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="处理尺度">
          <el-radio-group v-model="form.scale">
            <el-radio-button label="loose">宽松</el-radio-button>
            <el-radio-button label="standard">标准</el-radio-button>
            <el-radio-button label="strict">严格</el-radio-button>
          </el-radio-group>
          <div class="scale-desc">{{ scaleDescription }}</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="submitReview">
            <el-icon><Search /></el-icon>
            开始识别
          </el-button>
          <el-button size="large" @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="panel">
      <template #header>
        <div class="card-header">
          <span>识别结果</span>
          <el-tag :type="decisionType(result.decision)" size="large" effect="dark">
            {{ decisionText(result.decision) }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="请求 ID">{{ result.request_id }}</el-descriptions-item>
        <el-descriptions-item label="识别时间">{{ result.timestamp }}</el-descriptions-item>
        <el-descriptions-item label="风险分数">
          <el-progress :percentage="Math.round(result.score * 100)" :color="scoreColor(result.score)" :stroke-width="16" />
        </el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="riskType(result.risk_level)">{{ riskText(result.risk_level) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理尺度">{{ scaleText(result.scale) }}</el-descriptions-item>
        <el-descriptions-item label="标签">
          <el-tag v-for="label in result.labels" :key="label" size="small" class="tag">{{ label }}</el-tag>
          <span v-if="!result.labels.length">无</span>
        </el-descriptions-item>
      </el-descriptions>

      <el-alert class="reason" :title="result.review_reason" :type="decisionType(result.decision)" :closable="false" show-icon />

      <el-table v-if="result.hit_rules.length" :data="result.hit_rules" border stripe>
        <el-table-column prop="rule_id" label="规则 ID" width="120" />
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="level" label="等级" width="100">
          <template #default="{ row }">
            <el-tag :type="levelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="panel">
      <template #header>
        <span>快捷测试</span>
      </template>
      <div class="sample-list">
        <el-button v-for="sample in testSamples" :key="sample.label" size="small" @click="form.content = sample.content">
          {{ sample.label }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { reviewContent } from '../api'

const loading = ref(false)
const result = ref(null)
const form = ref({ content: '', scale: 'standard', biz_type: 'default' })

const scaleDescription = computed(() => ({
  loose: '宽松：只拦截最明显的高危内容。',
  standard: '标准：平衡准确率和召回率，推荐默认使用。',
  strict: '严格：更容易转人工或拦截，适合高风险场景。'
}[form.value.scale]))

const decisionType = (decision) => ({ pass: 'success', review: 'warning', reject: 'danger' }[decision] || 'info')
const decisionText = (decision) => ({ pass: '放行', review: '转人工', reject: '拦截' }[decision] || decision)
const riskType = (level) => ({ low: 'success', medium: 'warning', high: 'danger' }[level] || 'info')
const riskText = (level) => ({ low: '低危', medium: '中危', high: '高危' }[level] || level)
const levelType = (level) => ({ L1: 'info', L2: 'warning', L3: 'danger' }[level] || 'info')
const scaleText = (scale) => ({ loose: '宽松', standard: '标准', strict: '严格' }[scale] || scale)
const scoreColor = (score) => (score >= 0.7 ? '#f56c6c' : score >= 0.35 ? '#e6a23c' : '#67c23a')

const submitReview = async () => {
  if (!form.value.content.trim()) {
    ElMessage.warning('请输入待识别内容')
    return
  }
  loading.value = true
  try {
    const res = await reviewContent(form.value)
    result.value = res.data
    ElMessage.success('识别完成')
  } catch (error) {
    ElMessage.error(`识别失败：${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = { content: '', scale: 'standard', biz_type: 'default' }
  result.value = null
}

const testSamples = [
  { label: '正常内容', content: '今天状态不错，想记录一下最近读书和散步的感受。' },
  { label: '硬广内容', content: '限时特惠，全网最低价，特价包邮，加微信下单。' },
  { label: '软广内容', content: '强烈推荐这款面霜，亲测好用，回购无数次，安利给大家。' },
  { label: '引流内容', content: '来我直播间下单有优惠，直播间福利很多，开播提醒已开启。' },
  { label: '疑似广告', content: '感兴趣私信了解详情，评论区见，点击下方链接查看。' }
]
</script>

<style scoped>
.review-page {
  max-width: 920px;
  margin: 0 auto;
}

.panel {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.scale-desc {
  margin-top: 8px;
  color: #64748b;
  font-size: 13px;
}

.reason {
  margin: 20px 0;
}

.tag {
  margin-right: 6px;
}

.sample-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
