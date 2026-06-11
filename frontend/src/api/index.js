import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const reviewContent = (data) => api.post('/review', data)
export const getReviewHistory = (params) => api.get('/review/history', { params })
export const getRules = () => api.get('/rules')
export const getManualTasks = (status = 'pending') => api.get('/manual/tasks', { params: { status } })
export const submitManualReview = (data) => api.post('/manual/review', data)
export const getStatistics = () => api.get('/stats')
export const healthCheck = () => api.get('/health', { baseURL: '' })

export default api
