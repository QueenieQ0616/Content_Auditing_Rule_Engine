<template>
  <div class="stats-page">
    <!-- 概览卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #ecf5ff; color: #409eff;">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_reviews || 0 }}</div>
            <div class="stat-label">总审核数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #f0f9eb; color: #67c23a;">
            <el-icon size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="color: #67c23a;">{{ stats.pass_count || 0 }}</div>
            <div class="stat-label">放行数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #fdf6ec; color: #e6a23c;">
            <el-icon size="32"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="color: #e6a23c;">{{ stats.manual_count || 0 }}</div>
            <div class="stat-label">转人工数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background-color: #fef0f0; color: #f56c6c;">
            <el-icon size="32"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="color: #f56c6c;">{{ stats.block_count || 0 }}</div>
            <div class="stat-label">拦截数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 比率卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>审核结果分布</span>
          </template>
          <div class="rate-item">
            <span class="rate-label">放行率</span>
            <el-progress 
              :percentage="Math.round((stats.pass_rate || 0) * 100)" 
              color="#67c23a"
              :stroke-width="18"
            />
          </div>
          <div class="rate-item">
            <span class="rate-label">拦截率</span>
            <el-progress 
              :percentage="Math.round((stats.block_rate || 0) * 100)" 
              color="#f56c6c"
              :stroke-width="18"
            />
          </div>
          <div class="rate-item">
            <span class="rate-label">转人工率</span>
            <el-progress 
              :percentage="Math.round(((stats.manual_count || 0) / (stats.total_reviews || 1)) * 100)" 
              color="#e6a23c"
              :stroke-width="18"
            />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>人工审核状态</span>
          </template>
          <div class="rate-item">
            <span class="rate-label">待人工审核</span>
            <el-progress 
              :percentage="Math.round(((stats.pending_manual || 0) / (stats.manual_count || 1)) * 100)" 
              color="#409eff"
              :stroke-width="18"
            />
            <span class="rate-value">{{ stats.pending_manual || 0 }} 个</span>
          </div>
          <div class="manual-hint">
            <el-alert
              title="提示"
              type="info"
              :closable="false"
              show-icon
            >
              <p>转人工的内容需要人工审核员进行最终判定。</p>
              <p>请及时处理待审核任务，避免积压。</p>
            </el-alert>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 规则库 -->
    <el-card class="rules-card">
      <template #header>
        <div class="card-header">
          <span>当前规则库</span>
          <el-tag type="info">{{ rules.length }} 条规则</el-tag>
        </div>
      </template>
      
      <el-table :data="rules" border stripe>
        <el-table-column prop="rule_id" label="规则ID" width="100" />
        <el-table-column prop="rule_name" label="规则名称" />
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="riskType(row.risk_level)">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="keywords" label="关键词">
          <template #default="{ row }">
            <el-tag 
              v-for="kw in row.keywords" 
              :key="kw" 
              size="small" 
              class="keyword-tag"
            >
              {{ kw }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStatistics, getRules } from '../api'
import { ElMessage } from 'element-plus'

const stats = ref({})
const rules = ref([])

const riskType = (level) => {
  const types = { L1: 'info', L2: 'warning', L3: 'danger' }
  return types[level] || 'info'
}

const fetchStats = async () => {
  try {
    const res = await getStatistics()
    stats.value = res.data
  } catch (error) {
    ElMessage.error('获取统计失败')
  }
}

const fetchRules = async () => {
  try {
    const res = await getRules()
    rules.value = res.data.rules || []
  } catch (error) {
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

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.rate-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.rate-item:last-child {
  margin-bottom: 0;
}

.rate-label {
  width: 80px;
  font-size: 14px;
  color: #606266;
}

.rate-value {
  width: 60px;
  font-size: 14px;
  color: #409EFF;
  text-align: right;
}

.manual-hint {
  margin-top: 20px;
}

.rules-card {
  margin-top: 20px;
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
