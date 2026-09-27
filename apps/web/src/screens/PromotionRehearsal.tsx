import { useState } from 'react'
import { post, useApi, useDataVersion } from '../api'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import { Card, Icon, Loading, PageHead, State } from '../components/ui'

export default function PromotionRehearsal({ go }: { go: Go }) {
  const { bump } = useDataVersion()
  const { data: presets } = useApi('/rehearsals/presets')
  const [changes, setChanges] = useState<{ component: string; version: string }[]>([{ component: 'mq-bridge', version: '3.1' }])
  const [result, setResult] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [title, setTitle] = useState('Promote mq-bridge 3.1 to PROD')

  const rehearse = async (ch = changes, t = title) => {
    setBusy(true)
    setResult(null)
    try {
      setResult(await post('/rehearsals', { environment: 'prod', changes: ch, title: t }))
      bump()
    } finally {
      setBusy(false)
    }
  }
  const components = presets ? Object.keys(presets.versions) : []

  return (
    <div className="page">
      <PageBanner video="meridian-pendulums">
        <PageHead eyebrow="Preview · deployment preview" title={<>See what a deployment changes <span className="grad-text">before you deploy it</span></>}
          sub="Current production plus your proposed change gives the versions you would end up with. Meridian checks the test history first, then runs a sandbox test for every untested connection. Nothing is deployed." />
      </PageBanner>

      <div className="grid g-1-2">
        <div className="stack">
          <Card title="Common deployments">
            {!presets ? <Loading /> : presets.presets.map((p: any) => (
              <button key={p.id} className="glass" style={{ width: '100%', textAlign: 'left', padding: 12, marginBottom: 8, cursor: 'pointer', color: 'inherit' }}
                onClick={() => { setChanges(p.changes); setTitle(p.title); rehearse(p.changes, p.title) }}>
                <div className="strong">{p.title}</div>
                <div className="small muted">{p.subtitle} · {p.changes.map((c: any) => `${c.component} ${c.version}`).join(' + ')}</div>
              </button>
            ))}
          </Card>
          <Card title="Custom deployment">
            {changes.map((c, i) => (
              <div key={i} className="row" style={{ marginBottom: 8 }}>
                <select className="select" value={c.component} onChange={(e) => setChanges(changes.map((x, j) => j === i ? { component: e.target.value, version: presets.versions[e.target.value].slice(-1)[0] } : x))}>
                  {components.map((k) => <option key={k}>{k}</option>)}
                </select>
                <select className="select" value={c.version} onChange={(e) => setChanges(changes.map((x, j) => j === i ? { ...x, version: e.target.value } : x))}>
                  {(presets?.versions[c.component] || []).map((v: string) => <option key={v}>{v}</option>)}
                </select>
                <button className="btn ghost sm" onClick={() => setChanges(changes.filter((_, j) => j !== i))}>✕</button>
              </div>
            ))}
            <div className="row">
              <button className="btn sm" onClick={() => setChanges([...changes, { component: 'legacy-backend', version: '7.0' }])}>+ service</button>
              <span className="spacer" />
              <button className="btn primary" onClick={() => rehearse(changes, 'Custom deployment')} disabled={busy || !changes.length}>
                {busy ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="rehearse" size={14} />} Preview deployment
              </button>
            </div>
            <div className="tiny muted mt-s">Target: PROD · read-only · tests run in an isolated sandbox</div>
          </Card>
        </div>

        <Card title={result ? result.title || 'Preview' : 'Result'} right={result && <State s={result.verdict} lg />}>
          {busy && <Loading what="Working out the new versions and testing untested connections" />}
          {!busy && !result && <div className="empty"><div className="big-num grad-text">Pick a deployment</div><p className="mt-s">Try “Promote mq-bridge 3.1 to PROD”: the exact deployment that happened on Friday at 11:42.</p></div>}
          {result && (
            <div className="rise">
              <div className="kicker">1 · production today</div>
              <div className="strip mt-s">{Object.entries(result.current_composition).map(([k, v]: any) => <div key={k} className="chip"><div className="chip-name">{k}</div><div className="chip-ver">{v}</div></div>)}</div>
              <div className="kicker mt">2 · proposed change</div>
              <div className="row wrap mt-s">{result.changes.map((c: any) => <span key={c.component} className="pill c-accent">{c.component} {c.from_version} → {c.to_version} <span className="dim mono">@{c.commit}</span></span>)}</div>
              <div className="kicker mt">3 · versions after the deployment</div>
              <div className="strip mt-s">{Object.entries(result.predicted_composition).map(([k, v]: any) => {
                const changed = result.changes.some((c: any) => c.component === k)
                const failing = result.edges.some((e: any) => e.state === 'FAILED' && (e.producer === k || e.consumer === k))
                return <div key={k} className={`chip ${failing ? 'bad' : changed ? 'changed' : ''}`}><div className="chip-name">{k}</div><div className="chip-ver">{v}</div></div>
              })}</div>
              <div className="kicker mt">4 · test history + sandbox tests</div>
              <table className="tbl mt-s">
                <tbody>{result.edges.map((e: any) => (
                  <tr key={e.edge_id} className={e.state === 'FAILED' ? 'hl' : ''}>
                    <td className="small"><b>{e.producer}</b> {e.producer_version} → <b>{e.consumer}</b> {e.consumer_version}</td>
                    <td><State s={e.state} /></td>
                    <td className="tiny muted">{e.reason}</td>
                  </tr>
                ))}</tbody>
              </table>
              <div className={`callout mt ${result.verdict === 'DIVERGED' ? 'fail' : result.verdict === 'CONVERGED' ? 'ok' : 'warn'}`}>
                <span>{result.verdict === 'DIVERGED' ? '✕' : result.verdict === 'CONVERGED' ? '✓' : '⚠'}</span>
                <div><div className="strong">5 · result</div><div className="small">{result.headline}</div><div className="tiny muted mt-s">{result.deployed_anything ? 'deployed' : 'nothing was deployed'} · preview {result.rehearsal_id}</div></div>
              </div>
              {result.verdict !== 'CONVERGED' && <button className="btn mt" onClick={() => go('/remediate')}>See fix options →</button>}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
