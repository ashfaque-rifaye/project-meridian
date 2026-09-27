import { GLYPH } from './ui'

const STATE_COLOR: Record<string, string> = {
  VERIFIED: 'var(--ok)',
  VERIFIED_BY_PROBE: 'var(--probe)',
  UNTESTED: 'var(--warn)',
  FAILED: 'var(--fail)',
  INCONCLUSIVE: 'var(--hold)',
  NEEDS_HUMAN: 'var(--hold)',
}

const W = 196
const H = 96
const GAP = 64
const X0 = 16
const ROW1 = 34
const ROW2 = ROW1 + H + 96

function pos(i: number) {
  const col = i % 4
  const row = Math.floor(i / 4)
  return { x: X0 + col * (W + GAP), y: row === 0 ? ROW1 : ROW2 }
}

export default function FlowGraph({
  components, edges, composition, selected, onSelect, highlight,
}: {
  components: any[]
  edges: any[]
  composition: Record<string, any>
  selected?: string | null
  onSelect?: (edgeId: string) => void
  highlight?: string[]
}) {
  const index: Record<string, number> = {}
  components.forEach((c, i) => (index[c.id] = i))
  const width = X0 * 2 + 4 * W + 3 * GAP
  const height = ROW2 + H + 20
  const bad = new Set(edges.filter((e) => e.state === 'FAILED').flatMap((e) => [e.producer, e.consumer]))

  return (
    <div className="graph-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ minWidth: 900, display: 'block' }}>
        <defs>
          {Object.entries(STATE_COLOR).map(([k, c]) => (
            <marker key={k} id={`arrow-${k}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill={c} />
            </marker>
          ))}
        </defs>

        {edges.map((e) => {
          const a = pos(index[e.producer])
          const b = pos(index[e.consumer])
          const sameRow = a.y === b.y
          const color = STATE_COLOR[e.state] || 'var(--muted)'
          let d: string
          let lx: number
          let ly: number
          if (sameRow) {
            d = `M ${a.x + W} ${a.y + H / 2} L ${b.x - 4} ${b.y + H / 2}`
            lx = (a.x + W + b.x) / 2
            ly = a.y + H / 2 - 12
          } else {
            const sx = a.x + W / 2
            const sy = a.y + H
            const ex = b.x + W / 2
            const ey = b.y - 4
            d = `M ${sx} ${sy} C ${sx} ${sy + 60}, ${ex} ${ey - 60}, ${ex} ${ey}`
            lx = (sx + ex) / 2
            ly = (sy + ey) / 2 - 2
          }
          const isSel = selected === e.edge_id
          const proto = (e.interface || '').split('·')[0].trim()
          return (
            <g key={e.edge_id} className="graph-edge" onClick={() => onSelect?.(e.edge_id)}>
              <path d={d} className="hit" />
              <path d={d} className="line" stroke={color} strokeWidth={isSel ? 3.2 : 2}
                strokeDasharray={e.state === 'FAILED' ? '7 5' : e.state === 'VERIFIED' ? undefined : '3 4'}
                markerEnd={`url(#arrow-${e.state in STATE_COLOR ? e.state : 'VERIFIED'})`}>
                {e.state === 'FAILED' && <animate attributeName="stroke-dashoffset" from="24" to="0" dur="0.9s" repeatCount="indefinite" />}
              </path>
              <foreignObject x={lx - 58} y={ly - 13} width={116} height={24}>
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5, height: 22,
                  background: 'var(--bg)', border: `1px solid ${color}`, borderRadius: 11, fontFamily: 'var(--mono)',
                  fontSize: 10.5, color, fontWeight: 600, padding: '0 7px', whiteSpace: 'nowrap',
                  boxShadow: isSel ? `0 0 0 3px color-mix(in srgb, ${color} 25%, transparent)` : undefined,
                }}>
                  <span>{GLYPH[e.state] || '•'}</span>
                  <span style={{ color: 'var(--text-2)', fontWeight: 500 }}>{proto}</span>
                </div>
              </foreignObject>
            </g>
          )
        })}

        {components.map((c, i) => {
          const { x, y } = pos(i)
          const comp = composition[c.id] || {}
          const isBad = bad.has(c.id)
          const hl = highlight?.includes(c.id)
          return (
            <foreignObject key={c.id} x={x} y={y} width={W} height={H}>
              <div style={{
                height: H - 2, margin: 1, borderRadius: 10, padding: '9px 12px', boxSizing: 'border-box',
                background: isBad ? 'color-mix(in srgb, var(--fail) 8%, var(--surface-2))' : 'var(--surface-2)',
                border: `1px solid ${isBad ? 'var(--fail)' : hl ? 'var(--accent)' : 'var(--border-2)'}`,
                display: 'flex', flexDirection: 'column', gap: 2, fontFamily: 'var(--sans)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontWeight: 600, fontSize: 12.5, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.label}</span>
                  <span style={{ marginLeft: 'auto', width: 7, height: 7, borderRadius: 4, background: (comp.health || '').startsWith('HEALTHY') ? 'var(--ok)' : 'var(--warn)', flex: 'none' }} title={comp.health} />
                </div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 20, fontWeight: 500, color: isBad ? 'var(--fail)' : 'var(--text)', lineHeight: 1.2 }}>
                  {comp.version || '—'}
                </div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--muted)', whiteSpace: 'nowrap', overflow: 'hidden' }}>
                  <span className={`platform pf-${c.platform.startsWith('WebSphere') ? 'WebSphere' : c.platform.startsWith('Db2') ? 'Db2' : c.platform}`}>{c.platform.split(' ')[0].toUpperCase()}</span>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.cloud}</span>
                </div>
              </div>
            </foreignObject>
          )
        })}
      </svg>
    </div>
  )
}
