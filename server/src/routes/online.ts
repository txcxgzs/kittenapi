import { Router, Request, Response } from 'express'
import { ConnectionManager } from '../core/connection-manager'
import { KittenCloudFunction } from 'kitten-cloud-function'

const router = Router()

router.get('/:workId', async (req: Request, res: Response): Promise<void> => {
  try {
    const workId = parseInt(req.params.workId, 10)
    
    if (isNaN(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    const onlineUserNumber = await connection.onlineUserNumber
    
    res.json({
      success: true,
      data: {
        workId,
        onlineUsers: onlineUserNumber.value
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取在线人数失败'
    })
  }
})

router.post('/', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId } = req.body
    
    if (!workId || typeof workId !== 'number') {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    const onlineUserNumber = await connection.onlineUserNumber
    
    res.json({
      success: true,
      data: {
        workId,
        onlineUsers: onlineUserNumber.value
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取在线人数失败'
    })
  }
})

export default router
