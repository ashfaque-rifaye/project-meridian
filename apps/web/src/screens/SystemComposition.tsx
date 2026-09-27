import { ENV_LABEL, fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import Scene3D from '../components/Scene3D'
import { Card, ErrorBox, Loading, PageHead, Platform, State } from '../components/ui'

export default function SystemComposition({ go }: { go: Go }) {
  const { data, error } = useApi('/matrix')
  const { data: overview } = useApi('/overview')
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data || !overview) return <div className="page"><Loading what="Reconstructing four environments" /></div>
  const envs: string[] = data.environments
  const stage = overview.environments.find((e: any) => e.environment === 'stage').composition

  return (
    <div className="page">
      <PageBanner video="env-layers">
        <PageHead eyebrow="Reconstruct · system composition" title={<>Observed together is <span className="grad-text">not validated together</span></>}
          sub="What is actually running in each environment, read-only from Kubernetes (EKS · AKS · GKE · OpenShift), WebSphere Liberty, Flyway and Schema Registry. Compared with the composition Stage validated." />
      </PageBanner>

      <div className="scene-frame">
        <div className="scene-caption">
          <div className="kicker">promotion path in 3D</div>
          <div className="small t2">Each glass layer is an environment. Red nodes run a version that differs from the validated Stage composition.</div>
        </div>
        <Scene3D mode="stack" height={430} components={data.components.map((r: any) => ({ id: r.component.id, label: r.component.id }))}
          envs={overview.environments} reference={stage} />
        <div className="scene-legend">
          {overview.environments.map((e: any) => <span key={e.environment}>{ENV_LABEL[e.environment]} <State s={e.verdict} /></span>)}
        </div>
      </div>

      <Card className="mt-l flush" title={<span style={{ padding: '14px 16px 0', display: 'block' }}>Component × environment</span>}>
        <div style={{ overflowX: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>Component</th><th>Runtime</th>{envs.map((e) => <th key={e}>{ENV_LABEL[e]}</th>)}<th>R-26.9 target</th></tr></thead>
            <tbody>
              {data.components.map((row: any) => (
                <tr key={row.component.id}>
                  <td><div className="strong">{row.component.id}</div><div className="tiny muted">{row.component.team}</div></td>
                  <td><Platform p={row.component.platform} /><div className="tiny muted mt-s">{row.component.cloud}</div></td>
                  {envs.map((e) => {
                    const c = row.cells[e]
                    const bad = e === 'prod' && c?.differs_from_validated
                    return (
                      <td key={e} style={bad ? { background: 'var(--fail-soft)' } : undefined} title={c ? `${c.location}\n${c.health}\ndeployed ${fmtTime(c.deployed_at)}\nevidence ${c.evidence_id}` : ''}>
                        <div className="mono" style={{ fontSize: 16, color: bad ? 'var(--fail)' : undefined }}>{c?.version ?? '—'}</div>
                        <div className="tiny dim mono">@{c?.commit} · {fmtTime(c?.deployed_at)}</div>
                        {bad && <div className="tiny c-fail">≠ validated {stage[row.component.id]}</div>}
                      </td>
                    )
                  })}
                  <td className="mono">{row.cells.prod?.release_target}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="mt-l flush" title={<span style={{ padding: '14px 16px 0', display: 'block' }}>Dependency boundary × environment · validation state of the exact running pair</span>}>
        <div style={{ overflowX: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>Boundary</th><th>Contract</th>{envs.map((e) => <th key={e}>{ENV_LABEL[e]}</th>)}</tr></thead>
            <tbody>
              {data.edges.map((row: any) => (
                <tr key={row.edge.id} className="clickable" onClick={() => go('/flow')}>
                  <td><div className="strong">{row.edge.producer} → {row.edge.consumer}</div><div className="tiny muted">{row.edge.interface}</div></td>
                  <td><span className={`tag ${row.edge.contract.formal ? '' : 'c-warn'}`}>{row.edge.contract.formal ? 'formal' : 'implicit'}</span><div className="tiny muted mt-s">{row.edge.contract.kind}</div></td>
                  {envs.map((e) => {
                    const c = row.cells[e]
                    return (
                      <td key={e} title={c.reason}>
                        <State s={c.state} />
                        <div className="tiny dim mono mt-s">{c.producer_version} → {c.consumer_version}</div>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
