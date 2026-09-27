import { useCallback, useEffect, useMemo, useState } from 'react'
import { DataVersion, fmtTime, post, useApi } from './api'
import Nav, { ROUTES } from './components/Nav'
import { Icon, Logo } from './components/ui'
import { InvestigationProvider, useInvestigation } from './investigation'
import BobIntegration from './screens/BobIntegration'
import BobInvestigation from './screens/BobInvestigation'
import CommandCenter from './screens/CommandCenter'
import DependencyExplorer from './screens/DependencyExplorer'
import DriftRelevance from './screens/DriftRelevance'
import EvidencePacket from './screens/EvidenceDrawer'
import FirstDivergence from './screens/FirstDivergence'
import ImplicitContract from './screens/ImplicitContract'
import Learn from './screens/Learn'
import ProbeConsole from './screens/ProbeConsole'
import PromotionRehearsal from './screens/PromotionRehearsal'
import ReleaseJourney from './screens/ReleaseJourney'
import Remediation from './screens/Remediation'
import SystemComposition from './screens/SystemComposition'

export type Go = (path: string) => void

const STAGES = [
  { id: 'RECONSTRUCT', q: 'What is actually running?', route: '/journey' },
  { id: 'UNDERSTAND', q: 'Why does it differ from what was validated?', route: '/flow' },
  { id: 'REHEARSE', q: 'What happens if these versions interact?', route: '/rehearse' },
  { id: 'PROVE', q: 'What executable evidence supports it?', route: '/divergence' },
  { id: 'REMEDIATE', q: 'Smallest safe change?', route: '/remediate' },
]

const STORY = [
  { route: '/', title: 'This release passed.', text: 'R-26.9 was validated end to end in Stage on Thursday: every boundary of Order-to-Ledger verified with semantic assertions.' },
  { route: '/', title: 'Production is healthy.', text: 'Every pod is ready, every pipeline is green, no alert has fired. Yet PROD is running a combination of versions that never ran together.' },
  { route: '/composition', title: 'Is PROD the system we validated?', text: 'No. legacy-ledger and ledger-db are still on the old versions while mq-bridge 3.1 is live. Observed together is not validated together.' },
  { route: '/journey', title: 'How it happened.', text: 'mq-bridge 3.1 reached PROD Friday 11:42 through an Argo CD auto-sync. legacy-ledger 7.0 waits for Sunday’s CAB window (CR-4471).' },
  { route: '/investigate', title: 'Bob investigates.', text: 'A release investigator reads the release notes, change request and ICD spreadsheet while four environment investigators reconstruct DEV, TEST, STAGE and PROD in parallel.', action: 'investigate' },
  { route: '/drift', title: 'Which differences matter?', text: '149 raw differences between Stage and Prod. Meridian narrows them to the single boundary that has no validation evidence.' },
  { route: '/contract', title: 'Discover the implicit contract.', text: 'No formal contract exists. Meridian reconstructs it from the bridge’s layout code, the ledger’s COBOL copybook and the ICD spreadsheet, at the exact deployed commits.' },
  { route: '/probe', title: 'Proof, not prediction.', text: 'The exact deployed commits run in an isolated sandbox with the same fixtures Stage used.' },
  { route: '/probe#silent', title: 'Silent semantic failure.', text: 'HTTP 200. MQ ACK. DB COMMIT. And CUST12345678 is posted to CUST123456, $149.50 becomes $780,000,149.00, EUR becomes USD.' },
  { route: '/divergence', title: 'First Demonstrated Divergence.', text: 'mq-bridge 3.1 → legacy-ledger 6.9, created Friday 11:42 by an Argo CD auto-sync. A fact with evidence, not a root-cause guess.' },
  { route: '/rehearse', title: 'See it before you create it.', text: 'Promotion rehearsal predicts the composition a deployment would create and probes it in the sandbox. Nothing is deployed.' },
  { route: '/remediate', title: 'Open in Bob.', text: 'The evidence packet goes to Bob’s meridian-remediator mode, which drafts an isolated compatibility mode for mq-bridge.' },
  { route: '/remediate', title: 'Regression probe: PASS.', text: 'Nothing is truncated any more; records the old ledger cannot represent are held explicitly. The human owns the release decision.' },
  { route: '/', title: 'Every component passed. The system didn’t.', text: 'We are not monitoring whether your services are alive. We are proving whether the system you assembled is the system you actually tested.' },
]

function useHashRoute(): [string, Go] {
  const read = () => window.location.hash.replace(/^#/, '') || '/'
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const on = () => setRoute(read())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  const go = useCallback((p: string) => {
    window.location.hash = p
  }, [])
  return [route, go]
}

function Shell() {
  const [route, go] = useHashRoute()
  const inv = useInvestigation()
  const { data: overview } = useApi('/overview')
  const [theme, setTheme] = useState<string>(() => (['neon', 'mono'].includes(localStorage.getItem('meridian-theme') || '') ? localStorage.getItem('meridian-theme')! : 'neon'))
  const [story, setStory] = useState<number | null>(null)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('meridian-theme', theme)
  }, [theme])

  const path = route.split('#')[0]
  const current = ROUTES.find((r) => r.path === path) || ROUTES[0]
  const activeStage = path === '/investigate' ? inv.stage : current.stage

  const runInvestigation = useCallback(() => {
    go('/investigate')
    inv.start(inv.pace)
  }, [go, inv])

  // story mode navigation
  useEffect(() => {
    if (story === null) return
    const scene = STORY[story]
    go(scene.route)
    if (scene.action === 'investigate' && inv.status !== 'running' && inv.status !== 'done') inv.start(inv.pace)
    if (scene.route.includes('#')) {
      setTimeout(() => document.getElementById(scene.route.split('#')[1])?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 500)
    } else {
      document.querySelector('.main')?.scrollTo({ top: 0, behavior: 'smooth' })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [story])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === 'INPUT' || (e.target as HTMLElement)?.tagName === 'TEXTAREA') return
      if (e.key === 's' && !e.ctrlKey && !e.metaKey) setStory((s) => (s === null ? 0 : null))
      if (story !== null && e.key === 'ArrowRight') setStory((s) => Math.min(STORY.length - 1, (s ?? 0) + 1))
      if (story !== null && e.key === 'ArrowLeft') setStory((s) => Math.max(0, (s ?? 0) - 1))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [story])

  const screen = useMemo(() => {
    switch (path) {
      case '/journey': return <ReleaseJourney go={go} />
      case '/composition': return <SystemComposition go={go} />
      case '/drift': return <DriftRelevance go={go} />
      case '/flow': return <DependencyExplorer go={go} />
      case '/contract': return <ImplicitContract go={go} />
      case '/investigate': return <BobInvestigation go={go} />
      case '/probe': return <ProbeConsole go={go} />
      case '/divergence': return <FirstDivergence go={go} />
      case '/evidence': return <EvidencePacket go={go} />
      case '/rehearse': return <PromotionRehearsal go={go} />
      case '/remediate': return <Remediation go={go} />
      case '/bob': return <BobIntegration go={go} />
      case '/learn': return <Learn go={go} />
      default: return <CommandCenter go={go} run={runInvestigation} />
    }
  }, [path, go, runInvestigation])

  const release = overview?.release
  return (
    <>
    <div className="aurora"><i /></div>
    <div className="gridfx" />
    <div className="noise" />
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <Logo />
          <span className="brand-name">MERIDIAN</span>
          <span className="brand-sub">Release convergence verification</span>
        </div>
        <div className="topbar-center">
          {release && (
            <span className="context-pill" title={release.title}>
              <b>{release.id}</b>
              <span className="sep" />
              <b>{overview.flow.name}</b>
              <span className="sep" />
              {overview.flow.components} components · {overview.flow.edges} boundaries
            </span>
          )}
        </div>
        <div className="topbar-right">
          <div className="clock">
            scenario clock<br />
            <b>{overview ? fmtTime(overview.snapshot_time) + ' UTC' : '—'}</b>
          </div>
          <span className="synthetic" title="All environments, people, hosts and timestamps are fictional">SYNTHETIC DATA</span>
          <button className="btn ghost icon-btn" title="Story mode (S)" onClick={() => setStory((s) => (s === null ? 0 : null))}><Icon name="story" /></button>
          <div className="tabs" title="Theme">
            <button className={`tab ${theme === 'neon' ? 'on' : ''}`} onClick={() => setTheme('neon')}>NEON</button>
            <button className={`tab ${theme === 'mono' ? 'on' : ''}`} onClick={() => setTheme('mono')}>B/W</button>
          </div>
          <button className="btn primary" onClick={runInvestigation} disabled={inv.status === 'running'}>
            {inv.status === 'running' ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="play" size={14} />}
            {inv.status === 'running' ? 'Investigating…' : 'Run investigation'}
          </button>
        </div>
      </header>

      <nav className="rail" aria-label="Workflow">
        {STAGES.map((s, i) => (
          <div key={s.id} className={`rail-step ${activeStage === s.id ? 'active' : ''} ${inv.stagesDone.includes(s.id) ? 'done' : ''}`}
            onClick={() => go(s.route)}>
            <span className="rail-num">{inv.stagesDone.includes(s.id) ? '✓' : i + 1}</span>
            <div style={{ minWidth: 0 }}>
              <div className="rail-title">{s.id}</div>
              <div className="rail-q">{s.q}</div>
            </div>
          </div>
        ))}
      </nav>

      <div className="body">
        <Nav route={path} go={go} overview={overview} />
        <main className="main">{screen}</main>
      </div>

      {story !== null && (
        <div className="story rise">
          <div className="story-n">SCENE {story + 1}/{STORY.length}</div>
          <div>
            <div className="story-title">{STORY[story].title}</div>
            <div className="story-text">{STORY[story].text}</div>
          </div>
          <div className="row">
            <button className="btn sm" disabled={story === 0} onClick={() => setStory(story - 1)}>←</button>
            <button className="btn sm primary" disabled={story === STORY.length - 1} onClick={() => setStory(story + 1)}>→</button>
            <button className="btn sm ghost" onClick={() => setStory(null)}>✕</button>
          </div>
          <div className="story-progress" style={{ width: `${((story + 1) / STORY.length) * 100}%` }} />
        </div>
      )}
    </div>
    </>
  )
}

export default function App() {
  const [version, setVersion] = useState(0)
  const bump = useCallback(() => setVersion((v) => v + 1), [])
  useEffect(() => {
    ;(window as any).meridianReset = async () => {
      await post('/demo/reset')
      bump()
    }
  }, [bump])
  return (
    <DataVersion.Provider value={{ version, bump }}>
      <InvestigationProvider>
        <Shell />
      </InvestigationProvider>
    </DataVersion.Provider>
  )
}
