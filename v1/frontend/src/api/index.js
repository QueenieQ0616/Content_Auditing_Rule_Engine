import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 内容审核 API
export const reviewContent = (data) => api.post('/review', data)
export const getReviewHistory = (params) => api.get('/review/history', { params })

// 规则管理 API
export const getRules = () => api.get('/rules')

// 人工审核 API
export const getManualTasks = (status = 'pending') => api.get('/manual/tasks', { params: { status } })
export const submitManualReview = (data) => api.post('/manual/review', data)

// 统计 API
export const getStatistics = () => api.get('/stats')

// 健康检查
export const healthCheck = () => api.get('/health', { baseURL: '' })

export default api
