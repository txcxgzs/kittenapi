import { Request, Response, NextFunction } from 'express'
import { IpBlacklistModel } from '../models/ip-blacklist'

export function ipFilter(req: Request, res: Response, next: NextFunction): void {
  const ip = getClientIp(req)
  
  if (IpBlacklistModel.exists(ip)) {
    res.status(403).json({
      success: false,
      error: 'IP_BLOCKED',
      message: '您的 IP 已被封禁'
    })
    return
  }
  
  next()
}

export function getClientIp(req: Request): string {
  const forwarded = req.headers['x-forwarded-for']
  if (typeof forwarded === 'string') {
    return forwarded.split(',')[0].trim()
  }
  if (Array.isArray(forwarded)) {
    return forwarded[0].trim()
  }
  
  const realIp = req.headers['x-real-ip']
  if (typeof realIp === 'string') {
    return realIp
  }
  
  return req.ip || req.socket.remoteAddress || 'unknown'
}
