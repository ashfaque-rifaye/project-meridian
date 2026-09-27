"""
legacy-ledger v6.9 — Record Parser
Fixed-width ledger record consumer (old format — INCOMPATIBLE with mq-bridge v3.1)

IMPORTANT: This parser was built for mq-bridge v3.0 (format v6).
It does NOT handle the new v7 format from mq-bridge v3.1.

Format v6 assumption:
  customerId    offset 0   length 10
  amount        offset 10  length 13

When fed a v7 record (length 25, 12-char customerId, 3-char currencyCode):
  - Parses successfully (no exception)
  - customerId is silently truncated to 10 chars
  - amount field includes currencyCode bytes + wrong amount bytes
  - Business data is WRONG but infrastructure shows SUCCESS

This is the "silent semantic failure" that Meridian detects.

Git commit for this version: a18c92
Release: legacy-ledger 6.9 (pre-R-26.9 state)
"""

RECORD_FORMAT_VERSION = "v6"
CUSTOMER_ID_LENGTH = 10
AMOUNT_LENGTH = 13
EXPECTED_RECORD_LENGTH = 23  # old format

# INTENTIONAL INCOMPATIBILITY DOCUMENTATION:
# mq-bridge 3.1 produces 25-char records.
# This parser expects 23-char records.
# Python string slicing does NOT raise IndexError on out-of-bounds — it silently truncates.
# The record is accepted, parsed, committed to DB, but with WRONG field values.


def parse_record(record: str) -> dict:
    """
    Parse a fixed-width ledger record using the v6 layout.
    
    WARNING: If fed a v7 record (from mq-bridge 3.1), this will:
    - Accept it without error (string slicing never raises on over-read)
    - Return customer_id as the first 10 chars only (truncated)
    - Return amount as chars 10-23 (includes currencyCode bytes)
    - The result will be semantically incorrect but appear valid
    
    This is the core silent failure scenario.
    """
    # No length check — v6 parsers were not defensive about record format changes
    customer_id = record[0:10].rstrip()
    amount_raw = record[10:23].rstrip()
    
    return {
        "format_version": RECORD_FORMAT_VERSION,
        "customer_id": customer_id,
        "amount": amount_raw,
        "parse_status": "SUCCESS",
        "record_length_received": len(record),
        "record_length_expected": EXPECTED_RECORD_LENGTH,
    }


def process_transaction(record: str) -> dict:
    """
    Process an incoming MQ ledger record.
    Simulates: read from MQ → parse → validate → commit to DB.
    
    Returns the processing result (HTTP 200 / MQ ACK / DB COMMIT equivalent).
    """
    parsed = parse_record(record)
    
    # Basic validation (does not catch field-width semantic errors)
    if not parsed["customer_id"]:
        return {"status": "ERROR", "reason": "missing customer_id"}
    
    try:
        float(parsed["amount"])
        amount_valid = True
    except ValueError:
        amount_valid = False
    
    return {
        "status": "SUCCESS",          # Always SUCCESS for any parseable record
        "http_status": 200,
        "mq_ack": True,
        "db_committed": True,
        "pod_health": "HEALTHY",
        "customer_id": parsed["customer_id"],
        "amount": parsed["amount"],
        "amount_parse_ok": amount_valid,
        "warning": None,              # No warning — silent failure
        "format_version_parsed": RECORD_FORMAT_VERSION,
    }


if __name__ == "__main__":
    # Demonstrate the silent failure:
    # Feed a v7 record (from mq-bridge 3.1) to the v6 parser
    v7_record = "CUST12345678USD0000149.50"
    print(f"Input record (v7): {v7_record!r}")
    print(f"Input length: {len(v7_record)}")
    print()
    
    result = process_transaction(v7_record)
    print("Processing result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
    
    print()
    print("EXPECTED customer_id: CUST12345678")
    print(f"ACTUAL   customer_id: {result['customer_id']}")
    print()
    if result["customer_id"] != "CUST12345678":
        print("*** SILENT SEMANTIC FAILURE DEMONSTRATED ***")
        print("Infrastructure: ALL GREEN")
        print("Business data:  WRONG")
