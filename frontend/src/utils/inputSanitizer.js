const REPLACEMENTS = {
  '<': '＜',
  '>': '＞',
  '"': '＂',
  "'": '＇',
  '`': '｀',
}

const FORBIDDEN_CHAR_REGEX = /[<>"'`]/g
const XSS_PATTERN =
  /(javascript:|data:text\/html|vbscript:|onerror\s*=|onload\s*=|onmouseover\s*=|<\s*\/?\s*script\b)/gi

export function sanitizeText(value) {
  if (typeof value !== 'string') return value
  const trimmed = value.trim()
  const removedXssPayload = trimmed.replace(XSS_PATTERN, '')
  return removedXssPayload.replace(FORBIDDEN_CHAR_REGEX, (match) => REPLACEMENTS[match] || '')
}

function isBinaryPayload(value) {
  return (
    value instanceof FormData ||
    (typeof Blob !== 'undefined' && value instanceof Blob) ||
    (typeof File !== 'undefined' && value instanceof File)
  )
}

export function sanitizePayload(payload) {
  if (payload == null) return payload
  if (typeof payload === 'string') return sanitizeText(payload)
  if (isBinaryPayload(payload) || payload instanceof Date) return payload
  if (Array.isArray(payload)) return payload.map((item) => sanitizePayload(item))
  if (typeof payload === 'object') {
    return Object.fromEntries(
      Object.entries(payload).map(([key, value]) => [key, sanitizePayload(value)]),
    )
  }
  return payload
}
