<template>
  <div class="ip-blacklist">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>IP 黑名单管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            添加 IP
          </el-button>
        </div>
      </template>
      
      <el-table :data="blacklist" style="width: 100%">
        <el-table-column prop="ip" label="IP 地址" width="200" />
        <el-table-column prop="reason" label="封禁原因" />
        <el-table-column prop="created_at" label="添加时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="removeIp(row.ip)">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" title="添加 IP 到黑名单" width="400px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="IP 地址">
          <el-input v-model="addForm.ip" placeholder="请输入 IP 地址" />
        </el-form-item>
        <el-form-item label="封禁原因">
          <el-input v-model="addForm.reason" placeholder="请输入封禁原因（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addIp">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi, type BlacklistItem } from '../api'

const blacklist = ref<BlacklistItem[]>([])
const showAddDialog = ref(false)
const addForm = ref({ ip: '', reason: '' })

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

async function loadData() {
  try {
    const res = await adminApi.getBlacklist()
    if (res.data.success && res.data.data) {
      blacklist.value = res.data.data.blacklist || []
    }
  } catch (e) {
    console.error(e)
  }
}

async function addIp() {
  if (!addForm.value.ip) {
    ElMessage.warning('请输入 IP 地址')
    return
  }
  
  try {
    const res = await adminApi.addBlacklist(addForm.value.ip, addForm.value.reason)
    if (res.data.success) {
      ElMessage.success('添加成功')
      showAddDialog.value = false
      addForm.value = { ip: '', reason: '' }
      loadData()
    }
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeIp(ip: string) {
  try {
    await ElMessageBox.confirm(`确定要将 ${ip} 从黑名单移除吗？`, '确认')
    const res = await adminApi.removeBlacklist(ip)
    if (res.data.success) {
      ElMessage.success('移除成功')
      loadData()
    }
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
</style>
