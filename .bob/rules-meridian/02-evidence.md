# Meridian Evidence Rules

Every finding must be traceable. These rules govern how Bob handles evidence.

## Evidence States

Use exactly these states — no others:

| State | Meaning | Requires |
|---|---|---|
| `VERIFIED` | Exact combination has passing evidence | Validation record with passing result |
| `OBSERVED_TOGETHER` | Co-existed but not exercised | Deployment overlap evidence |
| `EXERCISED` | Flow crossed the edge without full verification | Exercise log entry |
| `UNTESTED` | No evidence exists | Confirmed absence of records |
| `FAILED` | Probe demonstrated failure | Deterministic probe result |
| `INCONCLUSIVE` | Cannot establish state from available evidence | Any gap |

## Rules

1. **Never invent state.** If no evidence record exists, the state is INCONCLUSIVE or UNTESTED.
2. **Never upgrade silently.** INCONCLUSIVE must remain visible. Never convert it to VERIFIED.
3. **Always include evidence IDs.** Every finding references at least one evidence ID.
4. **Separate layers:** Observed co-existence ≠ Exercised integration ≠ Verified compatibility.
5. **Deterministic probe results are final.** A probe FAIL cannot be overridden by LLM opinion.
6. **Never claim "root cause."** Use "First Demonstrated Divergence" — it is a factual observation, not a causal claim.
7. **Uncertainty is honest.** A visible INCONCLUSIVE is better than a hidden gap.
8. **Probe assertions must be code-evaluated.** Not natural language comparisons.

## Evidence Packet Requirements

Every First Demonstrated Divergence must include:
- release ID
- environment
- business flow
- connection (upstream → downstream)
- upstream: version, commit, artifact, deploy time
- downstream: version, commit, artifact, deploy time
- validation history for this pair
- implicit contract evidence (source + document references)
- probe ID, input, output, result
- first-divergence timestamp
- triggering deployment event
