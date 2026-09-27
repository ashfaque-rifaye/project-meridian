const FIELD_CLASS: Record<string, string> = { customer_id: 'bm-f0', currency_code: 'bm-f1', amount: 'bm-f2' }
const BYTE = 30

type Field = { name: string; offset: number; width: number }

function fieldAt(fields: Field[], pos: number) {
  return fields.find((f) => pos >= f.offset && pos < f.offset + f.width)?.name
}

export default function ByteMap({ record, producer, consumer, producerLabel, consumerLabel, consumerLength, consumerOk }: {
  record: string
  producer: Field[]
  consumer: Field[]
  producerLabel: string
  consumerLabel: string
  consumerLength: number
  consumerOk?: boolean
}) {
  const bytes = record.split('')
  const bar = (fields: Field[], trailing?: number) => (
    <div className="bm-fields">
      {fields.map((f) => (
        <div key={f.name} className={`bm-field ${FIELD_CLASS[f.name] || 'bm-f3'}`} style={{ width: f.width * BYTE - 3 }} title={`${f.name}: bytes ${f.offset}–${f.offset + f.width - 1}`}>
          {f.width < 6 ? `${f.name === 'currency_code' ? 'ccy' : f.name.slice(0, 4)} ${f.offset}–${f.offset + f.width - 1}` : `${f.name} [${f.offset}–${f.offset + f.width - 1}]`}
        </div>
      ))}
      {trailing ? (
        <div className="bm-field bm-f3" style={{ width: trailing * BYTE - 3, background: 'var(--hold-soft)', color: 'var(--hold)' }}>ignored</div>
      ) : null}
    </div>
  )
  const extra = Math.max(0, bytes.length - consumerLength)

  return (
    <div className="bytemap">
      <div className="bm-row"><div className="bm-side"><span><b style={{ color: 'var(--text)' }}>Producer writes</b><br />{producerLabel}</span></div>{bar(producer)}</div>
      <div className="bm-row" style={{ marginTop: 18 }}>
        <div className="bm-side"><span>record on LEDGER.IN<br /><span className="mono">{bytes.length} bytes</span></span></div>
        {bytes.map((ch, i) => {
          const pos = i + 1
          const p = fieldAt(producer, pos)
          const c = fieldAt(consumer, pos)
          const ignored = pos > consumerLength
          const mis = !ignored && p !== c && !consumerOk
          return (
            <div key={i} className={`bm-byte ${ch === ' ' ? 'space' : ''} ${mis ? 'mis' : ''} ${ignored ? 'ignored' : ''}`}
              title={`byte ${pos} · producer: ${p ?? '—'} · consumer: ${ignored ? 'ignored' : c ?? '—'}`}>
              {(pos === 1 || pos % 5 === 0) && <small>{pos}</small>}
              {ch === ' ' ? '·' : ch}
            </div>
          )
        })}
      </div>
      <div className="bm-row"><div className="bm-side"><span><b style={{ color: 'var(--text)' }}>Consumer reads</b><br />{consumerLabel}</span></div>{bar(consumer, extra)}</div>
    </div>
  )
}
