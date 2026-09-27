"""
mq-bridge :: ledger record builder

Converts BILL.OUT billing events (JSON, produced by billing-service) into the
fixed-width LEDGREC record that legacy-ledger consumes from IBM MQ queue
LEDGER.IN.

Layout: LEDGREC v7 (Interface Control Document LEDG-ICD-007, rev 7)
R-26.9 / LEDG-2231, LEDG-2232

    field          width   notes
    customer_id    12      widened from 10 (new 12-character customer IDs)
    currency_code  3       new, mandatory ISO 4217 code
    amount         10      zero padded, explicit decimal point (9(7).99)
"""

LAYOUT_VERSION = "LEDGREC-v7"

# (field, width) in record order. Mirrors copybook LEDGREC (rev 7).
LAYOUT = (
    ("customer_id", 12),
    ("currency_code", 3),
    ("amount", 10),
)
RECORD_LENGTH = sum(width for _, width in LAYOUT)  # 25

TARGET_QUEUE = "LEDGER.IN"


def _format_amount(amount: str, width: int) -> str:
    whole, _, frac = f"{float(amount):.2f}".partition(".")
    return f"{whole}.{frac}".rjust(width, "0")


def to_ledger_record(event: dict, config: dict | None = None) -> dict:
    """Build the LEDGER.IN message for one BILL.OUT event."""
    customer_id = str(event["customerId"])
    currency = str(event["currencyCode"]).upper()
    if len(currency) != 3:
        raise ValueError(f"currencyCode must be 3 characters, got {currency!r}")

    record = (
        customer_id[:12].ljust(12)
        + currency
        + _format_amount(event["amount"], 10)
    )
    assert len(record) == RECORD_LENGTH
    return {
        "outcome": "DELIVER",
        "queue": TARGET_QUEUE,
        "record": record,
        "layout": LAYOUT_VERSION,
    }
