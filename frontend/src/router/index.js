import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '../views/LoginPage.vue'
import ReviewPage from '../views/ReviewPage.vue'
import BatchReviewPage from '../views/BatchReviewPage.vue'
import ManualQueue from '../views/ManualQueue.vue'
import ManualTaskDetail from '../views/ManualTaskDetail.vue'
import TracePage from '../views/TracePage.vue'
import StatsPage from '../views/StatsPage.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    name: 'Review',
    component: ReviewPage,
    meta: { title: '内容审核', requiresAuth: true }
  },
  {
    path: '/batch',
    name: 'BatchReview',
    component: BatchReviewPage,
    meta: { title: '批量审核', requiresAuth: true }
  },
  {
    path: '/manual',
    name: 'ManualQueue',
    component: ManualQueue,
    meta: { title: '人工审核队列', requiresAuth: true }
  },
  {
    path: '/manual/:taskId',
    name: 'ManualTaskDetail',
    component: ManualTaskDetail,
    meta: { title: '人工审核详情', requiresAuth: true }
  },
  {
    path: '/trace',
    name: 'Trace',
    component: TracePage,
    meta: { title: '命中过程展示', requiresAuth: true }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: StatsPage,
    meta: { title: '统计看板', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('auth_token')
  if (to.meta.requiresAuth && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && token) {
    return '/'
  }
  return true
})

export default router
