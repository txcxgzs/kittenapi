<template>
  <div class="api-logs">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>API 调用日志</span>
          <div class="header-actions">
            <el-input
              v-model="filters.ip"
              placeholder="筛选 IP"
              style="width: 150px; margin-right: 10px"
              @change="loadData"
            />
            <el-input
              v-model="filters.path"
              placeholder="筛选路径"
              style="width: 200px; margin-right: 10px"
              @change="loadData"
            />
            <el-button type="danger" @click="clearLogs">清空日志</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="logs" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getMethodType(row.method)">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" width="200" />
        <el-table-column prop="body" label="请求体">
          <template #default="{ row }">
            <el-tooltip v-if="row.body" :content="row.body" placement="top">
              <span class="body-text">{{ truncate(row.body, 50) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态码" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_time" label="耗时(ms)" width="100" />
        <el-table-column prop="error" label="错误">
          <template #default="{ row }">
            <span v-if="row.error" class="error-text">{{ row.error }}</span>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="limit"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi, type ApiLog } from '../api'

const logs = ref<ApiLog[]>([])
const page = ref(1)
const limit = ref(20)
const total = ref(0)
const filters = ref({ ip: '', path: '' })

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

function getMethodType(method: string) {
  switch (method) {
    case 'GET': return 'success'
    case 'POST': return 'primary'
    case 'PUT': return 'warning'
    case 'DELETE': return 'danger'
    default: return 'info'
  }
}

function getStatusType(status: number | null) {
  if (!status) return 'info'
  if (status >= 200 && status < 300) return 'success'
  if (status >= 400 && status < 500) return 'warning'
  if (status >= 500) return 'danger'
  return 'info'
}

function truncate(str: string, len: number) {
  if (str.length <= len) return str
  return str.substring(0, len) + '...'
}

async function loadData() {
  try {
    const res = await adminApi.getLogs({
      page: page.value,
      limit: limit.value,
      ip: filters.value.ip || undefined,
      path: filters.value.path || undefined
    })
    if (res.data.success && res.data.data) {
      logs.value = res.data.data.logs || []
      total.value = res.data.data.total || 0
    }
  } catch (e) {
    console.error(e)
  }
}

async function clearLogs() {
  try {
    await ElMessageBox.confirm('确定要清空所有日志吗？', '警告', {
      type: 'warning'
    })
    await adminApi.clearLogs()
    ElMessage.success('日志已清空')
    loadData()
  } catch (e) {
    // 取消
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.body-text {
  color: #606266;
  font-size: 12px;
}

.error-text {
  color: #F56C6C;
  font-size: 12px;
}
</style>
