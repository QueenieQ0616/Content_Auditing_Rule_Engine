<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <div class="brand">
            <el-icon size="32"><Shield /></el-icon>
            <div>
              <div class="brand-title">审核引擎</div>
              <div class="brand-subtitle">账号登录与注册</div>
            </div>
          </div>
          <el-tag type="success">Content Auditing</el-tag>
        </div>
      </template>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" />
            </el-form-item>
            <el-button type="primary" class="submit-btn" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" placeholder="3-32 位，支持中文、字母、数字、下划线和短横线" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" show-password placeholder="至少 6 位" />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="registerForm.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
            </el-form-item>
            <el-button type="primary" class="submit-btn" :loading="loading" @click="handleRegister">
              注册并登录
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginAccount, registerAccount } from '../api'

const route = useRoute()
const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)

const loginForm = ref({
  username: '',
  password: ''
})

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const saveAuth = (data) => {
  localStorage.setItem('auth_token', data.token)
  localStorage.setItem('auth_user', JSON.stringify(data.user))
  window.dispatchEvent(new Event('auth-changed'))
}

const redirectAfterAuth = () => {
  router.push(route.query.redirect || '/')
}

const validateBase = (form) => {
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return false
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return false
  }
  return true
}

const handleLogin = async () => {
  if (!validateBase(loginForm.value)) return
  loading.value = true
  try {
    const res = await loginAccount(loginForm.value)
    saveAuth(res.data)
    ElMessage.success('登录成功')
    redirectAfterAuth()
  } catch (error) {
    ElMessage.error(`登录失败：${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!validateBase(registerForm.value)) return
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    const res = await registerAccount({
      username: registerForm.value.username,
      password: registerForm.value.password
    })
    saveAuth(res.data)
    ElMessage.success('注册成功，已自动登录')
    redirectAfterAuth()
  } catch (error) {
    ElMessage.error(`注册失败：${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at top left, rgba(103, 232, 249, 0.18), transparent 32%),
    linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 24px;
}

.login-card {
  width: 460px;
  border: 0;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
}

.login-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1f2937;
}

.brand-title {
  font-size: 20px;
  font-weight: 800;
}

.brand-subtitle {
  color: #64748b;
  font-size: 13px;
  margin-top: 2px;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
}
</style>
