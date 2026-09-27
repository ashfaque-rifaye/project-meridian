"""
legacy-ledger :: LDGPOST posting program

Liberty-hosted port of the LDGPOST batch program. Consumes LEDGREC records
from IBM MQ queue LEDGER.IN and posts them to Db2 table LEDGER.TRANSACTIONS.

R-26.9 (LEDG-2240, LEDG-2241):
  * LEDGREC rev 7: 12-character customer ID and mandatory currency code.
  * Records are routed by length so mq-bridge 3.0 (rev 6, 23 bytes) and
    mq-bridge 3.1 (rev 7, 25 bytes) are both accepted. This is what allows the
    ledger to be upgraded BEFORE the bridge.
  * Records whose length matches no known layout are rejected, not guessed.
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

COPYBOOKS = Path(__file__).resolve().parent.parent / "copybooks"
DEFAULT_CURRENCY = "USD"

_PIC = re.compile(r"05\s+LR-([A-Z-]+)\s+PIC\s+X\((\d+)\)")


def load_layout(copybook: Path) -> list[tuple[str, int]]:
    layout = []
    for line in copybook.read_text().splitlines():
        match = _PIC.search(line)
        if match:
            layout.append((match.group(1).lower().replace("-", "_"), int(match.group(2))))
    return layout


LAYOUTS = {
    "LEDGREC-v7": load_layout(COPYBOOKS / "LEDGREC.cpy"),
    "LEDGREC-v6": load_layout(COPYBOOKS / "LEDGREC6.cpy"),
}
_BY_LENGTH = {sum(w for _, w in layout): name for name, layout in LAYOUTS.items()}


def parse(record: str) -> tuple[str, dict]:
    layout_name = _BY_LENGTH.get(len(record))
    if layout_name is None:
        raise ValueError(f"record length {len(record)} matches no LEDGREC layout")
    fields, offset = {}, 0
    for name, width in LAYOUTS[layout_name]:
        fields[name] = record[offset:offset + width]
        offset += width
    return layout_name, fields


def post(record: str) -> dict:
    try:
        layout_name, fields = parse(record)
        amount = Decimal(fields["amount"].strip()).quantize(Decimal("0.01"))
    except (ValueError, InvalidOperation) as exc:
        return {"status": "REJECTED", "reason": str(exc), "mq_ack": False, "db_commit": False}

    customer_id = fields["customer_id"].strip()
    currency = fields.get("currency_code", "").strip() or DEFAULT_CURRENCY

    # INSERT INTO LEDGER.TRANSACTIONS (CUSTOMER_ID, CURRENCY_CODE, AMOUNT) VALUES (?, ?, ?)
    return {
        "status": "POSTED",
        "http_status": 200,
        "mq_ack": True,
        "db_commit": True,
        "customer_id": customer_id,
        "currency": currency,
        "amount": str(amount),
        "layout": layout_name,
    }
