import { useState } from 'react'
import { fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import { Card, Drawer, Icon, PageHead, State } from '../components/ui'

const KIND_ICON: Record<string, string> = {
  deployment: '▣', 'deployment-event': '◆', validation: '↯', coexistence: '◐', source: '⟨⟩', document: '📄', probe: '⚗',
}

export default function EvidencePacket({ go }: { go: Go }) {
  const { data, error } = useApi('/evidence/latest')
  const [item, setItem] = useState<any>(null)
  if (error || !data) {
    return (
      <div className="page">
        <PageHead eyebrow="Prove · evidence packet" title={<>No evidence packet <span className="grad-text">yet</span></>}
          sub="An evidence packet is produced when an investigation demonstrates a divergence." />
        <button className="btn primary" onClick={() => go('/investigate')}><Icon name="play" size={14} /> Run investigation</button>
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
        <PageHead eyebrow="Prove · evidence packet" title={<>Every claim, <span className="grad-text">traced to a source</span></>}
          sub={data.human_summary}
          actions={<><State s={data.review.verdict} lg /><button className="btn" onClick={download}>Download JSON</button></>} />
      </PageBanner>

      <div className="grid g3">
        {[['Upstream', data.upstream], ['Downstream', data.downstream]].map(([label, x]: any) => (
          <Card key={label} title={label}>
            <div className="big-num">{x.component} <span className="grad-text">{x.version}</span></div>
            <dl className="kv mt small"><dt>commit</dt><dd className="mono">{x.commit}</dd><dt>deployed</dt><dd>{fmtTime(x.deployed_at)} UTC</dd><dt>source</dt><dd className="mono tiny">{x.artifact}</dd></dl>
          </Card>
        ))}
        <Card title="Packet">
          <dl className="kv small">
            <dt>packet</dt><dd className="mono tiny">{data.packet_id}</dd>
            <dt>release</dt><dd>{data.release}</dd>
            <dt>environment</dt><dd>{data.environment.toUpperCase()}</dd>
            <dt>flow</dt><dd>{data.business_flow}</dd>
            <dt>connection</dt><dd>{data.connection}</dd>
            <dt>divergence at</dt><dd>{fmtTime(data.first_divergence_timestamp)} UTC</dd>
            <dt>trigger</dt><dd className="mono tiny">{data.triggering_deployment?.event_id}</dd>
          </dl>
        </Card>
      </div>

      <Card className="mt-l" title={<>Evidence items · {data.evidence_items.length}</>}>
        <div style={{ display: 'grid', gap: 8 }}>
          {data.evidence_items.map((e: any) => (
            <div key={e.id} className="glass row" style={{ padding: '10px 14px', cursor: 'pointer' }} onClick={() => setItem(e)}>
              <span style={{ width: 22, textAlign: 'center' }}>{KIND_ICON[e.kind] || '•'}</span>
              <span className="tag">{e.kind}</span>
              <span className="small" style={{ flex: 1, minWidth: 0 }}>{e.title}</span>
              <span className="tiny muted mono">{e.at ? fmtTime(e.at) : ''}</span>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid g2 mt-l">
        <Card title="Deterministic evidence review" right={<span className="small muted">{data.review.reviewer}</span>}>
          {data.review.checks.map((ck: any) => (
            <div key={ck.id} className="glass" style={{ padding: 10, marginBottom: 8 }}>
              <div className="row"><span className={ck.passed ? 'c-ok' : 'c-fail'}>{ck.passed ? '✓' : '✕'}</span><span className="strong small">{ck.label}</span></div>
              <div className="tiny muted mono">{ck.detail}</div>
            </div>
          ))}
        </Card>
        <Card title="Promotion pattern">
          {data.promotion_pattern.map((s: string) => <p key={s} className="small t2" style={{ marginBottom: 8 }}>{s}</p>)}
          <div className="sep-grad" />
          <div className="small muted">{data.claim_type}</div>
        </Card>
      </div>

      <Drawer open={!!item} onClose={() => setItem(null)} title={item?.title}>
        {item && (
          <dl className="kv small">
            <dt>kind</dt><dd>{item.kind}</dd>
            <dt>evidence id</dt><dd className="mono">{item.id}</dd>
            <dt>source</dt><dd className="mono">{item.source}</dd>
            <dt>time</dt><dd>{item.at ? fmtTime(item.at) + ' UTC' : '—'}</dd>
          </dl>
        )}
      </Drawer>
    </div>
  )
}
