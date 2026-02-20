<template>
  <div v-if="errorOccurred" class="error-container">
    <el-result
      icon="error"
      title="应用出错了"
      sub-title="抱歉，应用遇到了一个错误"
    >
      <template #extra>
        <el-button type="primary" @click="reloadPage">刷新页面</el-button>
      </template>
    </el-result>
  </div>
  <div v-else-if="loading" class="loading-container">
    <el-icon class="is-loading" :size="40"><Loading /></el-icon>
    <p>加载中...</p>
  </div>
  <Login v-else-if="!isLoggedIn" @login-success="handleLoginSuccess" />
  <el-container v-else class="app-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h1>Kitten Cloud API</h1>
      </div>
      <el-menu
        :default-active="currentRoute"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <span>API 日志</span>
        </el-menu-item>
        <el-menu-item index="/blacklist">
          <el-icon><Lock /></el-icon>
          <span>IP 黑名单</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
        <el-menu-item index="/api-doc">
          <el-icon><Notebook /></el-icon>
          <span>API 文档</span>
        </el-menu-item>
      </el-menu>
      <div class="logout-btn">
        <el-button type="danger" text @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>
    </el-aside>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onErrorCaptured } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Monitor, Document, Lock, Setting, Notebook, SwitchButton, Loading } from '@element-plus/icons-vue'
import Login from './views/Login.vue'
import { authApi, setAuthToken, getAuthToken, adminApi } from './api'

const route = useRoute()
const currentRoute = computed(() => route.path)

const loading = ref(true)
const isLoggedIn = ref(false)
const errorOccurred = ref(false)

onErrorCaptured((error: Error) => {
  console.error('应用错误:', error)
  errorOccurred.value = true
  return false
})

const reloadPage = () => {
  window.location.reload()
}

onMounted(async () => {
  try {
    const res = await authApi.getStatus()
    const needsPassword = res.data.data?.hasPassword || false
    
    if (!needsPassword) {
      isLoggedIn.value = true
    } else {
      const token = getAuthToken()
      if (token) {
        try {
          await adminApi.getStatus()
          isLoggedIn.value = true
        } catch (error) {
          setAuthToken(null)
          isLoggedIn.value = false
        }
      }
    }
  } catch (error) {
    console.error('获取认证状态失败:', error)
  } finally {
    loading.value = false
  }
})

const handleLoginSuccess = (token: string) => {
  setAuthToken(token)
  isLoggedIn.value = true
}

const handleLogout = async () => {
  try {
    await authApi.logout()
  } catch (error) {
    // ignore
  }
  setAuthToken(null)
  isLoggedIn.value = false
  ElMessage.success('已退出登录')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

.app-container {
  height: 100%;
}

.sidebar {
  background-color: #304156;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.logo h1 {
  font-size: 16px;
  font-weight: 600;
}

.el-menu {
  border-right: none;
  flex: 1;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}

.logout-btn {
  padding: 10px;
  border-top: 1px solid #3a4a5c;
}

.loading-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #409EFF;
}

.loading-container p {
  margin-top: 10px;
  color: #606266;
}

.error-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
