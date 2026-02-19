import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface ConnectionInfo {
  workId: number
  status: string
  onlineUsers: number
  connectedAt: string
  error?: string
}

export interface ConnectionsResponse {
  connections: ConnectionInfo[]
  total: number
}

export interface VariableInfo {
  name: string
  value: string | number
  type?: string
  cvid?: string
}

export interface VariablesResponse {
  publicVariables: VariableInfo[]
  privateVariables: VariableInfo[]
}

export interface ListItem {
  name: string
  length: number
  items: (string | number)[]
}

export interface RankItem {
  rank: number
  value: number
  userId: number
  nickname: string
  avatarURL: string
}

export interface RankResponse {
  rankingList: RankItem[]
}

export interface UserInfo {
  id: number
  username: string
  nickname: string
  avatarURL: string
  email: string
  grade: number
  description: string
}

export interface ApiLog {
  id: number
  timestamp: string
  ip: string
  method: string
  path: string
  body: string | null
  status: number | null
  response_time: number | null
  error: string | null
}

export interface LogsResponse {
  logs: ApiLog[]
  total: number
}

export interface BlacklistItem {
  id: number
  ip: string
  reason: string | null
  created_at: string
}

export interface BlacklistResponse {
  blacklist: BlacklistItem[]
}

export interface SettingsResponse {
  port: number
  apiKeyEnabled: boolean
  logRetentionDays: number
  authorizationConfigured: boolean
}

export interface ServerStatus {
  server: {
    port: number
    host: string
    uptime: number
  }
  authorization: {
    configured: boolean
    valid: boolean | null
  }
  connections: {
    total: number
    connected: number
  }
  apiKey: {
    enabled: boolean
  }
}

export interface AuthorizationStatus {
  configured: boolean
  valid: boolean | null
}

export interface AuthorizationVerifyResult {
  valid: boolean
  userInfo?: {
    id: number
    nickname: string
  }
}

export interface AuthStatus {
  hasPassword: boolean
}

let authToken: string | null = localStorage.getItem('authToken')

export function setAuthToken(token: string | null) {
  authToken = token
  if (token) {
    localStorage.setItem('authToken', token)
    api.defaults.headers.common['x-auth-token'] = token
  } else {
    localStorage.removeItem('authToken')
    delete api.defaults.headers.common['x-auth-token']
  }
}

export function getAuthToken(): string | null {
  return authToken
}

if (authToken) {
  api.defaults.headers.common['x-auth-token'] = authToken
}

export const connectionsApi = {
  getAll: () => api.get<ApiResponse<ConnectionsResponse>>('/connections'),
  connect: (workId: number) => api.post<ApiResponse<ConnectionInfo>>('/connection/connect', { workId }),
  disconnect: (workId: number) => api.post<ApiResponse>('/connection/disconnect', { workId })
}

export const variableApi = {
  get: (workId: number, name: string) => api.get<ApiResponse<VariableInfo>>(`/var/${workId}/${name}`),
  set: (workId: number, name: string, value: string | number, type?: string) => 
    api.post<ApiResponse>('/var/set', { workId, name, value, type }),
  list: (workId: number) => api.get<ApiResponse<VariablesResponse>>(`/var/${workId}`),
  rank: (workId: number, name: string, limit?: number, order?: number) =>
    api.post<ApiResponse<RankResponse>>('/var/rank', { workId, name, limit, order })
}

export const listApi = {
  getAll: (workId: number) => api.get<ApiResponse<{ lists: ListItem[] }>>(`/list/${workId}`),
  get: (workId: number, name: string) => api.get<ApiResponse<ListItem>>(`/list/${workId}/${name}`),
  push: (workId: number, name: string, value: string | number) =>
    api.post<ApiResponse>('/list/push', { workId, name, value }),
  unshift: (workId: number, name: string, value: string | number) =>
    api.post<ApiResponse>('/list/unshift', { workId, name, value }),
  add: (workId: number, name: string, index: number, value: string | number) =>
    api.post<ApiResponse>('/list/add', { workId, name, index, value }),
  pop: (workId: number, name: string) =>
    api.post<ApiResponse>('/list/pop', { workId, name }),
  remove: (workId: number, name: string, index: number) =>
    api.post<ApiResponse>('/list/remove', { workId, name, index }),
  empty: (workId: number, name: string) =>
    api.post<ApiResponse>('/list/empty', { workId, name }),
  replace: (workId: number, name: string, index: number, value: string | number) =>
    api.post<ApiResponse>('/list/replace', { workId, name, index, value }),
  setAll: (workId: number, name: string, items: (string | number)[]) =>
    api.post<ApiResponse>('/list/setAll', { workId, name, items })
}

export const onlineApi = {
  get: (workId: number) => api.get<ApiResponse<{ workId: number; onlineUsers: number }>>(`/online/${workId}`)
}

export const userApi = {
  info: () => api.get<ApiResponse<UserInfo>>('/user/info')
}

export const adminApi = {
  getStatus: () => api.get<ApiResponse<ServerStatus>>('/admin/status'),
  getLogs: (params: { page?: number; limit?: number; ip?: string; path?: string }) =>
    api.get<ApiResponse<LogsResponse>>('/admin/logs', { params }),
  clearLogs: () => api.delete<ApiResponse>('/admin/logs'),
  getBlacklist: () => api.get<ApiResponse<BlacklistResponse>>('/admin/blacklist'),
  addBlacklist: (ip: string, reason?: string) =>
    api.post<ApiResponse>('/admin/blacklist/add', { ip, reason }),
  removeBlacklist: (ip: string) =>
    api.post<ApiResponse>('/admin/blacklist/remove', { ip }),
  clearBlacklist: () => api.delete<ApiResponse>('/admin/blacklist'),
  getSettings: () => api.get<ApiResponse<SettingsResponse>>('/admin/settings'),
  updateSettings: (settings: { logRetentionDays?: number; apiKey?: string | null }) =>
    api.post<ApiResponse>('/admin/settings', settings),
  setPort: (port: number) =>
    api.post<ApiResponse<{ port: number }>>('/admin/settings/port', { port }),
  getAuthorization: () => api.get<ApiResponse<AuthorizationStatus>>('/admin/authorization'),
  verifyAuthorization: (authorization: string) =>
    api.post<ApiResponse<AuthorizationVerifyResult>>('/admin/authorization/verify', { authorization }),
  setAuthorization: (authorization: string) =>
    api.post<ApiResponse<AuthorizationVerifyResult>>('/admin/authorization/set', { authorization }),
  clearAuthorization: () => api.delete<ApiResponse>('/admin/authorization'),
  disconnectAll: () => api.post<ApiResponse>('/admin/connections/disconnect-all')
}

export const authApi = {
  getStatus: () => api.get<ApiResponse<AuthStatus>>('/auth/status'),
  login: (password: string) => api.post<ApiResponse<{ token: string }>>('/auth/login', { password }),
  logout: () => api.post<ApiResponse>('/auth/logout'),
  changePassword: (oldPassword: string, newPassword: string) =>
    api.post<ApiResponse>('/auth/change-password', { oldPassword, newPassword }),
  initPassword: (password: string) =>
    api.post<ApiResponse<{ token: string }>>('/auth/init', { password })
}

export default api
