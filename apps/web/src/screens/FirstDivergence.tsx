import { useState } from 'react'
import { ENV_LABEL, fmtDuration, fmtMs, fmtTime, post, useApi } from '../api'
import type { Go } from '../App'
import { AmbientVideo } from '../components/Media'
import { Card, copy, ErrorBox, Icon, Loading, Modal, PageHead, Platform, State } from '../components/ui'

export default function FirstDivergence({ go }: { go: Go }) {
  const { data, error } = useApi('/divergence?env=prod')
  const { data: flow } = useApi('/flow')
  const [handoff, setHandoff] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data || !flow) return <div className="page"><Loading what="Evaluating PROD" /></div>
  const fd = data.first_divergence
  if (!fd) {
    return (
      <div className="page">
        <PageHead eyebrow="Prove · first demonstrated divergence" title={<>No divergence <span className="grad-text">demonstrated yet</span></>}
          sub={data.unvalidated_edges.length ? `${data.unvalidated_edges.length} boundary lacks validation evidence. Meridian will not call it failed until an isolated probe demonstrates it.` : 'Every boundary on the flow in PROD has passing validation evidence.'} />
        <button className="btn primary" onClick={() => go('/investigate')}><Icon name="play" size={14} /> Run investigation</button>
      </div>
    )
  }
  const meta = (id: string) => flow.components.find((c: any) => c.id === id)
  const p = data.composition[fd.producer]
  const c = data.composition[fd.consumer]
  const packet = data.packet
  const evidence = packet?.validation_history
  const run = data.probe_run
  const constraints = data.contract?.constraints || []

  const openInBob = async () => {
    setBusy(true)
    try { setHandoff(await post('/handoff')) } finally { setBusy(false) }
  }

  const checklist = [
    ['Source at deployed commits', `${fd.producer}@${fd.producer_commit} · ${fd.consumer}@${fd.consumer_commit}`, '/contract'],
    ['Deployment evidence', `${p.source} · ${c.source}`, '/composition'],
    ['Interface document', 'LEDG-ICD-007 (interface-control.xlsx) · CR-4471 (change-request.pdf)', '/contract'],
    ['Validation history', evidence ? `tier ${evidence.tier} · ${evidence.exercised.length} exercised · ${evidence.observed.length} co-existence window(s) · 0 verified` : fd.evidence_tier, '/flow'],
    ['Probe output', run ? `${run.run_id} · ${run.assertions_failed}/${run.assertions_total} assertions failed` : '—', '/probe'],
  ]

  return (
    <div className="page">
      <section className="hero" style={{ minHeight: 0 }}>
        <div className="hero-media"><AmbientVideo name="silent-failure" /></div>
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div className="fdd-label">✕ FIRST DEMONSTRATED DIVERGENCE · {ENV_LABEL[fd.environment]} · {flow.name}</div>
          <div className="fdd-edge">
            <div className="fdd-node">
              <div className="row"><span className="fdd-name">{fd.producer}</span><Platform p={meta(fd.producer).platform} /></div>
              <div className="fdd-ver">{fd.producer_version}</div>
              <div className="fdd-meta">@{fd.producer_commit} · {meta(fd.producer).cloud}</div>
              <div className="fdd-meta">deployed {fmtTime(fd.producer_deployed_at)} · {meta(fd.producer).deploy_tool}</div>
            </div>
            <div className="fdd-arrow">⟶ ✕<small>{fd.interface}</small></div>
            <div className="fdd-node bad">
              <div className="row"><span className="fdd-name">{fd.consumer}</span><Platform p={meta(fd.consumer).platform} /></div>
              <div className="fdd-ver" style={{ color: 'var(--fail)' }}>{fd.consumer_version}</div>
              <div className="fdd-meta">@{fd.consumer_commit} · {meta(fd.consumer).cloud}</div>
              <div className="fdd-meta">deployed {fmtTime(fd.consumer_deployed_at)} · {meta(fd.consumer).deploy_tool}</div>
            </div>
          </div>
          <div className="row wrap">
            <span className="pill">unvalidated since {fmtTime(fd.unvalidated_since)} UTC</span>
            <span className="pill">exposure {fmtDuration((new Date('2026-09-25T16:20:00Z').getTime() - new Date(fd.unvalidated_since).getTime()) / 1000)} at scenario time</span>
            {fd.triggering_deployment && <span className="pill">created by {fd.triggering_deployment.event_id}</span>}
            {fd.probe && <span className="pill c-fail">probe {fd.probe.result}{fd.probe.silent_failure ? ' · silent' : ''} · {fmtMs(fd.probe.duration_ms)}</span>}
          </div>
          <div className="row mt">
            <button className="btn primary lg" onClick={openInBob} disabled={busy}><Icon name="bot" /> Open in Bob</button>
            <button className="btn lg" onClick={() => go('/rehearse')}><Icon name="rehearse" /> Rehearse promotion</button>
            <button className="btn lg" onClick={() => go('/remediate')}><Icon name="wrench" /> Remediate</button>
            <button className="btn lg" onClick={() => go('/evidence')}><Icon name="packet" /> Evidence packet</button>
          </div>
        </div>
      </section>

      <div className="grid g2 mt-l">
        <Card title="Why?">
          <ul style={{ paddingLeft: 18, display: 'grid', gap: 8 }} className="t2">
            {constraints.filter((k: any) => !k.compatible).map((k: any) => (
              <li key={k.field}><b className="mono">{k.field}</b>: producer {k.producer}, consumer {k.consumer}. {k.risk}</li>
            ))}
            <li>{data.contract?.summary}</li>
            <li>No formal contract exists for {fd.interface}: only a copybook, layout constants and an ICD spreadsheet.</li>
          </ul>
          <div className="sep-grad" />
          <div className="kicker">evidence</div>
          <div style={{ display: 'grid', gap: 6 }} className="mt-s">
            {checklist.map(([label, detail, to]) => (
              <div key={label} className="row" style={{ cursor: 'pointer' }} onClick={() => go(to)}>
                <span className="c-ok">✓</span><span className="strong small" style={{ flex: 'none' }}>{label}</span><span className="tiny muted ellipsis" style={{ minWidth: 0, flex: 1 }}>{detail}</span>
              </div>
            ))}
          </div>
        </Card>
        <Card title="How the system got here">
          {[
            { at: fd.consumer_deployed_at, t: `${fd.consumer} ${fd.consumer_version} deployed to PROD`, s: 'CAB window CR-4402 (R-26.8)', k: 'ok' },
            { at: '2026-09-24T14:30:00Z', t: 'Stage validates R-26.9 end to end', s: `${fd.producer} 3.1 + ${fd.consumer} 7.0 · every boundary verified`, k: 'ok' },
            { at: fd.producer_deployed_at, t: `${fd.producer} ${fd.producer_version} promoted to PROD`, s: fd.triggering_deployment ? `${fd.triggering_deployment.tool} · ${fd.triggering_deployment.trigger} · ${fd.triggering_deployment.note || ''}` : '', k: 'fail' },
            { at: fd.unvalidated_since, t: 'Untested composition created', s: `${fd.producer} ${fd.producer_version} → ${fd.consumer} ${fd.consumer_version} never ran together with semantic checks`, k: 'fail' },
            { at: '2026-09-27T02:00:00Z', t: 'CR-4471 window (scheduled)', s: 'legacy-ledger 7.0 + ledger-db V15', k: 'hold' },
          ].map((e, i) => (
            <div key={i} className="row" style={{ alignItems: 'flex-start', marginBottom: 12 }}>
              <span className={`dot ${e.k === 'fail' ? 'fail' : e.k === 'hold' ? 'accent' : 'ok'}`} style={{ marginTop: 6 }} />
              <div>
                <div className="mono tiny muted">{fmtTime(e.at)} UTC</div>
                <div className="strong">{e.t}</div>
                <div className="small muted">{e.s}</div>
              </div>
            </div>
          ))}
          <div className="sep-grad" />
          {data.pattern.story.slice(-1).map((s: string) => <p key={s} className="small t2">{s}</p>)}
        </Card>
      </div>

      {packet && (
        <div className="grid g2 mt-l">
          <Card title="Human summary">
            <p className="t2">{packet.human_summary}</p>
            <div className="tiny muted mt">{packet.claim_type}</div>
          </Card>
          <Card title="Evidence review" right={<State s={packet.review.verdict} />}>
            {packet.review.checks.map((ck: any) => (
              <div key={ck.id} className="row small" style={{ marginBottom: 5 }}>
                <span className={ck.passed ? 'c-ok' : 'c-fail'}>{ck.passed ? '✓' : '✕'}</span>{ck.label}<span className="spacer" /><span className="tiny dim ellipsis" style={{ maxWidth: 220 }}>{ck.detail}</span>
              </div>
            ))}
          </Card>
        </div>
      )}

      <Modal open={!!handoff} onClose={() => setHandoff(null)} title="Open in IBM Bob · meridian-remediator">
        {handoff && (
          <>
            <p className="small t2">The evidence packet and this task were written to <span className="mono">{handoff.evidence_file}</span> and <span className="mono">{handoff.prompt_file}</span>. Paste the prompt into Bob (or reference the file with @). Bob drafts the fix in an isolated candidate; nothing is deployed.</p>
            <pre className="block mt">{handoff.prompt}</pre>
            <div className="row mt">
              <button className="btn primary" onClick={() => copy(handoff.prompt)}>Copy prompt</button>
              <button className="btn" onClick={() => go('/remediate')}>Go to remediation</button>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
