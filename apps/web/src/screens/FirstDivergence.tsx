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
  if (!data || !flow) return <div className="page"><Loading what="Checking production" /></div>
  const fd = data.first_divergence
  if (!fd) {
    return (
      <div className="page">
        <PageHead eyebrow="Test · failing connection" title={<>No failing connection <span className="grad-text">found yet</span></>}
          sub={data.unvalidated_edges.length ? `${data.unvalidated_edges.length} connection has never been tested. Meridian won’t mark it as failing until a compatibility test shows it.` : 'Every connection in production has a passing test.'} />
        <button className="btn primary" onClick={() => go('/investigate')}><Icon name="play" size={14} /> Run release check</button>
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
    ['Code at the deployed commits', `${fd.producer}@${fd.producer_commit} · ${fd.consumer}@${fd.consumer_commit}`, '/contract'],
    ['Where the versions came from', `${p.source} · ${c.source}`, '/composition'],
    ['Documents', 'interface-control.xlsx · CR-4471 (change-request.pdf)', '/contract'],
    ['Test history', evidence ? `${evidence.exercised.length} smoke test(s) · ran side by side ${evidence.observed.length} time(s) · 0 full tests` : fd.evidence_tier, '/flow'],
    ['Test output', run ? `${run.run_id} · ${run.assertions_failed} of ${run.assertions_total} checks failed` : '—', '/probe'],
  ]

  return (
    <div className="page">
      <section className="hero" style={{ minHeight: 0 }}>
        <div className="hero-media"><AmbientVideo name="silent-failure" /></div>
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div className="fdd-label">✕ FAILING CONNECTION · {ENV_LABEL[fd.environment]} · {flow.name}</div>
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
            <span className="pill">untested since {fmtTime(fd.unvalidated_since)} UTC</span>
            <span className="pill">running untested for {fmtDuration((new Date('2026-09-25T16:20:00Z').getTime() - new Date(fd.unvalidated_since).getTime()) / 1000)}</span>
            {fd.triggering_deployment && <span className="pill">started by {fd.triggering_deployment.event_id}</span>}
            {fd.probe && <span className="pill c-fail">test {fd.probe.result}{fd.probe.silent_failure ? ' · no error raised' : ''} · {fmtMs(fd.probe.duration_ms)}</span>}
          </div>
          <div className="row mt">
            <button className="btn primary lg" onClick={openInBob} disabled={busy}><Icon name="bot" /> Send to IBM Bob</button>
            <button className="btn lg" onClick={() => go('/rehearse')}><Icon name="rehearse" /> Preview a deployment</button>
            <button className="btn lg" onClick={() => go('/remediate')}><Icon name="wrench" /> Fix options</button>
            <button className="btn lg" onClick={() => go('/evidence')}><Icon name="packet" /> Evidence report</button>
          </div>
        </div>
      </section>

      <div className="grid g2 mt-l">
        <Card title="Why it fails">
          <ul style={{ paddingLeft: 18, display: 'grid', gap: 8 }} className="t2">
            {constraints.filter((k: any) => !k.compatible).map((k: any) => (
              <li key={k.field}><b className="mono">{k.field}</b>: sender writes {k.producer}, receiver reads {k.consumer}. {k.risk}</li>
            ))}
            <li>{data.contract?.summary}</li>
            <li>There is no written spec for {fd.interface}. The format only exists in a COBOL copybook, constants in the code and a spreadsheet.</li>
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
            { at: fd.consumer_deployed_at, t: `${fd.consumer} ${fd.consumer_version} deployed to PROD`, s: 'Change window CR-4402 (R-26.8)', k: 'ok' },
            { at: '2026-09-24T14:30:00Z', t: 'Stage tests R-26.9 end to end', s: `${fd.producer} 3.1 + ${fd.consumer} 7.0 · every connection passed`, k: 'ok' },
            { at: fd.producer_deployed_at, t: `${fd.producer} ${fd.producer_version} deployed to PROD`, s: fd.triggering_deployment ? `${fd.triggering_deployment.tool} · ${fd.triggering_deployment.trigger} · ${fd.triggering_deployment.note || ''}` : '', k: 'fail' },
            { at: fd.unvalidated_since, t: 'Untested versions go live', s: `${fd.producer} ${fd.producer_version} → ${fd.consumer} ${fd.consumer_version} were never tested together`, k: 'fail' },
            { at: '2026-09-27T02:00:00Z', t: 'CR-4471 change window (scheduled)', s: 'legacy-backend 7.0 + backend-db V15', k: 'hold' },
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
          <Card title="Summary">
            <p className="t2">{packet.human_summary}</p>
            <div className="tiny muted mt">Based on test results and deployment records. It shows where the problem is, not why the team deployed it.</div>
          </Card>
          <Card title="Evidence checks" right={<State s={packet.review.verdict} />}>
            {packet.review.checks.map((ck: any) => (
              <div key={ck.id} className="row small" style={{ marginBottom: 5 }}>
                <span className={ck.passed ? 'c-ok' : 'c-fail'}>{ck.passed ? '✓' : '✕'}</span>{ck.label}<span className="spacer" /><span className="tiny dim ellipsis" style={{ maxWidth: 220 }}>{ck.detail}</span>
              </div>
            ))}
          </Card>
        </div>
      )}

      <Modal open={!!handoff} onClose={() => setHandoff(null)} title="Send to IBM Bob · fix mode">
        {handoff && (
          <>
            <p className="small t2">The evidence report and this task were saved to <span className="mono">{handoff.evidence_file}</span> and <span className="mono">{handoff.prompt_file}</span>. Paste the prompt into Bob (or reference the file with @). Bob drafts the fix on a separate branch. Nothing is deployed.</p>
            <pre className="block mt">{handoff.prompt}</pre>
            <div className="row mt">
              <button className="btn primary" onClick={() => copy(handoff.prompt)}>Copy prompt</button>
              <button className="btn" onClick={() => go('/remediate')}>Go to fix options</button>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
