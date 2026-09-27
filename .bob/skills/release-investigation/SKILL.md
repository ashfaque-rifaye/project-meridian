---
name: release-investigation
description: >-
  Use when reconstructing a release across environments, identifying what changed, what is
  actually running, and which dependency combinations lack validation evidence. Activate when
  the user asks about release investigation, divergence investigation, or environment comparison.
---

# Release Investigation Skill

Reconstruct release R-26.9 (or any specified release) across all environments and identify
unvalidated component combinations.

## Step 1 — Load Release Intent

Call `get_release_intent` via MCP with the release ID.

Extract:
- changed components and their target versions
- expected deployment order
- explicit dependencies documented in the change request
- relevant documents (interface docs, release notes)

Record each fact with its evidence source and evidence ID.
Never infer versions from environment state.

## Step 2 — Gather Environment Reality (parallel)

For each environment (DEV, TEST, STAGE, PROD), call `get_environment_snapshot`.

For each component in the business flow, record:
- actual running version
- deployed commit
- deployment timestamp
- artifact/image reference
- config fingerprint
- schema version
- evidence source

Mark any missing or ambiguous facts as INCONCLUSIVE. Do not fill gaps.

## Step 3 — Compare Intent vs Reality

For each environment:
- Compare target versions from release intent against actual running versions.
- Classify each difference:
  - `irrelevant` — config/infra difference with no contract impact
  - `relevant` — version or schema difference on the flow path
  - `contract-affecting` — difference that changes an interface boundary
  - `release-convergence-risk` — running combination never validated together

## Step 4 — Load Validation Memory

Call `get_validation_history` for the affected edges.

For each edge in the business flow, determine:
- VERIFIED — exact combination has passing evidence
- OBSERVED_TOGETHER — co-existed but no compatibility exercise
- EXERCISED — flow crossed the edge without formal verification criteria
- UNTESTED — no evidence
- FAILED — probe failed
- INCONCLUSIVE — insufficient evidence to determine state

## Step 5 — Identify Unvalidated Edges

Call `get_untested_edges` for the target environment and flow.

For each unvalidated edge:
- Record producer version, consumer version, and interface
- Record the timestamp when this combination first appeared in the target environment
- Record the deployment event that created it

## Step 6 — Hand Off to Contract Discovery

For each unvalidated edge, invoke the `implicit-contract-discovery` skill.

## Step 7 — Produce Structured Output

Output:
```json
{
  "release_id": "R-26.9",
  "environment": "prod",
  "changed_components": [],
  "environment_reality": {},
  "validation_summary": {},
  "unvalidated_edges": [],
  "convergence_risk": "HIGH|MEDIUM|LOW|NONE",
  "evidence": []
}
```

## Rules

- Never invent deployment state.
- Always use evidence IDs.
- Separate observed facts from interpretation.
- Preserve INCONCLUSIVE — never silently upgrade to a stronger state.
- Return structured JSON plus concise human-readable findings.
