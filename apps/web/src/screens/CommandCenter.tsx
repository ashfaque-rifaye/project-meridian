import { useState } from 'react'
import { ENV_LABEL, fmtDuration, fmtMs, fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { AmbientVideo } from '../components/Media'
import Scene3D from '../components/Scene3D'
import { Card, ErrorBox, Icon, Loading, State, Stat } from '../components/ui'
import { useInvestigation } from '../investigation'

const KEY_COMPONENTS = ['mq-bridge', 'legacy-backend', 'backend-db']
const CONNECTIONS = ['web-checkout--order-api', 'order-api--payment-service', 'payment-service--kafka-orders', 'kafka-orders--billing-service',
  'billing-service--mq-bridge', 'mq-bridge--legacy-backend', 'legacy-backend--backend-db']
const TIPS_KEY = 'meridian-dashboard-tips-dismissed'

/** Numbered marker that links a section of the page to the matching onboarding tip. */
function Cue({ n, on }: { n: number; on: boolean }) {
  return on ? <span className="cue" aria-label={`Tip ${n}`}>{n}</span> : null
}

function Onboarding({ onClose, onTour, go }: { onClose: () => void; onTour: () => void; go: Go }) {
  const tips = [
    ['Status', 'The banner tells you whether production is running a set of versions that was tested together.'],
    ['Environments', 'One card per environment. Each bar is a connection between two services: green is tested, amber is not tested, red failed a test.'],
    ['Failing connection', 'The exact pair of services that breaks, which deployment caused it and when.'],
    ['Next steps', 'Run a release check to repeat every step live, preview a deployment, or look at fix options.'],
  ]
  return (
    <section className="onboard rise" aria-labelledby="onboard-title">
      <div className="row between wrap" style={{ gap: 12 }}>
        <div>
          <div className="eyebrow">Getting started</div>
          <h2 id="onboard-title" className="onboard-title">What this dashboard shows</h2>
          <p className="onboard-lede">
            Meridian answers one question: are the versions running in production the same set that was tested together?
            Every service can pass its own tests and still break when combined with an older version of another service.
          </p>
        </div>
        <button className="btn ghost sm" onClick={onClose} aria-label="Hide tips">✕</button>
      </div>
      <ol className="onboard-steps">
        {tips.map(([t, d], i) => (
          <li key={t}><span className="cue">{i + 1}</span><div><div className="strong">{t}</div><div className="small t2">{d}</div></div></li>
        ))}
      </ol>
      <div className="callout info small mt">
        <span>ℹ</span>
        <div>
          <b>Dashboard or Release check?</b> The dashboard is a read-only summary of the latest results.
          The <b>Release check (live)</b> page runs the whole check again and shows each step and its log as it happens.
        </div>
      </div>
      <div className="row wrap mt">
        <button className="btn primary" onClick={onClose}>Got it</button>
        <button className="btn" onClick={onTour}><Icon name="story" size={14} /> Take the guided tour</button>
        <button className="btn ghost" onClick={() => go('/investigate')}><Icon name="bot" size={14} /> Open release check</button>
      </div>
    </section>
  )
}

export default function CommandCenter({ go, run, tour }: { go: Go; run: () => void; tour: () => void }) {
  const { data, error } = useApi('/overview')
  const { data: drift } = useApi('/drift')
  const { data: flow } = useApi('/flow')
  const { data: prodEnv } = useApi('/environments/prod')
  const inv = useInvestigation()
  const [tips, setTips] = useState(() => localStorage.getItem(TIPS_KEY) !== '1')
  const closeTips = () => {
    localStorage.setItem(TIPS_KEY, '1')
    setTips(false)
  }
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data) return <div className="page"><Loading what="Loading environments" /></div>

  const prod = data.prod
  const fd = prod.first_divergence
  const tone = prod.verdict === 'DIVERGED' ? '' : prod.verdict === 'UNVALIDATED' ? 'warn' : 'ok'
  const stage = data.environments.find((e: any) => e.environment === 'stage')
  const stageVerified = stage?.counts?.VERIFIED ?? 0

  return (
    <div className="page">
      <div className="row between wrap" style={{ marginBottom: 14, gap: 10 }}>
        <div>
          <div className="eyebrow">Dashboard</div>
          <div className="small muted">Latest results for production. Read-only: nothing here changes an environment.</div>
        </div>
        {!tips && <button className="btn ghost sm" onClick={() => setTips(true)}>? Show tips</button>}
      </div>

      {tips && <Onboarding onClose={closeTips} onTour={tour} go={go} />}

      <section className={`hero ${tone}`}>
        <div className="hero-media"><AmbientVideo name="hero-convergence" /></div>
        <div className="hero-grid">
          <div>
            <div className="hero-kicker"><Cue n={1} on={tips} /> {data.release.id} · {data.flow.name} · PRODUCTION · data as of {fmtTime(data.snapshot_time)} UTC</div>
            {prod.verdict === 'DIVERGED' && (
              <h1 className="hero-title">Production is running <em>versions that were never tested together.</em></h1>
            )}
            {prod.verdict === 'UNVALIDATED' && (
              <h1 className="hero-title">Production is running <em>an untested mix of versions.</em></h1>
            )}
            {prod.verdict === 'CONVERGED' && (
              <h1 className="hero-title">Production matches <em>the versions that were tested.</em></h1>
            )}
            <p className="hero-tag">
              {prod.verdict === 'CONVERGED'
                ? 'Every connection in this flow has a passing test for the exact versions that are running.'
                : 'Stage tested this release end to end, every service is healthy and every pipeline is green. But the exact versions now running together in production were never tested together in any environment.'}
            </p>
            <div className="row wrap mt">
              <Cue n={4} on={tips} />
              {prod.verdict !== 'DIVERGED' && (
                <button className="btn primary lg" onClick={run} disabled={inv.status === 'running'}>
                  <Icon name="play" size={14} /> Run release check
                </button>
              )}
              {fd && <button className="btn danger lg" onClick={() => go('/divergence')}><Icon name="target" /> See failing connection</button>}
              <button className="btn lg" onClick={() => go('/rehearse')}><Icon name="rehearse" /> Preview a deployment</button>
              {fd && <button className="btn lg" onClick={() => go('/remediate')}><Icon name="wrench" /> See fix options</button>}
            </div>
          </div>
          <div style={{ minHeight: 340 }}>
            {flow && prodEnv ? (
              <Scene3D mode="flow" height={340} components={flow.components}
                edges={prodEnv.edges.map((e: any) => ({ producer: e.producer, consumer: e.consumer, state: e.state }))}
                composition={prodEnv.composition} />
            ) : <Loading what="Drawing the service map" />}
            <div className="row wrap small muted" style={{ justifyContent: 'center', gap: 14 }}>
              <span><span className="dot ok" /> tested</span>
              <span><span className="dot warn" /> not tested</span>
              <span><span className="dot fail" /> failed test</span>
              <span className="dim">3D view · move your mouse</span>
            </div>
          </div>
        </div>
      </section>
          <div className="grid g4 mt">
            <Stat label="Untested for" value={fmtDuration(prod.exposure_seconds)} tone={prod.verdict === 'CONVERGED' ? 'ok' : 'fail'}
              sub={prod.unvalidated_since ? `since ${fmtTime(prod.unvalidated_since)} UTC` : 'every connection is tested'} />
            <Stat label="Next change window" value={data.next_window_in_seconds ? `in ${fmtDuration(data.next_window_in_seconds)}` : '—'}
              sub={data.scheduled_changes[0] ? `${data.scheduled_changes[0].change_request} · ${fmtTime(data.scheduled_changes[0].window_start)}` : ''} />
            <Stat label="Service health" value={prod.all_healthy ? '8 / 8 healthy' : 'degraded'} tone="ok" sub="all pods ready · all apps started" />
            <Stat label="Pipelines" value="all green" tone="ok" sub="Cloud Deploy · Argo CD · Azure DevOps · Jenkins" />
          </div>

      <div className="mt-l">
        <div className="card-title"><span><Cue n={2} on={tips} /> Environments · test status of each connection</span>
          <span className="right small muted">connections: <span className="c-ok">▬ tested</span> · <span className="c-warn">▬ not tested</span> · <span className="c-fail">▬ failed</span></span>
        </div>
        <div className="lanes">
          {data.environments.map((env: any) => (
            <div key={env.environment} className={`lane ${env.verdict}`} onClick={() => go('/composition')}>
              <div className="row between">
                <span className="lane-env">{ENV_LABEL[env.environment]}</span>
                <State s={env.verdict} />
              </div>
              <div className="edge-dots">
                {CONNECTIONS.map((id) => {
                  const unval = env.unvalidated_edges.includes(id)
                  const st = env.first_divergence?.edge_id === id ? 'FAILED' : unval ? 'UNTESTED' : 'VERIFIED'
                  return <span key={id} className={`edge-dot ${st}`} title={`${id.replace('--', ' → ')}: ${st === 'VERIFIED' ? 'tested' : st === 'FAILED' ? 'failed' : 'not tested'}`} />
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

      <Card className="mt-l" title={<>Versions running in production <span className="tag" style={{ marginLeft: 8 }}>PROD</span></>}
        right={<span className="small muted">compared with Stage · {stageVerified}/7 connections tested</span>}>
        <div className="strip">
          {data.system_nobody_tested.map((c: any) => (
            <div key={c.component} className={`chip ${c.matches_validated ? '' : 'bad'}`}>
              <div className="chip-name">{c.component}</div>
              <div className="chip-ver">{c.version}</div>
              <div className="chip-sub">{c.matches_validated ? 'same as tested' : `tested: ${c.validated_version}`}</div>
            </div>
          ))}
        </div>
        <p className="small muted mt">
          {prod.verdict === 'CONVERGED'
            ? 'This exact set of versions has passed testing together.'
            : 'This exact set of versions has never passed a test together. Services running side by side is not the same as being tested together.'}
        </p>
      </Card>

      <div className="grid g-2-1 mt-l">
        {fd ? (
          <section className="fdd rise">
            <div className="fdd-label"><Cue n={3} on={tips} /> ✕ FAILING CONNECTION · PRODUCTION</div>
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
              <span className="pill">untested since {fmtTime(fd.unvalidated_since)} UTC</span>
              {fd.triggering_deployment && <span className="pill">started by {fd.triggering_deployment.tool} · {fd.triggering_deployment.trigger}</span>}
              {fd.probe && <span className="pill">test {fd.probe.result} · {fd.probe.assertions_failed} of {fd.probe.assertions_total} checks failed · {fmtMs(fd.probe.duration_ms)}</span>}
            </div>
            <div className="row mt">
              <button className="btn danger" onClick={() => go('/divergence')}>Open details <Icon name="arrow" size={14} /></button>
              <button className="btn" onClick={() => go('/probe')}>Test output</button>
              <button className="btn" onClick={() => go('/evidence')}>Evidence report</button>
            </div>
          </section>
        ) : (
          <Card title={<><Cue n={3} on={tips} /> Failing connection</>}>
            {prod.untested.length ? (
              <>
                <div className="callout warn">
                  <span>⚠</span>
                  <div>
                    <div className="strong">{prod.untested.length} connection in production has never been tested</div>
                    <div className="small t2">{prod.untested.join(', ')}. Meridian doesn’t guess whether it works. Run a release check to work out its message format and test it in the sandbox.</div>
                  </div>
                </div>
                <button className="btn primary mt" onClick={run} disabled={inv.status === 'running'}><Icon name="play" size={14} /> Run release check</button>
              </>
            ) : (
              <div className="callout ok"><span>✓</span><div>Every connection in production has a passing test.</div></div>
            )}
          </Card>
        )}

        <Card title="Which differences matter" right={<a onClick={() => go('/drift')} style={{ cursor: 'pointer' }}>details →</a>}>
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
              <div className="tiny dim">Stage compared with production.</div>
            </div>
          ) : <Loading />}
        </Card>
      </div>

      <div className="grid g4 mt-l">
        <Stat label="Data sources read" value={data.environments.length * 8} sub="tool outputs across 4 environments" />
        <Stat label="Tests run" value={data.probe_runs} sub="isolated · exact deployed code" />
        <Stat label="Evidence report" value={data.latest_packet_id ? 'ready' : '—'} sub={data.latest_packet_id || 'run a release check'} />
        <Stat label="Last release check" value={inv.result ? fmtMs(inv.result.duration_ms) : '—'} sub={inv.result ? `includes ${inv.result.pace_ms} ms display delay per step` : 'not run yet'} />
      </div>
    </div>
  )
}
