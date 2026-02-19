<template>
  <div class="api-doc">
    <el-card>
      <template #header>
        <span>API 接口文档</span>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="连接管理" name="connection">
          <div class="api-section">
            <h3>POST /api/connection/connect</h3>
            <p>连接到指定作品</p>
            <pre class="code-block">
{
  "workId": 114514
}</pre>
            
            <h3>POST /api/connection/disconnect</h3>
            <p>断开与指定作品的连接</p>
            <pre class="code-block">
{
  "workId": 114514
}</pre>
            
            <h3>GET /api/connections</h3>
            <p>获取所有活跃连接</p>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="云变量" name="variable">
          <div class="api-section">
            <h3>GET /api/var/:workId/:name</h3>
            <p>获取云变量值</p>
            
            <h3>POST /api/var/get</h3>
            <p>获取云变量值（POST 方式）</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "分数"
}</pre>
            
            <h3>POST /api/var/set</h3>
            <p>设置云变量值</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "分数",
  "value": 100,
  "type": "public"
}</pre>
            
            <h3>GET /api/var/:workId</h3>
            <p>获取作品所有云变量</p>
            
            <h3>POST /api/var/rank</h3>
            <p>获取私有变量排行榜</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "金币",
  "limit": 10,
  "order": -1
}</pre>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="云列表" name="list">
          <div class="api-section">
            <h3>GET /api/list/:workId/:name</h3>
            <p>获取云列表内容</p>
            
            <h3>POST /api/list/push</h3>
            <p>尾部添加项</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "排行榜",
  "value": "新玩家"
}</pre>
            
            <h3>POST /api/list/unshift</h3>
            <p>头部添加项</p>
            
            <h3>POST /api/list/add</h3>
            <p>指定位置添加项</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "排行榜",
  "index": 0,
  "value": "新玩家"
}</pre>
            
            <h3>POST /api/list/pop</h3>
            <p>移除尾部项</p>
            
            <h3>POST /api/list/remove</h3>
            <p>移除指定位置项</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "排行榜",
  "index": 0
}</pre>
            
            <h3>POST /api/list/empty</h3>
            <p>清空列表</p>
            
            <h3>POST /api/list/replace</h3>
            <p>替换指定位置项</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "排行榜",
  "index": 0,
  "value": "新值"
}</pre>
            
            <h3>POST /api/list/setAll</h3>
            <p>批量替换列表</p>
            <pre class="code-block">
{
  "workId": 114514,
  "name": "排行榜",
  "items": ["第一名", "第二名", "第三名"]
}</pre>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="其他" name="other">
          <div class="api-section">
            <h3>GET /api/online/:workId</h3>
            <p>获取作品在线人数</p>
            
            <h3>GET /api/user/info</h3>
            <p>获取当前登录用户信息</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('connection')
</script>

<style scoped>
.api-section {
  padding: 10px 0;
}

.api-section h3 {
  margin: 20px 0 10px;
  color: #303133;
  font-size: 16px;
}

.api-section h3:first-child {
  margin-top: 0;
}

.api-section p {
  color: #606266;
  margin-bottom: 10px;
}

.code-block {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  overflow-x: auto;
}
</style>
