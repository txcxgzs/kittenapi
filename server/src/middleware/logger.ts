import { Request, Response, NextFunction } from 'express'
import { ApiLogModel } from '../models/api-log'
import { getClientIp } from './ip-filter'

const IGNORE_PATHS = [
  '/assets/',
  '/index.html',
  '/favicon.ico',
  '.js',
  '.css',
  '.png',
  '.jpg',
  '.ico',
  '.svg',
  '.woff',
  '.woff2',
  '.ttf'
]

const IGNORE_ADMIN_GET_PATHS = [
  '/admin/logs',
  '/admin/status',
  '/admin/settings',
  '/admin/authorization',
  '/admin/blacklist'
]

const IGNORE_EXACT_PATHS = [
  '/',
  '/health'
]

function shouldIgnore(path: string, method: string): boolean {
  if (IGNORE_PATHS.some(ignore => path.includes(ignore))) {
    return true
  }
  if (IGNORE_EXACT_PATHS.includes(path)) {
    return true
  }
  if (method === 'GET' && IGNORE_ADMIN_GET_PATHS.some(ignore => path.includes(ignore))) {
    return true
  }
  return false
}

export function apiLogger(req: Request, res: Response, next: NextFunction): void {
  if (shouldIgnore(req.path, req.method)) {
    return next()
  }
  
  const startTime = Date.now()
  const ip = getClientIp(req)
  
  let responseBody: unknown
  const originalJson = res.json.bind(res)
  res.json = (body: unknown): Response => {
    responseBody = body
    return originalJson(body)
  }
  
  res.on('finish', () => {
    const duration = Date.now() - startTime
    const logData = {
      ip,
      method: req.method,
      path: req.path,
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
      status: res.statusCode,
      response_time: duration,
      error: res.statusCode >= 400 && responseBody && typeof responseBody === 'object' && 'message' in responseBody
        ? (responseBody as { message?: string }).message
        : undefined
    }
    
    try {
      ApiLogModel.create(logData)
    } catch (e) {
      console.error('记录 API 日志失败:', e)
    }
  })
  
  next()
}
