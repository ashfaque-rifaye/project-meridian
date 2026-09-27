import { useApi } from '../api'
import type { Go } from '../App'
import { AmbientVideo } from '../components/Media'
import Scene3D from '../components/Scene3D'
import { Icon } from '../components/ui'

const STAGES = [
  { n: '01', id: 'WHAT’S RUNNING', q: 'Which versions are live right now?', route: '/composition',
    a: 'Meridian reads the real versions from Kubernetes, WebSphere Liberty, Flyway and Schema Registry. It reports what is actually deployed, not what the pipeline intended.' },
  { n: '02', id: 'WHAT CHANGED', q: 'Was this exact set of versions ever tested?', route: '/flow',
    a: 'Meridian keeps a record of which version pairs were really tested, and separates them from versions that only ran side by side. It then works out message formats nobody wrote down.' },
  { n: '03', id: 'PREVIEW', q: 'What would this deployment change?', route: '/rehearse',
    a: 'Preview any deployment before it happens. Meridian combines the current environment with the proposed change and checks the result. Nothing is deployed.' },
  { n: '04', id: 'TEST', q: 'Does the connection actually work?', route: '/probe',
    a: 'Both services run at their exact deployed code in an isolated sandbox. The test decides pass or fail. The AI never makes that call.' },
  { n: '05', id: 'FIX', q: 'What is the safest fix?', route: '/remediate',
    a: 'Each fix option is previewed and tested again. IBM Bob drafts the code on a separate branch, and a person makes the release decision.' },
]

const PAINS = [
  { t: 'Teams deploy on different schedules',
    d: 'Cloud services deploy as soon as a pull request merges. The older backend waits for Sunday’s change window. For a day and a half, production runs a mix of versions nobody planned.' },
  { t: 'Green doesn’t mean correct',
    d: 'The pipeline passed, every pod is ready, the queue accepted the message and the database saved it. None of those checks confirm the backend saved the right customer.' },
  { t: 'The riskiest connections have no spec',
    d: 'REST APIs have OpenAPI and Kafka has a schema registry. The fixed-width record between mq-bridge and the backend is only described in a COBOL copybook and a spreadsheet.' },
]

const COMPARE = [
  ['Contract testing (e.g. Pact can-i-deploy)', 'Works when every team writes and maintains contract tests. Rarely covers copybooks, database schemas or older message queues.'],
  ['Release tooling (e.g. snapshots, Kargo)', 'Only guarantees tested sets when the whole release ships as one unit, which independent teams rarely do.'],
  ['Drift detection', 'Lists every difference between environments without saying which one matters.'],
  ['Monitoring and alerting', 'Tells you something is unhealthy after it breaks. Silently wrong data never triggers an alert.'],
]

export default function Home({ go }: { go: Go }) {
  const { data: flow } = useApi('/flow')
  const { data: prod } = useApi('/environments/prod')
  const { data: overview } = useApi('/overview')
  const fd = overview?.prod?.first_divergence

  return (
    <div className="landing">
      {/* ---------------------------------------------------------------- hero */}
      <section className="l-hero">
        <div className="l-hero-media"><AmbientVideo name="hero-convergence" /></div>
        <div className="l-hero-inner">
          <div className="l-kicker"><span className="dot accent" /> Version checks for multi-team releases · built with IBM Bob</div>
          <h1 className="l-title">Every component passed.<br /><span className="grad-text">The system didn’t.</span></h1>
          <p className="l-lede">
            Meridian answers a question your pipelines can’t: were the versions running in production ever tested together?
            If not, Meridian finds the connection that changed, works out the message format between the two services,
            and tests it in a sandbox before your customers notice.
          </p>
          <div className="row wrap" style={{ gap: 12, marginTop: 26 }}>
            <button className="btn primary lg" onClick={() => go('/command')}><Icon name="home" /> Open dashboard</button>
            <button className="btn lg" onClick={() => go('/investigate')}><Icon name="play" size={14} /> Run a release check</button>
            <a className="btn lg ghost" href="/presentation.html" target="_blank" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 8, borderColor: 'var(--accent)', color: 'var(--accent)' }}><Icon name="story" /> Executive Deck (6-Slider) ↗</a>
            <button className="btn lg ghost" onClick={() => document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' })}>How it works ↓</button>
          </div>
          <div className="l-facts">
            <div><b>8</b><span>services in one checkout flow</span></div>
            <div><b>4 + 1</b><span>clouds and an on-prem data centre</span></div>
            <div><b>149 → 1</b><span>differences narrowed to the one that matters</span></div>
            <div><b>0</b><span>changes made to any environment</span></div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- problem */}
      <section className="l-section">
        <div className="l-head">
          <div className="eyebrow">The problem</div>
          <h2 className="l-h2">Teams don’t ship one release any more.<br />Production is a mix of many.</h2>
          <p className="l-p">
            A single checkout in a large retailer or bank passes through services on three clouds, a Kafka topic, an IBM MQ queue,
            a WebSphere application and a Db2 database. Each piece has its own team and its own pipeline. Every team tests its
            own change. Nobody tests the exact mix that ends up running together on a Friday afternoon. When that mix is wrong
            it usually doesn’t crash. It quietly saves bad data.
          </p>
        </div>
        <div className="grid g3">
          {PAINS.map((p, i) => (
            <div key={p.t} className="glass l-card">
              <div className="l-num">0{i + 1}</div>
              <div className="l-card-t">{p.t}</div>
              <p className="l-card-d">{p.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------------------------------------------------------- story */}
      <section className="l-section">
        <div className="grid g2" style={{ alignItems: 'center', gap: 34 }}>
          <div>
            <div className="eyebrow">Example incident</div>
            <h2 className="l-h2">The release passed Stage on Thursday. On Friday it met an older backend.</h2>
            <div className="l-timeline">
              <div><span className="dot ok" /><span><b>Thu 14:30</b> Stage tests release R-26.9 end to end. Every connection passes.</span></div>
              <div><span className="dot fail" /><span><b>Fri 11:42</b> An automatic Argo CD sync deploys mq-bridge 3.1 to production. It now sends a 25-byte record with a 12-character customer ID.</span></div>
              <div><span className="dot warn" /><span><b>Waiting</b> legacy-backend 7.0, the version that can read that record, is booked for Sunday’s change window.</span></div>
              <div><span className="dot fail" /><span><b>Meanwhile</b> HTTP 200, message accepted, database saved. Yet customer CUST12345678 is saved as CUST123456, and $149.50 is saved as $780,000,149.00.</span></div>
            </div>
            <p className="l-p" style={{ marginTop: 14 }}>
              No alert fires and nothing is down. Meridian catches it by asking a different question: has this exact pair of
              versions ever been tested together? It hasn’t, so Meridian runs that test itself, safely, and shows you the result.
            </p>
            {fd ? (
              <button className="btn danger mt" onClick={() => go('/divergence')}>See the failing connection →</button>
            ) : (
              <button className="btn primary mt" onClick={() => go('/investigate')}>Run the release check →</button>
            )}
          </div>
          <div className="scene-frame" style={{ height: 420 }}>
            {flow && prod && (
              <Scene3D mode="flow" height={420} components={flow.components}
                edges={prod.edges.map((e: any) => ({ producer: e.producer, consumer: e.consumer, state: e.state }))}
                composition={prod.composition} />
            )}
            <div className="scene-legend"><span>live view of production · checkout flow</span></div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- how */}
      <section className="l-section" id="how">
        <div className="l-head">
          <div className="eyebrow">How it works</div>
          <h2 className="l-h2">Five questions, each answered with evidence.</h2>
          <p className="l-p">Rules and real tests make the decisions. AI agents do the reading. Every answer links back to the file, deployment, test run or document it came from.</p>
        </div>
        <div className="l-stages">
          {STAGES.map((s) => (
            <button key={s.id} className="glass l-stage" onClick={() => go(s.route)}>
              <div className="row between"><span className="l-num">{s.n}</span><span className="kicker">{s.id}</span></div>
              <div className="l-card-t">{s.q}</div>
              <p className="l-card-d">{s.a}</p>
              <span className="small c-accent">Open →</span>
            </button>
          ))}
        </div>
      </section>

      {/* ---------------------------------------------------------------- difference */}
      <section className="l-section">
        <div className="grid g2" style={{ gap: 34 }}>
          <div>
            <div className="eyebrow">What’s different</div>
            <h2 className="l-h2">Tested, not guessed.</h2>
            <p className="l-p">
              Other tools cover part of this. Meridian puts the pieces together: the real versions in each environment, a record
              of which version pairs were actually tested, message formats rebuilt from code and documents, and real tests for
              the connections nobody tested.
            </p>
            <ul className="l-list">
              <li>Tests run the code at the <b>exact deployed commits</b>, with the same test data Stage used.</li>
              <li><b>Ran side by side</b>, <b>smoke tested</b> and <b>fully tested</b> are kept separate. A smoke test that got a reply is not a full test.</li>
              <li>The result names the <b>failing connection</b>, backed by test results, not a guess.</li>
              <li><b>Read-only.</b> A safety hook blocks every command that would change a cloud or cluster.</li>
            </ul>
          </div>
          <div className="glass" style={{ padding: 0 }}>
            <table className="tbl">
              <thead><tr><th>Existing approach</th><th>Where it stops</th></tr></thead>
              <tbody>
                {COMPARE.map(([a, b]) => <tr key={a}><td className="strong small">{a}</td><td className="small t2">{b}</td></tr>)}
                <tr><td className="strong small grad-text">Meridian</td><td className="small">Finds the untested set of versions, works out the message format and tests the outcome, without asking any team to write new tests first.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- bob */}
      <section className="l-section">
        <div className="l-bob">
          <div className="l-bob-media"><AmbientVideo name="bob-core" /></div>
          <div className="l-bob-inner">
            <div className="eyebrow">Built inside IBM Bob 2.0</div>
            <h2 className="l-h2">Bob does the reading. The tests make the call.</h2>
            <p className="l-p">
              Meridian ships as an IBM Bob plugin. Bob’s agents work in parallel, one per environment and one per untested
              connection. They read the release notes, change request and interface spreadsheet, look at the code at the deployed
              commits, and call Meridian’s tools. When a test fails, Bob drafts a fix on a separate branch and Meridian tests it again.
            </p>
            <div className="l-bob-grid">
              <div><b>4</b><span>Bob modes: investigate, test, fix, demo</span></div>
              <div><b>5</b><span>skills that describe each step</span></div>
              <div><b>22</b><span>tools, all read-only or sandboxed</span></div>
              <div><b>2</b><span>hooks: a safety check and an activity log</span></div>
            </div>
            <div className="row wrap mt">
              <button className="btn primary" onClick={() => go('/bob')}>See the Bob setup →</button>
              <button className="btn" onClick={() => go('/learn')}>Watch the video guides</button>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- architecture */}
      <section className="l-section">
        <div className="l-head">
          <div className="eyebrow">Architecture</div>
          <h2 className="l-h2">A few simple parts.</h2>
        </div>
        <div className="l-arch">
          <div className="glass l-arch-col">
            <div className="kicker">IBM Bob 2.0</div>
            <div className="l-chip">Release reader</div>
            <div className="l-chip">Environment readers × 4</div>
            <div className="l-chip">Message format finder</div>
            <div className="l-chip">Evidence reviewer</div>
            <div className="l-chip">Fix author</div>
          </div>
          <div className="l-arrow">⟷<span>MCP · stdio</span></div>
          <div className="glass l-arch-col">
            <div className="kicker">Meridian engine (rule-based)</div>
            <div className="l-chip">Read-only connectors</div>
            <div className="l-chip">Test history</div>
            <div className="l-chip">Message format discovery</div>
            <div className="l-chip">Test sandbox · exact commits</div>
            <div className="l-chip">Failing connection · evidence report</div>
            <div className="l-chip">Deployment preview · fix options</div>
          </div>
          <div className="l-arrow">⟵<span>read-only connectors</span></div>
          <div className="glass l-arch-col">
            <div className="kicker">Sources (read-only)</div>
            <div className="l-chip">EKS · AKS · GKE · OpenShift</div>
            <div className="l-chip">WebSphere Liberty · Db2 Flyway</div>
            <div className="l-chip">Kafka Schema Registry · IBM MQ</div>
            <div className="l-chip">Git at deployed commits</div>
            <div className="l-chip">Change request PDF · release notes DOCX · interface XLSX</div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- cta */}
      <section className="l-section">
        <div className="l-cta">
          <h2 className="l-h2">Health checks tell you your services are up.<br /><span className="grad-text">Meridian tells you whether they were tested together.</span></h2>
          <div className="row wrap" style={{ justifyContent: 'center', gap: 12, marginTop: 22 }}>
            <button className="btn primary lg" onClick={() => go('/command')}>Open dashboard</button>
            <button className="btn lg" onClick={() => go('/journey')}>Start with the deployment timeline</button>
          </div>
        </div>
        <div className="l-foot">
          Meridian only reads from your environments. Tests run in an isolated sandbox. Background video made with Google Flow (Veo 3.1).
        </div>
      </section>
    </div>
  )
}
