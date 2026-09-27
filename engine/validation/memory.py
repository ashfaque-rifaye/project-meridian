"""
Validation memory.

Observed together is not the same as validated together. For one exact
(producer version, consumer version) pair on one edge this module separates:

  VERIFIED           a validation run crossed the edge with semantic assertions that passed
  EXERCISED          traffic crossed the edge, but nothing checked the content
  OBSERVED_TOGETHER  both versions were deployed at the same time; no evidence of traffic
  FAILED             a validation run crossed the edge and failed
  NONE               the pair never existed anywhere on the promotion path

Validation runs come from environments/validation-runs.json (test pipelines).
Co-existence windows are computed from deployment history.
"""

from __future__ import annotations

import json
from functools import lru_cache

from engine.domain import flows
from engine.domain.models import DependencyEdge, EdgeEvidence, EvidenceTier
from engine.paths import ENVIRONMENTS
from engine.reconciliation import history


@lru_cache(maxsize=1)
def _runs_doc() -> dict:
    return json.loads((ENVIRONMENTS / "validation-runs.json").read_text(encoding="utf-8"))


def reload() -> None:
    _runs_doc.cache_clear()


def validation_runs() -> list[dict]:
    return sorted(_runs_doc()["runs"], key=lambda r: r["started_at"])


def fixtures() -> list[dict]:
    return _runs_doc().get("fixtures", [])


def _run_summary(run: dict, edge_record: dict) -> dict:
    return {
        "evidence_id": f"{run['run_id']}:{edge_record['edge_id']}",
        "run_id": run["run_id"],
        "environment": run["environment"],
        "release": run.get("release"),
        "suite": run["suite"],
        "method": run["method"],
        "pipeline": run.get("pipeline"),
        "executed_at": run["started_at"],
        "messages": edge_record["messages"],
        "semantic_assertions": edge_record["semantic_assertions"],
        "semantic_assertions_passed": edge_record["semantic_assertions_passed"],
        "technical_checks": edge_record.get("technical_checks", []),
        "fixtures": run.get("fixtures", []),
        "result": run["result"],
        "producer_commit": edge_record.get("producer_commit"),
        "consumer_commit": edge_record.get("consumer_commit"),
    }


def edge_evidence(edge: DependencyEdge, producer_version: str, consumer_version: str,
                  environments: list[str] | None = None) -> EdgeEvidence:
    """Collect every piece of evidence for an exact version pair on an edge."""
    environments = environments or flows.environments()
    verified, exercised, failed = [], [], []
    for run in validation_runs():
        if run["environment"] not in environments:
            continue
        for rec in run["edges"]:
            if (rec["edge_id"] != edge.id or rec["producer_version"] != producer_version
                    or rec["consumer_version"] != consumer_version):
                continue
            summary = _run_summary(run, rec)
            if run["result"] != "PASS":
                failed.append(summary)
            elif rec["semantic_assertions"] > 0 and rec["semantic_assertions_passed"] == rec["semantic_assertions"]:
                verified.append(summary)
            elif rec["messages"] > 0:
                exercised.append(summary)

    observed = []
    for env in environments:
        for window in history.pair_windows(env, edge.producer, edge.consumer, producer_version, consumer_version):
            window["evidence_id"] = f"coexist-{env}-{edge.id}-{producer_version}-{consumer_version}-{window['start'][:16]}"
            observed.append(window)

    if verified:
        tier = EvidenceTier.VERIFIED
    elif failed:
        tier = EvidenceTier.FAILED
    elif exercised:
        tier = EvidenceTier.EXERCISED
    elif observed:
        tier = EvidenceTier.OBSERVED_TOGETHER
    else:
        tier = EvidenceTier.NONE

    return EdgeEvidence(
        edge_id=edge.id,
        producer_version=producer_version,
        consumer_version=consumer_version,
        tier=tier,
        verified=verified,
        exercised=exercised,
        observed=observed,
        failed=failed,
    )


def describe(evidence: EdgeEvidence, target_env: str | None = None) -> str:
    """One-line human description, never stronger than the evidence."""
    if evidence.tier == EvidenceTier.VERIFIED:
        v = evidence.verified[-1]
        return (f"Verified in {v['environment'].upper()} by {v['suite']} "
                f"({v['semantic_assertions']} semantic assertions passed).")
    parts = []
    for e in evidence.exercised:
        parts.append(f"exercised in {e['environment'].upper()} by {e['suite']} "
                     f"({e['messages']} message, 0 semantic assertions)")
    for w in evidence.observed:
        if w["environment"] == target_env and w["ongoing"]:
            continue
        hours = w["duration_seconds"] / 3600
        parts.append(f"observed together in {w['environment'].upper()} for {hours:.1f}h")
    if evidence.failed:
        parts.append(f"failed in {evidence.failed[-1]['environment'].upper()}")
    if not parts:
        return "This exact pair never existed on the promotion path."
    return "Never verified. " + "; ".join(parts).capitalize() + "."


def pair_validated(edge: DependencyEdge, producer_version: str, consumer_version: str) -> bool:
    return edge_evidence(edge, producer_version, consumer_version).tier == EvidenceTier.VERIFIED


def edge_ledger(edge: DependencyEdge) -> list[dict]:
    """Every version pair ever seen on an edge, with its strongest evidence tier."""
    pairs: set[tuple[str, str]] = set()
    for run in validation_runs():
        for rec in run["edges"]:
            if rec["edge_id"] == edge.id:
                pairs.add((rec["producer_version"], rec["consumer_version"]))
    for env in flows.environments():
        for seg in history.segments(env):
            pv, cv = seg.versions.get(edge.producer), seg.versions.get(edge.consumer)
            if pv and cv:
                pairs.add((pv, cv))
    rows = []
    for pv, cv in sorted(pairs):
        ev = edge_evidence(edge, pv, cv)
        rows.append({
            "producer_version": pv, "consumer_version": cv, "tier": ev.tier.value,
            "verified_in": sorted({v["environment"] for v in ev.verified}),
            "exercised_in": sorted({v["environment"] for v in ev.exercised}),
            "observed_in": sorted({w["environment"] for w in ev.observed}),
            "summary": describe(ev),
        })
    return rows
