import { useApi, fmtMs } from '../api'
import type { Go } from '../App'
import Console from '../components/Console'
import { PageBanner } from '../components/Media'
import { Card, Icon, PageHead, State } from '../components/ui'
import { useInvestigation } from '../investigation'

const STAGES = [
  { id: 'RECONSTRUCT', q: 'What is actually running?' },
  { id: 'UNDERSTAND', q: 'Why is it different from the validated system?' },
  { id: 'PROVE', q: 'What executable evidence supports the result?' },
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
        <PageHead eyebrow="Live investigation · IBM Bob agent lanes" title={<>Parallel agents, <span className="grad-text">deterministic verdicts</span></>}
          sub="The same lanes Bob runs as subagents through the Meridian MCP server. Durations are measured; presentation pacing only adds spacing between steps."
          actions={<>
            <button className="btn primary lg" onClick={() => inv.start(inv.pace)} disabled={inv.status === 'running'}>
              {inv.status === 'running' ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="play" size={14} />}
              {inv.status === 'running' ? 'Investigating…' : inv.status === 'done' ? 'Run again' : 'Start investigation'}
            </button>
          </>} />
      </PageBanner>

      {inv.status === 'done' && inv.result && (
        <div className={`callout ${inv.result.verdict === 'DIVERGED' ? 'fail' : 'ok'} rise`} style={{ marginBottom: 18 }}>
          <span style={{ fontSize: 18 }}>{inv.result.verdict === 'DIVERGED' ? '✕' : '✓'}</span>
          <div style={{ flex: 1 }}>
            <div className="strong" style={{ fontSize: 15 }}>
              PROD {inv.result.verdict}
              {inv.result.first_divergence && <> · first demonstrated divergence {inv.result.first_divergence.producer} {inv.result.first_divergence.producer_version} → {inv.result.first_divergence.consumer} {inv.result.first_divergence.consumer_version}</>}
            </div>
            <div className="small t2">Completed in {fmtMs(inv.result.duration_ms)} (including {inv.result.pace_ms} ms presentation pacing per step) · evidence packet {inv.result.packet_id}</div>
          </div>
          {inv.result.first_divergence && <button className="btn danger" onClick={() => go('/divergence')}>Forensic view →</button>}
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
                  <span className="stage-name grad-text">{s.id}</span>
                  <span className="stage-q">{s.q}</span>
                  {inv.stagesDone.includes(s.id) && <span className="c-ok small" style={{ marginLeft: 'auto' }}>✓</span>}
                </div>
                <div className={`agent-grid ${lane.length === 1 ? 'one' : ''}`}>
                  {lane.map((a: any) => (
                    <div key={a.id} className={`agent ${a.status}`}>
                      <div className="row"><span className="agent-name">{a.name}</span>{statusView(a)}</div>
                      <div className="agent-meta">skill {a.skill} · {a.bob}</div>
                      {a.summary && <div className="agent-sum">{a.summary}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
        <Card title="Agent log · streamed from the engine" right={inv.status === 'running' ? <span className="c-accent small pulse">● live</span> : <State s={inv.status === 'done' ? 'PASS' : undefined} label="complete" />}>
          {lines.length ? <Console lines={lines} height={760} /> : (
            <div className="empty">
              <div className="big-num grad-text">Ready</div>
              <p className="mt-s">Start an investigation to watch the release investigator, four environment investigators, contract discovery, the probe engineer and the evidence reviewer work in parallel.</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
