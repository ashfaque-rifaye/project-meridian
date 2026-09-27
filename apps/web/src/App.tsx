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
import Home from './screens/Home'
import FirstDivergence from './screens/FirstDivergence'
import ImplicitContract from './screens/ImplicitContract'
import Learn from './screens/Learn'
import PitchDeck from './screens/PitchDeck'
import ProbeConsole from './screens/ProbeConsole'
import PromotionRehearsal from './screens/PromotionRehearsal'
import ReleaseJourney from './screens/ReleaseJourney'
import Remediation from './screens/Remediation'
import SystemComposition from './screens/SystemComposition'

export type Go = (path: string) => void

/** Workflow steps. `id` is the engine's stage key; `name` and `q` are what people see. */
const STAGES = [
  { id: 'RECONSTRUCT', name: 'What’s running', q: 'Which versions are live in each environment?', route: '/journey' },
  { id: 'UNDERSTAND', name: 'What changed', q: 'Which change left a connection untested?', route: '/flow' },
  { id: 'REHEARSE', name: 'Preview', q: 'What would a deployment change?', route: '/rehearse' },
  { id: 'PROVE', name: 'Test', q: 'Does the connection actually work?', route: '/divergence' },
  { id: 'REMEDIATE', name: 'Fix', q: 'What is the safest fix?', route: '/remediate' },
]

const STORY = [
  { route: '/command', title: 'The release passed testing.', text: 'Release R-26.9 was tested end to end in Stage on Thursday. Every connection in the checkout flow passed.' },
  { route: '/command', title: 'Production looks healthy.', text: 'All pods are ready, all pipelines are green and no alert has fired. But production is now running a mix of versions that was never tested together.' },
  { route: '/composition', title: 'Production doesn’t match Stage.', text: 'mq-bridge 3.1 is live, but legacy-backend and backend-db are still on their old versions. Running side by side is not the same as tested together.' },
  { route: '/journey', title: 'How it happened.', text: 'mq-bridge 3.1 reached production on Friday at 11:42 through an automatic Argo CD sync. legacy-backend 7.0 is waiting for Sunday’s change window (CR-4471).' },
  { route: '/investigate', title: 'Run the release check.', text: 'Bob’s agents read the release notes, change request and interface spreadsheet, and check DEV, TEST, STAGE and PROD in parallel.', action: 'investigate' },
  { route: '/drift', title: 'Which differences matter?', text: 'Stage and production differ in 149 ways. Only one of them leaves a connection untested.' },
  { route: '/contract', title: 'Work out the message format.', text: 'There is no written spec for this connection. Meridian rebuilds the format from mq-bridge’s code, legacy-backend’s COBOL copybook and the interface spreadsheet.' },
  { route: '/probe', title: 'Test it for real.', text: 'The exact deployed code runs in an isolated sandbox with the same test data Stage used.' },
  { route: '/probe#silent', title: 'A silent failure.', text: 'HTTP 200, message acknowledged, database committed. Yet customer CUST12345678 is saved as CUST123456, $149.50 becomes $780,000,149.00 and EUR becomes USD.' },
  { route: '/divergence', title: 'The failing connection.', text: 'mq-bridge 3.1 → legacy-backend 6.9, created on Friday at 11:42 by an automatic Argo CD sync. Backed by test results, not a guess.' },
  { route: '/rehearse', title: 'Preview before you deploy.', text: 'Deployment preview shows which versions a deployment would create and tests them in the sandbox. Nothing is deployed.' },
  { route: '/remediate', title: 'Hand it to Bob.', text: 'The evidence report goes to IBM Bob, which drafts a compatibility fix for mq-bridge on a separate branch.' },
  { route: '/remediate', title: 'The fix passes.', text: 'No data is cut off any more. Records the old backend can’t store are held until the upgrade. A person still makes the release decision.' },
  { route: '/', title: 'Every component passed. The system didn’t.', text: 'Health checks tell you your services are up. Meridian tells you whether the versions you’re running were ever tested together.' },
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
  const isHome = path === '/'
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
      case '/deck': return <PitchDeck go={go} />
      case '/command': return <CommandCenter go={go} run={runInvestigation} tour={() => setStory(0)} />
      default: return <Home go={go} />
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
        <div className="brand" style={{ cursor: 'pointer' }} onClick={() => go('/')}>
          <Logo />
          <span className="brand-name">MERIDIAN</span>
          <span className="brand-sub">Release version checks</span>
        </div>
        <div className="topbar-center">
          {release && (
            <span className="context-pill" title={release.title}>
              <span className="muted">Release</span>
              <b>{release.id}</b>
              <span className="sep" />
              <b>{overview.flow.name}</b>
            </span>
          )}
        </div>
        <div className="topbar-right">
          <div className="clock" title="Time the environment data was collected">
            data as of<br />
            <b>{overview ? fmtTime(overview.snapshot_time) + ' UTC' : '—'}</b>
          </div>
          <button className="btn ghost icon-btn" title="Guided tour (S)" aria-label="Guided tour" onClick={() => setStory((s) => (s === null ? 0 : null))}><Icon name="story" /></button>
          <div className="tabs" title="Theme">
            <button className={`tab ${theme === 'neon' ? 'on' : ''}`} onClick={() => setTheme('neon')}>NEON</button>
            <button className={`tab ${theme === 'mono' ? 'on' : ''}`} onClick={() => setTheme('mono')}>B/W</button>
          </div>
          <button className="btn primary" onClick={runInvestigation} disabled={inv.status === 'running'}>
            {inv.status === 'running' ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="play" size={14} />}
            {inv.status === 'running' ? 'Checking…' : 'Run release check'}
          </button>
        </div>
      </header>

      {!isHome && <nav className="rail" aria-label="Workflow">
        {STAGES.map((s, i) => (
          <div key={s.id} className={`rail-step ${activeStage === s.id ? 'active' : ''} ${inv.stagesDone.includes(s.id) ? 'done' : ''}`}
            onClick={() => go(s.route)}>
            <span className="rail-num">{inv.stagesDone.includes(s.id) ? '✓' : i + 1}</span>
            <div style={{ minWidth: 0 }}>
              <div className="rail-title">{s.name}</div>
              <div className="rail-q">{s.q}</div>
            </div>
          </div>
        ))}
      </nav>}

      <div className={`body ${isHome ? 'home' : ''}`}>
        {!isHome && <Nav route={path} go={go} overview={overview} />}
        <main className="main">{screen}</main>
      </div>

      {story !== null && (
        <div className="story rise">
          <div className="story-n">STEP {story + 1}/{STORY.length}</div>
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
