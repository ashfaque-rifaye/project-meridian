---
name: probe-generation
description: >-
  Use when creating a deterministic executable compatibility probe for an unvalidated dependency
  boundary, or when running an existing probe safely in an isolated environment. Activate when
  the user asks to generate a probe, run a probe, or verify a compatibility claim with execution.
---

# Probe Generation Skill

Create and execute a reproducible compatibility probe in an isolated subprocess environment.

## Step 1 — Receive Probe Specification

Obtain a probe specification (JSON) from the contract discovery stage, or from MCP via
`create_probe_spec`. The spec must include:
- probe_id
- edge (producer → consumer)
- producer_version and producer_commit
- consumer_version and consumer_commit
- interface_type (fixed_width_mq / rest_json / db_schema)
- fixture inputs (field values)
- assertions (list of expected outcomes)

## Step 2 — Verify Source Availability

Confirm that the probe source files exist:
- Producer implementation at the specified version
- Consumer implementation at the specified version
- Fixture data

If source files are missing, return INCONCLUSIVE with evidence.

## Step 3 — Generate Fixture

Create a realistic input fixture that exercises the boundary condition.

For the fixed-width MQ hero scenario:
```
customerId  = CUST12345678   (12 chars — the new format)
currencyCode = USD           (3 chars — new field)
amount       = 0000149.50   (10 chars)
```

Raw fixed-width record: `CUST12345678USD0000149.50`

## Step 4 — Run Probe in Isolation

Call `run_probe(probe_id)` via MCP, which executes:
```
[1/4] Serialize input with producer at producer_commit
[2/4] Produce fixed-width record
[3/4] Parse record with consumer at consumer_commit
[4/4] Evaluate semantic assertions
```

The probe runs in subprocess isolation — never against production.

Capture:
- probe_id
- producer_commit
- consumer_commit
- fixture hash
- stdout
- stderr
- exit_code
- assertion_results (field by field)
- result: PASS | FAIL | INCONCLUSIVE
- timestamp

## Step 5 — Evaluate Assertions Deterministically

For each assertion in the spec, compare actual output against expected:

```python
assert parsed.customer_id == expected.customer_id
assert parsed.amount == expected.amount
assert parsed.currency_code == expected.currency_code
```

The LLM does NOT decide the probe result. The assertion evaluator is deterministic Python code.

## Step 6 — Persist Evidence

Write probe result to `.meridian/runs/<probe_id>.json`.
Update the MCP validation memory via `get_probe_result`.

## Step 7 — Return Result

```json
{
  "probe_id": "probe-001",
  "connection": "mq-bridge@3.1 → legacy-ledger@6.9",
  "result": "FAILED",
  "assertion_results": [
    {
      "assertion": "customerId == 'CUST12345678'",
      "expected": "CUST12345678",
      "actual": "CUST123456",
      "passed": false
    }
  ],
  "stdout": "...",
  "stderr": "",
  "exit_code": 1,
  "executed_at": "2026-09-26T11:42:08Z",
  "evidence_id": "ev-probe-001"
}
```

## Rules

- Use exact deployed commits — never HEAD.
- Generate realistic fixtures that exercise the actual failure mode.
- Run outside production — always subprocess isolation.
- The deterministic runtime decides PASS/FAIL, not the LLM.
- Return INCONCLUSIVE if the probe cannot execute cleanly.
- Always persist evidence with a unique probe ID.
