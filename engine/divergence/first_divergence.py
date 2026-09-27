"""
First Demonstrated Divergence.

Given a business flow and a composition (the versions running in an
environment, or a hypothetical one during a promotion rehearsal):

  1. resolve the running version pair on every edge, in flow order
  2. if validation memory has VERIFIED evidence for the exact pair, continue
  3. otherwise the edge is UNTESTED; an isolated probe may be run for it
  4. probe FAIL -> FAILED, PASS -> VERIFIED_BY_PROBE, not executable -> INCONCLUSIVE
  5. the earliest edge that is both unvalidated and FAILED is the
     First Demonstrated Divergence
  6. record when the environment entered that exact combination and which
     deployment created it

This is a factual observation, not a causal claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.contracts import discovery
from engine.domain import flows
from engine.domain.models import DependencyEdge, EdgeEvaluation, EdgeState, EvidenceTier, Verdict
from engine.probes import probe_engine, workspace
from engine.reconciliation import history
from engine.reconciliation.reconciler import EnvironmentReality, reconstruct_environment
from engine.validation import memory

# Runtime configuration keys that change an interface's wire format.
FORMAT_CONFIG = {"mq-bridge": ("env.LEDGER_RECORD_LAYOUT", "ledger.recordLayout")}


@dataclass
class Member:
    """One component in a composition being evaluated."""

    version: str | None
    commit: str | None
    config: dict
    label: str | None = None
    deployed_at: str | None = None
    evidence_id: str | None = None


def observed_config(reality: EnvironmentReality, component: str) -> dict:
    if component not in FORMAT_CONFIG:
        return {}
    attribute, key = FORMAT_CONFIG[component]
    for workload in reality.workloads:
        if workload.component == component and attribute in workload.attributes:
            value = workload.attributes[attribute]
            # v7 is the producer default; only non-default layouts change behaviour.
            return {} if value in ("", "v7") else {key: value}
    return {}


def members_from_reality(reality: EnvironmentReality) -> dict[str, Member]:
    out = {}
    for comp, obs in reality.components.items():
        out[comp] = Member(obs.version, obs.commit, observed_config(reality, comp), obs.version,
                           obs.deployed_at, obs.evidence_id)
    return out


def _probe_for(edge: DependencyEdge, p: Member, c: Member, run_probes: bool) -> tuple[dict | None, dict | None]:
    """Return (probe_result, contract) for an unvalidated edge."""
    result = probe_engine.latest_result(edge.id, p.commit, c.commit, p.config)
    contract = None
    if result is None and run_probes:
        contract = discovery.discover(edge, p.version, p.commit, c.version, c.commit, p.config)
        spec = contract.get("probe_spec")
        if spec:
            if p.label and p.label != p.version:
                spec["producer"]["label"] = p.label
            result = probe_engine.run_probe(spec)
    return result, contract


def evaluate_edge(edge: DependencyEdge, p: Member | None, c: Member | None, environment: str | None,
                  run_probes: bool = False) -> tuple[EdgeEvaluation, dict | None]:
    common = dict(
        edge_id=edge.id, order=edge.order, producer=edge.producer, consumer=edge.consumer,
        producer_version=p.version if p else None, consumer_version=c.version if c else None,
        producer_commit=p.commit if p else None, consumer_commit=c.commit if c else None,
        interface=edge.interface, contract=edge.contract,
    )
    if not p or not c or not p.version or not c.version:
        missing = edge.producer if not p or not p.version else edge.consumer
        return EdgeEvaluation(**common, state=EdgeState.INCONCLUSIVE, evidence=None, probe=None,
                              reason=f"Running version of {missing} could not be established."), None

    evidence = memory.edge_evidence(edge, p.version, c.version)
    if evidence.tier == EvidenceTier.VERIFIED:
        return EdgeEvaluation(**common, state=EdgeState.VERIFIED, evidence=evidence, probe=None,
                              reason=memory.describe(evidence, environment)), None

    if not edge.probe_type:
        return EdgeEvaluation(
            **common, state=EdgeState.NEEDS_HUMAN, evidence=evidence, probe=None,
            reason=(memory.describe(evidence, environment) + f" No executable probe exists for "
                    f"{edge.interface} ({edge.contract['kind']}); Meridian will not guess."),
        ), None

    if not p.commit or not c.commit:
        return EdgeEvaluation(**common, state=EdgeState.INCONCLUSIVE, evidence=evidence, probe=None,
                              reason="Deployed commit unknown; the probe cannot use the exact code."), None

    probe, contract = _probe_for(edge, p, c, run_probes)
    if probe is None:
        state, suffix = EdgeState.UNTESTED, " Waiting for a compatibility test in the sandbox."
    elif probe["result"] == "FAIL":
        state, suffix = EdgeState.FAILED, (" The sandbox compatibility test FAILED"
                                           + (" without raising an error (systems green, saved data wrong)." if probe["silent_failure"] else "."))
    elif probe["result"] == "PASS":
        state, suffix = EdgeState.VERIFIED_BY_PROBE, " The sandbox test passed, but this pair has still not been tested in any environment."
    else:
        state, suffix = EdgeState.INCONCLUSIVE, " The test could not tell whether the versions are compatible."
    probe_summary = None
    if probe:
        probe_summary = {k: probe[k] for k in ("run_id", "probe_id", "evidence_id", "result", "silent_failure",
                                                "assertions_total", "assertions_failed", "held", "finished_at",
                                                "duration_ms")}
        probe_summary["producer_config"] = probe["producer"].get("config") or {}
        probe_summary["producer_label"] = probe["producer"].get("label")
    return EdgeEvaluation(**common, state=state, evidence=evidence, probe=probe_summary,
                          reason=memory.describe(evidence, environment) + suffix), contract


def evaluate_composition(environment: str, members: dict[str, Member], run_probes: bool = False,
                         flow_id: str | None = None, track_history: bool = True) -> dict:
    flow_id = flow_id or flows.default_flow_id()
    edges: list[EdgeEvaluation] = []
    contracts: dict[str, dict] = {}
    for edge in flows.get_edges(flow_id):
        p, c = members.get(edge.producer), members.get(edge.consumer)
        evaluation, contract = evaluate_edge(edge, p, c, environment, run_probes)
        if track_history and p and c and p.version and c.version:
            window = history.combination_created(environment, edge.producer, edge.consumer, p.version, c.version)
            if window:
                evaluation.combination_since = window["start"]
                evaluation.created_by_event = window.get("started_by")
        if contract:
            contracts[edge.id] = contract
        edges.append(evaluation)

    unvalidated = [e for e in edges if e.state != EdgeState.VERIFIED]
    first = next((e for e in edges if e.state == EdgeState.FAILED), None)
    if first:
        verdict = Verdict.DIVERGED
    elif not unvalidated:
        verdict = Verdict.CONVERGED
    else:
        verdict = Verdict.UNVALIDATED

    counts = {s.value: sum(1 for e in edges if e.state == s) for s in EdgeState}
    return {
        "environment": environment,
        "flow_id": flow_id,
        "verdict": verdict.value,
        "edges": [e.to_dict() for e in edges],
        "counts": counts,
        "unvalidated_edges": [e.edge_id for e in unvalidated],
        "first_divergence_edge": first.edge_id if first else None,
        "contracts": contracts,
    }


def evaluate_environment(environment: str, run_probes: bool = False, flow_id: str | None = None) -> dict:
    reality = reconstruct_environment(environment, flow_id)
    members = members_from_reality(reality)
    result = evaluate_composition(environment, members, run_probes, flow_id)
    result["snapshot_id"] = reality.snapshot_id
    result["collected_at"] = reality.collected_at
    result["composition"] = {
        comp: {
            "version": m.version, "commit": m.commit, "deployed_at": m.deployed_at, "config": m.config,
            "evidence_id": m.evidence_id,
            "platform": reality.components[comp].platform, "location": reality.components[comp].location,
            "health": reality.components[comp].health, "source": reality.components[comp].source,
        } for comp, m in members.items()
    }
    result["missing"] = reality.missing
    result["first_divergence"] = first_divergence_detail(result, reality)
    return result


def first_divergence_detail(evaluation: dict, reality: EnvironmentReality | None = None) -> dict | None:
    edge_id = evaluation.get("first_divergence_edge")
    if not edge_id:
        return None
    edge = next(e for e in evaluation["edges"] if e["edge_id"] == edge_id)
    comp = evaluation.get("composition", {})
    p, c = comp.get(edge["producer"], {}), comp.get(edge["consumer"], {})
    event = edge.get("created_by_event")
    return {
        "divergence_id": f"fdd-{evaluation['environment']}-{edge_id}-{edge['producer_version']}-{edge['consumer_version']}",
        "environment": evaluation["environment"],
        "flow_id": evaluation["flow_id"],
        "edge_id": edge_id,
        "interface": edge["interface"],
        "producer": edge["producer"], "producer_version": edge["producer_version"],
        "producer_commit": edge["producer_commit"], "producer_deployed_at": p.get("deployed_at"),
        "consumer": edge["consumer"], "consumer_version": edge["consumer_version"],
        "consumer_commit": edge["consumer_commit"], "consumer_deployed_at": c.get("deployed_at"),
        "unvalidated_since": edge.get("combination_since"),
        "triggering_deployment": event,
        "probe": edge.get("probe"),
        "reason": edge["reason"],
        "evidence_tier": (edge.get("evidence") or {}).get("tier"),
    }


def resolve_commit(component: str, version: str) -> str | None:
    return workspace.commit_for(component, version)
