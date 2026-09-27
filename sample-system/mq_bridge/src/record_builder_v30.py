"""
mq-bridge v3.0 — Record Builder
Fixed-width ledger record producer (old format)

Format v6:
  customerId    offset 1   length 10
  amount        offset 11  length 13
"""

RECORD_FORMAT_VERSION = "v6"
CUSTOMER_ID_LENGTH = 10
AMOUNT_LENGTH = 13
RECORD_LENGTH = 23


def build_record(customer_id: str, amount: str) -> str:
    """
    Build a fixed-width ledger record in the v6 format.
    
    Args:
        customer_id: Up to 10 characters
        amount: Up to 13 characters (right-padded with spaces)
    
    Returns:
        Fixed-width record string of length 23
    """
    cid = customer_id[:CUSTOMER_ID_LENGTH].ljust(CUSTOMER_ID_LENGTH)
    amt = amount[:AMOUNT_LENGTH].ljust(AMOUNT_LENGTH)
    record = cid + amt
    assert len(record) == RECORD_LENGTH, f"Record length {len(record)} != {RECORD_LENGTH}"
    return record


def parse_record(record: str) -> dict:
    """
    Parse a v6 fixed-width ledger record.
    """
    if len(record) < RECORD_LENGTH:
        raise ValueError(f"Record too short: {len(record)} < {RECORD_LENGTH}")
    return {
        "format_version": RECORD_FORMAT_VERSION,
        "customer_id": record[0:10].rstrip(),
        "amount": record[10:23].rstrip(),
    }


if __name__ == "__main__":
    # Demo: build a sample record
    rec = build_record("CUST123456", "0000149.50   ")
    print(f"Record (hex): {rec!r}")
    parsed = parse_record(rec)
    print(f"Parsed: {parsed}")
