import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'

export async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const post = <T = any>(path: string, body?: unknown) =>
  api<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })

/** Bumped whenever evidence changes (probe run, investigation, reset) so every view refetches. */
export const DataVersion = createContext<{ version: number; bump: () => void }>({ version: 0, bump: () => {} })

export function useDataVersion() {
  return useContext(DataVersion)
}

export function useApi<T = any>(path: string | null, deps: unknown[] = []) {
  const { version } = useDataVersion()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const seq = useRef(0)

  const load = useCallback(() => {
    if (!path) return
    const id = ++seq.current
    setLoading(true)
    api<T>(path)
      .then((d) => {
        if (id === seq.current) {
          setData(d)
          setError(null)
        }
      })
      .catch((e) => id === seq.current && setError(String(e.message || e)))
      .finally(() => id === seq.current && setLoading(false))
  }, [path])

  useEffect(load, [load, version, ...deps])
  return { data, error, loading, reload: load, setData }
}

// ----------------------------------------------------------------- formatting

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export function fmtTime(ts?: string | null, opts: { date?: boolean; seconds?: boolean } = { date: true }) {
  if (!ts) return '—'
  const d = new Date(ts)
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  const ss = String(d.getUTCSeconds()).padStart(2, '0')
  const time = `${hh}:${mm}${opts.seconds ? ':' + ss : ''}`
  if (opts.date === false) return time
  return `${DAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${time}`
}

export function fmtDuration(seconds?: number | null) {
  if (seconds === null || seconds === undefined) return '—'
  const s = Math.abs(seconds)
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (d) return `${d}d ${h}h ${m}m`
  if (h) return `${h}h ${m}m`
  return `${m}m`
}

export function fmtMs(ms?: number | null) {
  if (ms === null || ms === undefined) return '—'
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(2)} s`
}

export function ago(ts?: string | null) {
  if (!ts) return ''
  const diff = (Date.now() - new Date(ts).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`
  return `${Math.floor(diff / 86400)} d ago`
}

export const ENV_LABEL: Record<string, string> = { dev: 'DEV', test: 'TEST', stage: 'STAGE', prod: 'PROD' }
