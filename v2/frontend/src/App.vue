<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28" color="#409EFF"><Shield /></el-icon>
        <span class="logo-text">审核引擎</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><Search /></el-icon>
          <span>内容审核</span>
        </el-menu-item>
        
        <el-menu-item index="/manual">
          <el-icon><UserFilled /></el-icon>
          <span>人工审核队列</span>
          <el-badge v-if="pendingCount > 0" :value="pendingCount" class="menu-badge" />
        </el-menu-item>
        
        <el-menu-item index="/stats">
          <el-icon><TrendCharts /></el-icon>
          <span>统计看板</span>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-tag type="info" size="small">W1 骨架版</el-tag>
      </div>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ $route.meta.title || '广告识别规则引擎' }}</div>
        <div class="header-actions">
          <el-tag type="success" effect="dark">运行中</el-tag>
        </div>
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
  } catch (e) {
    // 静默处理
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
  background-color: #304156;
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
  border-bottom: 1px solid #1f2d3d;
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
  color: #fff;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.menu-badge {
  margin-left: 8px;
}

.sidebar-footer {
  padding: 15px;
  text-align: center;
  border-top: 1px solid #1f2d3d;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
