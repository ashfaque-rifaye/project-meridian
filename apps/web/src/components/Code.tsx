import { useApi } from '../api'

export function CodeView({ component, commit, path, highlight = [], danger = [], maxHeight = 320 }: {
  component: string; commit: string; path: string; highlight?: number[]; danger?: number[]; maxHeight?: number
}) {
  const { data, error } = useApi(`/source/${component}?commit=${commit}&path=${encodeURIComponent(path)}`, [component, commit, path])
  return (
    <div className="code" style={{ maxHeight }}>
      <div className="code-head">
        <span className="tag">{component}@{commit}</span>
        <span className="mono">{path}</span>
        <span className="spacer" />
        <span className="tiny dim">git show {commit}:{path}</span>
      </div>
      {error && <div className="err" style={{ padding: 12 }}>{error}</div>}
      {data?.lines.map((line: string, i: number) => (
        <div key={i} className={`code-line ${danger.includes(i + 1) ? 'hl-fail' : highlight.includes(i + 1) ? 'hl' : ''}`}>
          <span className="ln">{i + 1}</span>
          <span>{line || ' '}</span>
        </div>
      ))}
    </div>
  )
}

export function DiffView({ diff, maxHeight = 460 }: { diff: string; maxHeight?: number }) {
  const lines = diff.split('\n')
  return (
    <div className="code diff" style={{ maxHeight }}>
      {lines.map((l, i) => {
        const cls = l.startsWith('+++') || l.startsWith('---') ? 'hunk'
          : l.startsWith('+') ? 'add' : l.startsWith('-') ? 'del' : l.startsWith('@@') ? 'hunk' : 'ctx'
        return (
          <div key={i} className={`code-line ${cls}`}>
            <span className="ln">{i + 1}</span>
            <span>{l || ' '}</span>
          </div>
        )
      })}
    </div>
  )
}

/** Line numbers referenced by evidence strings like "repo@abc:path#L12". */
export function linesFrom(sources: string[], path: string) {
  return sources
    .filter((s) => s && s.includes(path) && s.includes('#L'))
    .map((s) => Number(s.split('#L')[1]))
    .filter((n) => !Number.isNaN(n))
}
