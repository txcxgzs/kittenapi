<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>服务器状态</span>
      </template>
      
      <el-descriptions :column="2" border v-if="serverStatus">
        <el-descriptions-item label="运行端口">{{ serverStatus.server.port }}</el-descriptions-item>
        <el-descriptions-item label="运行时间">{{ formatUptime(serverStatus.server.uptime) }}</el-descriptions-item>
        <el-descriptions-item label="活跃连接">{{ serverStatus.connections.connected }} / {{ serverStatus.connections.total }}</el-descriptions-item>
        <el-descriptions-item label="API Key">
          <el-tag :type="serverStatus.apiKey.enabled ? 'success' : 'info'">
            {{ serverStatus.apiKey.enabled ? '已启用' : '未启用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>修改密码</span>
      </template>
      
      <el-form :model="passwordForm" label-width="120px" style="max-width: 400px">
        <el-form-item label="原密码">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="changePassword" :loading="changingPassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>身份认证配置</span>
          <el-tag v-if="authStatus?.configured" type="success">已配置</el-tag>
          <el-tag v-else type="warning">未配置</el-tag>
        </div>
      </template>
      
      <template v-if="!authStatus?.configured">
        <el-alert type="warning" :closable="false" style="margin-bottom: 20px">
          未配置编程猫身份认证，请先设置 Cookie 才能使用云功能
        </el-alert>
        
        <el-form :model="authForm" label-width="120px">
          <el-form-item label="Cookie">
            <el-input
              v-model="authForm.authorization"
              type="textarea"
              :rows="3"
              placeholder="请粘贴编程猫 Cookie 中的 authorization 值"
            />
          </el-form-item>
          <el-form-item>
            <el-button @click="verifyAuth" :loading="verifying">验证</el-button>
            <el-button type="primary" @click="setAuth" :loading="settingAuth" :disabled="!authVerified">
              保存
            </el-button>
          </el-form-item>
        </el-form>
        
        <el-alert v-if="authVerifyResult" :type="authVerifyResult.valid ? 'success' : 'error'" :closable="false">
          <template v-if="authVerifyResult.valid">
            验证成功！用户：{{ authVerifyResult.userInfo?.nickname }} (ID: {{ authVerifyResult.userInfo?.id }})
          </template>
          <template v-else>
            验证失败：身份认证无效
          </template>
        </el-alert>
      </template>
      
      <template v-else>
        <el-alert type="success" :closable="false" style="margin-bottom: 20px">
          身份认证已配置，状态：{{ authStatus?.valid ? '有效' : '未知' }}
        </el-alert>
        
        <el-button type="danger" @click="clearAuth" :loading="clearingAuth">
          清除身份认证
        </el-button>
      </template>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>系统设置</span>
      </template>
      
      <el-form :model="settings" label-width="150px" style="max-width: 500px">
        <el-form-item label="服务端口">
          <el-input-number v-model="settings.port" :min="1" :max="65535" />
          <el-button type="primary" size="small" style="margin-left: 10px" @click="setPort" :loading="settingPort">
            更改
          </el-button>
          <div class="form-tip">更改端口后需要重启服务</div>
        </el-form-item>
        
        <el-form-item label="API Key">
          <el-input
            v-model="settings.apiKey"
            placeholder="留空则不启用认证"
            show-password
          />
          <div class="form-tip">设置后访问 API 需要携带 X-API-Key 请求头</div>
        </el-form-item>
        
        <el-form-item label="日志保留天数">
          <el-input-number v-model="settings.logRetentionDays" :min="1" :max="365" />
          <span class="form-tip">超过天数的日志将被自动删除</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>连接管理</span>
      </template>
      
      <el-button type="danger" @click="disconnectAll" :loading="disconnecting">
        断开所有连接
      </el-button>
      <span class="form-tip" style="margin-left: 10px">断开后相关作品将无法访问云数据</span>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  adminApi, 
  authApi,
  type ServerStatus, 
  type AuthorizationStatus,
  type AuthorizationVerifyResult,
  type SettingsResponse
} from '../api'

const serverStatus = ref<ServerStatus | null>(null)
const authStatus = ref<AuthorizationStatus | null>(null)
const authForm = ref({ authorization: '' })
const authVerifyResult = ref<AuthorizationVerifyResult | null>(null)
const authVerified = ref(false)
const verifying = ref(false)
const settingAuth = ref(false)
const clearingAuth = ref(false)
const settingPort = ref(false)
const saving = ref(false)
const disconnecting = ref(false)
const changingPassword = ref(false)

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const settings = ref<{
  port: number
  apiKey: string
  logRetentionDays: number
}>({
  port: 9178,
  apiKey: '',
  logRetentionDays: 30
})

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  
  let result = ''
  if (days > 0) result += `${days}天 `
  if (hours > 0) result += `${hours}小时 `
  result += `${mins}分钟`
  return result
}

async function loadServerStatus() {
  try {
    const res = await adminApi.getStatus()
    if (res.data.success && res.data.data) {
      serverStatus.value = res.data.data
    }
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error('获取服务器状态失败：' + (e instanceof Error ? e.message : '未知错误'))
  }
}

async function loadAuthStatus() {
  try {
    const res = await adminApi.getAuthorization()
    if (res.data.success && res.data.data) {
      authStatus.value = res.data.data
    }
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error('获取认证状态失败：' + (e instanceof Error ? e.message : '未知错误'))
  }
}

async function loadSettings() {
  try {
    const res = await adminApi.getSettings()
    if (res.data.success && res.data.data) {
      const data = res.data.data as SettingsResponse
      settings.value.port = data.port
      settings.value.logRetentionDays = data.logRetentionDays
      settings.value.apiKey = ''
    }
  } catch (e: unknown) {
    console.error(e)
    ElMessage.error('获取设置失败：' + (e instanceof Error ? e.message : '未知错误'))
  }
}

async function verifyAuth() {
  if (!authForm.value.authorization) {
    ElMessage.warning('请输入 Cookie')
    return
  }
  
  verifying.value = true
  authVerifyResult.value = null
  
  try {
    const res = await adminApi.verifyAuthorization(authForm.value.authorization)
    authVerifyResult.value = res.data.data || null
    authVerified.value = res.data.success && !!res.data.data?.valid
    
    if (res.data.success && res.data.data?.valid) {
      ElMessage.success('验证成功')
    } else {
      ElMessage.error(res.data.message || '验证失败')
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    ElMessage.error(err.response?.data?.message || '验证失败')
    authVerified.value = false
  } finally {
    verifying.value = false
  }
}

async function setAuth() {
  if (!authForm.value.authorization) {
    ElMessage.warning('请输入 Cookie')
    return
  }
  
  settingAuth.value = true
  
  try {
    const res = await adminApi.setAuthorization(authForm.value.authorization)
    if (res.data.success) {
      ElMessage.success('身份认证设置成功')
      loadAuthStatus()
      loadServerStatus()
      authForm.value.authorization = ''
      authVerifyResult.value = null
      authVerified.value = false
    } else {
      ElMessage.error(res.data.message || '设置失败')
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    ElMessage.error(err.response?.data?.message || '设置失败')
  } finally {
    settingAuth.value = false
  }
}

async function clearAuth() {
  try {
    await ElMessageBox.confirm('确定要清除身份认证吗？清除后需要重新配置才能使用云功能。', '警告', {
      type: 'warning'
    })
    
    clearingAuth.value = true
    const res = await adminApi.clearAuthorization()
    
    if (res.data.success) {
      ElMessage.success('身份认证已清除')
      loadAuthStatus()
      loadServerStatus()
    }
  } catch (e) {
    // 取消
  } finally {
    clearingAuth.value = false
  }
}

async function setPort() {
  if (settings.value.port < 1 || settings.value.port > 65535) {
    ElMessage.warning('端口号必须在 1-65535 之间')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要将端口更改为 ${settings.value.port} 吗？更改后需要重启服务。`,
      '确认'
    )
    
    settingPort.value = true
    const res = await adminApi.setPort(settings.value.port)
    
    if (res.data.success) {
      ElMessage.success('端口已更新，请重启服务')
      loadServerStatus()
    }
  } catch (e) {
    // 取消
  } finally {
    settingPort.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const res = await adminApi.updateSettings({
      logRetentionDays: settings.value.logRetentionDays,
      apiKey: settings.value.apiKey || null
    })
    if (res.data.success) {
      ElMessage.success('设置已保存')
      loadServerStatus()
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function disconnectAll() {
  try {
    await ElMessageBox.confirm('确定要断开所有连接吗？', '警告', {
      type: 'warning'
    })
    
    disconnecting.value = true
    const res = await adminApi.disconnectAll()
    
    if (res.data.success) {
      ElMessage.success('所有连接已断开')
      loadServerStatus()
    }
  } catch (e) {
    // 取消
  } finally {
    disconnecting.value = false
  }
}

async function changePassword() {
  if (!passwordForm.value.oldPassword) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (!passwordForm.value.newPassword || passwordForm.value.newPassword.length < 6) {
    ElMessage.warning('新密码长度至少6位')
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  
  changingPassword.value = true
  try {
    const res = await authApi.changePassword(passwordForm.value.oldPassword, passwordForm.value.newPassword)
    if (res.data.success) {
      ElMessage.success('密码修改成功')
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
    } else {
      ElMessage.error(res.data.message || '修改失败')
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    ElMessage.error(err.response?.data?.message || '修改失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => {
  loadServerStatus()
  loadAuthStatus()
  loadSettings()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
