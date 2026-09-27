import { ReactNode, useEffect } from 'react'

export const GLYPH: Record<string, string> = {
  VERIFIED: '✓',
  CONVERGED: '✓',
  PASS: '✓',
  SUPPORTED: '✓',
  ALLOWED: '✓',
  VERIFIED_BY_PROBE: '◆',
  UNTESTED: '⚠',
  UNVALIDATED: '⚠',
  EXERCISED: '↯',
  OBSERVED_TOGETHER: '◐',
  FAILED: '✕',
  FAIL: '✕',
  DIVERGED: '✕',
  BLOCKED: '⛔',
  INCONCLUSIVE: '?',
  NEEDS_HUMAN: '⚑',
  HELD: '⏸',
  NONE: '∅',
}

/** Plain-language names for engine states. The engine values themselves are unchanged. */
export const LABEL: Record<string, string> = {
  VERIFIED: 'TESTED',
  VERIFIED_BY_PROBE: 'PASSED TEST',
  UNTESTED: 'NOT TESTED',
  UNVALIDATED: 'NOT TESTED',
  EXERCISED: 'SMOKE TEST ONLY',
  OBSERVED_TOGETHER: 'RAN SIDE BY SIDE',
  FAILED: 'FAILED',
  DIVERGED: 'FAILING',
  CONVERGED: 'ALL TESTED',
  SUPPORTED: 'CONFIRMED',
  NEEDS_HUMAN: 'NEEDS REVIEW',
  NONE: 'NO TEST RECORD',
}

export function State({ s, lg, label }: { s?: string | null; lg?: boolean; label?: string }) {
  if (!s) return null
  return (
    <span className={`state s-${s} ${lg ? 'lg' : ''}`}>
      <span className="g">{GLYPH[s] ?? '•'}</span>
      {label ?? LABEL[s] ?? s}
    </span>
  )
}

export function Platform({ p }: { p: string }) {
  const key = p.startsWith('WebSphere') ? 'WebSphere' : p.startsWith('Db2') ? 'Db2' : p
  const short: Record<string, string> = { WebSphere: 'LIBERTY', OpenShift: 'OPENSHIFT', Db2: 'DB2', Kafka: 'KAFKA' }
  return <span className={`platform pf-${key}`}>{short[key] ?? p}</span>
}

export function Card({ title, right, children, className = '', style }: {
  title?: ReactNode; right?: ReactNode; children: ReactNode; className?: string; style?: React.CSSProperties
}) {
  return (
    <section className={`card ${className}`} style={style}>
      {title && (
        <div className="card-title">
          <span>{title}</span>
          {right && <span className="right">{right}</span>}
        </div>
      )}
      {children}
    </section>
  )
}

export function PageHead({ eyebrow, title, sub, actions }: { eyebrow: string; title: ReactNode; sub?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="page-head">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="page-title">{title}</h1>
        {sub && <p className="page-sub">{sub}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export function Loading({ what = 'Loading' }: { what?: string }) {
  return (
    <div className="empty">
      <span className="spinner" /> <span style={{ marginLeft: 8 }}>{what}…</span>
    </div>
  )
}

export function ErrorBox({ error }: { error: string }) {
  return (
    <div className="callout fail">
      <span>✕</span>
      <div>
        <div className="strong">Request failed</div>
        <div className="err">{error}</div>
        <div className="small muted mt-s">Is the API running? Start it with <code>uvicorn apps.api.main:app --port 8000</code>, then load the environment data with <code>./demo/seed.sh</code>.</div>
      </div>
    </div>
  )
}

export function Drawer({ open, onClose, children, title }: { open: boolean; onClose: () => void; children: ReactNode; title?: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  if (!open) return null
  return (
    <>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer">
        <div className="row between" style={{ marginBottom: 14 }}>
          <div className="strong" style={{ fontSize: 16 }}>{title}</div>
          <button className="btn ghost sm" onClick={onClose}>Close · Esc</button>
        </div>
        {children}
      </aside>
    </>
  )
}

export function Modal({ open, onClose, children, title }: { open: boolean; onClose: () => void; children: ReactNode; title?: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  if (!open) return null
  return (
    <>
      <div className="scrim" onClick={onClose} />
      <div className="modal">
        <div className="row between" style={{ marginBottom: 14 }}>
          <div className="strong" style={{ fontSize: 17 }}>{title}</div>
          <button className="btn ghost sm" onClick={onClose}>Close · Esc</button>
        </div>
        {children}
      </div>
    </>
  )
}

export function Stat({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: 'ok' | 'fail' | 'warn' }) {
  return (
    <div className="hstat">
      <div className="hstat-label">{label}</div>
      <div className={`hstat-value ${tone ? 'c-' + tone : ''}`}>{value}</div>
      {sub && <div className="hstat-sub">{sub}</div>}
    </div>
  )
}

export function Mono({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <span className={`mono ${className}`}>{children}</span>
}

export function copy(text: string) {
  navigator.clipboard?.writeText(text).catch(() => {})
}

/* --------------------------------------------------------------------- icons */
type IconName =
  | 'home' | 'journey' | 'matrix' | 'drift' | 'graph' | 'bot' | 'contract' | 'terminal' | 'target' | 'packet'
  | 'rehearse' | 'wrench' | 'plug' | 'play' | 'sun' | 'moon' | 'story' | 'reset' | 'doc' | 'shield' | 'arrow' | 'external'

const PATHS: Record<IconName, ReactNode> = {
  home: <path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z" />,
  journey: <><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /><path d="M7 12h3M14 12h3" /></>,
  matrix: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  drift: <path d="M3 5h18l-7 8v6l-4 2v-8z" />,
  graph: <><circle cx="5" cy="6" r="2.2" /><circle cx="19" cy="6" r="2.2" /><circle cx="12" cy="18" r="2.2" /><path d="M7 7l4 9M17 7l-4 9M7.2 6h9.6" /></>,
  bot: <><rect x="4" y="8" width="16" height="11" rx="3" /><path d="M12 4v4M9 13h.01M15 13h.01" /></>,
  contract: <><path d="M6 3h9l4 4v14H6z" /><path d="M9 11h7M9 15h7M9 7h3" /></>,
  terminal: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="m7 9 3 3-3 3M13 15h4" /></>,
  target: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><circle cx="12" cy="12" r="1" /></>,
  packet: <><path d="M4 7.5 12 3l8 4.5v9L12 21l-8-4.5z" /><path d="M4 7.5 12 12l8-4.5M12 12v9" /></>,
  rehearse: <><path d="M4 12a8 8 0 0 1 14-5.3L20 9" /><path d="M20 4v5h-5" /><path d="M20 12a8 8 0 0 1-14 5.3L4 15" /><path d="M4 20v-5h5" /></>,
  wrench: <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z" />,
  plug: <><path d="M9 2v5M15 2v5" /><path d="M6 7h12v4a6 6 0 0 1-12 0z" /><path d="M12 17v5" /></>,
  play: <path d="M7 4v16l13-8z" />,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  moon: <path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" />,
  story: <><path d="M4 5h16v14H4z" /><path d="m10 9 5 3-5 3z" /></>,
  reset: <><path d="M4 4v6h6" /><path d="M5 15a8 8 0 1 0 2-8.6L4 10" /></>,
  doc: <><path d="M6 3h9l4 4v14H6z" /><path d="M15 3v4h4" /></>,
  shield: <path d="M12 3 4 6v6c0 5 3.4 8.3 8 9 4.6-.7 8-4 8-9V6z" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  external: <><path d="M14 4h6v6M20 4l-9 9" /><path d="M18 14v6H4V6h6" /></>,
}

export function Icon({ name, size = 16 }: { name: IconName; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      {PATHS[name]}
    </svg>
  )
}

export function Logo({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-label="Meridian">
      <rect width="32" height="32" rx="7" fill="#0f62fe" />
      <rect x="7" y="9" width="11" height="4" rx="1" fill="#fff" />
      <rect x="14" y="19" width="11" height="4" rx="1" fill="#fff" />
      <rect x="14" y="13" width="4" height="6" fill="#fff" opacity="0.55" />
    </svg>
  )
}
