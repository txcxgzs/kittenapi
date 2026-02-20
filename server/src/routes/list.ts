import { Router, Request, Response } from 'express'
import { ConnectionManager } from '../core/connection-manager'
import { isValidWorkId, isValidString, isValidNonNegativeNumber, hasValue } from '../utils/validation'

const router = Router()

async function getList(workId: number, name: string) {
  const connection = await ConnectionManager.ensureConnection(workId)
  return await connection.list.get(name)
}

function sendErrorResponse(res: Response, statusCode: number, errorCode: string, message: string): void {
  res.status(statusCode).json({
    success: false,
    error: errorCode,
    message
  })
}

function sendInvalidParamError(res: Response, paramName: string): void {
  sendErrorResponse(res, 400, 'INVALID_PARAMS', `${paramName} 参数无效`)
}

function sendInternalError(res: Response, error: unknown, defaultMessage: string): void {
  const message = error instanceof Error ? error.message : defaultMessage
  sendErrorResponse(res, 500, 'INTERNAL_ERROR', message)
}

function sendListNotFoundError(res: Response, error: unknown, defaultMessage: string): void {
  const message = error instanceof Error ? error.message : defaultMessage
  sendErrorResponse(res, 500, 'LIST_NOT_FOUND', message)
}

function validateRequiredString(value: unknown): value is string {
  return isValidString(value)
}

function validateNonNegativeNumber(value: unknown): value is number {
  return isValidNonNegativeNumber(value)
}

function validateRequiredValue(value: unknown): boolean {
  return hasValue(value)
}

function validateWorkId(workId: unknown): workId is number {
  return isValidWorkId(workId)
}

router.get('/:workId', async (req: Request, res: Response): Promise<void> => {
  try {
    const workId = parseInt(req.params.workId, 10)
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    const connection = await ConnectionManager.ensureConnection(workId)
    const lists = await connection.list.getAll()
    
    res.json({
      success: true,
      data: {
        lists: lists.map(l => ({
          name: l.name,
          length: l.length,
          items: l.copy(),
          cvid: l.cvid
        }))
      }
    })
  } catch (error) {
    sendInternalError(res, error, '获取列表失败')
  }
})

router.get('/:workId/:name', async (req: Request, res: Response): Promise<void> => {
  try {
    const workId = parseInt(req.params.workId, 10)
    const name = req.params.name
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    const list = await getList(workId, name)
    
    res.json({
      success: true,
      data: {
        name,
        length: list.length,
        items: list.copy()
      }
    })
  } catch (error) {
    sendListNotFoundError(res, error, '获取列表失败')
  }
})

router.post('/get', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    const list = await getList(workId, name)
    
    res.json({
      success: true,
      data: {
        name,
        length: list.length,
        items: list.copy()
      }
    })
  } catch (error) {
    sendListNotFoundError(res, error, '获取列表失败')
  }
})

router.post('/push', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, value } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!validateRequiredValue(value)) {
      return sendInvalidParamError(res, 'value')
    }
    
    const list = await getList(workId, name)
    await list.push(value)
    
    res.json({
      success: true,
      data: {
        newLength: list.length
      },
      message: '尾部添加成功'
    })
  } catch (error) {
    sendInternalError(res, error, '添加失败')
  }
})

router.post('/unshift', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, value } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!validateRequiredValue(value)) {
      return sendInvalidParamError(res, 'value')
    }
    
    const list = await getList(workId, name)
    await list.unshift(value)
    
    res.json({
      success: true,
      data: {
        newLength: list.length
      },
      message: '头部添加成功'
    })
  } catch (error) {
    sendInternalError(res, error, '添加失败')
  }
})

router.post('/add', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, index, value } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!validateNonNegativeNumber(index)) {
      return sendInvalidParamError(res, 'index')
    }
    
    if (!validateRequiredValue(value)) {
      return sendInvalidParamError(res, 'value')
    }
    
    const list = await getList(workId, name)
    await list.add(index, value)
    
    res.json({
      success: true,
      data: {
        newLength: list.length
      },
      message: '指定位置添加成功'
    })
  } catch (error) {
    sendInternalError(res, error, '添加失败')
  }
})

router.post('/pop', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    const list = await getList(workId, name)
    
    if (list.length === 0) {
      return sendErrorResponse(res, 400, 'LIST_EMPTY', '列表为空，无法执行 pop 操作')
    }
    
    const removedItem = list.get(list.length - 1)
    await list.pop()
    
    res.json({
      success: true,
      data: {
        removedItem,
        newLength: list.length
      },
      message: '移除尾部成功'
    })
  } catch (error) {
    sendInternalError(res, error, '移除失败')
  }
})

router.post('/remove', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, index } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!validateNonNegativeNumber(index)) {
      return sendInvalidParamError(res, 'index')
    }
    
    const list = await getList(workId, name)
    
    if (list.length === 0) {
      return sendErrorResponse(res, 400, 'LIST_EMPTY', '列表为空，无法执行 remove 操作')
    }
    
    if (index >= list.length) {
      return sendErrorResponse(res, 400, 'INDEX_OUT_OF_RANGE', `索引 ${index} 超出范围，列表长度为 ${list.length}`)
    }
    
    const removedItem = list.get(index)
    await list.remove(index)
    
    res.json({
      success: true,
      data: {
        removedItem,
        newLength: list.length
      },
      message: '移除成功'
    })
  } catch (error) {
    sendInternalError(res, error, '移除失败')
  }
})

router.post('/empty', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    const list = await getList(workId, name)
    await list.empty()
    
    res.json({
      success: true,
      data: {
        newLength: 0
      },
      message: '清空成功'
    })
  } catch (error) {
    sendInternalError(res, error, '清空失败')
  }
})

router.post('/replace', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, index, value } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!validateNonNegativeNumber(index)) {
      return sendInvalidParamError(res, 'index')
    }
    
    if (!validateRequiredValue(value)) {
      return sendInvalidParamError(res, 'value')
    }
    
    const list = await getList(workId, name)
    
    if (list.length === 0) {
      return sendErrorResponse(res, 400, 'LIST_EMPTY', '列表为空，无法执行 replace 操作')
    }
    
    if (index >= list.length) {
      return sendErrorResponse(res, 400, 'INDEX_OUT_OF_RANGE', `索引 ${index} 超出范围，列表长度为 ${list.length}`)
    }
    
    const originalItem = list.get(index)
    await list.replace(index, value)
    
    res.json({
      success: true,
      data: {
        originalItem,
        newItem: value
      },
      message: '替换成功'
    })
  } catch (error) {
    sendInternalError(res, error, '替换失败')
  }
})

router.post('/replaceLast', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, value } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!validateRequiredValue(value)) {
      return sendInvalidParamError(res, 'value')
    }
    
    const list = await getList(workId, name)
    
    if (list.length === 0) {
      return sendErrorResponse(res, 400, 'LIST_EMPTY', '列表为空，无法执行 replaceLast 操作')
    }
    
    const originalItem = list.get(list.length - 1)
    await list.replaceLast(value)
    
    res.json({
      success: true,
      data: {
        originalItem,
        newItem: value
      },
      message: '替换尾部成功'
    })
  } catch (error) {
    sendInternalError(res, error, '替换失败')
  }
})

router.post('/setAll', async (req: Request, res: Response): Promise<void> => {
  try {
    const { workId, name, items } = req.body
    
    if (!validateWorkId(workId)) {
      return sendInvalidParamError(res, 'workId')
    }
    
    if (!validateRequiredString(name)) {
      return sendInvalidParamError(res, 'name')
    }
    
    if (!Array.isArray(items)) {
      return sendErrorResponse(res, 400, 'INVALID_PARAMS', 'items 参数必须是数组')
    }
    
    const list = await getList(workId, name)
    await list.copyFrom(items)
    
    res.json({
      success: true,
      data: {
        newLength: list.length,
        items: list.copy()
      },
      message: '批量替换成功'
    })
  } catch (error) {
    sendInternalError(res, error, '批量替换失败')
  }
})

export default router
