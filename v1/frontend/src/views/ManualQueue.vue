<template>
  <div class="manual-queue">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待审核</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.approved }}</div>
          <div class="stat-label">已通过</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.rejected }}</div>
          <div class="stat-label">已拒绝</div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 任务列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>审核任务列表</span>
          <el-radio-group v-model="filterStatus" size="small" @change="fetchTasks">
            <el-radio-button label="pending">待审核</el-radio-button>
            <el-radio-button label="approved">已通过</el-radio-button>
            <el-radio-button label="rejected">已拒绝</el-radio-button>
            <el-radio-button label="all">全部</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      
      <el-table :data="tasks" border stripe v-loading="loading">
        <el-table-column prop="task_id" label="任务ID" width="180" />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="machine_score" label="机器分数" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.round(row.machine_score * 100)" 
              :color="scoreColor(row.machine_score)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="machine_result" label="机器建议" width="100">
          <template #default="{ row }">
            <el-tag :type="resultType(row.machine_result)">
              {{ resultText(row.machine_result) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hit_rules" label="命中规则" width="200">
          <template #default="{ row }">
            <el-tag 
              v-for="rule in row.hit_rules.slice(0, 2)" 
              :key="rule.rule_id"
              size="small"
              class="rule-tag"
            >
              {{ rule.rule_name }}
            </el-tag>
            <el-tag v-if="row.hit_rules.length > 2" size="small" type="info">
              +{{ row.hit_rules.length - 2 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleReview(row, 'pass')">
                通过
              </el-button>
              <el-button type="danger" size="small" @click="handleReview(row, 'block')">
                拒绝
              </el-button>
            </template>
            <template v-else>
              <el-tag :type="row.status === 'approved' ? 'success' : 'danger'">
                {{ row.status === 'approved' ? '已通过' : '已拒绝' }}
              </el-tag>
              <span v-if="row.reviewer" class="reviewer-info">
                by {{ row.reviewer }}
              </span>
            </template>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="tasks.length === 0 && !loading" description="暂无任务" />
    </el-card>
    
    <!-- 审核弹窗 -->
    <el-dialog v-model="dialogVisible" title="人工审核" width="600px">
      <div v-if="currentTask" class="review-dialog">
        <el-alert
          :title="`机器建议：${resultText(currentTask.machine_result)}（分数：${Math.round(currentTask.machine_score * 100)}%）`"
          :type="resultType(currentTask.machine_result)"
          :closable="false"
          show-icon
          class="machine-suggestion"
        />
        
        <div class="content-box">
          <h4>待审核内容</h4>
          <p>{{ currentTask.content }}</p>
        </div>
        
        <div class="hit-rules-box">
          <h4>命中规则</h4>
          <el-tag 
            v-for="rule in currentTask.hit_rules" 
            :key="rule.rule_id"
            :type="riskType(rule.risk_level)"
            class="rule-tag"
          >
            {{ rule.rule_name }} ({{ rule.risk_level }})
          </el-tag>
        </div>
        
        <el-form :model="reviewForm" label-position="top">
          <el-form-item label="审核结果">
            <el-radio-group v-model="reviewForm.result">
              <el-radio-button label="pass">放行</el-radio-button>
              <el-radio-button label="manual">继续转人工</el-radio-button>
              <el-radio-button label="block">拦截</el-radio-button>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item label="审核人">
            <el-input v-model="reviewForm.reviewer" placeholder="请输入审核人姓名" />
          </el-form-item>
          
          <el-form-item label="审核意见">
            <el-input 
              v-model="reviewForm.comment" 
              type="textarea" 
              :rows="3"
              placeholder="可选：填写审核意见..."
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview" :loading="submitting">
          提交审核
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getManualTasks, submitManualReview } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const tasks = ref([])
const filterStatus = ref('pending')
const dialogVisible = ref(false)
const currentTask = ref(null)

const stats = ref({
  pending: 0,
  approved: 0,
  rejected: 0
})

const reviewForm = ref({
  result: 'pass',
  reviewer: '',
  comment: ''
})

let timer = null

const scoreColor = (score) => {
  if (score >= 0.7) return '#F56C6C'
  if (score >= 0.4) return '#E6A23C'
  return '#67C23A'
}

const resultType = (result) => {
  const types = { pass: 'success', manual: 'warning', block: 'danger' }
  return types[result] || 'info'
}

const resultText = (result) => {
  const texts = { pass: '放行', manual: '转人工', block: '拦截' }
  return texts[result] || result
}

const riskType = (level) => {
  const types = { L1: 'info', L2: 'warning', L3: 'danger' }
  return types[level] || 'info'
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await getManualTasks(filterStatus.value)
    tasks.value = res.data.tasks || []
    
    // 更新统计
    const allRes = await getManualTasks('all')
    const allTasks = allRes.data.tasks || []
    stats.value = {
      pending: allTasks.filter(t => t.status === 'pending').length,
      approved: allTasks.filter(t => t.status === 'approved').length,
      rejected: allTasks.filter(t => t.status === 'rejected').length
    }
  } catch (error) {
    ElMessage.error('获取任务失败')
  } finally {
    loading.value = false
  }
}

const handleReview = (row, result) => {
  currentTask.value = row
  reviewForm.value = {
    result: result,
    reviewer: '',
    comment: ''
  }
  dialogVisible.value = true
}

const submitReview = async () => {
  if (!reviewForm.value.reviewer.trim()) {
    ElMessage.warning('请输入审核人姓名')
    return
  }
  
  submitting.value = true
  try {
    await submitManualReview({
      task_id: currentTask.value.task_id,
      result: reviewForm.value.result,
      reviewer: reviewForm.value.reviewer,
      comment: reviewForm.value.comment
    })
    
    ElMessage.success('审核提交成功')
    dialogVisible.value = false
    fetchTasks()
  } catch (error) {
    ElMessage.error('提交失败：' + (error.response?.data?.detail || error.message))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchTasks()
  timer = setInterval(fetchTasks, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.manual-queue {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rule-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.reviewer-info {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.review-dialog {
  padding: 10px;
}

.machine-suggestion {
  margin-bottom: 20px;
}

.content-box {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.content-box h4 {
  margin-bottom: 10px;
  color: #303133;
}

.content-box p {
  color: #606266;
  line-height: 1.6;
}

.hit-rules-box {
  margin-bottom: 20px;
}

.hit-rules-box h4 {
  margin-bottom: 10px;
  color: #303133;
}
</style>
