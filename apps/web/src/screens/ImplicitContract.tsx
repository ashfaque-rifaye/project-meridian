import { useState } from 'react'
import { useApi } from '../api'
import type { Go } from '../App'
import ByteMap from '../components/ByteMap'
import { CodeView, linesFrom } from '../components/Code'
import { Card, ErrorBox, Loading, PageHead, State } from '../components/ui'

function fallbackRecord(event: any) {
  const [w, f] = Number(event.amount).toFixed(2).split('.')
  return event.customerId.slice(0, 12).padEnd(12, ' ') + event.currencyCode + `${w}.${f}`.padStart(10, '0')
}

export default function ImplicitContract({ go }: { go: Go }) {
  const { data, error } = useApi('/edges/mq-bridge--legacy-backend?env=prod')
  const [fx, setFx] = useState(0)
  const [showSpec, setShowSpec] = useState(false)
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data) return <div className="page"><Loading what="Reading deployed code and the interface spreadsheet" /></div>
  const c = data.contract
  const ev = data.evaluation
  if (!c) {
    return (
      <div className="page">
        <PageHead eyebrow="What changed · message format" title="This connection is tested" sub="Meridian only works out the message format for connections that have never been tested." />
      </div>
    )
  }
  const run = data.probe_run
  const fixtures = c.probe_spec?.fixtures || []
  const fixture = fixtures[fx]
  const observed = run?.fixtures?.find((f: any) => f.fixture === fixture?.id)
  const record = observed?.record || (fixture ? fallbackRecord(fixture.event) : '')
  const consumerBook = c.consumer_copybooks.find((b: any) => b.length < record.length) || c.consumer_copybooks[0]
  const producerSrc = c.producer_layout.fields.map((f: any) => f.source)
  const consumerSrc = c.consumer_copybooks.flatMap((b: any) => b.fields.map((f: any) => f.source))
  const behaviourSrc = c.consumer_behaviour.map((b: any) => b.source)
  const icd = c.documents.interface_control.sheets

  return (
    <div className="page">
      <PageHead eyebrow="What changed · message format"
        title={<>No written spec for this connection. <span className="grad-text">Rebuilt from code and documents.</span></>}
        sub={<>{ev.producer} {ev.producer_version} @{ev.producer_commit} → {ev.consumer} {ev.consumer_version} @{ev.consumer_commit} · {ev.interface}. This page predicts a mismatch; only the compatibility test decides pass or fail.</>}
        actions={<><State s={c.prediction === 'INCOMPATIBLE' ? 'UNTESTED' : 'VERIFIED'} label={c.prediction === 'INCOMPATIBLE' ? 'PREDICTION: FORMATS DON’T MATCH' : 'PREDICTION: FORMATS MATCH'} /><button className="btn primary" onClick={() => go('/probe')}>Run the compatibility test →</button></>} />

      <Card title={<>The message on {ev.interface.split('·').pop()?.trim() || 'the queue'}, byte by byte</>} right={
        <div className="tabs">{fixtures.map((f: any, i: number) => <button key={f.id} className={`tab ${fx === i ? 'on' : ''}`} onClick={() => setFx(i)}>{f.label}</button>)}</div>}>
        <ByteMap record={record} producer={c.producer_layout.fields} consumer={consumerBook.fields}
          producerLabel={`${ev.producer} ${ev.producer_version} · ${c.producer_layout.name}`}
          consumerLabel={`${ev.consumer} ${ev.consumer_version} · copybook ${consumerBook.name}`}
          queueLabel={`message on ${ev.interface.split('·').pop()?.trim() || 'the queue'}`}
          consumerLength={consumerBook.length} consumerOk={c.prediction === 'COMPATIBLE'} />
        <div className="row wrap mt small">
          <span className="pill">{observed ? 'real message captured by the compatibility test' : 'message predicted from the code (run the test to see the real bytes)'}</span>
          {observed?.assertions?.map((a: any) => (
            <span key={a.field} className={`pill ${a.passed ? 'c-ok' : 'c-fail'}`}>{a.field}: {a.expected} → {a.actual} {a.passed ? '✓' : '✕'}</span>
          ))}
        </div>
      </Card>

      <div className="grid g-2-1 mt-l">
        <Card title="Field by field" right={<span className="small muted">{c.method}</span>}>
          <table className="tbl">
            <thead><tr><th>Field</th><th>Sender writes</th><th>Receiver reads</th><th></th><th>Risk</th></tr></thead>
            <tbody>
              {c.constraints.map((k: any) => (
                <tr key={k.field} className={k.compatible ? '' : 'hl'}>
                  <td className="mono strong">{k.field}</td>
                  <td className="mono small" style={{ width: '24%' }}>{k.producer}<div className="tiny dim" style={{ overflowWrap: 'anywhere' }}>{k.producer_source}</div></td>
                  <td className="mono small" style={{ width: '24%' }}>{k.consumer}<div className="tiny dim" style={{ overflowWrap: 'anywhere' }}>{k.consumer_source}</div></td>
                  <td>{k.compatible ? <span className="c-ok">✓</span> : <span className="c-fail">✕</span>}</td>
                  <td className="small" style={{ width: '34%' }}>{k.risk}<div className="tiny muted">{k.detail}</div></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="callout warn mt small"><span>⚠</span><div>{c.summary}</div></div>
        </Card>
        <Card title="Why no error is raised">
          {c.consumer_behaviour.map((b: any) => (
            <div key={b.id} className="glass mt-s" style={{ padding: 12 }}>
              <div className="row between"><span className="small strong">{b.id}</span><span className={`tag ${b.risk === 'high' ? 'c-fail' : b.risk === 'medium' ? 'c-warn' : ''}`}>{b.risk}</span></div>
              <div className="small t2 mt-s">{b.value}</div>
              <div className="tiny dim mono mt-s">{b.source}</div>
            </div>
          ))}
        </Card>
      </div>

      <div className="grid g3 mt-l">
        <Card title="Sender code · deployed commit">
          <CodeView component={ev.producer} commit={ev.producer_commit} path="src/ledger_record.py" highlight={linesFrom(producerSrc, 'ledger_record.py')} maxHeight={380} />
        </Card>
        <Card title="Receiver code · deployed commit">
          <CodeView component={ev.consumer} commit={ev.consumer_commit} path="copybooks/LEDGREC.cpy" danger={linesFrom(consumerSrc, 'LEDGREC.cpy')} maxHeight={200} />
          <div className="mt-s" />
          <CodeView component={ev.consumer} commit={ev.consumer_commit} path="src/ldgpost.py" highlight={linesFrom(behaviourSrc, 'ldgpost.py')} maxHeight={260} />
        </Card>
        <Card title="Interface spreadsheet (interface-control.xlsx)">
          {Object.entries(icd).map(([sheet, rows]: any) => (
            <div key={sheet} className="mt-s">
              <div className="kicker">{sheet}</div>
              <table className="tbl mt-s">
                <thead><tr><th>Field</th><th>Offset</th><th>Len</th></tr></thead>
                <tbody>{rows.map((r: any) => <tr key={r.name}><td className="mono">{r.name}</td><td className="mono">{r.offset}</td><td className="mono">{r.width}</td></tr>)}</tbody>
              </table>
            </div>
          ))}
          {c.documents.change_request && <div className="callout info mt small"><span>📄</span><div><b>{c.documents.change_request.id}</b> · {c.documents.change_request.dependency}</div></div>}
          {c.documents.release_notes.map((n: any) => <div key={n.source} className="quote small mt-s">{n.text}<div className="tiny dim">{n.source}</div></div>)}
        </Card>
      </div>

      <Card className="mt-l" title="Generated test plan" right={<button className="btn sm" onClick={() => setShowSpec(!showSpec)}>{showSpec ? 'Hide' : 'Show'} JSON</button>}>
        <div className="small t2">{c.probe_spec.assertions.join(' · ')}</div>
        <div className="tiny muted mt-s">Test data: {c.probe_spec.fixture_source} · Sandbox: {c.probe_spec.isolation}</div>
        {showSpec && <pre className="block mt">{JSON.stringify(c.probe_spec, null, 2)}</pre>}
        {c.agent_findings?.length > 0 && (
          <div className="callout hold mt small"><span>🤖</span><div>{c.agent_findings.length} note(s) from IBM Bob: {c.agent_findings.map((f: any) => f.summary).join(' · ')}</div></div>
        )}
      </Card>
    </div>
  )
}
