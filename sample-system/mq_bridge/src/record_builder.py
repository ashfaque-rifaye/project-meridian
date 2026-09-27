"""
mq-bridge v3.1 — Record Builder
Fixed-width ledger record producer (new format)

Release R-26.9 change:
  Increase customerId capacity from 10 to 12 characters.
  Add mandatory currencyCode (3 characters).

Format v7:
  customerId    offset 1   length 12
  currencyCode  offset 13  length 3
  amount        offset 16  length 10
"""

RECORD_FORMAT_VERSION = "v7"
CUSTOMER_ID_LENGTH = 12
CURRENCY_CODE_LENGTH = 3
AMOUNT_LENGTH = 10
RECORD_LENGTH = 25

# Git commit for this version: 8f7a91
# Release: R-26.9
# Branch: release/R-26.9


def build_record(customer_id: str, currency_code: str, amount: str) -> str:
    """
    Build a fixed-width ledger record in the v7 format.
    
    Args:
        customer_id: Up to 12 characters (padded right with spaces)
        currency_code: Exactly 3 characters (ISO 4217)
        amount: Up to 10 characters (zero-padded right)
    
    Returns:
        Fixed-width record string of length 25
    
    Example:
        build_record("CUST12345678", "USD", "0000149.50")
        -> "CUST12345678USD0000149.50"
    """
    if len(currency_code) != CURRENCY_CODE_LENGTH:
        raise ValueError(f"currencyCode must be exactly 3 chars, got {len(currency_code)!r}")
    
    cid = customer_id[:CUSTOMER_ID_LENGTH].ljust(CUSTOMER_ID_LENGTH)
    ccy = currency_code.upper()
    amt = amount[:AMOUNT_LENGTH].ljust(AMOUNT_LENGTH)
    record = cid + ccy + amt
    
    assert len(record) == RECORD_LENGTH, f"Record length {len(record)} != {RECORD_LENGTH}"
    return record


def get_format_spec() -> dict:
    """Return the format specification for documentation and contract discovery."""
    return {
        "format_version": RECORD_FORMAT_VERSION,
        "record_length": RECORD_LENGTH,
        "fields": [
            {"name": "customerId", "offset": 0, "length": 12, "type": "string", "required": True},
            {"name": "currencyCode", "offset": 12, "length": 3, "type": "string", "required": True},
            {"name": "amount", "offset": 15, "length": 10, "type": "decimal", "required": True},
        ]
    }


if __name__ == "__main__":
    # Demo: build sample records
    rec = build_record("CUST12345678", "USD", "0000149.50")
    print(f"Record (repr): {rec!r}")
    print(f"Record length: {len(rec)}")
    print(f"Format spec: {get_format_spec()}")
