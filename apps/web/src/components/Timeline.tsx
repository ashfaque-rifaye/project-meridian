import { fmtTime } from '../api'

const LANE_H = 58
const TOP = 46
const LEFT = 70
const RIGHT = 16

export default function Timeline({ data, onSegment, selected }: { data: any; onSegment?: (seg: any) => void; selected?: any }) {
  const W = 1180
  const t0 = new Date(data.window_start).getTime()
  const t1 = new Date(data.window_end).getTime()
  const x = (ts: string) => LEFT + ((new Date(ts).getTime() - t0) / (t1 - t0)) * (W - LEFT - RIGHT)
  const clampX = (ts: string) => Math.max(LEFT, Math.min(W - RIGHT, x(ts)))
  const H = TOP + data.lanes.length * LANE_H + 34
  const now = data.snapshot_time
  const days: string[] = []
  for (let d = new Date(t0); d.getTime() <= t1; d = new Date(d.getTime() + 86400000)) {
    const day = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
    if (day.getTime() >= t0) days.push(day.toISOString())
  }
  const fdd = data.divergence
  const laneY = (i: number) => TOP + i * LANE_H

  return (
    <svg className="tl" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Release timeline across environments">
      <defs>
        <pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="7" height="7" fill="var(--hold-soft)" />
          <line x1="0" y1="0" x2="0" y2="7" stroke="var(--hold)" strokeWidth="2" opacity="0.5" />
        </pattern>
      </defs>

      {days.map((d) => (
        <g key={d}>
          <line x1={x(d)} x2={x(d)} y1={TOP - 16} y2={H - 26} stroke="var(--border)" />
          <text x={x(d) + 4} y={H - 10}>{fmtTime(d).split(' ').slice(0, 3).join(' ')}</text>
        </g>
      ))}

      {data.lanes.map((lane: any, i: number) => {
        const y = laneY(i)
        return (
          <g key={lane.environment}>
            <text className="lane-label" x={8} y={y + 26}>{lane.environment.toUpperCase()}</text>
            <rect x={LEFT} y={y + 8} width={W - LEFT - RIGHT} height={30} rx={5} fill="var(--surface-2)" opacity={0.5} />
            {lane.segments.map((seg: any, j: number) => {
              const x1 = clampX(seg.start)
              const x2 = clampX(seg.end || now)
              if (x2 - x1 < 0.5) return null
              const isCurrentFdd = lane.environment === fdd?.environment && !seg.end && fdd
              const fill = isCurrentFdd ? 'var(--fail-soft)' : seg.validated ? 'var(--ok-soft)' : 'var(--warn-soft)'
              const stroke = isCurrentFdd ? 'var(--fail)' : seg.validated ? 'var(--ok)' : 'var(--warn)'
              const sel = selected && selected.environment === seg.environment && selected.start === seg.start
              return (
                <rect key={j} className="seg" x={x1 + 1} y={y + 10} width={x2 - x1 - 2} height={26} rx={4}
                  fill={fill} stroke={stroke} strokeWidth={sel ? 2 : 1} onClick={() => onSegment?.(seg)}>
                  <title>{`${lane.environment.toUpperCase()} ${fmtTime(seg.start)} → ${seg.end ? fmtTime(seg.end) : 'now'}\n${seg.validated ? 'Versions tested' : 'Not tested: ' + seg.unvalidated.map((u: any) => `${u.edge_id.replace('--', ' → ')} (${u.pair.join(' → ')})`).join(', ')}`}</title>
                </rect>
              )
            })}
            {lane.events.filter((e: any) => new Date(e.deployed_at).getTime() >= t0).map((e: any) => (
              <g key={e.event_id} transform={`translate(${x(e.deployed_at)}, ${y + 8})`}>
                <path d="M0 -6 L5 0 L0 6 L-5 0 Z" fill={e.component === 'mq-bridge' && lane.environment === 'prod' ? 'var(--fail)' : 'var(--text-2)'} stroke="var(--bg)" strokeWidth={1} />
                <title>{`${fmtTime(e.deployed_at)}  ${e.component} ${e.from_version} → ${e.to_version}\n${e.tool} · ${e.trigger}${e.note ? '\n' + e.note : ''}`}</title>
              </g>
            ))}
            {data.validation_runs.filter((r: any) => r.environment === lane.environment && new Date(r.started_at).getTime() >= t0).map((r: any) => (
              <g key={r.run_id} transform={`translate(${x(r.started_at)}, ${y + 44})`}>
                <rect x={-8} y={-7} width={16} height={14} rx={3} fill={r.semantic ? 'var(--ok)' : 'var(--warn)'} />
                <text x={0} y={4} textAnchor="middle" style={{ fill: '#08110b', fontWeight: 700, fontSize: 10 }}>{r.semantic ? '✓' : '↯'}</text>
                <title>{`${r.suite} · ${r.method}\n${fmtTime(r.started_at)} · ${r.messages} messages · ${r.result}`}</title>
              </g>
            ))}
          </g>
        )
      })}

      {data.scheduled_changes.map((c: any) => {
        const i = data.lanes.findIndex((l: any) => l.environment === c.environment)
        if (i < 0) return null
        const y = laneY(i)
        const x1 = clampX(c.window_start)
        const x2 = clampX(c.window_end)
        return (
          <g key={c.change_request}>
            <rect x={x1} y={y + 10} width={Math.max(x2 - x1, 8)} height={26} rx={4} fill="url(#hatch)" stroke="var(--hold)" strokeDasharray="3 3" />
            <text x={x1 - 6} y={y + 4} textAnchor="end" style={{ fill: 'var(--hold)', fontWeight: 600 }}>{c.change_request} window</text>
            <title>{`${c.change_request}: ${c.changes.map((ch: any) => `${ch.component} ${ch.to_version}`).join(', ')}\n${c.status}`}</title>
          </g>
        )
      })}

      {fdd?.unvalidated_since && (() => {
        const i = data.lanes.findIndex((l: any) => l.environment === fdd.environment)
        const fx = x(fdd.unvalidated_since)
        return (
          <g>
            <line x1={fx} x2={fx} y1={TOP - 22} y2={laneY(i) + 40} stroke="var(--fail)" strokeWidth={1.5} strokeDasharray="4 3" />
            <text x={fx + 6} y={TOP - 24} style={{ fill: 'var(--fail)', fontWeight: 600 }}>{fmtTime(fdd.unvalidated_since, { date: false })} untested versions go live</text>
          </g>
        )
      })()}

      <line x1={x(now)} x2={x(now)} y1={TOP - 22} y2={H - 26} stroke="var(--accent)" strokeWidth={1.5} />
      <text x={x(now) + 5} y={H - 28} style={{ fill: 'var(--accent)', fontWeight: 600 }}>data as of</text>
    </svg>
  )
}
