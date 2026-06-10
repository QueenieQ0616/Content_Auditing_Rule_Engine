import { createRouter, createWebHistory } from 'vue-router'
import ReviewPage from '../views/ReviewPage.vue'
import ManualQueue from '../views/ManualQueue.vue'
import StatsPage from '../views/StatsPage.vue'

const routes = [
  {
    path: '/',
    name: 'Review',
    component: ReviewPage,
    meta: { title: '内容审核', icon: 'Search' }
  },
  {
    path: '/manual',
    name: 'ManualQueue',
    component: ManualQueue,
    meta: { title: '人工审核队列', icon: 'UserFilled' }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: StatsPage,
    meta: { title: '统计看板', icon: 'TrendCharts' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
