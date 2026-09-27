import { useState } from 'react'
import { fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import { Card, Drawer, Icon, PageHead, State } from '../components/ui'

const KIND_ICON: Record<string, string> = {
  deployment: '▣', 'deployment-event': '◆', validation: '↯', coexistence: '◐', source: '⟨⟩', document: '📄', probe: '⚗',
}
const KIND_LABEL: Record<string, string> = {
  deployment: 'running version', 'deployment-event': 'deployment', validation: 'test run', coexistence: 'side by side',
  source: 'code', document: 'document', probe: 'compatibility test',
}

export default function EvidencePacket({ go }: { go: Go }) {
  const { data, error } = useApi('/evidence/latest')
  const [item, setItem] = useState<any>(null)
  if (error || !data) {
    return (
      <div className="page">
        <PageHead eyebrow="Test · evidence report" title={<>No evidence report <span className="grad-text">yet</span></>}
          sub="A report is created when a release check finds a failing connection." />
        <button className="btn primary" onClick={() => go('/investigate')}><Icon name="play" size={14} /> Run release check</button>
      </div>
    )
  }
  const download = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${data.packet_id}.json`
    a.click()
  }
  return (
    <div className="page">
      <PageBanner video="evidence-crystal">
        <PageHead eyebrow="Test · evidence report" title={<>Every finding, <span className="grad-text">linked to its source</span></>}
          sub={data.human_summary}
          actions={<><State s={data.review.verdict} lg /><button className="btn" onClick={download}>Download JSON</button></>} />
      </PageBanner>

      <div className="grid g3">
        {[['Sender', data.upstream], ['Receiver', data.downstream]].map(([label, x]: any) => (
          <Card key={label} title={label}>
            <div className="big-num">{x.component} <span className="grad-text">{x.version}</span></div>
            <dl className="kv mt small"><dt>commit</dt><dd className="mono">{x.commit}</dd><dt>deployed</dt><dd>{fmtTime(x.deployed_at)} UTC</dd><dt>source</dt><dd className="mono tiny">{x.artifact}</dd></dl>
          </Card>
        ))}
        <Card title="Report">
          <dl className="kv small">
            <dt>report</dt><dd className="mono tiny">{data.packet_id}</dd>
            <dt>release</dt><dd>{data.release}</dd>
            <dt>environment</dt><dd>{data.environment.toUpperCase()}</dd>
            <dt>flow</dt><dd>{data.business_flow}</dd>
            <dt>connection</dt><dd>{data.connection}</dd>
            <dt>untested since</dt><dd>{fmtTime(data.first_divergence_timestamp)} UTC</dd>
            <dt>started by</dt><dd className="mono tiny">{data.triggering_deployment?.event_id}</dd>
          </dl>
        </Card>
      </div>

      <Card className="mt-l" title={<>Evidence items · {data.evidence_items.length}</>}>
        <div style={{ display: 'grid', gap: 8 }}>
          {data.evidence_items.map((e: any) => (
            <div key={e.id} className="glass row" style={{ padding: '10px 14px', cursor: 'pointer' }} onClick={() => setItem(e)}>
              <span style={{ width: 22, textAlign: 'center' }}>{KIND_ICON[e.kind] || '•'}</span>
              <span className="tag">{KIND_LABEL[e.kind] || e.kind}</span>
              <span className="small" style={{ flex: 1, minWidth: 0 }}>{e.title}</span>
              <span className="tiny muted mono">{e.at ? fmtTime(e.at) : ''}</span>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid g2 mt-l">
        <Card title="Evidence checks" right={<span className="small muted">rule-based, no AI</span>}>
          {data.review.checks.map((ck: any) => (
            <div key={ck.id} className="glass" style={{ padding: 10, marginBottom: 8 }}>
              <div className="row"><span className={ck.passed ? 'c-ok' : 'c-fail'}>{ck.passed ? '✓' : '✕'}</span><span className="strong small">{ck.label}</span></div>
              <div className="tiny muted mono">{ck.detail}</div>
            </div>
          ))}
        </Card>
        <Card title="How the deployments happened">
          {data.promotion_pattern.map((s: string) => <p key={s} className="small t2" style={{ marginBottom: 8 }}>{s}</p>)}
          <div className="sep-grad" />
          <div className="small muted">Based on test results and deployment records. It shows where the problem is, not why the team deployed it.</div>
        </Card>
      </div>

      <Drawer open={!!item} onClose={() => setItem(null)} title={item?.title}>
        {item && (
          <dl className="kv small">
            <dt>type</dt><dd>{KIND_LABEL[item.kind] || item.kind}</dd>
            <dt>evidence id</dt><dd className="mono">{item.id}</dd>
            <dt>source</dt><dd className="mono">{item.source}</dd>
            <dt>time</dt><dd>{item.at ? fmtTime(item.at) + ' UTC' : '—'}</dd>
          </dl>
        )}
      </Drawer>
    </div>
  )
}
