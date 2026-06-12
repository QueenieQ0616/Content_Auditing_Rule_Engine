<template>
  <div class="manual-queue">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card"><div class="stat-value">{{ stats.pending }}</div><div class="stat-label">待审核</div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card"><div class="stat-value">{{ stats.approved }}</div><div class="stat-label">已通过</div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card"><div class="stat-value">{{ stats.rejected }}</div><div class="stat-label">已拒绝</div></el-card>
      </el-col>
    </el-row>

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
        <el-table-column prop="task_id" label="任务 ID" width="180" />
        <el-table-column prop="content" label="内容" min-width="260">
          <template #default="{ row }">
            <div class="content-preview">{{ row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="machine_score" label="机器分数" width="140">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.machine_score * 100)" :color="scoreColor(row.machine_score)" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="machine_decision" label="机器建议" width="110">
          <template #default="{ row }">
            <el-tag :type="decisionType(row.machine_decision)">{{ decisionText(row.machine_decision) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="命中规则" width="220">
          <template #default="{ row }">
            <el-tag v-for="rule in row.hit_rules.slice(0, 2)" :key="rule.rule_id" size="small" class="rule-tag">{{ rule.name }}</el-tag>
            <el-tag v-if="row.hit_rules.length > 2" size="small" type="info">+{{ row.hit_rules.length - 2 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="primary" size="small" plain @click="goDetail(row)">详情审核</el-button>
              <el-button type="success" size="small" @click="openReview(row, 'pass')">通过</el-button>
              <el-button type="danger" size="small" @click="openReview(row, 'reject')">拒绝</el-button>
            </template>
            <template v-else>
              <el-tag :type="row.status === 'approved' ? 'success' : 'danger'">{{ row.status === 'approved' ? '已通过' : '已拒绝' }}</el-tag>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="tasks.length === 0 && !loading" description="暂无任务" />
    </el-card>

    <el-dialog v-model="dialogVisible" title="人工审核" width="600px">
      <div v-if="currentTask">
        <el-alert
          :title="`机器建议：${decisionText(currentTask.machine_decision)}（${Math.round(currentTask.machine_score * 100)}%）`"
          :type="decisionType(currentTask.machine_decision)"
          :closable="false"
          show-icon
        />
        <div class="content-box">{{ currentTask.content }}</div>
        <el-form :model="reviewForm" label-position="top">
          <el-form-item label="审核结果">
            <el-radio-group v-model="reviewForm.decision">
              <el-radio-button label="pass">放行</el-radio-button>
              <el-radio-button label="reject">拦截</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="审核人">
            <el-input v-model="reviewForm.reviewer" placeholder="请输入审核人姓名" />
          </el-form-item>
          <el-form-item label="审核意见">
            <el-input v-model="reviewForm.comment" type="textarea" :rows="3" placeholder="可选" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReview">提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getManualTasks, submitManualReview } from '../api'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const tasks = ref([])
const filterStatus = ref('pending')
const dialogVisible = ref(false)
const currentTask = ref(null)
const stats = ref({ pending: 0, approved: 0, rejected: 0 })
const reviewForm = ref({ decision: 'pass', reviewer: '', comment: '' })
let timer = null

const scoreColor = (score) => (score >= 0.7 ? '#f56c6c' : score >= 0.35 ? '#e6a23c' : '#67c23a')
const decisionType = (decision) => ({ pass: 'success', review: 'warning', reject: 'danger' }[decision] || 'info')
const decisionText = (decision) => ({ pass: '放行', review: '转人工', reject: '拦截' }[decision] || decision)

const fetchTasks = async () => {
  loading.value = true
  try {
    const [current, all] = await Promise.all([getManualTasks(filterStatus.value), getManualTasks('all')])
    tasks.value = current.data.tasks || []
    const allTasks = all.data.tasks || []
    stats.value = {
      pending: allTasks.filter((t) => t.status === 'pending').length,
      approved: allTasks.filter((t) => t.status === 'approved').length,
      rejected: allTasks.filter((t) => t.status === 'rejected').length
    }
  } catch {
    ElMessage.error('获取任务失败')
  } finally {
    loading.value = false
  }
}

const openReview = (row, decision) => {
  currentTask.value = row
  reviewForm.value = { decision, reviewer: '', comment: '' }
  dialogVisible.value = true
}

const goDetail = (row) => {
  router.push(`/manual/${row.task_id}`)
}

const submitReview = async () => {
  if (!reviewForm.value.reviewer.trim()) {
    ElMessage.warning('请输入审核人姓名')
    return
  }
  submitting.value = true
  try {
    await submitManualReview({ task_id: currentTask.value.task_id, ...reviewForm.value })
    ElMessage.success('审核已提交')
    dialogVisible.value = false
    fetchTasks()
  } catch (error) {
    ElMessage.error(`提交失败：${error.response?.data?.detail || error.message}`)
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
  font-size: 32px;
  font-weight: 700;
  color: #2563eb;
}

.stat-label {
  color: #64748b;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rule-tag {
  margin-right: 4px;
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

.content-box {
  margin: 18px 0;
  padding: 14px;
  background: #f8fafc;
  border-radius: 6px;
  line-height: 1.6;
}
</style>
