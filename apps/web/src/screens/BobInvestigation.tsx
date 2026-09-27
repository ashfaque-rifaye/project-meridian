import { useApi, fmtMs } from '../api'
import type { Go } from '../App'
import Console from '../components/Console'
import { PageBanner } from '../components/Media'
import { Card, Icon, PageHead, State } from '../components/ui'
import { useInvestigation } from '../investigation'

/** `id` is the engine's stage key used to group agents; `name` and `q` are what people see. */
const STAGES = [
  { id: 'RECONSTRUCT', name: 'What’s running', q: 'Read the live versions in every environment' },
  { id: 'UNDERSTAND', name: 'What changed', q: 'Compare with what was tested and find the untested connection' },
  { id: 'PROVE', name: 'Test', q: 'Run the missing test in the sandbox and check the result' },
]

export default function BobInvestigation({ go }: { go: Go }) {
  const inv = useInvestigation()
  const { data: agentsDef } = useApi('/investigations/agents')
  const agents = inv.order.length ? inv.order.map((id) => inv.agents[id]) : (agentsDef || []).map((a: any) => ({ ...a, status: 'idle' }))
  const lines = inv.logs.map((l) => ({ kind: l.text.startsWith('$') ? 'cmd' : l.text.startsWith('Result') ? `result ${l.text.includes('FAILED') ? 'FAIL' : 'PASS'}` : 'detail', text: `[${l.agent}] ${l.text}` }))

  const statusView = (a: any) => {
    if (a.status === 'running') return <span className="agent-status c-accent"><span className="spinner" /> running</span>
    if (a.status === 'done') return <span className="agent-status c-ok">✓ {fmtMs(a.duration_ms)}</span>
    if (a.status === 'queued') return <span className="agent-status">queued</span>
    if (a.status === 'error') return <span className="agent-status c-fail">error</span>
    return <span className="agent-status dim">idle</span>
  }

  return (
    <div className="page">
      <PageBanner video="agents-parallel">
        <PageHead eyebrow="Release check · live" title={<>Watch the check <span className="grad-text">step by step</span></>}
          sub="Starts a fresh check of production. IBM Bob’s agents collect versions, read the release documents and run the missing test in parallel. The pass or fail result comes from the test itself, not from the AI."
          actions={<>
            <button className="btn primary lg" onClick={() => inv.start(inv.pace)} disabled={inv.status === 'running'}>
              {inv.status === 'running' ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="play" size={14} />}
              {inv.status === 'running' ? 'Checking…' : inv.status === 'done' ? 'Run again' : 'Start release check'}
            </button>
          </>} />
      </PageBanner>

      <div className="callout info small" style={{ marginBottom: 18 }}>
        <span>ℹ</span>
        <div>
          <b>How this differs from the Dashboard:</b> the Dashboard shows the latest saved results. This page runs the whole check again and
          streams each step and its log live. Results update the Dashboard when the check finishes.
          <a style={{ cursor: 'pointer', marginLeft: 6 }} onClick={() => go('/command')}>Go to Dashboard →</a>
        </div>
      </div>

      {inv.status === 'done' && inv.result && (
        <div className={`callout ${inv.result.verdict === 'DIVERGED' ? 'fail' : 'ok'} rise`} style={{ marginBottom: 18 }}>
          <span style={{ fontSize: 18 }}>{inv.result.verdict === 'DIVERGED' ? '✕' : '✓'}</span>
          <div style={{ flex: 1 }}>
            <div className="strong" style={{ fontSize: 15 }}>
              Production: <State s={inv.result.verdict} />
              {inv.result.first_divergence && <> · failing connection {inv.result.first_divergence.producer} {inv.result.first_divergence.producer_version} → {inv.result.first_divergence.consumer} {inv.result.first_divergence.consumer_version}</>}
            </div>
            <div className="small t2">Finished in {fmtMs(inv.result.duration_ms)} (includes a {inv.result.pace_ms} ms display delay per step) · evidence report {inv.result.packet_id}</div>
          </div>
          {inv.result.first_divergence && <button className="btn danger" onClick={() => go('/divergence')}>See failing connection →</button>}
        </div>
      )}
      {inv.status === 'error' && <div className="callout fail" style={{ marginBottom: 18 }}><span>✕</span><div className="err">{inv.error}</div></div>}

      <div className="grid g-1-2">
        <div className="agents">
          {STAGES.map((s) => {
            const lane = agents.filter((a: any) => a.stage === s.id)
            const active = inv.stage === s.id
            return (
              <div key={s.id} className="stage-block" style={active ? { boxShadow: 'var(--glow-accent)' } : undefined}>
                <div className="stage-head">
                  <span className="stage-name grad-text">{s.name}</span>
                  <span className="stage-q">{s.q}</span>
                  {inv.stagesDone.includes(s.id) && <span className="c-ok small" style={{ marginLeft: 'auto' }}>✓</span>}
                </div>
                <div className={`agent-grid ${lane.length === 1 ? 'one' : ''}`}>
                  {lane.map((a: any) => (
                    <div key={a.id} className={`agent ${a.status}`}>
                      <div className="row"><span className="agent-name">{a.name}</span>{statusView(a)}</div>
                      <div className="agent-meta">Bob skill: {a.skill} · {a.bob}</div>
                      {a.summary && <div className="agent-sum">{a.summary}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
        <Card title="Live log" right={inv.status === 'running' ? <span className="c-accent small pulse">● live</span> : <State s={inv.status === 'done' ? 'PASS' : undefined} label="finished" />}>
          {lines.length ? <Console lines={lines} height={760} /> : (
            <div className="empty">
              <div className="big-num grad-text">Ready</div>
              <p className="mt-s">Press <b>Start release check</b>. You’ll see one agent read the release documents, four agents read DEV, TEST, STAGE and PROD, one work out the message format, one run the test and one review the evidence.</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
