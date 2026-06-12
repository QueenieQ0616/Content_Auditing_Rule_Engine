<template>
  <router-view v-if="$route.meta.public" />
  <el-container v-else class="app-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28"><Shield /></el-icon>
        <span>审核引擎</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#263241"
        text-color="#cbd5e1"
        active-text-color="#67e8f9"
      >
        <el-menu-item index="/">
          <el-icon><Search /></el-icon>
          <span>内容审核</span>
        </el-menu-item>
        <el-menu-item index="/batch">
          <el-icon><Files /></el-icon>
          <span>批量审核</span>
        </el-menu-item>
        <el-menu-item index="/manual">
          <el-icon><UserFilled /></el-icon>
          <span class="menu-label">
            人工队列
            <el-badge v-if="pendingCount > 0" :value="pendingCount" class="menu-badge" />
          </span>
        </el-menu-item>
        <el-menu-item index="/trace">
          <el-icon><Connection /></el-icon>
          <span>命中过程</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><TrendCharts /></el-icon>
          <span>统计看板</span>
        </el-menu-item>
      </el-menu>

    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ $route.meta.title }}</div>
        <div class="header-actions">
          <el-tag type="success" effect="dark">运行中</el-tag>
          <el-dropdown @command="handleUserCommand">
            <span class="user-entry">
              <el-icon><User /></el-icon>
              {{ currentUser?.username || '未登录' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>角色：{{ currentUser?.role || 'user' }}</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getManualTasks, logoutAccount } from './api'

const route = useRoute()
const router = useRouter()
const pendingCount = ref(0)
const currentUser = ref(null)
let timer = null

const activeMenu = computed(() => {
  if (route.path.startsWith('/manual')) return '/manual'
  return route.path
})

const fetchPendingCount = async () => {
  try {
    const res = await getManualTasks('pending')
    pendingCount.value = res.data.total || 0
  } catch {
    pendingCount.value = 0
  }
}

const loadCurrentUser = () => {
  try {
    currentUser.value = JSON.parse(localStorage.getItem('auth_user') || 'null')
  } catch {
    currentUser.value = null
  }
}

const handleUserCommand = async (command) => {
  if (command !== 'logout') return
  try {
    await logoutAccount()
  } catch {
    // 退出时即使服务端会话已失效，也清理本地登录态。
  }
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_user')
  currentUser.value = null
  router.push('/login')
}

onMounted(() => {
  loadCurrentUser()
  window.addEventListener('auth-changed', loadCurrentUser)
  fetchPendingCount()
  timer = setInterval(fetchPendingCount, 5000)
})

onUnmounted(() => {
  window.removeEventListener('auth-changed', loadCurrentUser)
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: #263241;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 18px;
  font-weight: 700;
  box-sizing: border-box;
  padding: 0 16px;
  letter-spacing: 1px;
}

.logo :deep(.el-icon) {
  flex-shrink: 0;
}

.sidebar-menu {
  flex: 1;
  border-right: 0;
}

.menu-badge {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.menu-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  line-height: 1;
}

.menu-badge :deep(.el-badge__content) {
  transform: translateY(-1px);
}

.sidebar-footer {
  padding: 14px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.header {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-entry {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #334155;
  cursor: pointer;
  outline: none;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
