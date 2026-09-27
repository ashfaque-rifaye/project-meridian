import { post, useDataVersion } from '../api'
import { Icon } from './ui'

/**
 * Page list. `group` is the sidebar heading; `stage` ties a page to a step in the top workflow bar.
 * Stage ids are internal keys (RECONSTRUCT, UNDERSTAND, ...); the visible names live in App.tsx.
 */
export const ROUTES = [
  { path: '/', label: 'Home', icon: 'story', group: 'START HERE', stage: null },
  { path: '/command', label: 'Dashboard', icon: 'home', group: 'START HERE', stage: null },
  { path: '/investigate', label: 'Release check (live)', icon: 'bot', group: 'START HERE', stage: null },
  { path: '/deck', label: 'Pitch deck (6 slides)', icon: 'terminal', group: 'START HERE', stage: null },
  { path: '/learn', label: 'Video guides', icon: 'play', group: 'START HERE', stage: null },
  { path: '/journey', label: 'Deployment timeline', icon: 'journey', group: '1 · WHAT’S RUNNING', stage: 'RECONSTRUCT' },
  { path: '/composition', label: 'Versions by environment', icon: 'matrix', group: '1 · WHAT’S RUNNING', stage: 'RECONSTRUCT' },
  { path: '/drift', label: 'What changed', icon: 'drift', group: '2 · WHAT CHANGED', stage: 'UNDERSTAND' },
  { path: '/flow', label: 'Service map', icon: 'graph', group: '2 · WHAT CHANGED', stage: 'UNDERSTAND' },
  { path: '/contract', label: 'Message format', icon: 'contract', group: '2 · WHAT CHANGED', stage: 'UNDERSTAND' },
  { path: '/rehearse', label: 'Deployment preview', icon: 'rehearse', group: '3 · PREVIEW', stage: 'REHEARSE' },
  { path: '/probe', label: 'Compatibility test', icon: 'terminal', group: '4 · TEST', stage: 'PROVE' },
  { path: '/divergence', label: 'Failing connection', icon: 'target', group: '4 · TEST', stage: 'PROVE' },
  { path: '/evidence', label: 'Evidence report', icon: 'packet', group: '4 · TEST', stage: 'PROVE' },
  { path: '/remediate', label: 'Fix options', icon: 'wrench', group: '5 · FIX', stage: 'REMEDIATE' },
  { path: '/bob', label: 'IBM Bob setup', icon: 'plug', group: 'SETUP', stage: null },
] as const

export default function Nav({ route, go, overview }: { route: string; go: (p: string) => void; overview: any }) {
  const { bump } = useDataVersion()
  const groups = Array.from(new Set(ROUTES.map((r) => r.group)))
  const verdict = overview?.prod?.verdict
  const dotFor = (path: string) => {
    if (path === '/divergence' && verdict === 'DIVERGED') return 'var(--fail)'
    if (path === '/command' && verdict) return verdict === 'DIVERGED' ? 'var(--fail)' : verdict === 'UNVALIDATED' ? 'var(--warn)' : 'var(--ok)'
    return null
  }
  const reset = async () => {
    if (!confirm('Clear test results? Test runs, release checks, deployment previews and the draft fix branch are removed. Environment data and Bob findings are kept.')) return
    await post('/demo/reset')
    bump()
    go('/command')
  }
  return (
    <aside className="sidebar">
      {groups.map((g) => (
        <div className="nav-group" key={g}>
          <div className="nav-group-title">{g}</div>
          {g === 'START HERE' && (
            <a
              href="/presentation.html"
              target="_blank"
              rel="noreferrer"
              className="nav-item"
              style={{ color: 'var(--accent)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}
            >
              <Icon name="story" />
              <span>Pitch Deck (6-Slider)</span>
              <span style={{ marginLeft: 'auto', fontSize: '9px', background: 'rgba(0, 212, 255, 0.2)', color: 'var(--accent)', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>6-SLIDE</span>
            </a>
          )}
          {ROUTES.filter((r) => r.group === g).map((r) => {
            const dot = dotFor(r.path)
            return (
              <button key={r.path} className={`nav-item ${route === r.path ? 'active' : ''}`} onClick={() => go(r.path)}>
                <Icon name={r.icon as any} />
                {r.label}
                {dot && <span className="nav-dot" style={{ background: dot }} />}
              </button>
            )
          })}
        </div>
      ))}
      <div className="sidebar-foot">
        <div>Meridian only reads from your environments. Tests run in an isolated sandbox.</div>
        <button className="btn ghost sm mt-s" onClick={reset}><Icon name="reset" size={13} /> Clear test results</button>
        <div className="tiny dim mt-s">Press <kbd>S</kbd> for a guided tour · ← → to step</div>
      </div>
    </aside>
  )
}
