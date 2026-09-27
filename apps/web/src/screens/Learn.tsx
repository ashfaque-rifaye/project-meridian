import { useState } from 'react'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import { Modal, PageHead } from '../components/ui'

const CHAPTERS = [
  { video: 'meridian-pendulums', title: 'What “meridian” means', route: '/',
    text: 'A release is only safe when its parts move together. When one component is promoted on its own cadence, the system slips out of phase long before any alarm fires.' },
  { video: 'hero-convergence', title: 'Every component passed. The system didn’t.', route: '/',
    text: 'Enterprise systems are assembled from independent releases. Each part can pass its tests while the exact combination running in production was never validated together.' },
  { video: 'env-layers', title: 'Reconstruct environment reality', route: '/composition',
    text: 'Read-only adapters rebuild what really runs in DEV, TEST, STAGE and PROD across EKS, AKS, GKE, OpenShift, WebSphere Liberty and Db2.' },
  { video: 'timeline-tracks', title: 'Independent cadences drift apart', route: '/journey',
    text: 'Cloud services promote continuously, on-prem systems wait for CAB windows. The timeline shows the exact deployment that created an untested composition.' },
  { video: 'agents-parallel', title: 'Parallel investigation with IBM Bob', route: '/investigate',
    text: 'Release and environment investigators run as Bob subagents through the Meridian MCP server, reading documents, adapters and deployed code in parallel.' },
  { video: 'hybrid-cloud', title: 'One flow, four clouds and a data centre', route: '/flow',
    text: 'Order-to-Ledger crosses GKE, EKS, AKS, Kafka, OpenShift, WebSphere Liberty and Db2. Meridian evaluates every boundary on that one flow, never the whole enterprise.' },
  { video: 'probe-sandbox', title: 'Proof, not prediction', route: '/probe',
    text: 'The implicit contract becomes an executable probe. Exact commits run in an isolated sandbox with the fixtures Stage used; the engine, not a model, decides.' },
  { video: 'silent-failure', title: 'The silent semantic failure', route: '/probe',
    text: 'HTTP 200, MQ ACK, DB COMMIT, every pod healthy, and the ledger books the wrong customer, the wrong amount and the wrong currency.' },
  { video: 'remediation-bridge', title: 'Rehearse the fix, then prove it', route: '/remediate',
    text: 'Remediation strategies are rehearsed like promotions. Bob drafts an isolated compatibility mode and a regression probe proves it before anyone deploys.' },
  { video: 'convergence-snap', title: 'Back in meridian', route: '/remediate',
    text: 'The regression probe passes: nothing is truncated, unrepresentable records are held explicitly, and rehearsal shows CR-4471 restores the validated composition.' },
  { video: 'shield-guard', title: 'Read-only by design', route: '/bob',
    text: 'A PreToolUse hook blocks every mutating kubectl, helm, aws, az and gcloud command before Bob can run it. Probes execute only in an isolated sandbox.' },
  { video: 'evidence-crystal', title: 'An evidence packet, not an opinion', route: '/evidence',
    text: 'Every statement traces to an adapter output, a deployment event, a validation run, a file at a commit, a document or a probe execution, and a deterministic review checks it.' },
  { video: 'bob-core', title: 'Built as a Bob plugin', route: '/bob',
    text: 'Custom modes, skills, a 22-tool MCP server and PreToolUse guardrails make Meridian a native part of the developer workflow in IBM Bob.' },
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
        <div className="tut-num">CHAPTER {String(i + 1).padStart(2, '0')}</div>
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
        <PageHead eyebrow="Tutorials · how Meridian works" title={<>Release convergence in <span className="grad-text">{CHAPTERS.length} short chapters</span></>}
          sub="Visuals generated with Google Flow (Veo 3.1). Hover to preview, click to watch and jump straight to the live screen." />
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
              <button className="btn primary" onClick={() => { setOpen(null); go(c.route) }}>Open the live screen →</button>
              {open! < CHAPTERS.length - 1 && <button className="btn" onClick={() => setOpen(open! + 1)}>Next chapter</button>}
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
