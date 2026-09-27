"""
mq-bridge :: ledger record builder

Converts BILL.OUT billing events (JSON, produced by billing-service) into the
fixed-width LEDGREC record that legacy-ledger consumes from IBM MQ queue
LEDGER.IN.

Layout: LEDGREC v6 (see Interface Control Document LEDG-ICD-007, rev 6)

    field         width   notes
    customer_id   10      left-aligned, space padded
    amount        13      zero padded, explicit decimal point (9(10).99)

The record carries no currency: the ledger books everything in USD.
"""

LAYOUT_VERSION = "LEDGREC-v6"

# (field, width) in record order. Mirrors copybook LEDGREC (rev 6).
LAYOUT = (
    ("customer_id", 10),
    ("amount", 13),
)
RECORD_LENGTH = sum(width for _, width in LAYOUT)  # 23

TARGET_QUEUE = "LEDGER.IN"


def _format_amount(amount: str, width: int) -> str:
    whole, _, frac = f"{float(amount):.2f}".partition(".")
    return f"{whole}.{frac}".rjust(width, "0")


def to_ledger_record(event: dict, config: dict | None = None) -> dict:
    """Build the LEDGER.IN message for one BILL.OUT event."""
    customer_id = str(event["customerId"])
    record = customer_id[:10].ljust(10) + _format_amount(event["amount"], 13)
    assert len(record) == RECORD_LENGTH
    return {
        "outcome": "DELIVER",
        "queue": TARGET_QUEUE,
        "record": record,
        "layout": LAYOUT_VERSION,
    }
