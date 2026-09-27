import { useState } from 'react'
import { ENV_LABEL, fmtDuration, fmtTime, useApi } from '../api'
import type { Go } from '../App'
import FlowGraph from '../components/FlowGraph'
import { PageBanner } from '../components/Media'
import { Card, ErrorBox, Loading, PageHead, Platform, State } from '../components/ui'

export default function DependencyExplorer({ go }: { go: Go }) {
  const [env, setEnv] = useState('prod')
  const [edgeId, setEdgeId] = useState<string>('mq-bridge--legacy-backend')
  const { data: flow } = useApi('/flow')
  const { data, error } = useApi(`/environments/${env}`, [env])
  const { data: edge } = useApi(`/edges/${edgeId}?env=${env}`, [edgeId, env])
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data || !flow) return <div className="page"><Loading what="Loading service map" /></div>
  const ev = edge?.evaluation
  const evidence = ev?.evidence

  return (
    <div className="page">
      <PageBanner video="hybrid-cloud">
        <PageHead eyebrow="What changed · service map" title={<>{flow.name}, <span className="grad-text">one connection at a time</span></>}
          sub="Only the services in this flow, not the whole company. Click a connection to see the exact version pair, its test history, its message format and its test result."
          actions={<div className="tabs">{['dev', 'test', 'stage', 'prod'].map((e) => <button key={e} className={`tab ${env === e ? 'on' : ''}`} onClick={() => setEnv(e)}>{ENV_LABEL[e]}</button>)}</div>} />
      </PageBanner>

      <Card title={<>{ENV_LABEL[env]} · <State s={data.verdict} /></>} right={<span className="small muted">snapshot {data.snapshot_id}</span>}>
        <FlowGraph components={flow.components} edges={data.edges} composition={data.composition} selected={edgeId} onSelect={setEdgeId} />
      </Card>

      {edge && ev && (
        <div className="grid g-2-1 mt-l rise">
          <Card title={<>Connection · {ev.producer} → {ev.consumer}</>} right={<State s={ev.state} lg />}>
            <div className="grid g2">
              {[edge.components[ev.producer], edge.components[ev.consumer]].map((c: any, i: number) => (
                <div key={c.id} className="glass" style={{ padding: 14 }}>
                  <div className="kicker">{i === 0 ? 'sends' : 'receives'}</div>
                  <div className="row mt-s"><span className="strong" style={{ fontSize: 15 }}>{c.id}</span><Platform p={c.platform} /></div>
                  <div className="big-num mt-s">{i === 0 ? ev.producer_version : ev.consumer_version}</div>
                  <div className="tiny mono dim">@{i === 0 ? ev.producer_commit : ev.consumer_commit} · {c.team} · {c.deploy_tool}</div>
                </div>
              ))}
            </div>
            <div className="mt small t2">{ev.reason}</div>
            <dl className="kv mt">
              <dt>Interface</dt><dd>{ev.interface}</dd>
              <dt>Spec</dt><dd>{ev.contract.formal ? 'Documented' : <span className="c-warn">No written spec</span>} · {ev.contract.kind} · <span className="muted">{ev.contract.ref}</span></dd>
              <dt>Pair running since</dt><dd>{ev.combination_since ? `${fmtTime(ev.combination_since)} UTC` : '—'}{ev.created_by_event ? ` · started by ${ev.created_by_event.component} ${ev.created_by_event.to_version} (${ev.created_by_event.tool})` : ''}</dd>
              <dt>Best test record</dt><dd><State s={evidence?.tier} /></dd>
            </dl>
            {evidence && (
              <div className="mt">
                <div className="kicker">test history for {ev.producer_version} → {ev.consumer_version}</div>
                <div className="grid g3 mt-s" style={{ gap: 8 }}>
                  <div className="glass" style={{ padding: 10 }}><div className="tiny muted">Full test runs</div><div className="big-num c-ok" style={{ fontSize: 26 }}>{evidence.verified.length}</div></div>
                  <div className="glass" style={{ padding: 10 }}><div className="tiny muted">Smoke tests only</div><div className="big-num c-warn" style={{ fontSize: 26 }}>{evidence.exercised.length}</div></div>
                  <div className="glass" style={{ padding: 10 }}><div className="tiny muted">Ran side by side</div><div className="big-num" style={{ fontSize: 26, color: 'var(--observe)' }}>{evidence.observed.length}</div></div>
                </div>
                {evidence.verified.map((v: any) => <div key={v.evidence_id} className="small mt-s">✓ <b>{v.suite}</b> in {ENV_LABEL[v.environment]} · {v.semantic_assertions} data checks passed · {fmtTime(v.executed_at)}</div>)}
                {evidence.exercised.map((v: any) => <div key={v.evidence_id} className="small mt-s c-warn">↯ <b>{v.suite}</b> in {ENV_LABEL[v.environment]} · {v.messages} message · checked: {v.technical_checks.join(', ')} · no data checks</div>)}
                {evidence.observed.map((w: any) => <div key={w.evidence_id} className="small mt-s" style={{ color: 'var(--observe)' }}>◐ ran side by side in {ENV_LABEL[w.environment]} for {fmtDuration(w.duration_seconds)}{w.ongoing ? ' (still running)' : ''}, no test traffic recorded</div>)}
              </div>
            )}
            <div className="row mt">
              {ev.state !== 'VERIFIED' && ev.contract && <button className="btn" onClick={() => go('/contract')}>Message format</button>}
              {ev.probe && <button className="btn" onClick={() => go('/probe')}>Test result · {ev.probe.result}</button>}
            </div>
          </Card>

          <Card title="Every version pair seen on this connection">
            <table className="tbl">
              <thead><tr><th>Pair</th><th>Best record</th><th>Where</th></tr></thead>
              <tbody>
                {edge.ledger.map((r: any) => {
                  const current = r.producer_version === ev.producer_version && r.consumer_version === ev.consumer_version
                  return (
                    <tr key={r.producer_version + r.consumer_version} className={current && r.tier !== 'VERIFIED' ? 'hl' : ''}>
                      <td className="mono">{r.producer_version} → {r.consumer_version}{current ? <div className="tiny c-accent">running in {ENV_LABEL[env]}</div> : null}</td>
                      <td><State s={r.tier} /></td>
                      <td className="tiny muted">
                        {r.verified_in.length ? `tested: ${r.verified_in.join(', ')}` : ''}
                        {r.exercised_in.length ? ` smoke tested: ${r.exercised_in.join(', ')}` : ''}
                        {r.observed_in.length ? ` side by side: ${r.observed_in.join(', ')}` : ''}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  )
}
