import { Request, Response, NextFunction } from 'express'
import { isValidSession, hasPassword } from '../routes/auth'
import { SettingsModel } from '../models/settings'

const PUBLIC_PATHS = [
  '/health',
  '/api/connection/connect',
  '/api/connection/disconnect',
  '/api/connections',
  '/api/var/',
  '/api/list/',
  '/api/online',
  '/api/user/'
]

function isPublicPath(path: string): boolean {
  return PUBLIC_PATHS.some(p => path.startsWith(p))
}

function hasApiKey(): boolean {
  const apiKey = SettingsModel.get('apiKey')
  return apiKey !== null && apiKey.length > 0
}

export function sessionAuthMiddleware(req: Request, res: Response, next: NextFunction): void {
  if (!hasPassword()) {
    next()
    return
  }
  
  if (isPublicPath(req.path)) {
    if (!hasApiKey()) {
      next()
      return
    }
    
    const apiKey = req.headers['x-api-key'] as string || req.query.apiKey as string
    const storedApiKey = SettingsModel.get('apiKey')
    
    if (apiKey && apiKey === storedApiKey) {
      next()
      return
    }
    
    res.status(401).json({
      success: false,
      error: 'UNAUTHORIZED',
      message: 'API Key 无效'
    })
    return
  }
  
  const token = req.headers['x-auth-token'] as string
  
  if (!token || !isValidSession(token)) {
    res.status(401).json({
      success: false,
      error: 'UNAUTHORIZED',
      message: '未登录或会话已过期'
    })
    return
  }
  
  next()
}

export function adminAuthMiddleware(req: Request, res: Response, next: NextFunction): void {
  if (!hasPassword()) {
    next()
    return
  }
  
  const token = req.headers['x-auth-token'] as string
  
  if (!token || !isValidSession(token)) {
    res.status(401).json({
      success: false,
      error: 'UNAUTHORIZED',
      message: '未登录或会话已过期'
    })
    return
  }
  
  next()
}

export const authMiddleware = sessionAuthMiddleware
