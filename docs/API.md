# API 接口文档

> 本文档描述 Kitten Cloud API 系统的所有接口

---

## 一、接口规范

### 1.1 基础信息

- **Base URL**: `http://your-server:3000/api`
- **Content-Type**: `application/json`
- **认证方式**: API Key（可选，在请求头添加 `X-API-Key`）

### 1.2 统一响应格式

**成功响应**
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

**错误响应**
```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "错误详情"
}
```

### 1.3 HTTP 方法使用规则

| 方法 | 用途 |
|------|------|
| GET | 查询操作（获取数据） |
| POST | 所有写操作和部分查询（推荐） |

---

## 二、连接管理

### 2.1 连接到作品

**POST** `/api/connection/connect`

连接到指定作品，建立 WebSocket 通信。

**请求体**
```json
{
  "workId": 114514
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workId | number | 是 | 作品 ID |

**响应**
```json
{
  "success": true,
  "data": {
    "workId": 114514,
    "status": "connected",
    "onlineUsers": 5,
    "connectedAt": "2026-02-15T10:00:00Z"
  },
  "message": "连接成功"
}
```

---

### 2.2 断开连接

**POST** `/api/connection/disconnect`

断开与指定作品的连接。

**请求体**
```json
{
  "workId": 114514
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workId | number | 是 | 作品 ID |

**响应**
```json
{
  "success": true,
  "message": "已断开连接"
}
```

---

### 2.3 获取所有连接状态

**GET** `/api/connections`

获取当前系统所有活跃连接。

**响应**
```json
{
  "success": true,
  "data": {
    "connections": [
      {
        "workId": 114514,
        "status": "connected",
        "onlineUsers": 5,
        "connectedAt": "2026-02-15T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

---

## 三、云变量操作

### 3.1 获取云变量值

**GET** `/api/var/:workId/:name`

获取指定作品的云变量值。

**URL 参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| workId | number | 作品 ID |
| name | string | 变量名 |

**响应**
```json
{
  "success": true,
  "data": {
    "name": "分数",
    "value": 100,
    "type": "public",
    "cvid": "xxx"
  }
}
```

---

### 3.2 获取云变量值（POST）

**POST** `/api/var/get`

**请求体**
```json
{
  "workId": 114514,
  "name": "分数"
}
```

---

### 3.3 设置云变量值

**POST** `/api/var/set`

设置指定作品的云变量值。

**请求体**
```json
{
  "workId": 114514,
  "name": "分数",
  "value": 999,
  "type": "public"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workId | number | 是 | 作品 ID |
| name | string | 是 | 变量名 |
| value | string \| number | 是 | 新值 |
| type | string | 否 | 变量类型：`public`(默认) 或 `private` |

**响应**
```json
{
  "success": true,
  "message": "设置成功"
}
```

---

### 3.4 获取作品所有云变量

**GET** `/api/var/:workId`

获取指定作品的所有云变量。

**响应**
```json
{
  "success": true,
  "data": {
    "publicVariables": [
      { "name": "分数", "value": 100, "cvid": "xxx" }
    ],
    "privateVariables": [
      { "name": "金币", "value": 50, "cvid": "yyy" }
    ]
  }
}
```

---

### 3.5 获取私有变量排行榜

**POST** `/api/var/rank`

获取私有云变量排行榜。

**请求体**
```json
{
  "workId": 114514,
  "name": "金币",
  "limit": 10,
  "order": -1
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workId | number | 是 | 作品 ID |
| name | string | 是 | 变量名 |
| limit | number | 否 | 数量限制，默认 10 |
| order | number | 否 | 排序：1(顺序)，-1(逆序，默认) |

**响应**
```json
{
  "success": true,
  "data": {
    "rankingList": [
      {
        "rank": 1,
        "value": 9999,
        "userId": 12345,
        "nickname": "玩家A",
        "avatarURL": "https://..."
      }
    ]
  }
}
```

---

## 四、云列表操作

### 4.1 获取所有云列表

**GET** `/api/list/:workId`

获取作品所有云列表。

**响应**
```json
{
  "success": true,
  "data": {
    "lists": [
      {
        "name": "排行榜",
        "length": 10,
        "items": ["玩家A", "玩家B", "玩家C"],
        "cvid": "xxx"
      }
    ]
  }
}
```

---

### 4.2 获取指定云列表

**GET** `/api/list/:workId/:name`

获取云列表内容。

**响应**
```json
{
  "success": true,
  "data": {
    "name": "排行榜",
    "length": 10,
    "items": ["玩家A", "玩家B", "玩家C"]
  }
}
```

---

### 4.2 尾部添加项

**POST** `/api/list/push`

在云列表尾部添加一项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "value": "新玩家"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workId | number | 是 | 作品 ID |
| name | string | 是 | 列表名 |
| value | string \| number | 是 | 添加的值 |

**响应**
```json
{
  "success": true,
  "data": {
    "newLength": 11
  }
}
```

---

### 4.3 头部添加项

**POST** `/api/list/unshift`

在云列表头部添加一项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "value": "新玩家"
}
```

---

### 4.4 指定位置添加项

**POST** `/api/list/add`

在云列表指定位置添加一项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "index": 0,
  "value": "新玩家"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 位置索引（从 0 开始） |

---

### 4.5 移除尾部项

**POST** `/api/list/pop`

移除云列表最后一项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜"
}
```

**响应**
```json
{
  "success": true,
  "data": {
    "removedItem": "最后一名",
    "newLength": 9
  }
}
```

---

### 4.6 移除指定位置项

**POST** `/api/list/remove`

移除云列表指定位置的项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "index": 0
}
```

---

### 4.7 清空列表

**POST** `/api/list/empty`

清空整个云列表。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜"
}
```

---

### 4.8 替换指定位置项

**POST** `/api/list/replace`

替换云列表指定位置的项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "index": 0,
  "value": "新第一名"
}
```

---

### 4.9 替换尾部项

**POST** `/api/list/replaceLast`

替换云列表最后一项。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "value": "新最后一名"
}
```

---

### 4.10 批量替换列表

**POST** `/api/list/setAll`

用新数组完全替换云列表。

**请求体**
```json
{
  "workId": 114514,
  "name": "排行榜",
  "items": ["第一名", "第二名", "第三名"]
}
```

---

## 五、在线人数

### 5.1 获取在线人数

**GET** `/api/online/:workId`

获取指定作品的在线人数。

**响应**
```json
{
  "success": true,
  "data": {
    "workId": 114514,
    "onlineUsers": 5
  }
}
```

**POST** `/api/online`

**请求体**
```json
{
  "workId": 114514
}
```

---

## 六、用户信息

### 6.1 获取当前登录用户信息

**GET** `/api/user/info`

获取当前配置的编程猫账号信息。

**响应**
```json
{
  "success": true,
  "data": {
    "id": 12345,
    "nickname": "用户昵称",
    "username": "username",
    "avatarURL": "https://...",
    "grade": 10
  }
}
```

---

## 七、后台管理 API

### 7.1 获取 API 调用日志

**GET** `/api/admin/logs`

**请求参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | number | 页码，默认 1 |
| limit | number | 每页数量，默认 20 |
| ip | string | 筛选 IP |
| path | string | 筛选路径 |

**响应**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "timestamp": "2026-02-15T10:00:00Z",
        "ip": "127.0.0.1",
        "method": "POST",
        "path": "/api/var/set",
        "body": "{\"workId\":114514}",
        "status": 200,
        "response_time": 50
      }
    ],
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

---

### 7.2 IP 黑名单管理

#### 获取黑名单列表

**GET** `/api/admin/blacklist`

**响应**
```json
{
  "success": true,
  "data": {
    "blacklist": [
      {
        "id": 1,
        "ip": "192.168.1.100",
        "reason": "恶意请求",
        "created_at": "2026-02-15T10:00:00Z"
      }
    ]
  }
}
```

#### 添加 IP 到黑名单

**POST** `/api/admin/blacklist/add`

**请求体**
```json
{
  "ip": "192.168.1.100",
  "reason": "恶意请求"
}
```

#### 从黑名单移除 IP

**POST** `/api/admin/blacklist/remove`

**请求体**
```json
{
  "ip": "192.168.1.100"
}
```

---

### 7.3 系统设置

#### 获取设置

**GET** `/api/admin/settings`

**响应**
```json
{
  "success": true,
  "data": {
    "apiKeyEnabled": true,
    "logRetentionDays": 30
  }
}
```

#### 更新设置

**POST** `/api/admin/settings`

**请求体**
```json
{
  "logRetentionDays": 30
}
```

---

## 八、错误码

| 错误码 | 说明 |
|--------|------|
| `INVALID_PARAMS` | 参数错误 |
| `WORK_NOT_CONNECTED` | 作品未连接 |
| `VARIABLE_NOT_FOUND` | 变量不存在 |
| `LIST_NOT_FOUND` | 列表不存在 |
| `CONNECTION_FAILED` | 连接失败 |
| `UNAUTHORIZED` | 未授权（IP 被拉黑或 API Key 错误） |
| `NOT_FOUND` | 接口不存在 |
| `INTERNAL_ERROR` | 内部错误 |

---

## 九、调用示例

### cURL

```bash
# 连接作品
curl -X POST http://localhost:3000/api/connection/connect \
  -H "Content-Type: application/json" \
  -d '{"workId": 114514}'

# 设置变量
curl -X POST http://localhost:3000/api/var/set \
  -H "Content-Type: application/json" \
  -d '{"workId": 114514, "name": "分数", "value": 100}'

# 获取列表
curl -X GET http://localhost:3000/api/list/114514/排行榜
```

### JavaScript (Axios)

```javascript
const axios = require('axios')
const BASE_URL = 'http://localhost:3000/api'

// 连接作品
await axios.post(`${BASE_URL}/connection/connect`, { workId: 114514 })

// 设置变量
await axios.post(`${BASE_URL}/var/set`, {
  workId: 114514,
  name: '分数',
  value: 100
})

// 获取列表
const { data } = await axios.get(`${BASE_URL}/list/114514/排行榜`)
console.log(data.data.items)
```

### Python (requests)

```python
import requests

BASE_URL = 'http://localhost:3000/api'

# 连接作品
requests.post(f'{BASE_URL}/connection/connect', json={'workId': 114514})

# 设置变量
requests.post(f'{BASE_URL}/var/set', json={
    'workId': 114514,
    'name': '分数',
    'value': 100
})

# 获取列表
resp = requests.get(f'{BASE_URL}/list/114514/排行榜')
print(resp.json()['data']['items'])
```

---

**文档版本**：1.0
**最后更新**：2026-02-15
