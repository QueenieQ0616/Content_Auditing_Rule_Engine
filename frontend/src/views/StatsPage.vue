<template>
  <div class="stats-page">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="item in overview" :key="item.label">
        <el-card class="stat-card">
          <el-icon :color="item.color" size="30"><component :is="item.icon" /></el-icon>
          <div>
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="12">
        <el-card>
          <template #header>审核结果分布</template>
          <div class="rate-item">
            <span>放行率</span>
            <el-progress :percentage="Math.round((stats.pass_rate || 0) * 100)" color="#67c23a" :stroke-width="18" />
          </div>
          <div class="rate-item">
            <span>拦截率</span>
            <el-progress :percentage="Math.round((stats.reject_rate || 0) * 100)" color="#f56c6c" :stroke-width="18" />
          </div>
          <div class="rate-item">
            <span>转人工率</span>
            <el-progress :percentage="Math.round(((stats.review_count || 0) / (stats.total_reviews || 1)) * 100)" color="#e6a23c" :stroke-width="18" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>人工审核状态</template>
          <div class="rate-item">
            <span>待人工审核</span>
            <el-progress :percentage="Math.round(((stats.pending_manual || 0) / (stats.review_count || 1)) * 100)" color="#409eff" :stroke-width="18" />
          </div>
          <el-alert title="转人工内容会进入人工审核队列，请及时处理。" type="info" :closable="false" show-icon />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>当前规则库</span>
          <el-tag type="info">{{ rules.length }} 条规则</el-tag>
        </div>
      </template>
      <el-table :data="rules" border stripe>
        <el-table-column prop="rule_id" label="规则 ID" width="120" />
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="level" label="等级" width="90">
          <template #default="{ row }">
            <el-tag :type="levelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="100" />
        <el-table-column prop="label" label="标签" width="130" />
        <el-table-column label="关键词">
          <template #default="{ row }">
            <el-tag v-for="kw in row.keywords" :key="kw" size="small" class="keyword-tag">{{ kw }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getRules, getStatistics } from '../api'

const stats = ref({})
const rules = ref([])

const overview = computed(() => [
  { label: '总审核数', value: stats.value.total_reviews || 0, color: '#409eff', icon: 'Document' },
  { label: '放行数', value: stats.value.pass_count || 0, color: '#67c23a', icon: 'CircleCheck' },
  { label: '转人工数', value: stats.value.review_count || 0, color: '#e6a23c', icon: 'Warning' },
  { label: '拦截数', value: stats.value.reject_count || 0, color: '#f56c6c', icon: 'CircleClose' }
])

const levelType = (level) => ({ L1: 'info', L2: 'warning', L3: 'danger' }[level] || 'info')

const fetchStats = async () => {
  try {
    const res = await getStatistics()
    stats.value = res.data
  } catch {
    ElMessage.error('获取统计失败')
  }
}

const fetchRules = async () => {
  try {
    const res = await getRules()
    rules.value = res.data.rules || []
  } catch {
    ElMessage.error('获取规则失败')
  }
}

onMounted(() => {
  fetchStats()
  fetchRules()
})
</script>

<style scoped>
.stats-page {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  color: #64748b;
}

.rate-item {
  display: grid;
  grid-template-columns: 90px 1fr;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.keyword-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}
</style>
