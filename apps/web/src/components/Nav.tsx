import { post, useDataVersion } from '../api'
import { Icon } from './ui'

export const ROUTES = [
  { path: '/', label: 'Command center', icon: 'home', group: 'OVERVIEW', stage: null },
  { path: '/investigate', label: 'Live investigation', icon: 'bot', group: 'OVERVIEW', stage: null },
  { path: '/learn', label: 'Tutorials', icon: 'story', group: 'OVERVIEW', stage: null },
  { path: '/journey', label: 'Release journey', icon: 'journey', group: 'RECONSTRUCT', stage: 'RECONSTRUCT' },
  { path: '/composition', label: 'System composition', icon: 'matrix', group: 'RECONSTRUCT', stage: 'RECONSTRUCT' },
  { path: '/drift', label: 'Drift relevance', icon: 'drift', group: 'UNDERSTAND', stage: 'UNDERSTAND' },
  { path: '/flow', label: 'Dependency explorer', icon: 'graph', group: 'UNDERSTAND', stage: 'UNDERSTAND' },
  { path: '/contract', label: 'Implicit contract', icon: 'contract', group: 'UNDERSTAND', stage: 'UNDERSTAND' },
  { path: '/rehearse', label: 'Promotion rehearsal', icon: 'rehearse', group: 'REHEARSE', stage: 'REHEARSE' },
  { path: '/probe', label: 'Probe console', icon: 'terminal', group: 'PROVE', stage: 'PROVE' },
  { path: '/divergence', label: 'First divergence', icon: 'target', group: 'PROVE', stage: 'PROVE' },
  { path: '/evidence', label: 'Evidence packet', icon: 'packet', group: 'PROVE', stage: 'PROVE' },
  { path: '/remediate', label: 'Remediation', icon: 'wrench', group: 'REMEDIATE', stage: 'REMEDIATE' },
  { path: '/bob', label: 'IBM Bob integration', icon: 'plug', group: 'IBM BOB', stage: null },
] as const

export default function Nav({ route, go, overview }: { route: string; go: (p: string) => void; overview: any }) {
  const { bump } = useDataVersion()
  const groups = Array.from(new Set(ROUTES.map((r) => r.group)))
  const verdict = overview?.prod?.verdict
  const dotFor = (path: string) => {
    if (path === '/divergence' && verdict === 'DIVERGED') return 'var(--fail)'
    if (path === '/' && verdict) return verdict === 'DIVERGED' ? 'var(--fail)' : verdict === 'UNVALIDATED' ? 'var(--warn)' : 'var(--ok)'
    return null
  }
  const reset = async () => {
    if (!confirm('Reset demo evidence? Probe runs, investigations, rehearsals and the candidate branch are removed. Scenario data and Bob findings are kept.')) return
    await post('/demo/reset')
    bump()
    go('/')
  }
  return (
    <aside className="sidebar">
      {groups.map((g) => (
        <div className="nav-group" key={g}>
          <div className="nav-group-title">{g}</div>
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
        <div>Read-only against target environments. Probes execute in isolation.</div>
        <button className="btn ghost sm mt-s" onClick={reset}><Icon name="reset" size={13} /> Reset demo evidence</button>
        <div className="tiny dim mt-s">Press <kbd>S</kbd> for story mode · ← → to step</div>
      </div>
    </aside>
  )
}
