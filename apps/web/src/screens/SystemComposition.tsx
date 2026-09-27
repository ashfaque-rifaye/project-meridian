import { ENV_LABEL, fmtTime, useApi } from '../api'
import type { Go } from '../App'
import { PageBanner } from '../components/Media'
import Scene3D from '../components/Scene3D'
import { Card, ErrorBox, Loading, PageHead, Platform, State } from '../components/ui'

export default function SystemComposition({ go }: { go: Go }) {
  const { data, error } = useApi('/matrix')
  const { data: overview } = useApi('/overview')
  if (error) return <div className="page"><ErrorBox error={error} /></div>
  if (!data || !overview) return <div className="page"><Loading what="Reading four environments" /></div>
  const envs: string[] = data.environments
  const stage = overview.environments.find((e: any) => e.environment === 'stage').composition

  return (
    <div className="page">
      <PageBanner video="env-layers">
        <PageHead eyebrow="What’s running · versions by environment" title={<>Running side by side is <span className="grad-text">not the same as tested together</span></>}
          sub="The versions actually deployed in each environment, read from Kubernetes (EKS · AKS · GKE · OpenShift), WebSphere Liberty, Flyway and Schema Registry, compared with the versions Stage tested." />
      </PageBanner>

      <div className="scene-frame">
        <div className="scene-caption">
          <div className="kicker">environments in 3D</div>
          <div className="small t2">Each layer is an environment. Red services run a different version from the one Stage tested.</div>
        </div>
        <Scene3D mode="stack" height={430} components={data.components.map((r: any) => ({ id: r.component.id, label: r.component.id }))}
          envs={overview.environments} reference={stage} />
        <div className="scene-legend">
          {overview.environments.map((e: any) => <span key={e.environment}>{ENV_LABEL[e.environment]} <State s={e.verdict} /></span>)}
        </div>
      </div>

      <Card className="mt-l flush" title={<span style={{ padding: '14px 16px 0', display: 'block' }}>Service versions in each environment</span>}>
        <div style={{ overflowX: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>Service</th><th>Runs on</th>{envs.map((e) => <th key={e}>{ENV_LABEL[e]}</th>)}<th>R-26.9 target</th></tr></thead>
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
                        {bad && <div className="tiny c-fail">Stage tested {stage[row.component.id]}</div>}
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

      <Card className="mt-l flush" title={<span style={{ padding: '14px 16px 0', display: 'block' }}>Connections in each environment · has this exact version pair been tested?</span>}>
        <div style={{ overflowX: 'auto' }}>
          <table className="tbl">
            <thead><tr><th>Connection</th><th>Spec</th>{envs.map((e) => <th key={e}>{ENV_LABEL[e]}</th>)}</tr></thead>
            <tbody>
              {data.edges.map((row: any) => (
                <tr key={row.edge.id} className="clickable" onClick={() => go('/flow')}>
                  <td><div className="strong">{row.edge.producer} → {row.edge.consumer}</div><div className="tiny muted">{row.edge.interface}</div></td>
                  <td><span className={`tag ${row.edge.contract.formal ? '' : 'c-warn'}`}>{row.edge.contract.formal ? 'documented' : 'no written spec'}</span><div className="tiny muted mt-s">{row.edge.contract.kind}</div></td>
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
