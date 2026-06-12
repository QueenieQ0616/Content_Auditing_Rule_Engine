<template>
  <div class="manual-detail">
    <div class="detail-topbar">
      <el-page-header title="返回队列" content="人工审核详情" @back="router.push('/manual')" />
      <div class="task-switcher">
        <el-button :disabled="!prevTask" :icon="ArrowLeft" @click="switchTask(prevTask)">上一个</el-button>
        <span class="task-position">{{ taskPositionText }}</span>
        <el-button type="primary" plain :disabled="!nextTask" @click="switchTask(nextTask)">
          下一个
          <el-icon class="right-icon"><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" class="detail-layout">
      <el-col :span="16">
        <el-card class="detail-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>任务详情</span>
              <el-tag v-if="task" :type="statusType(task.status)">{{ statusText(task.status) }}</el-tag>
            </div>
          </template>

          <template v-if="task">
            <el-descriptions :column="2" border class="meta-box">
              <el-descriptions-item label="任务 ID">{{ task.task_id }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ task.created_at }}</el-descriptions-item>
              <el-descriptions-item label="机器建议">
                <el-tag :type="decisionType(task.machine_decision)">{{ decisionText(task.machine_decision) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="机器分数">
                <el-progress :percentage="Math.round(task.machine_score * 100)" :color="scoreColor(task.machine_score)" :stroke-width="14" />
              </el-descriptions-item>
            </el-descriptions>

            <section class="content-section">
              <h3>完整待审核内容</h3>
              <div class="full-content">{{ task.content }}</div>
            </section>

            <section class="content-section">
              <h3>命中规则</h3>
              <el-empty v-if="!task.hit_rules || task.hit_rules.length === 0" description="未命中规则" />
              <el-table v-else :data="task.hit_rules" border stripe>
                <el-table-column prop="rule_id" label="规则 ID" width="120" />
                <el-table-column prop="name" label="规则名称" />
                <el-table-column prop="level" label="等级" width="100">
                  <template #default="{ row }">
                    <el-tag :type="levelType(row.level)">{{ row.level }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </template>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="review-card">
          <template #header>
            <span>人工判定</span>
          </template>

          <template v-if="task">
            <el-alert
              v-if="task.status !== 'pending'"
              :title="`该任务已处理：${statusText(task.status)}`"
              :type="statusType(task.status)"
              :closable="false"
              show-icon
              class="handled-alert"
            />

            <el-form :model="reviewForm" label-position="top">
              <el-form-item label="审核结果">
                <el-radio-group v-model="reviewForm.decision" :disabled="task.status !== 'pending'">
                  <el-radio-button label="pass">放行</el-radio-button>
                  <el-radio-button label="review">继续转人工</el-radio-button>
                  <el-radio-button label="reject">拦截</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="审核人">
                <el-input v-model="reviewForm.reviewer" :disabled="task.status !== 'pending'" placeholder="请输入审核人姓名" />
              </el-form-item>

              <el-form-item label="审核意见">
                <el-input v-model="reviewForm.comment" type="textarea" :rows="5" :disabled="task.status !== 'pending'" placeholder="可选：填写审核意见" />
              </el-form-item>

              <el-button type="primary" size="large" class="submit-btn" :loading="submitting" :disabled="task.status !== 'pending'" @click="submitReview">
                提交审核
              </el-button>
            </el-form>
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { getManualTaskDetail, getManualTasks, submitManualReview } from '../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const task = ref(null)
const taskList = ref([])
const reviewForm = ref({ decision: 'pass', reviewer: '', comment: '' })

const scoreColor = (score) => (score >= 0.7 ? '#f56c6c' : score >= 0.35 ? '#e6a23c' : '#67c23a')
const decisionType = (decision) => ({ pass: 'success', review: 'warning', reject: 'danger' }[decision] || 'info')
const decisionText = (decision) => ({ pass: '放行', review: '转人工', reject: '拦截' }[decision] || decision)
const levelType = (level) => ({ L1: 'info', L2: 'warning', L3: 'danger' }[level] || 'info')
const statusType = (status) => ({ pending: 'warning', approved: 'success', rejected: 'danger' }[status] || 'info')
const statusText = (status) => ({ pending: '待审核', approved: '已通过', rejected: '已拒绝' }[status] || status)

const currentIndex = computed(() => taskList.value.findIndex((item) => item.task_id === route.params.taskId))
const prevTask = computed(() => (currentIndex.value > 0 ? taskList.value[currentIndex.value - 1] : null))
const nextTask = computed(() => (
  currentIndex.value >= 0 && currentIndex.value < taskList.value.length - 1 ? taskList.value[currentIndex.value + 1] : null
))
const taskPositionText = computed(() => {
  if (!taskList.value.length || currentIndex.value < 0) return '当前任务'
  return `${currentIndex.value + 1} / ${taskList.value.length}`
})

const fetchTaskList = async () => {
  const res = await getManualTasks('all')
  taskList.value = res.data.tasks || []
}

const fetchTask = async () => {
  loading.value = true
  try {
    const [detailRes] = await Promise.all([getManualTaskDetail(route.params.taskId), fetchTaskList()])
    task.value = detailRes.data
    reviewForm.value = { decision: 'pass', reviewer: '', comment: '' }
  } catch (error) {
    ElMessage.error(`获取任务详情失败：${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const switchTask = (targetTask) => {
  if (targetTask) router.push(`/manual/${targetTask.task_id}`)
}

const submitReview = async () => {
  if (!reviewForm.value.reviewer.trim()) {
    ElMessage.warning('请输入审核人姓名')
    return
  }
  submitting.value = true
  try {
    await submitManualReview({ task_id: task.value.task_id, ...reviewForm.value })
    ElMessage.success('审核已提交')
    await fetchTask()
  } catch (error) {
    ElMessage.error(`提交失败：${error.response?.data?.detail || error.message}`)
  } finally {
    submitting.value = false
  }
}

onMounted(fetchTask)
watch(() => route.params.taskId, fetchTask)
</script>

<style scoped>
.manual-detail {
  max-width: 1280px;
  margin: 0 auto;
}

.detail-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.task-switcher {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.task-position {
  min-width: 58px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}

.right-icon {
  margin-left: 4px;
}

.detail-layout {
  margin-top: 18px;
}

.detail-card,
.review-card {
  min-height: 380px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meta-box {
  margin-bottom: 22px;
}

.content-section {
  margin-top: 22px;
}

.content-section h3 {
  margin: 0 0 12px;
  color: #1f2937;
  font-size: 16px;
}

.full-content {
  min-height: 220px;
  max-height: 520px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  color: #1f2937;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 18px;
}

.handled-alert {
  margin-bottom: 18px;
}

.submit-btn {
  width: 100%;
}
</style>
