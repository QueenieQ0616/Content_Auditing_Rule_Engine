import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const registerAccount = (data) => api.post('/auth/register', data)
export const loginAccount = (data) => api.post('/auth/login', data)
export const getCurrentUser = () => api.get('/auth/me')
export const logoutAccount = () => api.post('/auth/logout')
export const reviewContent = (data) => api.post('/review', data)
export const batchReviewContent = (data) => api.post('/review/batch', data)
export const traceContent = (data) => api.post('/trace', data)
export const getReviewHistory = (params) => api.get('/review/history', { params })
export const getRules = () => api.get('/rules')
export const getManualTasks = (status = 'pending') => api.get('/manual/tasks', { params: { status } })
export const getManualTaskDetail = (taskId) => api.get(`/manual/tasks/${taskId}`)
export const submitManualReview = (data) => api.post('/manual/review', data)
export const getStatistics = () => api.get('/stats')
export const healthCheck = () => api.get('/health', { baseURL: '' })

export default api
