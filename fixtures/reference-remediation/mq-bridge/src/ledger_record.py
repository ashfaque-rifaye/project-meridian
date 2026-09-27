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

Compatibility mode (ledger.recordLayout = v6-compat)
    For deployments where legacy-ledger is still below 7.0 (LEDGREC rev 6).
    Events that rev 6 can represent exactly (customer ID <= 10 characters,
    currency USD) are emitted in the rev 6 layout. Every other event is routed
    to LEDGER.HOLD with a reason instead of being truncated, so nothing is
    posted with a shortened customer ID or a dropped currency. Held events are
    replayed after the ledger upgrade (CR-4471).
"""

LAYOUT_VERSION = "LEDGREC-v7"

# (field, width) in record order. Mirrors copybook LEDGREC (rev 7).
LAYOUT = (
    ("customer_id", 12),
    ("currency_code", 3),
    ("amount", 10),
)
RECORD_LENGTH = sum(width for _, width in LAYOUT)  # 25

LEGACY_LAYOUT_VERSION = "LEDGREC-v6"
LEGACY_LAYOUT = (
    ("customer_id", 10),
    ("amount", 13),
)
LEGACY_RECORD_LENGTH = sum(width for _, width in LEGACY_LAYOUT)  # 23
LEGACY_CURRENCY = "USD"

TARGET_QUEUE = "LEDGER.IN"
HOLD_QUEUE = "LEDGER.HOLD"


def _format_amount(amount: str, width: int) -> str:
    whole, _, frac = f"{float(amount):.2f}".partition(".")
    return f"{whole}.{frac}".rjust(width, "0")


def _record_layout(config: dict | None) -> str:
    return (config or {}).get("ledger.recordLayout", "v7")


def to_ledger_record(event: dict, config: dict | None = None) -> dict:
    """Build the LEDGER.IN message for one BILL.OUT event."""
    customer_id = str(event["customerId"])
    currency = str(event["currencyCode"]).upper()
    if len(currency) != 3:
        raise ValueError(f"currencyCode must be 3 characters, got {currency!r}")

    if _record_layout(config) == "v6-compat":
        return _to_legacy_record(customer_id, currency, event["amount"])

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


def _to_legacy_record(customer_id: str, currency: str, amount: str) -> dict:
    reasons = []
    if len(customer_id) > 10:
        reasons.append(f"customerId has {len(customer_id)} characters; LEDGREC rev 6 holds 10")
    if currency != LEGACY_CURRENCY:
        reasons.append(f"currency {currency} cannot be represented; LEDGREC rev 6 books USD only")
    if reasons:
        return {
            "outcome": "HOLD",
            "queue": HOLD_QUEUE,
            "record": None,
            "layout": LEGACY_LAYOUT_VERSION,
            "reason": "; ".join(reasons),
        }

    record = customer_id.ljust(10) + _format_amount(amount, 13)
    assert len(record) == LEGACY_RECORD_LENGTH
    return {
        "outcome": "DELIVER",
        "queue": TARGET_QUEUE,
        "record": record,
        "layout": LEGACY_LAYOUT_VERSION,
    }
