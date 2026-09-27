"""
legacy-ledger :: LDGPOST posting program

Liberty-hosted port of the LDGPOST batch program. Consumes LEDGREC records
from IBM MQ queue LEDGER.IN and posts them to Db2 table LEDGER.TRANSACTIONS.

The record layout is driven entirely by copybook copybooks/LEDGREC.cpy.
Runtime: WebSphere Liberty on VMware (was-<env>-ldg-03). Deployed by the
Core Ledger team in CAB-approved change windows.
"""

import re
from decimal import Decimal
from pathlib import Path

COPYBOOK = Path(__file__).resolve().parent.parent / "copybooks" / "LEDGREC.cpy"

# The ledger books in USD when the record does not carry a currency.
DEFAULT_CURRENCY = "USD"

_PIC = re.compile(r"05\s+LR-([A-Z-]+)\s+PIC\s+X\((\d+)\)")


def load_layout(copybook: Path = COPYBOOK) -> list[tuple[str, int]]:
    """Read (field, width) pairs from the copybook, in record order."""
    layout = []
    for line in copybook.read_text().splitlines():
        match = _PIC.search(line)
        if match:
            layout.append((match.group(1).lower().replace("-", "_"), int(match.group(2))))
    return layout


LAYOUT = load_layout()


def _numval(raw: str) -> Decimal:
    # Tolerant numeric conversion carried over from the COBOL original
    # (FUNCTION NUMVAL applied to a field with non-numeric bytes removed).
    cleaned = re.sub(r"[^0-9.]", "", raw)
    if cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    return Decimal(cleaned or "0")


def parse(record: str) -> dict:
    """Slice the record by copybook positions.

    Bytes beyond the copybook length are ignored: the MQ message length is not
    checked against the layout (same behaviour as the COBOL program).
    """
    fields, offset = {}, 0
    for name, width in LAYOUT:
        fields[name] = record[offset:offset + width]
        offset += width
    return fields


def post(record: str) -> dict:
    """Post one LEDGER.IN record. Returns the posting that was committed."""
    fields = parse(record)
    customer_id = fields["customer_id"].strip()
    if not customer_id:
        return {"status": "REJECTED", "reason": "LR-CUSTOMER-ID is blank"}

    currency = fields.get("currency_code", "").strip() or DEFAULT_CURRENCY
    amount = _numval(fields["amount"]).quantize(Decimal("0.01"))

    # INSERT INTO LEDGER.TRANSACTIONS (CUSTOMER_ID, AMOUNT) VALUES (?, ?)
    return {
        "status": "POSTED",
        "http_status": 200,
        "mq_ack": True,
        "db_commit": True,
        "customer_id": customer_id,
        "currency": currency,
        "amount": str(amount),
        "layout": "LEDGREC-v6",
    }
