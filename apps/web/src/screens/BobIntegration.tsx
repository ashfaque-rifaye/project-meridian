import { useState } from 'react'
import { fmtTime, post, useApi } from '../api'
import type { Go } from '../App'
import { AmbientVideo, PageBanner } from '../components/Media'
import { Card, Loading, PageHead, State } from '../components/ui'

const EXAMPLES = [
  'kubectl --context ocp-prod-dc2 -n integration rollout undo deploy/mq-bridge',
  'helm --kube-context eks-prod-use1 upgrade order-api ./chart',
  'az webapp deploy --name payments-prod --src-path app.zip',
  'kubectl --context ocp-prod-dc2 get deployments -A -o json',
  'python mcp-server/meridian_mcp.py --list',
]

export default function BobIntegration({ go }: { go: Go }) {
  const { data } = useApi('/bob')
  const { data: activity, reload } = useApi('/bob/activity')
  const [cmd, setCmd] = useState(EXAMPLES[0])
  const [res, setRes] = useState<any>(null)
  const test = async (c = cmd) => {
    setCmd(c)
    setRes(await post('/bob/hook-test', { command: c }))
    reload()
  }
  if (!data) return <div className="page"><Loading what="Reading .bob/" /></div>

  return (
    <div className="page">
      <PageBanner video="bob-core">
        <PageHead eyebrow="IBM Bob 2.0 integration" title={<>Meridian runs <span className="grad-text">inside Bob</span></>}
          sub="A project-local plugin: AGENTS.md context, four custom modes, five skills, a 22-tool MCP server and lifecycle hooks that make the investigator physically unable to touch an environment." />
      </PageBanner>

      <div className="grid g4">
        {[['Custom modes', data.modes.length], ['Skills', data.skills.length], ['MCP tools', data.tools.length], ['Hooks', Object.keys(data.hooks).length]].map(([k, v]) => (
          <Card key={k as string}><div className="kicker">{k}</div><div className="big-num grad-text mt-s">{v}</div></Card>
        ))}
      </div>

      <div className="grid g2 mt-l">
        <Card title="Live guardrail · PreToolUse hook" className="card-video">
          <AmbientVideo name="shield-guard" className="card-bg" />
          <p className="small t2">Runs the real <span className="mono">.bob/hooks/guard.py</span> exactly as Bob does before <span className="mono">execute_command</span>. Exit code 2 blocks the tool call.</p>
          <div className="row mt">
            <input className="input" value={cmd} onChange={(e) => setCmd(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && test()} />
            <button className="btn primary" onClick={() => test()}>Test</button>
          </div>
          <div className="row wrap mt-s">{EXAMPLES.map((e) => <button key={e} className="btn sm ghost mono" onClick={() => test(e)}>{e.length > 46 ? e.slice(0, 46) + '…' : e}</button>)}</div>
          {res && (
            <div className={`callout mt rise ${res.blocked ? 'fail' : 'ok'}`}>
              <span style={{ fontSize: 18 }}>{res.blocked ? '⛔' : '✓'}</span>
              <div>
                <State s={res.blocked ? 'BLOCKED' : 'ALLOWED'} label={res.blocked ? `BLOCKED · exit ${res.exit_code}` : `ALLOWED · exit ${res.exit_code}`} />
                {res.stderr && <div className="small mono mt-s">{res.stderr}</div>}
                <div className="tiny muted mt-s">{res.hook}</div>
              </div>
            </div>
          )}
        </Card>
        <Card title="Custom modes · .bob/custom_modes.yaml">
          {data.modes.map((m: any) => (
            <div key={m.slug} className="glass" style={{ padding: 12, marginBottom: 8 }}>
              <div className="row between"><span className="strong">{m.name}</span><span className="tag">{m.slug}</span></div>
              <div className="row wrap mt-s">{m.groups.map((g: string) => <span key={g} className="pill">{g}</span>)}</div>
              <div className="tiny muted mt-s">{m.when}</div>
            </div>
          ))}
        </Card>
      </div>

      <div className="grid g2 mt-l">
        <Card title="Skills · .bob/skills/*/SKILL.md">
          {data.skills.map((s: any) => (
            <div key={s.name} style={{ marginBottom: 12 }}>
              <div className="row"><span className="strong mono">{s.name}</span><span className="tiny dim">{s.files.join(' · ')}</span></div>
              <div className="small muted">{s.description}</div>
            </div>
          ))}
        </Card>
        <Card title="MCP server · meridian (stdio)" right={<span className="small muted mono">{data.mcp?.mcpServers?.meridian?.args?.[0]}</span>}>
          <div style={{ maxHeight: 420, overflow: 'auto' }}>
            <table className="tbl">
              <thead><tr><th>Tool</th><th>Access</th></tr></thead>
              <tbody>{data.tools.map((t: any) => (
                <tr key={t.name}><td><div className="mono small strong">{t.name}</div><div className="tiny muted">{t.description}</div></td>
                  <td><span className={`tag ${t.access === 'read-only' ? 'c-ok' : t.access.includes('sandbox') ? 'c-warn' : ''}`}>{t.access}</span></td></tr>
              ))}</tbody>
            </table>
          </div>
        </Card>
      </div>

      <Card className="mt-l" title="Bob activity · hook log and agent findings" right={<button className="btn sm" onClick={reload}>Refresh</button>}>
        {!activity?.hook_log?.length && !activity?.agent_findings?.length ? (
          <div className="small muted">No Bob activity recorded yet. Run the investigation from Bob in the <span className="mono">meridian-investigator</span> mode; every tool call is logged here by the PostToolUse hook.</div>
        ) : (
          <div style={{ maxHeight: 360, overflow: 'auto' }}>
            {activity.agent_findings.map((f: any) => (
              <div key={f.finding_id} className="callout hold small" style={{ marginBottom: 8 }}><span>🤖</span><div><b>{f.agent}</b> · {f.kind} · {f.summary}<div className="tiny muted">{f.recorded_at}</div></div></div>
            ))}
            <table className="tbl"><tbody>{activity.hook_log.map((h: any, i: number) => (
              <tr key={i}><td className="mono tiny">{fmtTime(h.at, { seconds: true })}</td><td className="tiny">{h.hook}</td>
                <td>{h.decision ? <State s={h.decision} /> : <span className="tag">{h.tool}</span>}</td>
                <td className="mono tiny ellipsis" style={{ maxWidth: 520 }}>{h.command || JSON.stringify(h.summary)}</td></tr>
            ))}</tbody></table>
          </div>
        )}
      </Card>
    </div>
  )
}
