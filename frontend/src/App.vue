<template>
  <el-container class="app-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28"><Shield /></el-icon>
        <span>审核引擎</span>
      </div>

      <el-menu
        :default-active="$route.path"
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
        <el-menu-item index="/manual">
          <el-icon><UserFilled /></el-icon>
          <span>人工队列</span>
          <el-badge v-if="pendingCount > 0" :value="pendingCount" class="menu-badge" />
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><TrendCharts /></el-icon>
          <span>统计看板</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-tag type="success" size="small">merged v2 + engine</el-tag>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ $route.meta.title }}</div>
        <el-tag type="success" effect="dark">运行中</el-tag>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getManualTasks } from './api'

const pendingCount = ref(0)
let timer = null

const fetchPendingCount = async () => {
  try {
    const res = await getManualTasks('pending')
    pendingCount.value = res.data.total || 0
  } catch {
    pendingCount.value = 0
  }
}

onMounted(() => {
  fetchPendingCount()
  timer = setInterval(fetchPendingCount, 5000)
})

onUnmounted(() => {
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
}

.sidebar-menu {
  flex: 1;
  border-right: 0;
}

.menu-badge {
  margin-left: 8px;
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
