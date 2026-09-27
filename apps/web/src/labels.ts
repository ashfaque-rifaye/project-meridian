/**
 * Display names for the demo scenario.
 *
 * The API and engine keep their original identifiers (legacy-ledger, ledger-db, order-to-ledger, ...).
 * The UI shows plain software names instead. Every API response passes through `fromApi`, and every
 * outgoing path or body passes through `toApi`, so the rest of the frontend only sees the display names.
 */

// Identifiers that round-trip: renamed on the way in, restored on the way out.
const IDS: [string, string][] = [
  ['legacy-ledger', 'legacy-backend'],
  ['ledger-db', 'backend-db'],
  ['order-to-ledger', 'checkout-flow'],
]

// One-way wording changes for text that is only displayed. File names (e.g. ledger_record.py, LEDGREC.cpy)
// are left alone so the code viewer and source links still match the real files.
const TEXT: [RegExp, string][] = [
  [/Order-to-Ledger/g, 'Checkout flow'],
  [/\bLEDG-ICD-/g, 'ICD-'],
  [/\bLEDG-(\d+)/g, 'BKND-$1'],
  [/\bQM\.LEDG\./g, 'QM.BACKEND.'],
  [/\bLEDGER\.(IN|HOLD|TRANSACTIONS)\b/g, 'BACKEND.$1'],
  [/\bLEDGREC-v(\d+)\b/g, 'layout v$1'],
  [/\bLEDGREC rev (\d+)/g, 'record layout rev $1'],
  [/\bLEDGREC\d*\b(?!\.cpy)/g, 'record layout'],
  [/\bLDGPOST\b/g, 'posting job'],
  [/\bLEDGDB\b/g, 'BACKENDDB'],
  [/\bNone — implicit in copybook \+ ICD spreadsheet/g, 'None, only a COBOL copybook and a spreadsheet'],
  [/\bStage validation corpus\b/g, 'Stage test data'],
  [/\bLEDGER\b(?![._])/g, 'BACKEND'],
  [/\bLedgers\b/g, 'Backends'],
  [/\bLedger\b/g, 'Backend'],
  [/\bledgers\b/g, 'backends'],
  [/\bledger\b/g, 'backend'],
]

// Raw code, diffs and the Bob hand-off prompt keep the real identifiers so they still work outside the UI.
const VERBATIM_KEYS = new Set(['diff', 'lines', 'prompt', 'prompt_file', 'evidence_file'])

function renameIds(s: string) {
  let out = s
  for (const [from, to] of IDS) out = out.split(from).join(to)
  return out
}

/** Plain display text for any string that came from the API. */
export function humanize(s: string) {
  let out = renameIds(s)
  for (const [re, to] of TEXT) out = out.replace(re, to)
  return out
}

/** Deep-convert an API response: object keys get the id rename, string values get the full wording pass. */
export function fromApi<T>(value: T): T {
  if (typeof value === 'string') return humanize(value) as T
  if (Array.isArray(value)) return value.map((v) => fromApi(v)) as T
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[renameIds(k)] = VERBATIM_KEYS.has(k) ? v : fromApi(v)
    }
    return out as T
  }
  return value
}

/** Restore the real identifiers before a path or request body is sent to the API. */
export function toApi(s: string) {
  let out = s
  for (const [real, shown] of IDS) out = out.split(shown).join(real)
  return out
}
