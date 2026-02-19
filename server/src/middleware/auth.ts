import { Request, Response, NextFunction } from 'express'
import { isValidSession, hasPassword } from '../routes/auth'

export function sessionAuthMiddleware(req: Request, res: Response, next: NextFunction): void {
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
