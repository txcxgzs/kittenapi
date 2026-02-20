import { Router, Request, Response } from 'express'
import { ConnectionManager } from '../core/connection-manager'
import { KittenCloudVariable } from 'kitten-cloud-function'
import { isValidWorkId, isValidString, hasValue } from '../utils/validation'

const router = Router()

router.get('/:workId/:name', async (req: Request, res: Response): Promise<void> => {
  try {
    const workId = parseInt(req.params.workId, 10)
    const name = req.params.name
    
    if (!isValidWorkId(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为正整数'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    
    let variable: KittenCloudVariable
    let type = 'unknown'
    
    try {
      variable = await connection.publicVariable.get(name)
      type = 'public'
    } catch {
      try {
        variable = await connection.privateVariable.get(name)
        type = 'private'
      } catch {
        res.status(404).json({
          success: false,
          error: 'VARIABLE_NOT_FOUND',
          message: `变量 ${name} 不存在`
        })
        return
      }
    }
    
    res.json({
      success: true,
      data: {
        name,
        value: variable.get(),
        type,
        cvid: variable.cvid
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取变量失败'
    })
  }
})

router.get('/:workId', async (req: Request, res: Response): Promise<void> => {
  try {
    const workId = parseInt(req.params.workId, 10)
    
    if (!isValidWorkId(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为正整数'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    
    const publicVariables = await connection.publicVariable.getAll()
    const privateVariables = await connection.privateVariable.getAll()
    
    res.json({
      success: true,
      data: {
        publicVariables: publicVariables.map(v => ({
          name: v.name,
          value: v.get(),
          cvid: v.cvid
        })),
        privateVariables: privateVariables.map(v => ({
          name: v.name,
          value: v.get(),
          cvid: v.cvid
        }))
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取变量列表失败'
    })
  }
})

router.post('/get', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name } = req.body
    
    if (!isValidWorkId(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为正整数'
      })
      return
    }
    
    if (!isValidString(name)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'name 参数无效'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    
    let variable: KittenCloudVariable
    let type = 'unknown'
    
    try {
      variable = await connection.publicVariable.get(name)
      type = 'public'
    } catch {
      try {
        variable = await connection.privateVariable.get(name)
        type = 'private'
      } catch {
        res.status(404).json({
          success: false,
          error: 'VARIABLE_NOT_FOUND',
          message: `变量 ${name} 不存在`
        })
        return
      }
    }
    
    res.json({
      success: true,
      data: {
        name,
        value: variable.get(),
        type,
        cvid: variable.cvid
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取变量失败'
    })
  }
})

router.post('/set', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, value, type = 'public' } = req.body
    
    if (!isValidWorkId(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为正整数'
      })
      return
    }
    
    if (!isValidString(name)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'name 参数无效'
      })
      return
    }
    
    if (!hasValue(value)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'value 参数无效'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    
    let variable: KittenCloudVariable
    
    if (type === 'private') {
      try {
        variable = await connection.privateVariable.get(name)
      } catch {
        res.status(404).json({
          success: false,
          error: 'VARIABLE_NOT_FOUND',
          message: `私有变量 ${name} 不存在`
        })
        return
      }
    } else {
      try {
        variable = await connection.publicVariable.get(name)
      } catch {
        res.status(404).json({
          success: false,
          error: 'VARIABLE_NOT_FOUND',
          message: `公有变量 ${name} 不存在`
        })
        return
      }
    }
    
    await variable.set(value)
    
    res.json({
      success: true,
      message: '设置成功',
      data: {
        name,
        value: variable.get()
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '设置变量失败'
    })
  }
})

router.post('/rank', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, limit = 10, order = -1 } = req.body
    
    if (!isValidWorkId(workId)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'workId 参数无效，必须为正整数'
      })
      return
    }
    
    if (!isValidString(name)) {
      res.status(400).json({
        success: false,
        error: 'INVALID_PARAMS',
        message: 'name 参数无效'
      })
      return
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    
    let variable
    try {
      variable = await connection.privateVariable.get(name)
    } catch {
      res.status(404).json({
        success: false,
        error: 'VARIABLE_NOT_FOUND',
        message: `私有变量 ${name} 不存在`
      })
      return
    }
    
    const rankList = await variable.getRankingList(limit, order)
    
    const result = []
    for (let i = 0; i < rankList.length; i++) {
      const item = rankList[i]
      result.push({
        rank: i + 1,
        value: item.value,
        userId: await item.user.info.id,
        nickname: await item.user.info.nickname,
        avatarURL: await item.user.info.avatarURL
      })
    }
    
    res.json({
      success: true,
      data: {
        rankingList: result
      }
    })
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'INTERNAL_ERROR',
      message: error instanceof Error ? error.message : '获取排行榜失败'
    })
  }
})

export default router
