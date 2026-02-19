import { Router, Request, Response } from 'express'
import { SettingsModel } from '../models/settings'
import crypto from 'crypto'

const router = Router()

const SESSION_TIMEOUT = 24 * 60 * 60 * 1000
const sessions: Map<string, { createdAt: number }> = new Map()

const MAX_LOGIN_ATTEMPTS = 5
const LOCKOUT_TIME = 15 * 60 * 1000
const loginAttempts: Map<string, { count: number; lockUntil: number }> = new Map()

function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password + 'kitten-cloud-api-salt').digest('hex')
}

function generateToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

function cleanExpiredSessions(): void {
  const now = Date.now()
  for (const [token, session] of sessions.entries()) {
    if (now - session.createdAt > SESSION_TIMEOUT) {
      sessions.delete(token)
    }
  }
}

function getClientIp(req: Request): string {
  return (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() || 
         req.socket.remoteAddress || 
         'unknown'
}

function checkLoginAttempts(ip: string): { allowed: boolean; remainingAttempts: number; lockTimeRemaining: number } {
  const now = Date.now()
  const attempts = loginAttempts.get(ip)
  
  if (!attempts) {
    return { allowed: true, remainingAttempts: MAX_LOGIN_ATTEMPTS, lockTimeRemaining: 0 }
  }
  
  if (attempts.lockUntil && now < attempts.lockUntil) {
    return { 
      allowed: false, 
      remainingAttempts: 0, 
      lockTimeRemaining: Math.ceil((attempts.lockUntil - now) / 1000) 
    }
  }
  
  if (attempts.lockUntil && now >= attempts.lockUntil) {
    loginAttempts.delete(ip)
    return { allowed: true, remainingAttempts: MAX_LOGIN_ATTEMPTS, lockTimeRemaining: 0 }
  }
  
  return { 
    allowed: true, 
    remainingAttempts: MAX_LOGIN_ATTEMPTS - attempts.count, 
    lockTimeRemaining: 0 
  }
}

function recordFailedAttempt(ip: string): void {
  const now = Date.now()
  const attempts = loginAttempts.get(ip) || { count: 0, lockUntil: 0 }
  
  attempts.count++
  
  if (attempts.count >= MAX_LOGIN_ATTEMPTS) {
    attempts.lockUntil = now + LOCKOUT_TIME
  }
  
  loginAttempts.set(ip, attempts)
}

function clearLoginAttempts(ip: string): void {
  loginAttempts.delete(ip)
}

export function isValidSession(token: string): boolean {
  cleanExpiredSessions()
  const session = sessions.get(token)
  if (!session) return false
  if (Date.now() - session.createdAt > SESSION_TIMEOUT) {
    sessions.delete(token)
    return false
  }
  return true
}

export function hasPassword(): boolean {
  return SettingsModel.get('adminPassword') !== null
}

router.post('/login', async (req: Request, res: Response): Promise<void> => {
  const { password } = req.body
  const ip = getClientIp(req)
  
  if (!password || typeof password !== 'string') {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: '密码参数无效'
    })
    return
  }
  
  const attemptCheck = checkLoginAttempts(ip)
  if (!attemptCheck.allowed) {
    res.status(429).json({
      success: false,
      error: 'TOO_MANY_ATTEMPTS',
      message: `登录失败次数过多，请 ${attemptCheck.lockTimeRemaining} 秒后重试`
    })
    return
  }
  
  const storedPassword = SettingsModel.get('adminPassword')
  
  if (!storedPassword) {
    res.status(400).json({
      success: false,
      error: 'NO_PASSWORD_SET',
      message: '系统未设置密码，请先通过部署脚本设置'
    })
    return
  }
  
  await new Promise(resolve => setTimeout(resolve, 500))
  
  if (hashPassword(password) !== storedPassword) {
    recordFailedAttempt(ip)
    const remaining = attemptCheck.remainingAttempts - 1
    
    if (remaining <= 0) {
      res.status(429).json({
        success: false,
        error: 'TOO_MANY_ATTEMPTS',
        message: '密码错误次数过多，账户已锁定15分钟'
      })
    } else {
      res.status(401).json({
        success: false,
        error: 'INVALID_PASSWORD',
        message: `密码错误，还剩 ${remaining} 次尝试机会`
      })
    }
    return
  }
  
  clearLoginAttempts(ip)
  
  const token = generateToken()
  sessions.set(token, { createdAt: Date.now() })
  
  res.json({
    success: true,
    message: '登录成功',
    data: { token }
  })
})

router.post('/logout', (req: Request, res: Response): void => {
  const token = req.headers['x-auth-token'] as string
  
  if (token && sessions.has(token)) {
    sessions.delete(token)
  }
  
  res.json({
    success: true,
    message: '已退出登录'
  })
})

router.post('/change-password', (req: Request, res: Response): void => {
  const { oldPassword, newPassword } = req.body
  const token = req.headers['x-auth-token'] as string
  
  if (!token || !isValidSession(token)) {
    res.status(401).json({
      success: false,
      error: 'UNAUTHORIZED',
      message: '未登录或会话已过期'
    })
    return
  }
  
  if (!oldPassword || !newPassword || typeof oldPassword !== 'string' || typeof newPassword !== 'string') {
    res.status(400).json({
      success: false,
      error: 'INVALID_PARAMS',
      message: '密码参数无效'
    })
    return
  }
  
  if (newPassword.length < 6) {
    res.status(400).json({
      success: false,
      error: 'INVALID_PASSWORD',
      message: '新密码长度至少6位'
    })
    return
  }
  
  const storedPassword = SettingsModel.get('adminPassword')
  
  if (!storedPassword || hashPassword(oldPassword) !== storedPassword) {
    res.status(401).json({
      success: false,
      error: 'INVALID_PASSWORD',
      message: '原密码错误'
    })
    return
  }
  
  SettingsModel.set('adminPassword', hashPassword(newPassword))
  
  res.json({
    success: true,
    message: '密码修改成功'
  })
})

router.get('/status', (req: Request, res: Response): void => {
  res.json({
    success: true,
    data: {
      hasPassword: hasPassword()
    }
  })
})

router.post('/init', (req: Request, res: Response): void => {
  const { password } = req.body
  
  if (hasPassword()) {
    res.status(400).json({
      success: false,
      error: 'ALREADY_INITIALIZED',
      message: '密码已设置'
    })
    return
  }
  
  if (!password || typeof password !== 'string' || password.length < 6) {
    res.status(400).json({
      success: false,
      error: 'INVALID_PASSWORD',
      message: '密码长度至少6位'
    })
    return
  }
  
  SettingsModel.set('adminPassword', hashPassword(password))
  
  const token = generateToken()
  sessions.set(token, { createdAt: Date.now() })
  
  res.json({
    success: true,
    message: '密码设置成功',
    data: { token }
  })
})

export default router
