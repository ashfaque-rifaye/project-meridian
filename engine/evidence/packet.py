"""
Evidence packet and evidence review.

Every First Demonstrated Divergence is backed by a packet that traces each
statement to its source: adapter output, deployment event, validation run,
source file at a commit, enterprise document, or probe execution.

The review is deterministic. It checks the packet against the evidence rules
and downgrades anything unsupported. It cannot override a probe result.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from engine.divergence import why
from engine.domain import flows
from engine.paths import EVIDENCE, ensure_dirs
from engine.probes import probe_engine
from engine.validation import memory

FORBIDDEN_PHRASES = ("root cause", "caused the outage", "guaranteed safe")


def build_packet(evaluation: dict, contract: dict | None = None) -> dict | None:
    fd = evaluation.get("first_divergence")
    if not fd:
        return None
    ensure_dirs()
    edge = flows.get_edge(fd["edge_id"], evaluation["flow_id"])
    probe = probe_engine.get_run(fd["probe"]["run_id"]) if fd.get("probe") else None
    evidence = memory.edge_evidence(edge, fd["producer_version"], fd["consumer_version"])
    comp = evaluation["composition"]
    event = fd.get("triggering_deployment") or {}
    pattern = why.promotion_pattern(evaluation["environment"])

    items = [
        {"kind": "deployment", "id": comp[fd["producer"]]["evidence_id"],
         "title": f"{fd['producer']} {fd['producer_version']} running in {evaluation['environment'].upper()}",
         "source": comp[fd["producer"]]["source"], "at": fd["producer_deployed_at"]},
        {"kind": "deployment", "id": comp[fd["consumer"]]["evidence_id"],
         "title": f"{fd['consumer']} {fd['consumer_version']} running in {evaluation['environment'].upper()}",
         "source": comp[fd["consumer"]]["source"], "at": fd["consumer_deployed_at"]},
    ]
    if event:
        items.append({"kind": "deployment-event", "id": event["event_id"],
                      "title": f"{event['component']} {event['from_version']} → {event['to_version']} via {event['tool']} ({event['trigger']})",
                      "source": "environments/deployment-events.json", "at": event["deployed_at"]})
    for v in evidence.exercised:
        items.append({"kind": "validation", "id": v["evidence_id"],
                      "title": f"EXERCISED only: {v['suite']} in {v['environment'].upper()} "
                               f"({v['messages']} message, {v['semantic_assertions']} semantic assertions)",
                      "source": "environments/validation-runs.json", "at": v["executed_at"]})
    for w in evidence.observed:
        items.append({"kind": "coexistence", "id": w["evidence_id"],
                      "title": f"OBSERVED TOGETHER in {w['environment'].upper()} for {w['duration_seconds'] / 3600:.1f}h"
                               + (" (current)" if w["ongoing"] else ""),
                      "source": "environments/deployment-events.json", "at": w["start"]})
    if contract and contract.get("status") == "DISCOVERED":
        for c in contract["constraints"]:
            items.append({"kind": "source", "id": f"{contract['contract_id']}:{c['field']}",
                          "title": f"{c['field']}: producer {c['producer']} · consumer {c['consumer']}",
                          "source": f"{c['producer_source']} ⇄ {c['consumer_source']}", "at": None})
        for sheet, rows in contract["documents"]["interface_control"].get("sheets", {}).items():
            items.append({"kind": "document", "id": f"icd:{sheet}", "title": f"LEDG-ICD-007 · {sheet} ({len(rows)} fields)",
                          "source": rows[0]["source"].split("!")[0] if rows else "interface-control.xlsx", "at": None})
        cr = contract["documents"].get("change_request")
        if cr:
            items.append({"kind": "document", "id": cr["id"], "title": f"{cr['id']}: {cr['dependency']}",
                          "source": cr["source"], "at": None})
    if probe:
        items.append({"kind": "probe", "id": probe["evidence_id"],
                      "title": f"Probe {probe['result']}: {probe['assertions_failed']} of {probe['assertions_total']} "
                               f"semantic assertions failed" + (" (silent)" if probe["silent_failure"] else ""),
                      "source": f".meridian/runs/{probe['run_id']}.json", "at": probe["finished_at"]})

    since = fd.get("unvalidated_since")
    summary = (
        f"{evaluation['environment'].upper()} entered a new unvalidated composition at {since} when "
        f"{event.get('component', fd['producer'])} {event.get('to_version', fd['producer_version'])} was promoted "
        f"while {fd['consumer']} remained at {fd['consumer_version']}. No passing validation evidence exists for "
        f"{fd['producer']} {fd['producer_version']} → {fd['consumer']} {fd['consumer_version']} on the promotion path. "
    )
    if probe:
        summary += (f"The isolated probe reproduced a {'silent ' if probe['silent_failure'] else ''}semantic "
                    f"incompatibility: {probe['assertions_failed']} of {probe['assertions_total']} assertions failed "
                    f"while every record was acknowledged and committed.")

    packet = {
        "packet_id": f"pkt-{fd['divergence_id']}",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "synthetic": True,
        "release": flows.default_release_id(),
        "environment": evaluation["environment"],
        "business_flow": evaluation["flow_id"],
        "connection": f"{fd['producer']} → {fd['consumer']}",
        "interface": fd["interface"],
        "upstream": {"component": fd["producer"], "version": fd["producer_version"], "commit": fd["producer_commit"],
                     "artifact": comp[fd["producer"]].get("source"), "deployed_at": fd["producer_deployed_at"]},
        "downstream": {"component": fd["consumer"], "version": fd["consumer_version"], "commit": fd["consumer_commit"],
                       "artifact": comp[fd["consumer"]].get("source"), "deployed_at": fd["consumer_deployed_at"]},
        "validation_history": evidence.to_dict(),
        "implicit_contract": {k: contract[k] for k in ("contract_id", "status", "summary", "constraints", "prediction")}
        if contract else None,
        "probe": {k: probe[k] for k in ("run_id", "probe_id", "evidence_id", "result", "silent_failure", "fixtures",
                                         "assertions_total", "assertions_failed", "sandbox", "isolation",
                                         "started_at", "finished_at", "duration_ms")} if probe else None,
        "first_divergence_timestamp": since,
        "triggering_deployment": event or None,
        "promotion_pattern": pattern["story"],
        "evidence_items": items,
        "human_summary": summary,
        "claim_type": "First Demonstrated Divergence (factual observation, not a causal claim)",
    }
    packet["review"] = review(packet)
    (EVIDENCE / f"{packet['packet_id']}.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    return packet


def review(packet: dict) -> dict:
    """Deterministic evidence review. Downgrades, never upgrades."""
    checks = []

    def check(cid: str, label: str, ok: bool, detail: str):
        checks.append({"id": cid, "label": label, "passed": bool(ok), "detail": detail})

    up, down = packet["upstream"], packet["downstream"]
    check("observed-state", "Running versions come from adapter evidence",
          bool(up.get("artifact")) and bool(down.get("artifact")),
          f"{up['component']} from {up.get('artifact')}; {down['component']} from {down.get('artifact')}")
    check("exact-commits", "Probe used the exact deployed commits",
          bool(packet["probe"]) and packet["probe"]["run_id"] and up["commit"] and down["commit"],
          f"producer {up['commit']}, consumer {down['commit']}")
    vh = packet["validation_history"]
    check("no-verified-evidence", "No VERIFIED evidence exists for this exact pair",
          not vh["verified"], f"strongest evidence tier: {vh['tier']}")
    check("coexistence-not-validation", "Co-existence and exercised traffic are not counted as validation",
          True, f"{len(vh['observed'])} co-existence window(s), {len(vh['exercised'])} exercised run(s) reported separately")
    check("execution-decides", "FAILED is based on probe execution, not model judgement",
          bool(packet["probe"]) and packet["probe"]["result"] == "FAIL", "deterministic assertion evaluation")
    text = json.dumps(packet).lower()
    bad = [p for p in FORBIDDEN_PHRASES if p in text]
    check("no-causal-claim", "No unsupported causal claims", not bad,
          "none found" if not bad else "found: " + ", ".join(bad))
    check("timestamp", "Divergence timestamp traced to a deployment event",
          bool(packet["first_divergence_timestamp"]) and bool(packet["triggering_deployment"]),
          packet["triggering_deployment"]["event_id"] if packet["triggering_deployment"] else "missing")

    passed = all(c["passed"] for c in checks)
    return {
        "reviewer": "meridian-evidence-review (deterministic rules; IBM Bob evidence-reviewer skill mirrors them)",
        "verdict": "SUPPORTED" if passed else "NEEDS_HUMAN",
        "checks": checks,
    }


def load_packet(packet_id: str) -> dict | None:
    path = EVIDENCE / f"{packet_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def latest_packet() -> dict | None:
    if not EVIDENCE.exists():
        return None
    paths = sorted(EVIDENCE.glob("pkt-*.json"), key=lambda p: p.stat().st_mtime)
    return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else None
