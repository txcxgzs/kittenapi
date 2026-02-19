import { Router, Request, Response } from 'express'
import { ApiLogModel } from '../models/api-log'
import { IpBlacklistModel } from '../models/ip-blacklist'
import { SettingsModel } from '../models/settings'
import { config, configManager } from '../core/config'
import { ConnectionManager } from '../core/connection-manager'
import { adminAuthMiddleware } from '../middleware/auth'

const router = Router()

router.use(adminAuthMiddleware)

router.get('/status', (req: Request, res: Response): void => {
  const connections = ConnectionManager.getAllConnections()
  
  res.json({
    success: true,
    data: {
      server: {
        port: config.port,
        host: config.host,
        uptime: process.uptime()
      },
      authorization: {
        configured: ConnectionManager.hasAuthorization(),
        valid: ConnectionManager.isAuthorizationValid()
      },
      connections: {
        total: connections.length,
        connected: connections.filter(c => c.status === 'connected').length
      },
      apiKey: {
        enabled: !!config.apiKey
      }
    }
  })
})

router.get('/logs', (req: Request, res: Response): void => {
  const page = parseInt(req.query.page as string, 10) || 1
  const limit = parseInt(req.query.limit as string, 10) || 20
  const ip = req.query.ip as string | undefined
  const path = req.query.path as string | undefined
  
  const result = ApiLogModel.findAll({ page, limit, ip, path })
  
  res.json({
    success: true,
    data: result
  })
})

router.delete('/logs', (req: Request, res: Response): void => {
  ApiLogModel.clear()
  res.json({
    success: true,
    message: '日志已清空'
  })
})

router.get('/blacklist', (req: Request, res: Response): void => {
  const blacklist = IpBlacklistModel.findAll()
  
  res.json({
    success: true,
    data: {
      blacklist
    }
  })
})

router.post('/blacklist/add', (req: Request, res: Response): void => {
  const { ip, reason } = req.body
  
  if (!ip || typeof ip !== 'string') {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: 'ip 参数无效'
    })
    return
  }

  const ipParts = ip.split('.')
  if (ipParts.length !== 4) {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: 'IP 地址格式无效'
    })
    return
  }
  
  for (const part of ipParts) {
    const num = parseInt(part, 10)
    if (isNaN(num) || num < 0 || num > 255) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'IP 地址格式无效，每段必须在 0-255 之间'
      })
      return
    }
  }
  
  const added = IpBlacklistModel.add(ip, reason)
  
  if (added) {
    res.json({
      success: true,
      message: 'IP 已添加到黑名单'
    })
  } else {
    res.json({
      success: true,
      message: 'IP 已在黑名单中'
    })
  }
})

router.post('/blacklist/remove', (req: Request, res: Response): void => {
  const { ip } = req.body
  
  if (!ip || typeof ip !== 'string') {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: 'ip 参数无效'
    })
    return
  }
  
  const removed = IpBlacklistModel.remove(ip)
  
  if (removed) {
    res.json({
      success: true,
      message: 'IP 已从黑名单移除'
    })
  } else {
    res.json({
      success: true,
      message: 'IP 不在黑名单中'
    })
  }
})

router.delete('/blacklist', (req: Request, res: Response): void => {
  IpBlacklistModel.clear()
  res.json({
    success: true,
    message: '黑名单已清空'
  })
})

router.get('/settings', (req: Request, res: Response): void => {
  const settings = SettingsModel.getAll()
  const storedLogRetentionDays = settings.logRetentionDays
    ? parseInt(settings.logRetentionDays, 10)
    : config.logRetentionDays
  
  res.json({
    success: true,
    data: {
      port: config.port,
      apiKeyEnabled: !!config.apiKey,
      logRetentionDays: storedLogRetentionDays,
      authorizationConfigured: ConnectionManager.hasAuthorization()
    }
  })
})

router.post('/settings', (req: Request, res: Response): void => {
  const { logRetentionDays, apiKey } = req.body
  
  if (typeof logRetentionDays === 'number' && logRetentionDays > 0) {
    SettingsModel.set('logRetentionDays', logRetentionDays.toString())
    configManager.setLogRetentionDays(logRetentionDays)
  }
  
  if (apiKey !== undefined) {
    if (apiKey === '' || apiKey === null) {
      configManager.setApiKey(null)
    } else if (typeof apiKey === 'string') {
      if (apiKey.length < 8) {
        res.status(400).json({
          success: false,
          error: 'INVALID_API_KEY',
          message: 'API Key 长度必须至少8位'
        })
        return
      }
      configManager.setApiKey(apiKey)
    }
  }
  
  res.json({
    success: true,
    message: '设置已保存'
  })
})

router.post('/settings/port', (req: Request, res: Response): void => {
  const { port } = req.body
  
  if (typeof port !== 'number' || port < 1 || port > 65535) {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: '端口号必须在 1-65535 之间'
    })
    return
  }
  
  configManager.setPort(port)
  
  res.json({
    success: true,
    message: '端口已更新，重启服务后生效',
    data: { port }
  })
})

router.get('/authorization', (req: Request, res: Response): void => {
  res.json({
    success: true,
    data: {
      configured: ConnectionManager.hasAuthorization(),
      valid: ConnectionManager.isAuthorizationValid()
    }
  })
})

router.post('/authorization/verify', async (req: Request, res: Response): Promise<void> => {
  const { authorization } = req.body
  
  if (!authorization || typeof authorization !== 'string') {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: 'authorization 参数无效'
    })
    return
  }
  
  const result = await ConnectionManager.verifyAuthorization(authorization)
  
  if (result.valid) {
    res.json({
      success: true,
      message: '身份认证有效',
      data: {
        userInfo: result.userInfo
      }
    })
  } else {
    res.json({
      success: false,
      error: 'INVALID_AUTHORIZATION',
      message: result.error || '身份认证无效'
    })
  }
})

router.post('/authorization/set', async (req: Request, res: Response): Promise<void> => {
  const { authorization } = req.body
  
  if (!authorization || typeof authorization !== 'string') {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: 'authorization 参数无效'
    })
    return
  }
  
  if (ConnectionManager.hasAuthorization()) {
    res.json({
      success: false,
      error: 'ALREADY_CONFIGURED',
      message: '身份认证已配置，如需更换请先清除'
    })
    return
  }
  
  const verifyResult = await ConnectionManager.verifyAuthorization(authorization)
  
  if (!verifyResult.valid) {
    res.status(400).json({
      success: false,
      error: 'INVALID_AUTHORIZATION',
      message: verifyResult.error || '身份认证无效'
    })
    return
  }
  
  const result = await ConnectionManager.setAuthorization(authorization)
  
  if (result.success) {
    res.json({
      success: true,
      message: '身份认证设置成功',
      data: {
        userInfo: verifyResult.userInfo
      }
    })
  } else {
    res.status(500).json({
      success: false,
      error: 'SET_FAILED',
      message: result.message
    })
  }
})

router.delete('/authorization', (req: Request, res: Response): void => {
  if (!ConnectionManager.hasAuthorization()) {
    res.json({
      success: true,
      message: '身份认证未配置'
    })
    return
  }
  
  configManager.setAuthorization('')
  
  res.json({
    success: true,
    message: '身份认证已清除，重启服务后生效'
  })
})

router.post('/connections/disconnect-all', async (req: Request, res: Response): Promise<void> => {
  await ConnectionManager.disconnectAll()
  res.json({
    success: true,
    message: '所有连接已断开'
  })
})

export default router
