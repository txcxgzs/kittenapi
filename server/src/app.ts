import express from 'express'
import cors from 'cors'
import path from 'path'
import { config, validateConfig } from './core/config'
import { ConnectionManager } from './core/connection-manager'
import { initDatabase } from './models/database'
import { SettingsModel } from './models/settings'
import { ipFilter } from './middleware/ip-filter'
import { apiLogger } from './middleware/logger'
import { authMiddleware } from './middleware/auth'
import routes from './routes'
import { logger } from './utils/logger'
import crypto from 'crypto'

const app = express()

const allowedOrigins = [
  'http://localhost:3000',
  'http://localhost:5173',
  'http://localhost:8080',
  'http://localhost:9178',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:5173',
  'http://127.0.0.1:8080',
  'http://127.0.0.1:9178'
]

const corsOptions = {
  origin: function (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) {
    if (!origin || allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true)
    } else {
      callback(null, true)
    }
  },
  credentials: true
}

app.use(cors(corsOptions))
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.use(ipFilter)
app.use(apiLogger)
app.use(authMiddleware)

app.use('/api', routes)

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  })
})

const webDistPath = path.join(__dirname, '../../web/dist')
const webExists = require('fs').existsSync(webDistPath)

if (webExists) {
  app.use(express.static(webDistPath))
  
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api')) {
      return next()
    }
    res.sendFile(path.join(webDistPath, 'index.html'))
  })
} else {
  app.get('/', (req, res) => {
    res.json({
      name: 'Kitten Cloud API',
      version: '1.0.0',
      message: '前端未构建，请先运行 cd web && npm run build',
      endpoints: {
        api: '/api',
        connections: '/api/connections',
        variable: '/api/var',
        list: '/api/list',
        online: '/api/online',
        user: '/api/user',
        admin: '/api/admin'
      }
    })
  })
}

app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'NOT_FOUND',
    message: '接口不存在'
  })
})

app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Error:', err)
  res.status(500).json({
    success: false,
    error: 'INTERNAL_ERROR',
    message: err.message || '服务器内部错误'
  })
})

function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password + 'kitten-cloud-api-salt').digest('hex')
}

function initAdminPassword(): void {
  const envPassword = process.env.ADMIN_PASSWORD
  
  if (envPassword && envPassword.length >= 6) {
    const currentPassword = SettingsModel.get('adminPassword')
    
    if (!currentPassword) {
      SettingsModel.set('adminPassword', hashPassword(envPassword))
      logger.info('管理员密码已从环境变量初始化')
    }
  }
}

async function start() {
  validateConfig()
  
  logger.info('正在初始化数据库...')
  await initDatabase()
  logger.info('数据库初始化完成')
  
  initAdminPassword()
  
  await ConnectionManager.initialize()
  
  app.listen(config.port, config.host, () => {
    logger.info('Kitten Cloud API 服务已启动')
    logger.info(`地址: http://${config.host}:${config.port}`)
    logger.info(`API 文档: http://${config.host}:${config.port}/api`)
    if (webExists) {
      logger.info(`管理后台: http://${config.host}:${config.port}`)
    } else {
      logger.info('提示: 前端未构建，请运行 cd web && npm run build')
    }
  })
}

process.on('SIGINT', async () => {
  logger.info('正在关闭服务...')
  await ConnectionManager.disconnectAll()
  process.exit(0)
})

process.on('SIGTERM', async () => {
  logger.info('正在关闭服务...')
  await ConnectionManager.disconnectAll()
  process.exit(0)
})

start().catch((err) => logger.error('启动失败:', err))
