import { getDb, saveDatabase } from './database'

export interface ApiLog {
  id: number
  timestamp: string
  ip: string
  method: string
  path: string
  body: string | null
  status: number | null
  response_time: number | null
  error: string | null
}

export interface ApiLogCreate {
  ip: string
  method: string
  path: string
  body?: string
  status?: number
  response_time?: number
  error?: string
}

type DbValue = string | number | Uint8Array | null

export const ApiLogModel = {
  create(log: ApiLogCreate): void {
    const db = getDb()
    db.run(
      `INSERT INTO api_logs (ip, method, path, body, status, response_time, error) VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [log.ip, log.method, log.path, log.body || null, log.status || null, log.response_time || null, log.error || null]
    )
    saveDatabase()
  },

  findAll(options: { page?: number; limit?: number; ip?: string; path?: string } = {}): { logs: ApiLog[]; total: number } {
    const db = getDb()
    const { page = 1, limit = 20, ip, path } = options
    const offset = (page - 1) * limit
    
    let whereClause = '1=1'
    const params: DbValue[] = []
    
    if (ip) {
      whereClause += ' AND ip LIKE ?'
      params.push(`%${ip}%`)
    }
    if (path) {
      whereClause += ' AND path LIKE ?'
      params.push(`%${path}%`)
    }
    
    const countResult = db.exec(`SELECT COUNT(*) as total FROM api_logs WHERE ${whereClause}`, params)
    const total = countResult[0]?.values[0]?.[0] as number || 0
    
    const result = db.exec(
      `SELECT * FROM api_logs WHERE ${whereClause} ORDER BY timestamp DESC LIMIT ? OFFSET ?`,
      [...params, limit, offset]
    )
    
    let logs: ApiLog[] = []
    if (result.length > 0) {
      const columns = result[0].columns
      logs = result[0].values.map((row: DbValue[]) => {
        const obj: Record<string, DbValue> = {}
        columns.forEach((col: string, i: number) => {
          obj[col] = row[i]
        })
        return obj as unknown as ApiLog
      })
    }
    
    return { logs, total }
  },

  deleteOlderThan(days: number): void {
    const db = getDb()
    db.run(`DELETE FROM api_logs WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')`, [days])
    saveDatabase()
  },

  clear(): void {
    const db = getDb()
    db.run('DELETE FROM api_logs')
    saveDatabase()
  }
}
