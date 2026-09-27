import { useState } from 'react'
import { useApi } from '../api'
import type { Go } from '../App'
import { Card, ErrorBox, Loading, PageHead, State } from '../components/ui'

const CLASS_LABEL: Record<string, string> = {
  irrelevant: 'not on this flow',
  relevant: 'operational · flow component',
  'contract-affecting': 'version change · boundaries still validated',
  'release-convergence-risk': 'creates an unvalidated pair',
}

export default function DriftRelevance({ go }: { go: Go }) {
  const { data, error } = useApi('/drift')
  const [filter, setFilter] = useState<string>('all')
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data) return <div className="page"><Loading what="Diffing STAGE and PROD" /></div>

  const stageMap: Record<string, string[]> = {
    raw: ['irrelevant', 'relevant', 'contract-affecting', 'release-convergence-risk'],
    flow: ['relevant', 'contract-affecting', 'release-convergence-risk'],
    boundary: ['contract-affecting', 'release-convergence-risk'],
    unvalidated: ['release-convergence-risk'],
    failed: ['release-convergence-risk'],
  }
  const diffs = data.differences.filter((d: any) => filter === 'all' || stageMap[filter]?.includes(d.classification))
  const top = data.funnel[0].count

  return (
    <div className="page">
      <PageHead eyebrow="Understand · drift relevance" title={<>{top} differences. <span className="grad-text">One that matters.</span></>}
        sub="A naive diff treats every difference between Stage and Prod as equally important. Meridian keeps only what changes a dependency boundary without validation evidence." />

      <div className="grid g-1-2">
        <Card title="Meridian narrows it down">
          <div className="funnel">
            {data.funnel.map((f: any, i: number) => (
              <div key={f.stage} className={`funnel-step ${i === data.funnel.length - 1 ? 'last' : ''} ${filter === f.stage ? 'sel' : ''}`}
                onClick={() => setFilter(filter === f.stage ? 'all' : f.stage)}>
                <div className={`funnel-n ${i === data.funnel.length - 1 && f.count ? 'c-fail' : ''}`}>{f.count}</div>
                <div>
                  <div className="funnel-bar">
                    <div className="funnel-fill" style={{ width: `${Math.max(4, (f.count / top) * 100)}%` }} />
                    <div className="funnel-label">{f.label}</div>
                  </div>
                  <div className="tiny muted" style={{ marginTop: 3 }}>{f.detail}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="sep-grad" />
          {data.boundary_changes.map((b: any) => (
            <div key={b.edge_id} className="glass mt-s" style={{ padding: 12 }}>
              <div className="row between"><span className="strong">{b.label}</span><State s={b.target_evidence === 'VERIFIED' ? 'VERIFIED' : b.probe === 'FAIL' ? 'FAILED' : 'UNTESTED'} /></div>
              <div className="small mono muted">STAGE {b.reference_pair.join(' → ')} · PROD {b.target_pair.join(' → ')}</div>
              <div className="tiny dim">strongest evidence for the PROD pair: {b.target_evidence}</div>
            </div>
          ))}
          {data.boundary_changes.some((b: any) => b.probe === 'FAIL') && (
            <button className="btn danger mt" onClick={() => go('/divergence')}>Open the first demonstrated divergence</button>
          )}
          <div className="tiny dim mt">{data.note}</div>
        </Card>

        <Card title={<>Naive environment diff · {diffs.length} shown</>} right={
          <div className="tabs">
            {['all', 'flow', 'boundary', 'unvalidated'].map((f) => <button key={f} className={`tab ${filter === f ? 'on' : ''}`} onClick={() => setFilter(f)}>{f}</button>)}
          </div>}>
          <div style={{ maxHeight: 640, overflow: 'auto' }}>
            <table className="tbl">
              <thead><tr><th>Workload</th><th>Attribute</th><th>STAGE</th><th>PROD</th><th>Meridian</th></tr></thead>
              <tbody>
                {diffs.map((d: any, i: number) => (
                  <tr key={i} className={d.classification === 'release-convergence-risk' ? 'hl' : ''} style={{ opacity: d.classification === 'irrelevant' ? 0.55 : 1 }}>
                    <td className="small">{d.name}<div className="tiny dim mono">{d.adapter}</div></td>
                    <td className="mono small" style={{ maxWidth: 260, overflowWrap: 'anywhere' }}>{d.attribute}</td>
                    <td className="mono small" style={{ maxWidth: 180, overflowWrap: 'anywhere' }}>{String(d.reference ?? '—')}</td>
                    <td className="mono small" style={{ maxWidth: 180, overflowWrap: 'anywhere' }}>{String(d.target ?? '—')}</td>
                    <td className="tiny" style={{ color: d.classification === 'release-convergence-risk' ? 'var(--fail)' : d.classification === 'irrelevant' ? 'var(--dim)' : 'var(--text-2)' }}>{CLASS_LABEL[d.classification]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
