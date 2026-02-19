<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>活跃连接</span>
            </div>
          </template>
          <div class="stat-number">{{ connections.length }}</div>
          <div class="stat-desc">当前连接的作品数</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>总在线人数</span>
            </div>
          </template>
          <div class="stat-number">{{ totalOnline }}</div>
          <div class="stat-desc">所有作品在线人数总和</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>API 调用</span>
            </div>
          </template>
          <div class="stat-number">{{ apiCalls }}</div>
          <div class="stat-desc">今日 API 调用次数</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="connection-card">
      <template #header>
        <div class="card-header">
          <span>连接管理</span>
          <el-button type="primary" @click="showConnectDialog = true">
            新建连接
          </el-button>
        </div>
      </template>
      
      <el-table :data="connections" style="width: 100%">
        <el-table-column prop="workId" label="作品 ID" width="120" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="onlineUsers" label="在线人数" width="100" />
        <el-table-column prop="connectedAt" label="连接时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.connectedAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="error" label="错误信息">
          <template #default="{ row }">
            <span v-if="row.error" class="error-text">{{ row.error }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="disconnect(row.workId)">
              断开
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showConnectDialog" title="新建连接" width="400px">
      <el-form :model="connectForm" label-width="80px">
        <el-form-item label="作品 ID">
          <el-input v-model.number="connectForm.workId" placeholder="请输入作品 ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConnectDialog = false">取消</el-button>
        <el-button type="primary" @click="connect" :loading="connecting">
          连接
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { connectionsApi, adminApi, type ConnectionInfo } from '../api'

const connections = ref<ConnectionInfo[]>([])
const apiCalls = ref(0)
const showConnectDialog = ref(false)
const connecting = ref(false)
const connectForm = ref({ workId: 0 })
let refreshTimer: number | null = null

const totalOnline = computed(() => {
  return connections.value.reduce((sum, c) => sum + c.onlineUsers, 0)
})

function getStatusType(status: string) {
  switch (status) {
    case 'connected': return 'success'
    case 'connecting': return 'warning'
    case 'disconnected': return 'info'
    case 'error': return 'danger'
    default: return 'info'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'connected': return '已连接'
    case 'connecting': return '连接中'
    case 'disconnected': return '已断开'
    case 'error': return '错误'
    default: return status
  }
}

function formatTime(time: string) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadData() {
  try {
    const res = await connectionsApi.getAll()
    if (res.data.success && res.data.data) {
      connections.value = res.data.data.connections || []
    }
  } catch (e) {
    console.error('加载连接数据失败:', e)
  }
}

async function loadApiCalls() {
  try {
    const res = await adminApi.getLogs({ limit: 1000 })
    if (res.data.success && res.data.data) {
      const today = new Date().toDateString()
      const todayLogs = res.data.data.logs?.filter(
        (log: { timestamp: string }) => new Date(log.timestamp).toDateString() === today
      )
      apiCalls.value = todayLogs?.length || 0
    }
  } catch (e) {
    console.error('加载API调用统计失败:', e)
  }
}

async function connect() {
  if (!connectForm.value.workId) {
    ElMessage.warning('请输入作品 ID')
    return
  }
  
  connecting.value = true
  try {
    const res = await connectionsApi.connect(connectForm.value.workId)
    if (res.data.success) {
      ElMessage.success('连接成功')
      showConnectDialog.value = false
      loadData()
    } else {
      ElMessage.error(res.data.message || '连接失败')
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    ElMessage.error(err.response?.data?.message || '连接失败')
  } finally {
    connecting.value = false
  }
}

async function disconnect(workId: number) {
  try {
    const res = await connectionsApi.disconnect(workId)
    if (res.data.success) {
      ElMessage.success('已断开连接')
      loadData()
    }
  } catch (e) {
    console.error('断开连接失败:', e)
    ElMessage.error('断开连接失败')
  }
}

onMounted(() => {
  loadData()
  loadApiCalls()
  refreshTimer = window.setInterval(() => {
    loadData()
    loadApiCalls()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #409EFF;
}

.stat-desc {
  color: #909399;
  margin-top: 10px;
}

.connection-card {
  margin-top: 20px;
}

.error-text {
  color: #F56C6C;
}
</style>
