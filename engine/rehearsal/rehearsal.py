"""
Counterfactual promotion rehearsal.

REHEARSE step: "See what this promotion creates before you create it."

    current environment  +  proposed change(s)  =  predicted composition

The predicted composition is evaluated exactly like a real one: validation
memory first, then isolated probes for every unvalidated boundary. Nothing is
deployed. Nothing outside the sandbox is touched.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from engine.divergence.first_divergence import (
    Member, evaluate_composition, members_from_reality, resolve_commit,
)
from engine.domain import flows
from engine.paths import REHEARSALS, ensure_dirs
from engine.reconciliation.reconciler import reconstruct_environment


def rehearse(environment: str, changes: list[dict], run_probes: bool = True,
             flow_id: str | None = None, title: str | None = None) -> dict:
    """
    changes: [{"component": "mq-bridge", "version": "3.1"},
              {"component": "mq-bridge", "version": "3.1.1-compat", "commit": "abc1234",
               "config": {"ledger.recordLayout": "v6-compat"}}]
    """
    ensure_dirs()
    flow_id = flow_id or flows.default_flow_id()
    reality = reconstruct_environment(environment, flow_id)
    current = members_from_reality(reality)
    predicted = {k: Member(m.version, m.commit, dict(m.config), m.label, m.deployed_at, m.evidence_id)
                 for k, m in current.items()}

    applied = []
    for change in changes:
        comp = change["component"]
        before = current.get(comp)
        commit = change.get("commit") or resolve_commit(comp, change["version"])
        predicted[comp] = Member(
            version=change.get("base_version") or change["version"],
            commit=commit,
            config=change.get("config", before.config if before else {}),
            label=change.get("label") or change["version"],
        )
        applied.append({
            "component": comp,
            "from_version": before.version if before else None,
            "to_version": change.get("label") or change["version"],
            "commit": commit,
            "config": predicted[comp].config,
            "resolved": commit is not None,
        })

    evaluation = evaluate_composition(environment, predicted, run_probes, flow_id, track_history=False)
    before_eval = evaluate_composition(environment, current, False, flow_id, track_history=False)

    changed = {c["component"] for c in changes}
    affected = [e for e in evaluation["edges"] if e["producer"] in changed or e["consumer"] in changed]
    newly_unvalidated = [
        e["edge_id"] for e in evaluation["edges"]
        if e["state"] != "VERIFIED"
        and next(b for b in before_eval["edges"] if b["edge_id"] == e["edge_id"])["state"] == "VERIFIED"
    ]

    verdict = evaluation["verdict"]
    first = evaluation["first_divergence_edge"]
    if verdict == "CONVERGED":
        headline = "Safe: every connection in the flow has a passing test for these versions."
    elif verdict == "DIVERGED":
        edge = next(e for e in evaluation["edges"] if e["edge_id"] == first)
        headline = (f"Would put untested versions live, and the sandbox test fails. Failing connection: "
                    f"{edge['producer']} {edge['producer_version']} → {edge['consumer']} {edge['consumer_version']}.")
    else:
        pending = [e for e in evaluation["edges"] if e["state"] != "VERIFIED"]
        kinds = sorted({e["state"] for e in pending})
        headline = (f"Not tested: {len(pending)} connection(s) have no passing test "
                    f"({', '.join(kinds)}). No failure found yet, but none ruled out.")

    rehearsal_id = "reh-" + hashlib.sha1(json.dumps([environment, applied], sort_keys=True).encode()).hexdigest()[:10]
    result = {
        "rehearsal_id": rehearsal_id,
        "title": title,
        "environment": environment,
        "flow_id": flow_id,
        "executed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deployed_anything": False,
        "current_composition": {k: m.version for k, m in current.items()},
        "predicted_composition": {k: (m.label or m.version) for k, m in predicted.items()},
        "changes": applied,
        "verdict": verdict,
        "headline": headline,
        "edges": evaluation["edges"],
        "affected_edges": [e["edge_id"] for e in affected],
        "newly_unvalidated": newly_unvalidated,
        "counts": evaluation["counts"],
        "first_divergence_edge": first,
        "matches_validated_release": verdict == "CONVERGED",
    }
    (REHEARSALS / f"{rehearsal_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
