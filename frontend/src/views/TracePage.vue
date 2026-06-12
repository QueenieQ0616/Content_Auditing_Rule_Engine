<template>
  <div class="trace-page">
    <el-card class="top-card">
      <template #header>
        <div class="card-header">
          <span>规则与关键词命中过程</span>
          <div class="header-actions">
            <el-tag type="info">来自内容审核历史</el-tag>
            <el-button size="small" type="primary" :loading="loading" @click="fetchHistory">刷新记录</el-button>
          </div>
        </div>
      </template>

      <el-alert
        title="该页面会自动读取每一次内容审核记录，选择一条记录后即可查看流程图，无需重复输入待分析内容。"
        type="info"
        :closable="false"
        show-icon
      />
    </el-card>

    <el-row :gutter="20">
      <el-col :span="7">
        <el-card class="history-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>审核记录</span>
              <el-tag>{{ history.length }} 条</el-tag>
            </div>
          </template>

          <el-empty v-if="!history.length" description="暂无审核记录，请先在内容审核页提交内容" />
          <div v-else class="record-list">
            <div
              v-for="record in history"
              :key="record.request_id"
              class="record-item"
              :class="{ active: selectedRecord?.request_id === record.request_id }"
              @click="selectRecord(record)"
            >
              <div class="record-head">
                <el-tag :type="decisionType(record.decision)" size="small">
                  {{ decisionText(record.decision) }}
                </el-tag>
                <span class="record-time">{{ formatTime(record.timestamp) }}</span>
              </div>
              <div class="record-content">{{ record.content }}</div>
              <div class="record-meta">
                分数 {{ record.score }} · {{ scaleText(record.scale) }} · 命中 {{ record.hit_rules?.length || 0 }} 条规则
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="17">
        <el-empty v-if="!selectedRecord" description="请选择一条审核记录查看命中流程" />

        <template v-else>
          <el-card class="summary-card">
            <template #header>
              <div class="card-header">
                <span>审核结果概览</span>
                <el-tag :type="decisionType(selectedRecord.decision)" effect="dark">
                  {{ decisionText(selectedRecord.decision) }}
                </el-tag>
              </div>
            </template>

            <el-descriptions :column="3" border>
              <el-descriptions-item label="请求 ID">{{ selectedRecord.request_id }}</el-descriptions-item>
              <el-descriptions-item label="审核尺度">{{ scaleText(selectedRecord.scale) }}</el-descriptions-item>
              <el-descriptions-item label="风险等级">
                <el-tag :type="riskType(selectedRecord.risk_level)">
                  {{ riskText(selectedRecord.risk_level) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="风险分数">
                <el-progress
                  :percentage="Math.round((selectedRecord.score || 0) * 100)"
                  :color="scoreColor(selectedRecord.score || 0)"
                  :stroke-width="14"
                />
              </el-descriptions-item>
              <el-descriptions-item label="命中标签">
                <el-tag
                  v-for="label in selectedRecord.labels"
                  :key="label"
                  size="small"
                  class="inline-tag"
                >
                  {{ label }}
                </el-tag>
                <span v-if="!selectedRecord.labels?.length">无</span>
              </el-descriptions-item>
              <el-descriptions-item label="审核时间">{{ selectedRecord.timestamp }}</el-descriptions-item>
              <el-descriptions-item label="待审内容" :span="3">
                <div class="full-content">{{ selectedRecord.content }}</div>
              </el-descriptions-item>
              <el-descriptions-item label="审核原因" :span="3">
                {{ selectedRecord.review_reason }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="flow-card">
            <template #header>
              <span>流程图展示</span>
            </template>

            <div class="flow-chart">
              <template v-for="(stage, index) in flowStages" :key="stage.stage">
                <div class="flow-node" :class="nodeClass(stage.status)">
                  <div class="node-index">{{ index + 1 }}</div>
                  <div class="node-body">
                    <div class="node-title">{{ stage.title }}</div>
                    <div class="node-detail">{{ stage.detail }}</div>
                    <el-collapse class="node-collapse">
                      <el-collapse-item title="查看阶段数据">
                        <pre class="stage-data">{{ formatData(stage.data) }}</pre>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </div>
                <div v-if="index < flowStages.length - 1" class="flow-arrow">
                  <span>↓</span>
                </div>
              </template>
            </div>
          </el-card>

          <el-row :gutter="20" class="detail-row">
            <el-col :span="12">
              <el-card class="detail-card">
                <template #header>
                  <span>关键词命中</span>
                </template>
                <el-empty v-if="!selectedRecord.hit_positions?.length" description="暂无关键词位置记录" />
                <div v-else class="hit-list">
                  <div v-for="(hit, index) in selectedRecord.hit_positions" :key="index" class="hit-item">
                    <div class="hit-main">
                      <el-tag :type="hit.match_type === 'adversarial_gap' ? 'danger' : 'success'">
                        {{ hit.keyword }}
                      </el-tag>
                      <span class="hit-range">{{ hit.start }} - {{ hit.end }}</span>
                    </div>
                    <div class="hit-meta">
                      类型：{{ hit.match_type === 'adversarial_gap' ? '插字规避命中' : '直接命中' }}
                    </div>
                    <div v-if="hit.matched_text" class="hit-meta">实际片段：{{ hit.matched_text }}</div>
                    <div class="hit-meta">关联规则：{{ hit.rule_ids?.join('、') }}</div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :span="12">
              <el-card class="detail-card">
                <template #header>
                  <span>命中规则与打分</span>
                </template>
                <el-empty v-if="!selectedRecord.hit_rules?.length" description="未命中规则" />
                <el-table v-else :data="selectedRecord.hit_rules" border size="small">
                  <el-table-column prop="rule_id" label="ID" width="90" />
                  <el-table-column prop="name" label="规则" />
                  <el-table-column prop="level" label="等级" width="70" />
                </el-table>
                <pre class="stage-data score-data">
{{ formatData({ score_detail: selectedRecord.score_detail, decision_detail: selectedRecord.decision_detail }) }}
                </pre>
              </el-card>
            </el-col>
          </el-row>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getReviewHistory } from '../api'

const loading = ref(false)
const history = ref([])
const selectedRecord = ref(null)

const flowStages = computed(() => selectedRecord.value?.trace?.stages || [])

const decisionType = (decision) => ({ pass: 'success', review: 'warning', reject: 'danger' }[decision] || 'info')
const decisionText = (decision) => ({ pass: '放行', review: '转人工', reject: '拦截' }[decision] || decision)
const riskType = (risk) => ({ low: 'success', medium: 'warning', high: 'danger' }[risk] || 'info')
const riskText = (risk) => ({ low: '低危', medium: '中危', high: '高危' }[risk] || risk)
const scaleText = (scale) => ({ loose: '宽松', standard: '标准', strict: '严格' }[scale] || scale)
const scoreColor = (score) => (score >= 0.7 ? '#f56c6c' : score >= 0.35 ? '#e6a23c' : '#67c23a')
const formatData = (data) => JSON.stringify(data || {}, null, 2)
const formatTime = (time) => (time ? String(time).replace('T', ' ').slice(0, 19) : '-')

const nodeClass = (status) => {
  if (status === 'pass' || status === 'success') return 'node-success'
  if (status === 'review' || status === 'warning') return 'node-warning'
  if (status === 'reject' || status === 'danger') return 'node-danger'
  return 'node-info'
}

const selectRecord = (record) => {
  selectedRecord.value = record
}

const fetchHistory = async () => {
  loading.value = true
  try {
    const res = await getReviewHistory({ limit: 100, offset: 0 })
    history.value = [...(res.data.items || [])].reverse()
    if (!selectedRecord.value && history.value.length) {
      selectedRecord.value = history.value[0]
    }
    if (selectedRecord.value) {
      const latestSame = history.value.find((item) => item.request_id === selectedRecord.value.request_id)
      selectedRecord.value = latestSame || history.value[0] || null
    }
  } catch (error) {
    ElMessage.error(`获取审核历史失败：${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

onMounted(fetchHistory)
</script>

<style scoped>
.trace-page {
  max-width: 1400px;
  margin: 0 auto;
}

.top-card,
.summary-card,
.flow-card,
.detail-row {
  margin-bottom: 20px;
}

.card-header,
.header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.history-card {
  position: sticky;
  top: 0;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(100vh - 230px);
  overflow-y: auto;
}

.record-item {
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.record-item:hover,
.record-item.active {
  border-color: #409eff;
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.14);
  background: #eff6ff;
}

.record-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.record-time,
.record-meta {
  color: #64748b;
  font-size: 12px;
}

.record-content {
  color: #1f2937;
  font-size: 14px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  margin-bottom: 8px;
}

.inline-tag {
  margin-right: 6px;
}

.full-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
}

.flow-chart {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.flow-node {
  display: grid;
  grid-template-columns: 46px 1fr;
  gap: 14px;
  border: 1px solid #e5e7eb;
  border-left-width: 6px;
  border-radius: 14px;
  background: #fff;
  padding: 16px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
}

.node-index {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  background: #64748b;
}

.node-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 6px;
}

.node-detail {
  color: #475569;
  line-height: 1.6;
}

.node-collapse {
  margin-top: 8px;
}

.node-info {
  border-left-color: #409eff;
}

.node-success {
  border-left-color: #67c23a;
}

.node-warning {
  border-left-color: #e6a23c;
}

.node-danger {
  border-left-color: #f56c6c;
}

.node-info .node-index {
  background: #409eff;
}

.node-success .node-index {
  background: #67c23a;
}

.node-warning .node-index {
  background: #e6a23c;
}

.node-danger .node-index {
  background: #f56c6c;
}

.flow-arrow {
  text-align: center;
  color: #94a3b8;
  font-size: 24px;
  line-height: 1;
}

.stage-data {
  background: #0f172a;
  color: #dbeafe;
  border-radius: 8px;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  max-height: 260px;
  overflow: auto;
}

.score-data {
  margin-top: 14px;
}

.detail-card {
  min-height: 280px;
}

.hit-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hit-item {
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
}

.hit-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.hit-range,
.hit-meta {
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}
</style>
