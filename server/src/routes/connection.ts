import { Router, Request, Response } from 'express'
import { ConnectionManager } from '../core/connection-manager'

const router = Router()

router.get('/', (req: Request, res: Response): void => {
  const connections = ConnectionManager.getAllConnections()
  
  res.json({
    success: true,
    data: {
      connections: connections.map(info => ({
        workId: info.workId,
        status: info.status,
        onlineUsers: info.onlineUsers,
        connectedAt: info.connectedAt,
        error: info.error
      })),
      total: connections.length
    }
  })
})

router.post('/connect', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId } = req.body
    
    if (typeof workId !== 'number' || isNaN(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为数字'
      })
      return
    }

    if (workId <= 0) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为正整数'
      })
      return
    }
    
    const info = await ConnectionManager.connect(workId)
    
    res.json({
      success: true,
      data: {
        workId: info.workId,
        status: info.status,
        onlineUsers: info.onlineUsers,
        connectedAt: info.connectedAt
      },
      message: '连接成功'
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '连接失败'
    
    if (errorMessage.includes('未配置编程猫身份认证')) {
      res.status(401).json({
        success: false,
        error: 'AUTHORIZATION_REQUIRED',
        message: errorMessage
      })
      return
    }

    if (errorMessage.includes('作品 ID 无效')) {
      res.status(400).json({
        success: false,
        error: 'INVALID_WORK_ID',
        message: errorMessage
      })
      return
    }
    
    res.status(500).json({
      success: false,
      error: 'CONNECTION_FAILED',
      message: errorMessage
    })
  }
})

router.post('/disconnect', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId } = req.body
    
    if (typeof workId !== 'number' || isNaN(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为数字'
      })
      return
    }
    
    await ConnectionManager.disconnect(workId)
    
    res.json({
      success: true,
      message: '已断开连接'
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '断开连接失败'
    })
  }
})

export default router
