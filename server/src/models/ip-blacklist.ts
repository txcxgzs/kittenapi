import { getDb, saveDatabase } from './database'

export interface IpBlacklistItem {
  id: number
  ip: string
  reason: string | null
  created_at: string
}

type DbValue = string | number | Uint8Array | null

export const IpBlacklistModel = {
  add(ip: string, reason?: string): boolean {
    const db = getDb()
    try {
      db.run('INSERT OR IGNORE INTO ip_blacklist (ip, reason) VALUES (?, ?)', [ip, reason || null])
      saveDatabase()
      return true
    } catch {
      return false
    }
  },

  remove(ip: string): boolean {
    const db = getDb()
    const exists = this.exists(ip)
    if (!exists) return false
    db.run('DELETE FROM ip_blacklist WHERE ip = ?', [ip])
    saveDatabase()
    return true
  },

  exists(ip: string): boolean {
    const db = getDb()
    const result = db.exec('SELECT 1 FROM ip_blacklist WHERE ip = ?', [ip])
    return result.length > 0 && result[0].values.length > 0
  },

  findAll(): IpBlacklistItem[] {
    const db = getDb()
    const result = db.exec('SELECT * FROM ip_blacklist ORDER BY created_at DESC')
    
    if (result.length === 0) return []
    
    const columns = result[0].columns
    return result[0].values.map((row: DbValue[]) => {
      const obj: Record<string, DbValue> = {}
      columns.forEach((col: string, i: number) => {
        obj[col] = row[i]
      })
      return obj as unknown as IpBlacklistItem
    })
  },

  clear(): void {
    const db = getDb()
    db.run('DELETE FROM ip_blacklist')
    saveDatabase()
  }
}
