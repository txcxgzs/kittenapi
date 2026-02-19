import { KittenCloudFunction, CodemaoUser } from 'kitten-cloud-function'
import { config, configManager } from './config'
import { logger } from '../utils/logger'

export interface ConnectionInfo {
  workId: number
  connection: KittenCloudFunction
  connectedAt: Date
  status: 'connecting' | 'connected' | 'disconnected' | 'error'
  onlineUsers: number
  error?: string
}

class ConnectionManagerClass {
  private connections: Map<number, ConnectionInfo> = new Map()
  private initialized: boolean = false
  private authorizationValid: boolean | null = null

  async initialize(): Promise<void> {
    if (this.initialized) return
    
    if (config.codemaoAuthorization) {
      try {
        await CodemaoUser.setAuthorization(config.codemaoAuthorization)
        this.authorizationValid = true
        logger.info('已设置编程猫身份认证')
      } catch (error) {
        this.authorizationValid = false
        logger.error('设置编程猫身份认证失败:', error)
      }
    }
    
    this.initialized = true
  }

  isAuthorizationValid(): boolean | null {
    return this.authorizationValid
  }

  hasAuthorization(): boolean {
    return configManager.hasAuthorization()
  }

  async setAuthorization(authorization: string): Promise<{ success: boolean; message: string }> {
    try {
      await CodemaoUser.setAuthorization(authorization)
      configManager.setAuthorization(authorization)
      this.authorizationValid = true
      this.initialized = true
      return { success: true, message: '身份认证设置成功' }
    } catch (error) {
      return { 
        success: false, 
        message: error instanceof Error ? error.message : '设置身份认证失败' 
      }
    }
  }

  async verifyAuthorization(authorization: string): Promise<{ valid: boolean; userInfo?: { id: number; nickname: string }; error?: string }> {
    try {
      const tempUser = new CodemaoUser()
      await CodemaoUser.setAuthorization(authorization)
      const id = await tempUser.info.id
      const nickname = await tempUser.info.nickname
      return { valid: true, userInfo: { id, nickname } }
    } catch (error) {
      return { 
        valid: false, 
        error: error instanceof Error ? error.message : '身份认证无效' 
      }
    }
  }

  async connect(workId: number): Promise<ConnectionInfo> {
    if (workId <= 0) {
      throw new Error('作品 ID 无效，必须为正整数')
    }

    if (!config.codemaoAuthorization) {
      throw new Error('未配置编程猫身份认证，请先在后台设置 Cookie')
    }

    if (this.connections.has(workId)) {
      const existing = this.connections.get(workId)!
      if (existing.status === 'connected') {
        return existing
      }
      await this.disconnect(workId)
    }

    await this.initialize()

    const connection = new KittenCloudFunction(workId)
    
    const info: ConnectionInfo = {
      workId,
      connection,
      connectedAt: new Date(),
      status: 'connecting',
      onlineUsers: 0
    }
    this.connections.set(workId, info)

    connection.opened.connect(() => {
      info.status = 'connected'
      info.connectedAt = new Date()
      logger.info(`[连接] 作品 ${workId} 连接成功`)
    })

    connection.disconnected.connect(() => {
      info.status = 'disconnected'
      logger.info(`[断开] 作品 ${workId} 连接断开`)
    })

    connection.closed.connect(() => {
      info.status = 'disconnected'
      logger.info(`[关闭] 作品 ${workId} 连接关闭`)
    })

    connection.errored.connect((error: unknown) => {
      info.status = 'error'
      info.error = error instanceof Error ? error.message : String(error)
      logger.error(`[错误] 作品 ${workId}:`, info.error)
    })

    connection.onlineUserNumber.then((onlineUserNumber) => {
      info.onlineUsers = onlineUserNumber.value
      onlineUserNumber.changed.connect((msg) => {
        info.onlineUsers = msg.newNumber
      })
    }).catch((err) => {
      logger.error(`[在线人数] 作品 ${workId} 获取失败:`, err)
    })

    try {
      await connection.waitOpen()
      info.status = 'connected'
      return info
    } catch (error) {
      info.status = 'error'
      info.error = error instanceof Error ? error.message : String(error)
      throw error
    }
  }

  async disconnect(workId: number): Promise<void> {
    const info = this.connections.get(workId)
    if (info) {
      try {
        info.connection.close()
      } catch (e) {
        // ignore
      }
      this.connections.delete(workId)
      logger.info(`[断开] 作品 ${workId} 已断开连接`)
    }
  }

  getConnection(workId: number): KittenCloudFunction | undefined {
    return this.connections.get(workId)?.connection
  }

  getConnectionInfo(workId: number): ConnectionInfo | undefined {
    return this.connections.get(workId)
  }

  getAllConnections(): ConnectionInfo[] {
    return Array.from(this.connections.values())
  }

  async ensureConnection(workId: number): Promise<KittenCloudFunction> {
    if (workId <= 0) {
      throw new Error('作品 ID 无效，必须为正整数')
    }
    
    const info = this.connections.get(workId)
    if (info && info.status === 'connected') {
      return info.connection
    }
    const newInfo = await this.connect(workId)
    return newInfo.connection
  }

  async disconnectAll(): Promise<void> {
    for (const workId of this.connections.keys()) {
      await this.disconnect(workId)
    }
  }
}

export const ConnectionManager = new ConnectionManagerClass()
