import { getDb, saveDatabase } from './database'

type DbValue = string | number | Uint8Array | null

export const SettingsModel = {
  get(key: string): string | null {
    const db = getDb()
    const result = db.exec('SELECT value FROM settings WHERE key = ?', [key])
    if (result.length > 0 && result[0].values.length > 0) {
      return result[0].values[0][0] as string
    }
    return null
  },

  set(key: string, value: string): void {
    const db = getDb()
    db.run(
      `INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
       ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')`,
      [key, value]
    )
    saveDatabase()
  },

  getAll(): Record<string, string> {
    const db = getDb()
    const result = db.exec('SELECT key, value FROM settings')
    const settings: Record<string, string> = {}
    
    if (result.length > 0) {
      result[0].values.forEach((row: DbValue[]) => {
        settings[row[0] as string] = row[1] as string
      })
    }
    
    return settings
  },

  delete(key: string): void {
    const db = getDb()
    db.run('DELETE FROM settings WHERE key = ?', [key])
    saveDatabase()
  }
}
