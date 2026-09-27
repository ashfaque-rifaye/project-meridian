import { useState } from 'react'
import { api, post, useApi, useDataVersion } from '../api'
import type { Go } from '../App'
import { DiffView } from '../components/Code'
import { AmbientVideo, PageBanner } from '../components/Media'
import { Card, copy, Icon, Loading, Modal, PageHead, State } from '../components/ui'

export default function Remediation({ go }: { go: Go }) {
  const { bump } = useDataVersion()
  const { data: strategies } = useApi('/remediation/strategies')
  const { data: candidate } = useApi('/remediation/candidate')
  const [results, setResults] = useState<Record<string, any>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const [probe, setProbe] = useState<any>(null)
  const [handoff, setHandoff] = useState<any>(null)

  const run = async (id: string) => {
    setBusy(id)
    try {
      const r = await post(`/remediation/${id}/rehearse`)
      setResults((s) => ({ ...s, [id]: r }))
      if (id === 'bridge-compat-mode' && r.critical_edge?.probe?.run_id) setProbe(await api(`/probes/runs/${r.critical_edge.probe.run_id}`))
      bump()
    } finally {
      setBusy(null)
    }
  }
  const openInBob = async () => setHandoff(await post('/handoff'))
  const b = results['bridge-compat-mode']
  const stepState = (i: number) => {
    if (!b) return i === 0 ? 'fail' : ''
    return ['fail', 'ok', 'ok', 'ok', b.critical_edge?.probe?.result === 'PASS' ? 'ok' : 'fail'][i]
  }

  return (
    <div className="page">
      <PageBanner video="remediation-bridge">
        <PageHead eyebrow="Remediate · smallest safe change" title={<>Every option rehearsed. <span className="grad-text">Nothing deployed.</span></>}
          sub="Each strategy is evaluated like a real promotion: validation memory, then isolated regression probes. The human owns the release decision."
          actions={<button className="btn primary lg" onClick={openInBob}><Icon name="bot" /> Open in Bob</button>} />
      </PageBanner>

      <div className="steps" style={{ marginBottom: 18 }}>
        {['FAILED', 'BOB FIX', 'REBUILD', 'PROBE', 'PASS'].map((s, i) => (
          <div key={s} className={`stepx ${stepState(i)}`}>{i === 0 ? '✕' : stepState(i) === 'ok' ? '✓' : '○'} {s}</div>
        ))}
      </div>

      {!strategies ? <Loading /> : (
        <div className="grid g3">
          {strategies.map((s: any) => {
            const r = results[s.id]
            return (
              <Card key={s.id} title={<>{s.letter} · {s.title}</>} right={r && <State s={r.rehearsal.verdict} />}>
                <p className="small t2">{s.action}</p>
                <div className="tiny muted mt-s">Owner: {s.owner}</div>
                <div className="callout mt small"><span>⚖</span><div>{s.tradeoff}</div></div>
                <button className="btn primary mt" onClick={() => run(s.id)} disabled={!!busy}>
                  {busy === s.id ? <span className="spinner" style={{ borderTopColor: '#fff' }} /> : <Icon name="rehearse" size={14} />} {s.id === 'bridge-compat-mode' ? 'Draft candidate + regression probe' : 'Rehearse'}
                </button>
                {r && (
                  <div className="mt rise">
                    <div className="small strong">{r.rehearsal.headline}</div>
                    <table className="tbl mt-s"><tbody>
                      {r.rehearsal.edges.filter((e: any) => e.state !== 'VERIFIED' || e.edge_id === 'mq-bridge--legacy-ledger').map((e: any) => (
                        <tr key={e.edge_id}><td className="small">{e.producer} {e.producer_version} → {e.consumer} {e.consumer_version}</td><td><State s={e.state} /></td></tr>
                      ))}
                    </tbody></table>
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {b?.candidate && (
        <div className="grid g-2-1 mt-l rise">
          <Card title={<>Candidate · mq-bridge {b.candidate.label}</>} right={<span className={`tag ${b.candidate.authored_by_bob ? 'c-accent' : ''}`}>{b.candidate.author}</span>}>
            <dl className="kv small">
              <dt>branch</dt><dd className="mono">{b.candidate.branch}</dd>
              <dt>commit</dt><dd className="mono">{b.candidate.base_commit} → {b.candidate.commit}</dd>
              <dt>worktree</dt><dd className="mono">{b.candidate.worktree}</dd>
              <dt>config</dt><dd className="mono">{Object.entries(b.candidate.config).map(([k, v]) => `${k}=${v}`).join(' ')}</dd>
            </dl>
            <div className="mt"><DiffView diff={b.candidate.diff} /></div>
          </Card>
          <Card title="Regression probe · against legacy-ledger 6.9" right={probe && <State s={probe.result} lg />} className="card-video">
            {probe?.result === 'PASS' && <AmbientVideo name="convergence-snap" className="card-bg" />}
            {probe ? (
              <>
                {probe.fixtures.map((f: any) => (
                  <div key={f.fixture} className="glass" style={{ padding: 10, marginBottom: 8 }}>
                    <div className="row between"><span className="small strong">{f.label}</span><State s={f.outcome === 'HELD' ? 'HELD' : f.passed ? 'PASS' : 'FAIL'} /></div>
                    <div className="tiny muted">{f.outcome === 'HELD' ? f.note : `posted exactly: ${f.assertions?.map((a: any) => a.actual).join(' · ')}`}</div>
                  </div>
                ))}
                <div className="callout ok small mt"><span>✓</span><div>No delivered record is corrupted. Records that LEDGREC rev 6 cannot represent wait on LEDGER.HOLD for CR-4471.</div></div>
                <button className="btn mt" onClick={() => go('/probe')}>Open in probe console</button>
              </>
            ) : <Loading what="Waiting for the regression probe" />}
          </Card>
        </div>
      )}

      <Card className="mt-l" title="Hand the evidence to IBM Bob">
        <div className="small t2">
          <b>Open in Bob</b> writes the evidence packet and a task for the <span className="mono">meridian-remediator</span> custom mode. Bob confirms the layouts with the <span className="mono">implicit-contract-discovery</span> skill, writes a candidate to <span className="mono">{candidate?.bob_candidate_path}</span>, and calls the MCP tool <span className="mono">verify_remediation</span>. Current candidate source: <b>{candidate?.author}</b>.
        </div>
      </Card>

      <Modal open={!!handoff} onClose={() => setHandoff(null)} title="Open in IBM Bob · meridian-remediator">
        {handoff && (<>
          <p className="small t2">Written to <span className="mono">{handoff.prompt_file}</span> and <span className="mono">{handoff.evidence_file}</span>.</p>
          <pre className="block mt">{handoff.prompt}</pre>
          <button className="btn primary mt" onClick={() => copy(handoff.prompt)}>Copy prompt</button>
        </>)}
      </Modal>
    </div>
  )
}
