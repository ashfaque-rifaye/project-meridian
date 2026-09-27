---
name: implicit-contract-discovery
description: >-
  Use when discovering undocumented compatibility constraints between two deployed components
  by inspecting their actual code and enterprise interface artifacts. Activate when investigating
  an unvalidated dependency boundary, when asked about implicit contracts, or when preparing a
  probe specification for an untested edge.
---

# Implicit Contract Discovery Skill

Discover the real compatibility assumptions governing an unvalidated dependency boundary,
from source code and enterprise documents.

## Step 1 — Identify the Edge

Receive:
- producer component + deployed version + commit
- consumer component + deployed version + commit
- interface type (fixed-width MQ / REST JSON / DB schema / Kafka)

## Step 2 — Load Interface Document

Call `get_interface_document(interface_name)` via MCP.

This returns the interface-control specification (XLSX-sourced) including:
- field names
- offsets
- lengths
- types
- required flags
- interface version

## Step 3 — Inspect Producer Source

Read the producer's serializer/message-builder code at the deployed commit.

For mq-bridge (the key demo scenario):
- Read `sample-system/mq-bridge/src/record_builder.py` at the appropriate version
- Extract: field layout, offsets, lengths, padding behavior

## Step 4 — Inspect Consumer Source

Read the consumer's parser/deserializer code at the deployed commit.

For legacy-ledger (the key demo scenario):
- Read `sample-system/legacy-ledger/src/record_parser.py` at the appropriate version
- Extract: field layout, expected offsets, expected lengths, error handling

## Step 5 — Cross-Reference Against Documents

Compare discovered code assumptions against:
- interface-control.xlsx (from MCP: `get_interface_document`)
- release-notes.docx (from MCP: `get_release_notes`)
- change-request.pdf (from MCP: `get_change_request`)

Look for:
- field width mismatches (producer length ≠ consumer length)
- required fields the consumer does not handle
- format/encoding differences
- version assumptions in the consumer code
- null/missing field behavior

## Step 6 — Record Each Constraint

For each discovered constraint:
```json
{
  "field": "customerId",
  "producer_expectation": "length 12",
  "consumer_expectation": "length 10",
  "producer_source": "sample-system/mq-bridge/src/record_builder.py:L23",
  "consumer_source": "sample-system/legacy-ledger/src/record_parser.py:L18",
  "document_source": "documents/interface-control.xlsx:row 2",
  "risk": "INCOMPATIBLE — consumer truncates field silently",
  "candidate_assertion": "parsed_customer_id == 'CUST12345678' (expected) but got 'CUST123456'"
}
```

## Step 7 — Generate Probe Specification

Call `create_probe_spec` via MCP with:
- edge ID
- constraints list
- fixture inputs
- expected assertions

The probe specification is machine-readable and passed to the probe runtime.

## Rules

- Inspect actual source code at the exact deployed commits — not HEAD.
- Do not state PASS or FAIL — only discover the contract and propose the probe.
- Every constraint must have a source evidence reference.
- Do not decide compatibility from prose alone — require code evidence.
- If source code is unavailable, mark as INCONCLUSIVE and escalate to NEEDS_HUMAN.
