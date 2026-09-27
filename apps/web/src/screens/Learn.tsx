import { useState } from 'react'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import { Modal, PageHead } from '../components/ui'

const CHAPTERS = [
  { video: 'meridian-pendulums', title: 'Why releases get out of sync', route: '/command',
    text: 'A release is only safe when its parts ship together. When one service deploys on its own schedule, production drifts away from what was tested long before any alert fires.' },
  { video: 'hero-convergence', title: 'Every component passed. The system didn’t.', route: '/',
    text: 'Large systems are built from many independent releases. Each part can pass its own tests while the exact mix running in production was never tested together.' },
  { video: 'env-layers', title: 'See what’s really running', route: '/composition',
    text: 'Read-only connectors show what actually runs in DEV, TEST, STAGE and PROD across EKS, AKS, GKE, OpenShift, WebSphere Liberty and Db2.' },
  { video: 'timeline-tracks', title: 'Different schedules drift apart', route: '/journey',
    text: 'Cloud services deploy continuously while on-prem systems wait for change windows. The timeline shows the exact deployment that created the untested mix.' },
  { video: 'agents-parallel', title: 'A release check with IBM Bob', route: '/investigate',
    text: 'Bob’s agents read the release documents, each environment and the deployed code in parallel, using Meridian’s tools.' },
  { video: 'hybrid-cloud', title: 'One flow, four clouds and a data centre', route: '/flow',
    text: 'The checkout flow crosses GKE, EKS, AKS, Kafka, OpenShift, WebSphere Liberty and Db2. Meridian checks every connection in that one flow, not the whole company.' },
  { video: 'probe-sandbox', title: 'Tested, not guessed', route: '/probe',
    text: 'The message format becomes a real test. The exact deployed code runs in an isolated sandbox with the test data Stage used, and the test decides the result.' },
  { video: 'silent-failure', title: 'A silent failure', route: '/probe',
    text: 'HTTP 200, message accepted, database saved, every pod healthy, and the backend saves the wrong customer, the wrong amount and the wrong currency.' },
  { video: 'remediation-bridge', title: 'Preview the fix, then test it', route: '/remediate',
    text: 'Fix options are previewed like deployments. Bob drafts a compatibility fix on a separate branch and a retest confirms it before anyone deploys.' },
  { video: 'convergence-snap', title: 'Back in sync', route: '/remediate',
    text: 'The retest passes: no data is cut off, records the old backend can’t store are held, and the preview shows CR-4471 brings production back to the tested versions.' },
  { video: 'shield-guard', title: 'Read-only by design', route: '/bob',
    text: 'A safety hook blocks every kubectl, helm, aws, az and gcloud command that would change something, before Bob can run it. Tests only run in an isolated sandbox.' },
  { video: 'evidence-crystal', title: 'An evidence report, not an opinion', route: '/evidence',
    text: 'Every statement links to a tool output, a deployment, a test run, a file at a commit, a document or a sandbox test, and rule-based checks review it.' },
  { video: 'bob-core', title: 'Built as an IBM Bob plugin', route: '/bob',
    text: 'Bob modes, skills, 22 tools and safety hooks make Meridian part of the everyday developer workflow in IBM Bob.' },
]

function Tile({ c, i, onOpen }: { c: typeof CHAPTERS[number]; i: number; onOpen: () => void }) {
  const [ok, setOk] = useState(true)
  return (
    <div className="tut" onClick={onOpen}
      onMouseEnter={(e) => (e.currentTarget.querySelector('video') as HTMLVideoElement | null)?.play().catch(() => {})}
      onMouseLeave={(e) => (e.currentTarget.querySelector('video') as HTMLVideoElement | null)?.pause()}>
      <div className="tut-media">
        {ok ? <video src={`/media/${c.video}.mp4`} muted loop playsInline preload="metadata" onError={() => setOk(false)} />
          : <div className="fallback">{String(i + 1).padStart(2, '0')}</div>}
        <div className="tut-num">VIDEO {String(i + 1).padStart(2, '0')}</div>
      </div>
      <div className="tut-body">
        <div className="tut-title">{c.title}</div>
        <div className="tut-text">{c.text}</div>
      </div>
    </div>
  )
}

export default function Learn({ go }: { go: Go }) {
  const [open, setOpen] = useState<number | null>(null)
  const c = open !== null ? CHAPTERS[open] : null
  return (
    <div className="page">
      <PageBanner video="tunnel-intro">
        <PageHead eyebrow="Video guides · how Meridian works" title={<>Meridian in <span className="grad-text">{CHAPTERS.length} short videos</span></>}
          sub="Hover to preview. Click to watch, then jump straight to the matching page. Videos made with Google Flow (Veo 3.1)." />
      </PageBanner>
      <div className="grid g4">
        {CHAPTERS.map((ch, i) => <Tile key={ch.video} c={ch} i={i} onOpen={() => setOpen(i)} />)}
      </div>
      <Modal open={!!c} onClose={() => setOpen(null)} title={c?.title}>
        {c && (
          <>
            <video className="player" src={`/media/${c.video}.mp4`} autoPlay muted loop playsInline controls />
            <p className="t2 mt">{c.text}</p>
            <div className="row mt">
              <button className="btn primary" onClick={() => { setOpen(null); go(c.route) }}>Open this page →</button>
              {open! < CHAPTERS.length - 1 && <button className="btn" onClick={() => setOpen(open! + 1)}>Next video</button>}
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
