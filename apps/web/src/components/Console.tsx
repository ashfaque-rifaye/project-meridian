import { useEffect, useRef, useState } from 'react'

export type Line = { kind: string; text: string; status?: string }

export default function Console({ lines, animate = false, height = 420, speed = 55, footer }: {
  lines: Line[]; animate?: boolean; height?: number; speed?: number; footer?: React.ReactNode
}) {
  const [shown, setShown] = useState(animate ? 0 : lines.length)
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!animate) {
      setShown(lines.length)
      return
    }
    setShown(0)
    let i = 0
    const t = setInterval(() => {
      i += 1
      setShown(i)
      if (i >= lines.length) clearInterval(t)
    }, speed)
    return () => clearInterval(t)
  }, [lines, animate, speed])

  useEffect(() => {
    if (box.current) box.current.scrollTop = box.current.scrollHeight
  }, [shown])

  return (
    <div className="console" style={{ maxHeight: height }} ref={box}>
      {lines.slice(0, shown).map((l, i) => {
        if (l.kind === 'step') {
          const st = l.status === 'ok' ? 'ok' : l.status || ''
          return (
            <div key={i} className="step">
              <span>{l.text}</span>
              <span className={`st ${st}`}>{st === 'ok' ? 'OK' : st.toUpperCase()}</span>
            </div>
          )
        }
        return <div key={i} className={`${l.kind} ${l.status || ''}`}>{l.text}</div>
      })}
      {shown < lines.length ? <span className="caret" /> : footer}
    </div>
  )
}
