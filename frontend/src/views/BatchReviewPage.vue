<template>
  <div class="batch-page">
    <el-card class="input-card">
      <template #header>
        <div class="card-header">
          <span>批量导入审核</span>
          <el-tag type="info">每行一条内容</el-tag>
        </div>
      </template>

      <el-alert
        title="支持直接粘贴多行文本，也支持导入 .txt / .csv 文件。批量审核的每条记录都会写入审核历史，转人工结果也会进入人工审核队列。"
        type="info"
        :closable="false"
        show-icon
        class="tip-alert"
      />

      <el-form :model="form" label-position="top">
        <el-form-item label="处理尺度">
          <el-radio-group v-model="form.scale">
            <el-radio-button label="loose">宽松</el-radio-button>
            <el-radio-button label="standard">标准</el-radio-button>
            <el-radio-button label="strict">严格</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="批量内容">
          <el-input
            v-model="rawText"
            type="textarea"
            :rows="10"
            maxlength="200000"
            show-word-limit
            placeholder="每行输入一条待审核内容，例如：&#10;今天天气很好&#10;加微信领取福利&#10;强/烈/推/荐这款产品"
          />
        </el-form-item>

        <div class="toolbar">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept=".txt,.csv"
            :on-change="handleFileChange"
          >
            <el-button>导入 TXT/CSV</el-button>
          </el-upload>
          <el-button @click="fillSample">填充样例</el-button>
          <el-button @click="clearAll">清空</el-button>
          <el-button type="primary" :loading="loading" @click="submitBatch">开始批量审核</el-button>
        </div>

        <div class="count-info">
          已解析 <strong>{{ parsedContents.length }}</strong> 条有效内容
        </div>
      </el-form>
    </el-card>

    <el-row v-if="batchResult" :gutter="20" class="summary-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ batchResult.total }}</div>
          <div class="stat-label">总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card success">
          <div class="stat-value">{{ batchResult.summary.pass_count }}</div>
          <div class="stat-label">放行</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-value">{{ batchResult.summary.review_count }}</div>
          <div class="stat-label">转人工</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card danger">
          <div class="stat-value">{{ batchResult.summary.reject_count }}</div>
          <div class="stat-label">拦截</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="batchResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>批量审核结果</span>
          <div class="header-actions">
            <el-tag>批次：{{ batchResult.batch_id }}</el-tag>
            <el-button size="small" @click="exportCsv">导出 CSV</el-button>
          </div>
        </div>
      </template>

      <el-table :data="batchResult.items" border stripe>
        <el-table-column prop="batch_index" label="#" width="70" />
        <el-table-column prop="content" label="内容" min-width="260">
          <template #default="{ row }">
            <div class="content-preview">{{ row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="decision" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="decisionType(row.decision)">{{ decisionText(row.decision) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="100">
          <template #default="{ row }">
            <el-tag :type="riskType(row.risk_level)">{{ riskText(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="分数" width="130">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.score * 100)" :color="scoreColor(row.score)" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column label="命中规则" min-width="220">
          <template #default="{ row }">
            <el-tag v-for="rule in row.hit_rules" :key="rule.rule_id" size="small" class="inline-tag">
              {{ rule.name }}
            </el-tag>
            <span v-if="!row.hit_rules?.length">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="review_reason" label="原因" min-width="260" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { batchReviewContent } from '../api'

const loading = ref(false)
const rawText = ref('')
const batchResult = ref(null)
const form = ref({
  scale: 'standard',
  biz_type: 'default'
})

const parsedContents = computed(() => {
  return rawText.value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
})

const decisionType = (decision) => ({ pass: 'success', review: 'warning', reject: 'danger' }[decision] || 'info')
const decisionText = (decision) => ({ pass: '放行', review: '转人工', reject: '拦截' }[decision] || decision)
const riskType = (risk) => ({ low: 'success', medium: 'warning', high: 'danger' }[risk] || 'info')
const riskText = (risk) => ({ low: '低危', medium: '中危', high: '高危' }[risk] || risk)
const scoreColor = (score) => (score >= 0.7 ? '#f56c6c' : score >= 0.35 ? '#e6a23c' : '#67c23a')

const handleFileChange = async (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return
  const text = await file.text()
  const lines = parseImportedText(text, file.name)
  rawText.value = lines.join('\n')
  ElMessage.success(`已导入 ${lines.length} 条内容`)
}

const parseImportedText = (text, fileName) => {
  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  if (!fileName.toLowerCase().endsWith('.csv')) return lines

  const rows = lines.map(parseCsvLine)
  const firstRow = rows[0] || []
  const normalizedHeader = firstRow.map((cell) => cell.replace(/^\ufeff/, '').trim().toLowerCase())
  const contentColumnIndex = normalizedHeader.findIndex((cell) => ['content', 'text', '内容', '文本'].includes(cell))

  if (contentColumnIndex >= 0) {
    return rows.slice(1).map((row) => row[contentColumnIndex]?.trim()).filter(Boolean)
  }

  return rows.map((row) => row[0]?.trim()).filter(Boolean)
}

const parseCsvLine = (line) => {
  const cells = []
  let current = ''
  let inQuotes = false

  for (let index = 0; index < line.length; index++) {
    const char = line[index]
    const nextChar = line[index + 1]

    if (char === '"' && inQuotes && nextChar === '"') {
      current += '"'
      index++
    } else if (char === '"') {
      inQuotes = !inQuotes
    } else if ((char === ',' || char === '，') && !inQuotes) {
      cells.push(current)
      current = ''
    } else {
      current += char
    }
  }

  cells.push(current)
  return cells.map((cell) => cell.trim())
}

const fillSample = () => {
  rawText.value = [
    '今天天气很好，适合出去散步。',
    '加微信领取限时福利，直播间下单更优惠。',
    '强/烈/推/荐这款面霜，亲/测/好/用。',
    '、床加前微明信月下光单。'
  ].join('\n')
}

const clearAll = () => {
  rawText.value = ''
  batchResult.value = null
}

const submitBatch = async () => {
  if (!parsedContents.value.length) {
    ElMessage.warning('请先输入或导入待审核内容')
    return
  }
  loading.value = true
  try {
    const res = await batchReviewContent({
      contents: parsedContents.value,
      scale: form.value.scale,
      biz_type: form.value.biz_type
    })
    batchResult.value = res.data
    ElMessage.success(`批量审核完成，共 ${res.data.total} 条`)
  } catch (error) {
    ElMessage.error(`批量审核失败：${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const csvEscape = (value) => {
  const text = String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

const exportCsv = () => {
  if (!batchResult.value?.items?.length) return
  const headers = ['序号', '内容', '结果', '风险等级', '分数', '命中规则', '原因']
  const rows = batchResult.value.items.map((item) => [
    item.batch_index,
    item.content,
    decisionText(item.decision),
    riskText(item.risk_level),
    item.score,
    (item.hit_rules || []).map((rule) => rule.name).join('；'),
    item.review_reason
  ])
  const csv = [headers, ...rows].map((row) => row.map(csvEscape).join(',')).join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${batchResult.value.batch_id}_审核结果.csv`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.batch-page {
  max-width: 1280px;
  margin: 0 auto;
}

.input-card,
.summary-row,
.result-card {
  margin-bottom: 20px;
}

.card-header,
.header-actions,
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.tip-alert {
  margin-bottom: 18px;
}

.toolbar {
  justify-content: flex-start;
  margin-bottom: 10px;
}

.count-info {
  color: #64748b;
  font-size: 14px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #2563eb;
}

.stat-label {
  color: #64748b;
}

.stat-card.success .stat-value {
  color: #67c23a;
}

.stat-card.warning .stat-value {
  color: #e6a23c;
}

.stat-card.danger .stat-value {
  color: #f56c6c;
}

.content-preview {
  color: #475569;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.inline-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}
</style>
