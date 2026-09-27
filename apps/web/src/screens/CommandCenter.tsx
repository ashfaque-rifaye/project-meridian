import { ENV_LABEL, fmtDuration, fmtMs, fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { AmbientVideo } from '../components/Media'
import Scene3D from '../components/Scene3D'
import { Card, ErrorBox, Icon, Loading, State, Stat } from '../components/ui'
import { useInvestigation } from '../investigation'

const KEY_COMPONENTS = ['mq-bridge', 'legacy-ledger', 'ledger-db']

export default function CommandCenter({ go, run }: { go: Go; run: () => void }) {
  const { data, error } = useApi('/overview')
  const { data: drift } = useApi('/drift')
  const { data: flow } = useApi('/flow')
  const { data: prodEnv } = useApi('/environments/prod')
  const inv = useInvestigation()
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data) return <div className="page"><Loading what="Reconstructing environments" /></div>

  const prod = data.prod
  const fd = prod.first_divergence
  const tone = prod.verdict === 'DIVERGED' ? '' : prod.verdict === 'UNVALIDATED' ? 'warn' : 'ok'
  const stage = data.environments.find((e: any) => e.environment === 'stage')
  const stageVerified = stage?.counts?.VERIFIED ?? 0

  return (
    <div className="page">
      <section className={`hero ${tone}`}>
        <div className="hero-media"><AmbientVideo name="hero-convergence" /></div>
        <div className="hero-grid">
          <div>
            <div className="hero-kicker">{data.release.id} · {data.flow.name} · PRODUCTION · {fmtTime(data.snapshot_time)} UTC</div>
            {prod.verdict === 'DIVERGED' && (
              <h1 className="hero-title">Production is running <em>a system nobody tested.</em></h1>
            )}
            {prod.verdict === 'UNVALIDATED' && (
              <h1 className="hero-title">Production is running <em>a combination nobody validated.</em></h1>
            )}
            {prod.verdict === 'CONVERGED' && (
              <h1 className="hero-title">Production matches <em>the system that was validated.</em></h1>
            )}
            <p className="hero-tag">
              {prod.verdict === 'CONVERGED'
                ? 'Every boundary on the flow has passing validation evidence for the exact versions running.'
                : 'Every component passed. The system didn’t. Stage validated this release end to end, every pod is healthy and every pipeline is green, yet the exact versions running together in PROD never ran together anywhere on the promotion path.'}
            </p>
            <div className="row wrap mt">
              {prod.verdict !== 'DIVERGED' && (
                <button className="btn primary lg" onClick={run} disabled={inv.status === 'running'}>
                  <Icon name="play" size={14} /> Run investigation
                </button>
              )}
              {fd && <button className="btn danger lg" onClick={() => go('/divergence')}><Icon name="target" /> First demonstrated divergence</button>}
              <button className="btn lg" onClick={() => go('/rehearse')}><Icon name="rehearse" /> Rehearse promotion</button>
              {fd && <button className="btn lg" onClick={() => go('/remediate')}><Icon name="wrench" /> Remediate</button>}
            </div>
          </div>
          <div style={{ minHeight: 340 }}>
            {flow && prodEnv ? (
              <Scene3D mode="flow" height={340} components={flow.components}
                edges={prodEnv.edges.map((e: any) => ({ producer: e.producer, consumer: e.consumer, state: e.state }))}
                composition={prodEnv.composition} />
            ) : <Loading what="Rendering system" />}
            <div className="row wrap small muted" style={{ justifyContent: 'center', gap: 14 }}>
              <span><span className="dot ok" /> verified boundary</span>
              <span><span className="dot warn" /> untested</span>
              <span><span className="dot fail" /> failed probe</span>
              <span className="dim">live 3D · move your mouse</span>
            </div>
          </div>
        </div>
      </section>
          <div className="grid g4 mt">
            <Stat label="Unvalidated for" value={fmtDuration(prod.exposure_seconds)} tone={prod.verdict === 'CONVERGED' ? 'ok' : 'fail'}
              sub={prod.unvalidated_since ? `since ${fmtTime(prod.unvalidated_since)} UTC` : 'no unvalidated boundary'} />
            <Stat label="Next CAB window" value={data.next_window_in_seconds ? `in ${fmtDuration(data.next_window_in_seconds)}` : '—'}
              sub={data.scheduled_changes[0] ? `${data.scheduled_changes[0].change_request} · ${fmtTime(data.scheduled_changes[0].window_start)}` : ''} />
            <Stat label="Component health" value={prod.all_healthy ? '8 / 8 healthy' : 'degraded'} tone="ok" sub="every pod ready · every app STARTED" />
            <Stat label="Pipelines" value="all green" tone="ok" sub="Cloud Deploy · Argo CD · Azure DevOps · Jenkins" />
          </div>

      <div className="mt-l">
        <div className="card-title"><span>Promotion path · validation verdict per environment</span>
          <span className="right small muted">edges: <span className="c-ok">▬ verified</span> · <span className="c-warn">▬ untested</span> · <span className="c-fail">▬ failed</span></span>
        </div>
        <div className="lanes">
          {data.environments.map((env: any) => (
            <div key={env.environment} className={`lane ${env.verdict}`} onClick={() => go('/composition')}>
              <div className="row between">
                <span className="lane-env">{ENV_LABEL[env.environment]}</span>
                <State s={env.verdict} />
              </div>
              <div className="edge-dots">
                {['web-checkout--order-api', 'order-api--payment-service', 'payment-service--kafka-orders', 'kafka-orders--billing-service',
                  'billing-service--mq-bridge', 'mq-bridge--legacy-ledger', 'legacy-ledger--ledger-db'].map((id) => {
                  const unval = env.unvalidated_edges.includes(id)
                  const st = env.first_divergence?.edge_id === id ? 'FAILED' : unval ? 'UNTESTED' : 'VERIFIED'
                  return <span key={id} className={`edge-dot ${st}`} title={`${id}: ${st}`} />
                })}
              </div>
              <div className="lane-comp">
                {KEY_COMPONENTS.map((c) => {
                  const v = env.composition[c]
                  const bad = env.environment === 'prod' && v !== stage?.composition?.[c]
                  return [<span key={c + 'n'}>{c}</span>, <span key={c + 'v'} className={`v ${bad ? 'bad' : ''}`}>{v}</span>]
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      <Card className="mt-l" title={<>The system nobody tested <span className="tag" style={{ marginLeft: 8 }}>PROD · exact composition</span></>}
        right={<span className="small muted">validated reference: STAGE · {stageVerified}/7 boundaries verified</span>}>
        <div className="strip">
          {data.system_nobody_tested.map((c: any) => (
            <div key={c.component} className={`chip ${c.matches_validated ? '' : 'bad'}`}>
              <div className="chip-name">{c.component}</div>
              <div className="chip-ver">{c.version}</div>
              <div className="chip-sub">{c.matches_validated ? 'as validated' : `validated: ${c.validated_version}`}</div>
            </div>
          ))}
        </div>
        <p className="small muted mt">
          {prod.verdict === 'CONVERGED'
            ? 'This exact combination has passing validation evidence.'
            : 'This exact combination has no passing validation evidence on the promotion path. Observed together is not the same as validated together.'}
        </p>
      </Card>

      <div className="grid g-2-1 mt-l">
        {fd ? (
          <section className="fdd rise">
            <div className="fdd-label">✕ FIRST DEMONSTRATED DIVERGENCE · PROD</div>
            <div className="fdd-edge">
              <div className="fdd-node">
                <div className="fdd-name">{fd.producer}</div>
                <div className="fdd-ver">{fd.producer_version}</div>
                <div className="fdd-meta">@{fd.producer_commit} · deployed {fmtTime(fd.producer_deployed_at)}</div>
              </div>
              <div className="fdd-arrow">⟶<small>{fd.interface}</small></div>
              <div className="fdd-node bad">
                <div className="fdd-name">{fd.consumer}</div>
                <div className="fdd-ver">{fd.consumer_version} ✕</div>
                <div className="fdd-meta">@{fd.consumer_commit} · deployed {fmtTime(fd.consumer_deployed_at)}</div>
              </div>
            </div>
            <p className="t2">{fd.reason}</p>
            <div className="row wrap mt small muted">
              <span className="pill">unvalidated since {fmtTime(fd.unvalidated_since)} UTC</span>
              {fd.triggering_deployment && <span className="pill">created by {fd.triggering_deployment.tool} · {fd.triggering_deployment.trigger}</span>}
              {fd.probe && <span className="pill">probe {fd.probe.result} · {fd.probe.assertions_failed}/{fd.probe.assertions_total} assertions failed · {fmtMs(fd.probe.duration_ms)}</span>}
            </div>
            <div className="row mt">
              <button className="btn danger" onClick={() => go('/divergence')}>Open forensic view <Icon name="arrow" size={14} /></button>
              <button className="btn" onClick={() => go('/probe')}>Probe output</button>
              <button className="btn" onClick={() => go('/evidence')}>Evidence packet</button>
            </div>
          </section>
        ) : (
          <Card title="First demonstrated divergence">
            {prod.untested.length ? (
              <>
                <div className="callout warn">
                  <span>⚠</span>
                  <div>
                    <div className="strong">{prod.untested.length} boundary in PROD lacks validation evidence</div>
                    <div className="small t2">{prod.untested.join(', ')}. Meridian has not guessed its compatibility. Run an investigation to discover its implicit contract and prove the result with an isolated probe.</div>
                  </div>
                </div>
                <button className="btn primary mt" onClick={run} disabled={inv.status === 'running'}><Icon name="play" size={14} /> Run investigation</button>
              </>
            ) : (
              <div className="callout ok"><span>✓</span><div>No unvalidated boundaries on the flow in PROD.</div></div>
            )}
          </Card>
        )}

        <Card title="Why most differences don’t matter" right={<a onClick={() => go('/drift')} style={{ cursor: 'pointer' }}>details →</a>}>
          {drift ? (
            <div className="funnel">
              {drift.funnel.map((f: any, i: number) => (
                <div key={f.stage} className={`funnel-step ${i === drift.funnel.length - 1 ? 'last' : ''}`} onClick={() => go('/drift')}>
                  <div className={`funnel-n ${i === drift.funnel.length - 1 && f.count ? 'c-fail' : ''}`}>{f.count}</div>
                  <div className="funnel-bar">
                    <div className="funnel-fill" style={{ width: `${Math.max(4, (f.count / drift.funnel[0].count) * 100)}%` }} />
                    <div className="funnel-label">{f.label}</div>
                  </div>
                </div>
              ))}
              <div className="tiny dim">Computed from this demo’s synthetic adapter data (STAGE vs PROD). Not an industry benchmark.</div>
            </div>
          ) : <Loading />}
        </Card>
      </div>

      <div className="grid g4 mt-l">
        <Stat label="Evidence sources read" value={data.environments.length * 8} sub="adapter outputs across 4 environments" />
        <Stat label="Probe runs recorded" value={data.probe_runs} sub="isolated · exact deployed commits" />
        <Stat label="Evidence packet" value={data.latest_packet_id ? 'ready' : '—'} sub={data.latest_packet_id || 'run an investigation'} />
        <Stat label="Last investigation" value={inv.result ? fmtMs(inv.result.duration_ms) : '—'} sub={inv.result ? `measured · incl. ${inv.result.pace_ms} ms/step presentation pacing` : 'measured in this demo'} />
      </div>
    </div>
  )
}
