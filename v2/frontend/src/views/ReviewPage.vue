<template>
  <div class="review-page">
    <!-- 审核输入区 -->
    <el-card class="review-card">
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
          <div class="scale-desc">
            <el-text type="info" size="small">
              {{ scaleDescription }}
            </el-text>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" size="large" @click="submitReview" :loading="loading">
            <el-icon><Search /></el-icon>
            开始识别
          </el-button>
          <el-button size="large" @click="resetForm">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 识别结果 -->
    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <span>识别结果</span>
          <el-tag :type="resultType" size="large" effect="dark">
            {{ resultText }}
          </el-tag>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="请求ID">{{ result.request_id }}</el-descriptions-item>
        <el-descriptions-item label="识别时间">{{ result.timestamp }}</el-descriptions-item>
        <el-descriptions-item label="危害分数">
          <el-progress 
            :percentage="Math.round(result.score * 100)" 
            :color="scoreColor"
            :stroke-width="16"
          />
        </el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="riskLevelType">{{ riskLevelText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理尺度">
          <el-tag>{{ scaleText(result.scale) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标签">
          <el-tag v-for="label in result.labels" :key="label" size="small" class="label-tag">
            {{ label }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <div class="result-reason">
        <el-alert :title="result.review_reason" :type="resultType" :closable="false" show-icon />
      </div>
      
      <!-- 命中规则详情 -->
      <div v-if="result.hit_rules && result.hit_rules.length > 0" class="hit-rules">
        <h4>命中规则详情</h4>
        <el-table :data="result.hit_rules" border stripe>
          <el-table-column prop="rule_id" label="规则ID" width="100" />
          <el-table-column prop="name" label="规则名称" />
          <el-table-column prop="level" label="规则等级" width="100">
            <template #default="{ row }">
              <el-tag :type="levelType(row.level)">{{ row.level }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <!-- 快捷测试 -->
    <el-card class="test-card">
      <template #header>
        <div class="card-header">
          <span>快捷测试</span>
          <el-text type="info" size="small">点击快速填充测试内容</el-text>
        </div>
      </template>
      
      <div class="test-samples">
        <el-button 
          v-for="sample in testSamples" 
          :key="sample.label"
          size="small"
          @click="form.content = sample.content"
        >
          {{ sample.label }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { reviewContent } from '../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const result = ref(null)

const form = ref({
  content: '',
  scale: 'standard',
  biz_type: 'default'
})

const scaleDescription = computed(() => {
  const desc = {
    loose: '宽松：只拦截最严重的内容，转人工区间较小',
    standard: '标准：平衡准确率和召回率，建议默认使用',
    strict: '严格：宁可错杀，多拦截、多转人工'
  }
  return desc[form.value.scale]
})

const resultType = computed(() => {
  if (!result.value) return 'info'
  const types = { pass: 'success', review: 'warning', reject: 'danger' }
  return types[result.value.decision] || 'info'
})

const resultText = computed(() => {
  if (!result.value) return ''
  const texts = { pass: '放行', review: '转人工', reject: '拦截' }
  return texts[result.value.decision] || result.value.decision
})

const riskLevelType = computed(() => {
  if (!result.value) return 'info'
  const types = { low: 'success', medium: 'warning', high: 'danger' }
  return types[result.value.risk_level] || 'info'
})

const riskLevelText = computed(() => {
  if (!result.value) return ''
  const texts = { low: '低危', medium: '中危', high: '高危' }
  return texts[result.value.risk_level] || result.value.risk_level
})

const scoreColor = computed(() => {
  if (!result.value) return '#67C23A'
  if (result.value.score >= 0.7) return '#F56C6C'
  if (result.value.score >= 0.4) return '#E6A23C'
  return '#67C23A'
})

const scaleText = (scale) => {
  const texts = { loose: '宽松', standard: '标准', strict: '严格' }
  return texts[scale] || scale
}

const levelType = (level) => {
  const types = { L1: 'info', L2: 'warning', L3: 'danger' }
  return types[level] || 'info'
}

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
    ElMessage.error('识别失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    content: '',
    scale: 'standard',
    biz_type: 'default'
  }
  result.value = null
}

const testSamples = [
  { label: '正常内容', content: '今天天气真好，适合出去散步。' },
  { label: '硬广内容', content: '亏本甩卖！全网最低价，限时特惠，特价包邮，加微信下单！' },
  { label: '软广内容', content: '强烈推荐这款面霜，亲测好用，回购无数次，必备好物，安利给大家！' },
  { label: '引流内容', content: '进直播间下单有优惠，直播间福利多多，开播提醒已开启。' },
  { label: '疑似广告', content: '感兴趣私信了解详情，评论区见，戳链接查看。' }
]
</script>

<style scoped>
.review-page {
  max-width: 900px;
  margin: 0 auto;
}

.review-card,
.result-card,
.test-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scale-desc {
  margin-top: 8px;
}

.result-reason {
  margin: 20px 0;
}

.hit-rules {
  margin-top: 20px;
}

.hit-rules h4 {
  margin-bottom: 12px;
  color: #303133;
}

.label-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}

.test-samples {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
