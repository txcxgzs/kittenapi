import initSqlJs, { Database } from 'sql.js'
import path from 'path'
import fs from 'fs'
import { config } from '../core/config'

let db: Database | null = null
let dbPath: string

export async function initDatabase(): Promise<Database> {
  if (db) return db
  
  const SQL = await initSqlJs()
  
  dbPath = config.databasePath
  const dbDir = path.dirname(dbPath)
  
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true })
  }
  
  if (fs.existsSync(dbPath)) {
    const buffer = fs.readFileSync(dbPath)
    db = new SQL.Database(buffer)
  } else {
    db = new SQL.Database()
  }
  
  db.run(`
    CREATE TABLE IF NOT EXISTS api_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      ip TEXT NOT NULL,
      method TEXT NOT NULL,
      path TEXT NOT NULL,
      body TEXT,
      status INTEGER,
      response_time INTEGER,
      error TEXT
    )
  `)
  
  db.run(`
    CREATE TABLE IF NOT EXISTS ip_blacklist (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ip TEXT UNIQUE NOT NULL,
      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `)
  
  db.run(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `)
  
  saveDatabase()
  
  return db
}

export function saveDatabase(): void {
  if (db && dbPath) {
    const data = db.export()
    const buffer = Buffer.from(data)
    fs.writeFileSync(dbPath, buffer)
  }
}

export function getDb(): Database {
  if (!db) {
    throw new Error('Database not initialized')
  }
  return db
}

export default {
  init: initDatabase,
  get: getDb,
  save: saveDatabase
}
