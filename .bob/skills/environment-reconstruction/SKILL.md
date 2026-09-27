---
name: environment-reconstruction
description: >-
  Use when normalizing actual component versions, deployment times, artifacts, commits,
  configuration fingerprints, and schema state for a target environment. Activate when the
  user asks about what is actually running in an environment or needs an environment snapshot.
---

# Environment Reconstruction Skill

Produce a normalized, evidence-backed snapshot of what is actually running in a target environment.

## Step 1 — Select Target Environment

Identify the target: DEV, TEST, STAGE, or PROD.

## Step 2 — Read Adapter Output

Call `get_environment_snapshot(environment, flow_id)` via MCP.

The adapter returns synthetic fixture data modeled after real infrastructure outputs:
- Kubernetes deployment JSON
- Argo CD application state
- Pipeline metadata
- Flyway migration history
- Legacy deployment inventory

## Step 3 — Normalize Each Component

For each component in the business flow, extract and normalize:

| Field | Source | Notes |
|---|---|---|
| component | adapter | exact name |
| version | adapter | semver or release label |
| commit | adapter | short SHA |
| image/artifact | adapter | digest or artifact ID |
| deployment_time | adapter | ISO 8601 UTC |
| config_fingerprint | adapter | SHA of relevant config |
| schema_version | flyway/migration | migration version |
| runtime_target | adapter | k8s cluster / VM / namespace |
| evidence_id | adapter | unique source reference |

## Step 4 — Preserve Raw Evidence

Attach the raw adapter response as evidence. Do not paraphrase it.

## Step 5 — Handle Missing Data

If any required field is absent:
- Mark the specific field as `INCONCLUSIVE`
- Do not substitute a default value
- Do not attempt to infer from other fields
- Surface the gap explicitly in the output

## Step 6 — Return Normalized Snapshot

```json
{
  "environment": "prod",
  "flow": "order-to-ledger",
  "snapshot_id": "snap-prod-2026-09-26-1142",
  "timestamp": "2026-09-26T11:42:00Z",
  "components": [
    {
      "name": "mq-bridge",
      "version": "3.1",
      "commit": "8f7a91",
      "artifact": "meridian/mq-bridge:3.1",
      "deployed_at": "2026-09-26T11:42:00Z",
      "config_fingerprint": "cf-mqb-31-prod",
      "schema_version": null,
      "runtime_target": "openshift/prod-mq-ns",
      "evidence_id": "ev-prod-mqb-001"
    }
  ],
  "evidence": []
}
```

## Rules

- Read only via MCP adapters — never read infrastructure directly.
- Preserve all timestamps exactly as reported.
- Preserve all evidence IDs.
- Do not "fix" or infer missing data.
- Return INCONCLUSIVE where state cannot be established from available evidence.
