import { useState } from 'react'
import { ENV_LABEL, fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import Timeline from '../components/Timeline'
import { Card, ErrorBox, Icon, Loading, PageHead, State } from '../components/ui'

export default function ReleaseJourney({ go }: { go: Go }) {
  const { data, error } = useApi('/timeline')
  const { data: rel } = useApi('/release')
  const { data: docs } = useApi('/documents')
  const [seg, setSeg] = useState<any>(null)
  const [envFilter, setEnvFilter] = useState<string>('all')

  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data || !rel) return <div className="page"><Loading what="Replaying deployment history" /></div>

  const pattern = rel.pattern
  const events = data.lanes.flatMap((l: any) => l.events).filter((e: any) => envFilter === 'all' || e.environment === envFilter)
    .sort((a: any, b: any) => (a.deployed_at < b.deployed_at ? 1 : -1))

  return (
    <div className="page">
      <PageBanner video="timeline-tracks">
        <PageHead eyebrow="Reconstruct · release journey" title={<>{rel.release.id} · how production <span className="grad-text">assembled itself</span></>}
          sub="Every composition each environment ran, when it started, which deployment created it, and whether that exact combination had validation evidence."
          actions={<button className="btn" onClick={() => go('/composition')}><Icon name="matrix" /> System composition</button>} />
      </PageBanner>

      <Card title="Promotion timeline · Mon 21 → Sun 27 Sep (UTC, synthetic)"
        right={<span className="row small muted" style={{ gap: 14 }}>
          <span><span className="dot ok" /> validated composition</span><span><span className="dot warn" /> unvalidated composition</span>
          <span><span className="dot fail" /> first divergence</span><span>◆ deployment</span><span>✓ semantic test run</span><span>↯ smoke only</span>
        </span>}>
        <Timeline data={data} onSegment={setSeg} selected={seg} />
        {seg ? (
          <div className="mt glass rise">
            <div className="row between">
              <div className="strong">{ENV_LABEL[seg.environment]} · {fmtTime(seg.start)} → {seg.end ? fmtTime(seg.end) : 'now'}</div>
              <State s={seg.validated ? 'VERIFIED' : 'UNTESTED'} label={seg.validated ? 'COMPOSITION VALIDATED' : 'UNVALIDATED COMPOSITION'} />
            </div>
            <div className="strip mt-s">
              {Object.entries(seg.versions).map(([c, v]: any) => {
                const bad = seg.unvalidated.some((u: any) => u.edge_id.includes(c))
                return <div key={c} className={`chip ${bad ? 'bad' : ''}`}><div className="chip-name">{c}</div><div className="chip-ver">{v}</div></div>
              })}
            </div>
            {seg.started_by && <div className="small muted mt-s">Created by {seg.started_by.component} {seg.started_by.from_version} → {seg.started_by.to_version} via {seg.started_by.tool} ({seg.started_by.trigger}){seg.started_by.note ? ` · ${seg.started_by.note}` : ''}</div>}
            {!seg.validated && <div className="small c-warn mt-s">No passing validation evidence for: {seg.unvalidated.map((u: any) => `${u.edge_id} (${u.pair.join(' → ')})`).join(', ')}</div>}
          </div>
        ) : <div className="small muted mt-s">Click a composition bar to see the exact versions it ran.</div>}
      </Card>

      <div className="grid g2 mt-l">
        <Card title="Why this happened · runbook vs reality">
          <div className="grid g2" style={{ gap: 12 }}>
            <div>
              <div className="kicker">Release runbook order</div>
              <ol className="mt-s" style={{ paddingLeft: 18, display: 'grid', gap: 4 }}>
                {pattern.expected_order.map((s: any) => {
                  const pending = pattern.pending.some((p: any) => p.component === s.component)
                  return <li key={s.step} className={pending ? 'c-warn' : ''}><span className="mono">{s.component} {s.version}</span>{pending ? ' · pending' : ''}</li>
                })}
              </ol>
            </div>
            <div>
              <div className="kicker">What PROD actually received</div>
              <div className="mt-s" style={{ display: 'grid', gap: 6 }}>
                {pattern.actual_order.map((a: any) => {
                  const dev = pattern.deviations.some((d: any) => d.event.component === a.component)
                  return (
                    <div key={a.component} className={`small ${dev ? 'c-fail' : ''}`}>
                      <span className="mono">{fmtTime(a.deployed_at, { date: true })}</span> · <b>{a.component} {a.version}</b>
                      <div className="tiny muted">{a.tool} · {a.trigger}</div>
                    </div>
                  )
                })}
                {pattern.pending.map((p: any) => (
                  <div key={p.component} className="small c-hold">
                    <span className="mono">{fmtTime(p.window_start)}</span> · <b>{p.component} {p.to_version}</b>
                    <div className="tiny muted">{p.change_request} · {p.status}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="sep-grad" />
          {pattern.story.map((s: string, i: number) => <p key={i} className="small t2" style={{ marginBottom: 6 }}>{s}</p>)}
        </Card>

        <Card title="Release intent · enterprise documents" right={<span className="small muted">read by Bob’s release investigator</span>}>
          <div className="small t2">{rel.release.requirement}</div>
          <div className="row wrap mt-s">{rel.release.tickets.map((t: string) => <span key={t} className="tag">{t}</span>)}</div>
          <div className="mt" style={{ display: 'grid', gap: 10 }}>
            {docs?.map((d: any) => (
              <a key={d.name} className="glass row" style={{ padding: 12, textDecoration: 'none', color: 'inherit' }} href={`/api/documents/${d.name}`} target="_blank" rel="noreferrer">
                <Icon name="doc" size={20} />
                <div style={{ minWidth: 0 }}>
                  <div className="strong">{d.title}</div>
                  <div className="tiny muted mono">documents/{d.name} · {(d.size / 1024).toFixed(1)} KB</div>
                </div>
                <span className="spacer" /><Icon name="external" size={14} />
              </a>
            ))}
          </div>
          <div className="callout info mt small">
            <span>ℹ</span>
            <div>CR-4471 states the dependency in plain words: <span className="quote">{rel.change_request?.dependency}</span> No pipeline enforces it.</div>
          </div>
        </Card>
      </div>

      <Card className="mt-l flush" title={<span style={{ padding: '14px 16px 0', display: 'block' }}>Deployment events</span>}>
        <div className="row" style={{ padding: '0 16px 10px' }}>
          <div className="tabs">
            {['all', 'dev', 'test', 'stage', 'prod'].map((e) => (
              <button key={e} className={`tab ${envFilter === e ? 'on' : ''}`} onClick={() => setEnvFilter(e)}>{e.toUpperCase()}</button>
            ))}
          </div>
        </div>
        <div style={{ maxHeight: 360, overflow: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>When (UTC)</th><th>Env</th><th>Component</th><th>Change</th><th>Commit</th><th>Tool · trigger</th><th>Note</th></tr></thead>
            <tbody>
              {events.map((e: any) => (
                <tr key={e.event_id} className={e.environment === 'prod' && e.component === 'mq-bridge' ? 'hl' : ''}>
                  <td className="mono">{fmtTime(e.deployed_at)}</td>
                  <td className="mono">{ENV_LABEL[e.environment]}</td>
                  <td>{e.component}</td>
                  <td className="mono">{e.from_version} → {e.to_version}</td>
                  <td className="mono dim">{e.commit || '—'}</td>
                  <td className="small">{e.tool} · {e.trigger}</td>
                  <td className="small muted">{e.note || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
