#!/usr/bin/env python3
"""
Generate synthetic enterprise documents for the Meridian demo.
Creates: interface-control.xlsx, change-request PDF text, release-notes content

SYNTHETIC DATA — All content is fictional, created for demonstration purposes.
"""

import json
from pathlib import Path


def generate_interface_control_data() -> list[dict]:
    """Return the interface-control field data for the fixed-width MQ format."""
    return [
        {
            "Field": "customerId",
            "Offset": 1,
            "Length": 12,
            "Type": "STRING",
            "Required": "YES",
            "InterfaceVersion": "v7",
            "Description": "Customer identifier (12 chars, expanded from 10 in R-26.9)"
        },
        {
            "Field": "currencyCode",
            "Offset": 13,
            "Length": 3,
            "Type": "STRING",
            "Required": "YES",
            "InterfaceVersion": "v7",
            "Description": "ISO 4217 currency code — NEW field in R-26.9"
        },
        {
            "Field": "amount",
            "Offset": 16,
            "Length": 10,
            "Type": "DECIMAL",
            "Required": "YES",
            "InterfaceVersion": "v7",
            "Description": "Transaction amount (zero-padded, 2 decimal places)"
        },
        {
            "Field": "[DEPRECATED] customerId (v6)",
            "Offset": 1,
            "Length": 10,
            "Type": "STRING",
            "Required": "YES",
            "InterfaceVersion": "v6",
            "Description": "DEPRECATED — old 10-char layout used by mq-bridge 3.0 / legacy-ledger 6.9"
        },
        {
            "Field": "[DEPRECATED] amount (v6)",
            "Offset": 11,
            "Length": 13,
            "Type": "DECIMAL",
            "Required": "YES",
            "InterfaceVersion": "v6",
            "Description": "DEPRECATED — old amount field (no currency prefix)"
        },
    ]


def generate_change_request_data() -> dict:
    """Return the CR-4471 change request data."""
    return {
        "cr_id": "CR-4471",
        "title": "R-26.9 — Legacy Ledger upgrade to support 12-char Customer ID and Currency Code",
        "component": "legacy-ledger",
        "from_version": "6.9",
        "target_version": "7.0",
        "cab_window": "Saturday 02:00–04:00 UTC",
        "cab_window_date": "2026-09-28",
        "requested_by": "Platform Engineering Team",
        "approved_by": "CAB Board",
        "status": "SCHEDULED",
        "dependency": "mq-bridge 3.1 must be deployed first (already in Prod as of 2026-09-26)",
        "risk": "MEDIUM — parser format change; backward-compatible mode available",
        "rollback_plan": "Revert to legacy-ledger 6.9 binary if V15 DB migration fails",
        "notes": [
            "mq-bridge 3.1 was promoted to Prod on 2026-09-26 (R-26.9 partial rollout)",
            "legacy-ledger upgrade is the second phase of R-26.9",
            "DB schema V14->V15 migration to run in the same CAB window",
            "CRITICAL: Production is currently running mq-bridge 3.1 + legacy-ledger 6.9",
            "This combination was NOT validated in Stage — only bridge 3.1 + ledger 7.0 was validated"
        ]
    }


def generate_release_notes_data() -> dict:
    """Return the R-26.9 release notes data."""
    return {
        "release_id": "R-26.9",
        "release_title": "Customer ID Expansion and Currency Code Support",
        "release_date": "2026-09-26",
        "business_requirement": "Increase customerId capacity from 10 to 12 characters and introduce mandatory currencyCode support for ledger transactions.",
        "changed_services": [
            {"service": "order-api", "from": "4.7", "to": "4.8", "change": "12-char customerId support"},
            {"service": "payment-service", "from": "8.3", "to": "8.4", "change": "currency propagation"},
            {"service": "billing-service", "from": "7.1", "to": "7.2", "change": "currencyCode to MQ message"},
            {"service": "mq-bridge", "from": "3.0", "to": "3.1", "change": "New fixed-width format v7 (12-char cid, currency)"},
            {"service": "legacy-ledger", "from": "6.9", "to": "7.0", "change": "New v7 parser with currencyCode support"},
            {"service": "ledger-db", "from": "V14", "to": "V15", "change": "customer_id VARCHAR(12), new currency_code column"},
        ],
        "deployment_dependencies": [
            "mq-bridge 3.1 must deploy before legacy-ledger 7.0",
            "legacy-ledger 7.0 must deploy before DB schema V15 migration OR concurrently",
            "order-api 4.8 is backward compatible — can deploy independently"
        ],
        "expected_rollout_order": [
            "1. order-api 4.8",
            "2. payment-service 8.4",
            "3. billing-service 7.2",
            "4. mq-bridge 3.1",
            "5. legacy-ledger 7.0 (CAB window required)",
            "6. ledger-db V15 migration (during CAB window)"
        ],
        "compatibility_notes": [
            "mq-bridge 3.1 emits v7 fixed-width format — legacy-ledger 6.9 CANNOT parse this correctly",
            "legacy-ledger 6.9 will silently truncate customerId from 12 to 10 chars",
            "Infrastructure health checks WILL NOT detect this semantic error",
            "Running mq-bridge 3.1 with legacy-ledger 6.9 is an UNVALIDATED combination"
        ],
        "validated_combination": {
            "mq-bridge": "3.1",
            "legacy-ledger": "7.0",
            "ledger-db": "V15",
            "environment": "stage",
            "validated_at": "2026-09-24T14:30:00Z"
        }
    }


if __name__ == "__main__":
    docs_dir = Path("documents")
    docs_dir.mkdir(exist_ok=True)
    
    # Save JSON fixtures (used by MCP server when actual office files aren't needed)
    with open(docs_dir / "interface-control-data.json", "w") as f:
        json.dump(generate_interface_control_data(), f, indent=2)
    
    with open(docs_dir / "change-request-data.json", "w") as f:
        json.dump(generate_change_request_data(), f, indent=2)
    
    with open(docs_dir / "release-notes-data.json", "w") as f:
        json.dump(generate_release_notes_data(), f, indent=2)
    
    print("Document fixtures generated in documents/")
    print("  interface-control-data.json")
    print("  change-request-data.json")
    print("  release-notes-data.json")
