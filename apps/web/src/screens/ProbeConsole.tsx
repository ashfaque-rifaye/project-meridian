import { useEffect, useState } from 'react'
import { ago, api, fmtMs, post, useApi, useDataVersion } from '../api'
import type { Go } from '../App'
import Console from '../components/Console'
import { AmbientVideo, PageBanner } from '../components/Media'
import { Card, Icon, Loading, PageHead, State } from '../components/ui'

function money(v?: string) {
  if (!v) return '—'
  const n = Number(v)
  return Number.isNaN(n) ? v : n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export default function ProbeConsole({ go }: { go: Go }) {
  const { bump } = useDataVersion()
  const { data: runs } = useApi('/probes/runs')
  const [runId, setRunId] = useState<string | null>(null)
  const [run, setRun] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [fresh, setFresh] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    const id = runId || runs?.find((r: any) => r.edge_id === 'mq-bridge--legacy-ledger' && !Object.keys(r.config).length)?.run_id || runs?.[0]?.run_id
    if (id) api(`/probes/runs/${id}`).then(setRun)
  }, [runId, runs])

  const runNow = async () => {
    setBusy(true)
    setErr(null)
    try {
      const r = await post('/probes/run', { edge_id: 'mq-bridge--legacy-ledger', environment: 'prod' })
      setFresh(true)
      setRun(r)
      setRunId(r.run_id)
      bump()
    } catch (e: any) {
      setErr(String(e.message || e))
    } finally {
      setBusy(false)
    }
  }

  const bad = run?.fixtures?.filter((f: any) => f.assertions?.some((a: any) => !a.passed)) || []
  const first = bad[0]
  const eur = bad.find((f: any) => f.assertions.some((a: any) => a.field === 'currency' && !a.passed))

  return (
    <div className="page">
      <PageBanner video="probe-sandbox">
        <PageHead eyebrow="Prove · compatibility probe" title={<>Proof, <span className="grad-text">not prediction</span></>}
          sub="The producer and the consumer run at their exact deployed commits, materialized with git archive into an isolated sandbox, fed the same fixtures Stage validated. The engine judges the observations; no model decides PASS or FAIL."
          actions={<button className="btn primary lg" onClick={runNow} disabled={busy}>{busy ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="play" size={14} />} Run probe in sandbox</button>} />
      </PageBanner>
      {err && <div className="callout fail" style={{ marginBottom: 16 }}><span>✕</span><div className="err">{err}</div></div>}

      <div className="grid g-2-1">
        <Card title={run ? <>Probe run · {run.run_id}</> : 'Probe run'} right={run && <State s={run.result} lg />}>
          {run ? <Console lines={run.transcript} animate={fresh} speed={90} height={470} /> : (
            <div className="empty">
              <div className="big-num grad-text">No probe yet</div>
              <p className="mt-s">Run the probe, or run an investigation, to execute mq-bridge 3.1 → legacy-ledger 6.9 in isolation.</p>
              <button className="btn primary mt" onClick={runNow} disabled={busy}>Run probe</button>
            </div>
          )}
        </Card>
        <Card title="Probe history" right={<span className="small muted">{runs?.length ?? 0} runs</span>}>
          {!runs ? <Loading /> : (
            <div style={{ display: 'grid', gap: 8, maxHeight: 470, overflow: 'auto' }}>
              {runs.map((r: any) => (
                <button key={r.run_id} className="glass" style={{ padding: 10, textAlign: 'left', cursor: 'pointer', color: 'inherit', borderColor: run?.run_id === r.run_id ? 'var(--accent)' : undefined }}
                  onClick={() => { setFresh(false); setRunId(r.run_id) }}>
                  <div className="row between"><span className="small strong">{r.producer} → {r.consumer}</span><State s={r.result} /></div>
                  <div className="tiny muted mono">{Object.keys(r.config).length ? `config ${Object.entries(r.config).map(([k, v]) => `${k}=${v}`).join(' ')} · ` : ''}{r.assertions_failed}/{r.assertions_total} failed · {r.held} held · {fmtMs(r.duration_ms)} · {ago(r.finished_at)}</div>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      {run && (
        <div className="grid g3 mt-l">
          {run.fixtures.map((f: any) => (
            <Card key={f.fixture} title={f.label} right={f.outcome === 'HELD' ? <State s="HELD" /> : <State s={f.passed ? 'PASS' : 'FAIL'} />}>
              <div className="tiny muted">BILL.OUT event</div>
              <div className="mono small">{f.event.customerId} · {f.event.currencyCode} · {f.event.amount}</div>
              {f.record && <>
                <div className="tiny muted mt-s">LEDGER.IN record ({f.record_length} bytes, {f.producer_layout})</div>
                <div className="mono small" style={{ letterSpacing: '0.08em' }}>{f.record.replace(/ /g, '·')}</div>
              </>}
              {f.assertions && (
                <table className="tbl mt-s">
                  <thead><tr><th>Field</th><th>Expected</th><th>Posted</th></tr></thead>
                  <tbody>{f.assertions.map((a: any) => (
                    <tr key={a.field} className={a.passed ? '' : 'hl'}><td className="mono small">{a.field}</td><td className="mono small">{a.expected}</td><td className={`mono small ${a.passed ? 'c-ok' : 'c-fail'}`}>{a.actual} {a.passed ? '✓' : '✕'}</td></tr>
                  ))}</tbody>
                </table>
              )}
              {f.note && <div className="small muted mt-s">{f.note}</div>}
            </Card>
          ))}
        </div>
      )}

      {run?.silent_failure && first && (
        <section id="silent" className="mt-l rise">
          <div className="page-bg" style={{ padding: 24 }}>
            <AmbientVideo name="silent-failure" />
            <div className="kicker" style={{ position: 'relative' }}>silent semantic failure</div>
            <h2 className="page-title" style={{ position: 'relative' }}>Infrastructure is green. <span style={{ color: 'var(--fail)' }}>The business data is wrong.</span></h2>
            <div className="silent mt" style={{ position: 'relative' }}>
              <div className="silent-col infra">
                <div className="kicker c-ok">what every dashboard saw</div>
                {[['HTTP', `${first.infrastructure.http_status}`], ['MQ', 'ACK'], ['Db2', 'COMMIT'], ['LDGPOST status', first.infrastructure.status], ['Pods', '8 / 8 healthy'], ['Pipelines', 'green']].map(([k, v]) => (
                  <div key={k} className="sig"><span className="c-ok">✓</span>{k}<span className="v c-ok">{v}</span></div>
                ))}
              </div>
              <div className="silent-mid">BUT</div>
              <div className="silent-col biz">
                <div className="kicker c-fail">what the ledger booked</div>
                {first.assertions.filter((a: any) => !a.passed).map((a: any) => (
                  <div key={a.field} className="sig"><span className="c-fail">✕</span>{a.field === 'customer_id' ? 'Customer' : a.field === 'amount' ? 'Amount' : 'Currency'}
                    <span className="v"><span className="dim">{a.field === 'amount' ? money(a.expected) : a.expected}</span> → <b className="c-fail">{a.field === 'amount' ? money(a.actual) : a.actual}</b></span></div>
                ))}
                {eur && eur !== first && eur.assertions.filter((a: any) => !a.passed).map((a: any) => (
                  <div key={'eur' + a.field} className="sig"><span className="c-fail">✕</span>Currency (existing customer)<span className="v"><span className="dim">{a.expected}</span> → <b className="c-fail">{a.actual}</b></span></div>
                ))}
                <div className="small t2 mt-s">{first.assertions[0].actual} is a different, real-looking account. No exception, no alert, no rollback trigger.</div>
              </div>
            </div>
            <div className="row mt" style={{ position: 'relative' }}>
              <button className="btn danger" onClick={() => go('/divergence')}>First demonstrated divergence →</button>
              <span className="small muted">Why the DEV smoke test passed: its only fixture was a 10-character USD customer, the one case that survives.</span>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
