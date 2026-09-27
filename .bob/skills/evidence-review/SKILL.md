---
name: evidence-review
description: >-
  Use when auditing Meridian findings for evidence completeness, contradictions, uncertainty,
  and unsupported causal claims. Activate when reviewing a First Divergence result, validating
  probe evidence, or preparing an evidence packet for presentation.
---

# Evidence Review Skill

Audit Meridian findings to ensure every claim is traceable to concrete evidence.

## Step 1 — Receive Finding

Obtain the proposed finding: a First Divergence result, probe result, or validation state change.

## Step 2 — Check Environment State Evidence

For each component version claimed:
- [ ] Is the version backed by an adapter evidence record?
- [ ] Does the evidence ID exist in `.meridian/` or the validation memory database?
- [ ] Is the deployment timestamp present and plausible?
- [ ] Is the source (kubectl / Argo / deployment inventory) identified?

If any check fails: downgrade to INCONCLUSIVE, do not proceed.

## Step 3 — Check Validation Evidence

For each claimed validation state:
- [ ] VERIFIED requires an actual passing validation record with fixture ID and result.
- [ ] EXERCISED requires a record showing the flow actually crossed the edge.
- [ ] OBSERVED_TOGETHER only requires co-existence evidence — is it labeled correctly?
- [ ] UNTESTED means no evidence exists — confirm, do not fill the gap.
- [ ] FAILED requires a deterministic probe result, not an LLM opinion.

## Step 4 — Check Probe Evidence

If a probe result is claimed:
- [ ] Does the probe_id exist in `.meridian/runs/`?
- [ ] Do the probe commits match the actual deployed versions?
- [ ] Were assertions evaluated by deterministic code, not by LLM judgment?
- [ ] Is stdout/stderr captured?
- [ ] Is the fixture hash recorded?

## Step 5 — Check Causal Language

Scan for prohibited phrases:
- "root cause" → replace with "First Demonstrated Divergence"
- "caused the outage" → replace with "is the earliest boundary where probe failed"
- "guaranteed" → replace with "probe demonstrated"
- "definitely" → replace with "evidence shows" or "probe confirmed"

Flag any use of these terms.

## Step 6 — Detect Contradictions

Check for:
- A component marked VERIFIED but with no passing validation record
- A probe marked PASS but with a failed assertion in the results
- Two different versions claimed for the same component in the same environment
- A deployment timestamp that precedes the component's first known build

## Step 7 — Produce Audit Report

```json
{
  "finding_id": "...",
  "audit_result": "VERIFIED | FAILED | INCONCLUSIVE | NEEDS_HUMAN",
  "checks_passed": [],
  "issues": [],
  "downgraded_states": [],
  "prohibited_language": [],
  "recommendation": "..."
}
```

## Permitted Verdict Changes

- May downgrade VERIFIED → INCONCLUSIVE if evidence is missing
- May downgrade FAILED → INCONCLUSIVE if probe result is absent
- May flag NEEDS_HUMAN if contradictions cannot be resolved
- May NEVER override a deterministic probe result (PASS stays PASS, FAIL stays FAIL)
- May NEVER upgrade INCONCLUSIVE to VERIFIED without new evidence

## Rules

- Every claim needs evidence with an ID.
- Separate observed state from inferred state.
- Never call First Divergence "root cause."
- Preserve uncertainty — hidden uncertainty is worse than visible uncertainty.
- Deterministic probe output is final — do not override it.
