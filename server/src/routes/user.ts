import { Router, Request, Response } from 'express'
import { KittenCloudFunction } from 'kitten-cloud-function'
import { ConnectionManager } from '../core/connection-manager'

const router = Router()

router.get('/info', async (req: Request, res: Response): Promise<void> => {
  try {
    if (!ConnectionManager.hasAuthorization()) {
      res.status(503).json({
        success: false,
        error: 'SERVICE_UNAVAILABLE',
        message: '用户服务未初始化，请先配置身份认证'
      })
      return
    }

    await ConnectionManager.waitForInitialization()

    const isValid = ConnectionManager.isAuthorizationValid()
    if (isValid === false) {
      res.status(401).json({
        success: false,
        error: 'AUTHORIZATION_INVALID',
        message: '身份认证已失效，请重新配置'
      })
      return
    }
    
    const user = KittenCloudFunction.user
    
    try {
      const info = {
        id: await user.info.id,
        nickname: await user.info.nickname,
        username: await user.info.username,
        avatarURL: await user.info.avatarURL,
        description: await user.info.description,
        grade: await user.info.grade,
        email: await user.info.email
      }
      
      res.json({
        success: true,
        data: info
      })
    } catch (userError) {
      res.status(401).json({
        success: false,
        error: 'AUTHORIZATION_INVALID',
        message: '身份认证无效或已过期，请检查 Cookie 配置'
      })
    }
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取用户信息失败'
    })
  }
})

export default router
