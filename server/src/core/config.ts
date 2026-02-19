import dotenv from 'dotenv'
import path from 'path'
import fs from 'fs'

dotenv.config()

export interface Config {
  port: number
  host: string
  codemaoAuthorization: string
  apiKey: string | null
  logRetentionDays: number
  databasePath: string
}

class ConfigManager {
  private _config: Config
  private envPath: string

  constructor() {
    this.envPath = path.join(__dirname, '../../.env')
    this._config = {
      port: parseInt(process.env.PORT || '9178', 10),
      host: process.env.HOST || '0.0.0.0',
      codemaoAuthorization: process.env.CODEMAO_AUTHORIZATION || '',
      apiKey: process.env.API_KEY || null,
      logRetentionDays: parseInt(process.env.LOG_RETENTION_DAYS || '30', 10),
      databasePath: process.env.DATABASE_PATH || path.join(__dirname, '../../data/kitten-cloud.db')
    }
  }

  get config(): Config {
    return this._config
  }

  hasAuthorization(): boolean {
    return !!this._config.codemaoAuthorization
  }

  setAuthorization(authorization: string): void {
    this._config.codemaoAuthorization = authorization
    this.saveToEnv('CODEMAO_AUTHORIZATION', authorization)
  }

  setPort(port: number): void {
    this._config.port = port
    this.saveToEnv('PORT', port.toString())
  }

  setApiKey(key: string | null): void {
    this._config.apiKey = key
    if (key) {
      this.saveToEnv('API_KEY', key)
    } else {
      this.removeEnvKey('API_KEY')
    }
  }

  setLogRetentionDays(days: number): void {
    this._config.logRetentionDays = days
    this.saveToEnv('LOG_RETENTION_DAYS', days.toString())
  }

  private saveToEnv(key: string, value: string): void {
    let content = ''
    
    if (fs.existsSync(this.envPath)) {
      content = fs.readFileSync(this.envPath, 'utf-8')
    }

    const lines = content.split('\n')
    let found = false
    const newLines = lines.map(line => {
      if (line.startsWith(`${key}=`) || line.startsWith(`# ${key}=`)) {
        found = true
        return `${key}=${value}`
      }
      return line
    })

    if (!found) {
      newLines.push(`${key}=${value}`)
    }

    fs.writeFileSync(this.envPath, newLines.join('\n'), 'utf-8')
  }

  private removeEnvKey(key: string): void {
    if (!fs.existsSync(this.envPath)) return

    const content = fs.readFileSync(this.envPath, 'utf-8')
    const lines = content.split('\n')
    const newLines = lines.filter(line => !line.startsWith(`${key}=`))

    fs.writeFileSync(this.envPath, newLines.join('\n'), 'utf-8')
  }
}

export const configManager = new ConfigManager()
export const config = configManager.config

export function validateConfig(): void {
  if (!config.codemaoAuthorization) {
    console.warn('警告: CODEMAO_AUTHORIZATION 未配置，部分功能可能无法使用')
  }
}
