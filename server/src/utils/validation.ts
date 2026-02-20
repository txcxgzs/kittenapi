export function isValidWorkId(workId: unknown): workId is number {
  return typeof workId === 'number' && 
         !isNaN(workId) && 
         Number.isInteger(workId) && 
         workId > 0
}

export function isValidString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
}

export function isValidNonNegativeNumber(value: unknown): value is number {
  return typeof value === 'number' && !isNaN(value) && value >= 0
}

export function hasValue(value: unknown): boolean {
  return value !== undefined && value !== null
}

export function isValidIPv4(ip: string): boolean {
  const parts = ip.split('.')
  if (parts.length !== 4) return false
  
  for (const part of parts) {
    if (part.length === 0 || part.length > 3) return false
    if (part.length > 1 && part[0] === '0') return false
    const num = parseInt(part, 10)
    if (isNaN(num) || num < 0 || num > 255) return false
  }
  
  return true
}

export function isValidIPv6(ip: string): boolean {
  if (ip.includes('::')) {
    const parts = ip.split('::')
    if (parts.length > 2) return false
    
    const left = parts[0] ? parts[0].split(':') : []
    const right = parts[1] ? parts[1].split(':') : []
    
    if (left.length + right.length > 7) return false
    
    const allParts = [...left, ...right]
    for (const part of allParts) {
      if (part.length === 0 || part.length > 4) return false
      if (!/^[0-9a-fA-F]+$/.test(part)) return false
    }
    
    return true
  } else {
    const parts = ip.split(':')
    if (parts.length !== 8) return false
    
    for (const part of parts) {
      if (part.length === 0 || part.length > 4) return false
      if (!/^[0-9a-fA-F]+$/.test(part)) return false
    }
    
    return true
  }
}

export function isValidIP(ip: string): boolean {
  return isValidIPv4(ip) || isValidIPv6(ip)
}
