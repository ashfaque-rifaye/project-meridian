"""Read-mostly endpoints: release, flow, environments, timeline, edges, drift, evidence."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from engine.contracts import discovery
from engine.divergence import why
from engine.divergence.first_divergence import evaluate_environment, members_from_reality
from engine.domain import flows
from engine.drift.relevance import relevance
from engine.evidence import packet as packets
from engine.paths import DOCUMENTS
from engine.probes import probe_engine, workspace
from engine.reconciliation import history
from engine.reconciliation.reconciler import parse_ts, reconstruct_environment
from engine.rehearsal.rehearsal import rehearse
from engine.validation import memory

router = APIRouter()


def _duration(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    return int((parse_ts(end) - parse_ts(start)).total_seconds())


def _env_summary(env: str) -> dict:
    ev = evaluate_environment(env)
    return {
        "environment": env,
        "verdict": ev["verdict"],
        "counts": ev["counts"],
        "snapshot_id": ev["snapshot_id"],
        "collected_at": ev["collected_at"],
        "first_divergence": ev["first_divergence"],
        "unvalidated_edges": ev["unvalidated_edges"],
        "composition": {k: v["version"] for k, v in ev["composition"].items()},
        "health": {k: v["health"] for k, v in ev["composition"].items()},
    }


@router.get("/overview")
def overview():
    release = flows.get_release()
    flow = flows.get_flow()
    envs = [_env_summary(e) for e in flows.environments()]
    prod = next(e for e in envs if e["environment"] == "prod")
    now = flows.snapshot_time()
    scheduled = history.scheduled_changes("prod")
    unvalidated_since = None
    evaluation = evaluate_environment("prod")
    for edge in evaluation["edges"]:
        if edge["state"] != "VERIFIED" and edge.get("combination_since"):
            unvalidated_since = min(filter(None, [unvalidated_since, edge["combination_since"]]))
    reference = "stage"
    stage_versions = next(e for e in envs if e["environment"] == reference)["composition"]
    nobody_tested = [
        {"component": c, "version": v, "matches_validated": stage_versions.get(c) == v,
         "validated_version": stage_versions.get(c)}
        for c, v in prod["composition"].items()
    ]
    order = [c["id"] for c in flow["components"]]
    nobody_tested.sort(key=lambda r: order.index(r["component"]))
    latest = packets.latest_packet()
    return {
        "release": release,
        "flow": {"id": flow["id"], "name": flow["name"], "description": flow["description"],
                 "components": len(flow["components"]), "edges": len(flow["edges"])},
        "organization": flows.catalog()["organization"],
        "snapshot_time": now,
        "environments": envs,
        "prod": {
            "verdict": prod["verdict"],
            "unvalidated_since": unvalidated_since,
            "exposure_seconds": _duration(unvalidated_since, now),
            "first_divergence": prod["first_divergence"],
            "untested": evaluation["unvalidated_edges"],
            "all_healthy": all(h.startswith("HEALTHY") for h in prod["health"].values()),
            "pipelines_green": True,
        },
        "system_nobody_tested": nobody_tested,
        "scheduled_changes": scheduled,
        "next_window_in_seconds": _duration(now, scheduled[0]["window_start"]) if scheduled else None,
        "latest_packet_id": latest["packet_id"] if latest else None,
        "probe_runs": len(probe_engine.all_runs()),
    }


@router.get("/release")
def release_detail():
    release = flows.get_release()
    return {
        "release": release,
        "change_request": discovery.change_request(),
        "release_notes": json.loads((DOCUMENTS / "release-notes-data.json").read_text(encoding="utf-8")),
        "pattern": why.promotion_pattern("prod"),
    }


@router.get("/flow")
def flow_detail():
    return flows.get_flow()


@router.get("/environments/{env}")
def environment_detail(env: str):
    if env not in flows.environments():
        raise HTTPException(404, f"Unknown environment {env}")
    ev = evaluate_environment(env)
    reality = reconstruct_environment(env)
    ev["sources"] = reality.sources
    ev["workload_count"] = len(reality.workloads)
    ev.pop("contracts", None)
    return ev


@router.get("/matrix")
def matrix():
    envs = flows.environments()
    evaluations = {e: evaluate_environment(e) for e in envs}
    stage = evaluations["stage"]["composition"]
    components = []
    for comp in flows.get_components():
        row = {"component": comp, "cells": {}}
        for e in envs:
            c = evaluations[e]["composition"].get(comp["id"])
            row["cells"][e] = c and {
                "version": c["version"], "commit": c["commit"], "deployed_at": c["deployed_at"],
                "health": c["health"], "location": c["location"], "evidence_id": c["evidence_id"],
                "differs_from_validated": c["version"] != stage.get(comp["id"], {}).get("version"),
                "release_target": flows.get_release()["target"].get(comp["id"]),
            }
        components.append(row)
    edges = []
    for edge in flows.get_edges():
        row = {"edge": edge.to_dict(), "cells": {}}
        for e in envs:
            ev = next(x for x in evaluations[e]["edges"] if x["edge_id"] == edge.id)
            row["cells"][e] = {k: ev[k] for k in ("state", "producer_version", "consumer_version", "reason",
                                                  "combination_since", "probe")}
            row["cells"][e]["tier"] = (ev.get("evidence") or {}).get("tier")
        edges.append(row)
    return {"environments": envs, "components": components, "edges": edges,
            "verdicts": {e: evaluations[e]["verdict"] for e in envs}}


def _segment_status(seg) -> dict:
    unvalidated = []
    for edge in flows.get_edges():
        pv, cv = seg.versions.get(edge.producer), seg.versions.get(edge.consumer)
        if pv and cv and not memory.pair_validated(edge, pv, cv):
            unvalidated.append({"edge_id": edge.id, "pair": [pv, cv]})
    return {"validated": not unvalidated, "unvalidated": unvalidated}


@router.get("/timeline")
def timeline():
    lanes = []
    for env in flows.environments():
        segs = []
        for seg in history.segments(env):
            item = seg.to_dict()
            item.update(_segment_status(seg))
            segs.append(item)
        lanes.append({"environment": env, "segments": segs, "events": history.events(env)})
    runs = [{k: r[k] for k in ("run_id", "environment", "release", "suite", "method", "started_at", "finished_at",
                                "result", "messages")} | {"semantic": any(e["semantic_assertions"] for e in r["edges"])}
            for r in memory.validation_runs()]
    evaluation = evaluate_environment("prod")
    return {
        "snapshot_time": flows.snapshot_time(),
        "window_start": "2026-09-21T12:00:00Z",
        "window_end": "2026-09-27T06:00:00Z",
        "lanes": lanes,
        "validation_runs": runs,
        "scheduled_changes": history.scheduled_changes(),
        "divergence": evaluation["first_divergence"],
        "pattern": why.promotion_pattern("prod"),
    }


@router.get("/edges/{edge_id}")
def edge_detail(edge_id: str, env: str = "prod"):
    try:
        edge = flows.get_edge(edge_id)
    except KeyError:
        raise HTTPException(404, f"Unknown edge {edge_id}")
    ev = evaluate_environment(env)
    evaluation = next(e for e in ev["edges"] if e["edge_id"] == edge_id)
    run = probe_engine.get_run(evaluation["probe"]["run_id"]) if evaluation.get("probe") else None
    contract = None
    if evaluation["state"] != "VERIFIED" and evaluation["producer_commit"] and evaluation["consumer_commit"]:
        reality = reconstruct_environment(env)
        p = members_from_reality(reality)[edge.producer]
        contract = discovery.discover(edge, evaluation["producer_version"], evaluation["producer_commit"],
                                      evaluation["consumer_version"], evaluation["consumer_commit"], p.config)
    return {
        "edge": edge.to_dict(),
        "environment": env,
        "evaluation": evaluation,
        "ledger": memory.edge_ledger(edge),
        "contract": contract,
        "probe_run": run,
        "components": {edge.producer: flows.component_meta(edge.producer), edge.consumer: flows.component_meta(edge.consumer)},
    }


@router.get("/drift")
def drift(reference: str = "stage", target: str = "prod"):
    return relevance(reference, target)


@router.get("/divergence")
def divergence(env: str = "prod"):
    ev = evaluate_environment(env)
    fd = ev["first_divergence"]
    packet = packets.latest_packet() if fd else None
    if packet and packet["environment"] != env:
        packet = None
    run = probe_engine.get_run(fd["probe"]["run_id"]) if fd and fd.get("probe") else None
    contract = None
    if fd:
        edge = flows.get_edge(fd["edge_id"])
        p = members_from_reality(reconstruct_environment(env))[edge.producer]
        contract = discovery.discover(edge, fd["producer_version"], fd["producer_commit"],
                                      fd["consumer_version"], fd["consumer_commit"], p.config)
    return {
        "environment": env,
        "verdict": ev["verdict"],
        "first_divergence": fd,
        "unvalidated_edges": ev["unvalidated_edges"],
        "edges": ev["edges"],
        "packet": packet,
        "probe_run": run,
        "contract": contract,
        "pattern": why.promotion_pattern(env),
        "composition": ev["composition"],
    }


@router.get("/evidence/latest")
def evidence_latest():
    packet = packets.latest_packet()
    if not packet:
        raise HTTPException(404, "No evidence packet yet. Run an investigation.")
    return packet


@router.get("/evidence/{packet_id}")
def evidence(packet_id: str):
    packet = packets.load_packet(packet_id)
    if not packet:
        raise HTTPException(404, f"Unknown evidence packet {packet_id}")
    return packet


class ProbeRequest(BaseModel):
    edge_id: str
    environment: str = "prod"


@router.post("/probes/run")
def run_probe(req: ProbeRequest):
    edge = flows.get_edge(req.edge_id)
    if not edge.probe_type:
        raise HTTPException(409, f"No executable probe exists for {edge.interface}.")
    reality = reconstruct_environment(req.environment)
    members = members_from_reality(reality)
    p, c = members[edge.producer], members[edge.consumer]
    contract = discovery.discover(edge, p.version, p.commit, c.version, c.commit, p.config)
    if not contract.get("probe_spec"):
        raise HTTPException(409, contract["summary"])
    return probe_engine.run_probe(contract["probe_spec"])


@router.get("/probes/runs")
def probe_runs():
    return [{k: r[k] for k in ("run_id", "probe_id", "edge_id", "result", "silent_failure", "finished_at",
                               "duration_ms", "assertions_total", "assertions_failed", "held")}
            | {"producer": f"{r['producer']['component']} {r['producer'].get('label', r['producer']['version'])}",
               "consumer": f"{r['consumer']['component']} {r['consumer']['version']}",
               "config": r["producer"].get("config") or {}}
            for r in reversed(probe_engine.all_runs())]


@router.get("/probes/runs/{run_id}")
def probe_run(run_id: str):
    run = probe_engine.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Unknown probe run {run_id}")
    return run


class RehearsalRequest(BaseModel):
    environment: str = "prod"
    changes: list[dict]
    title: str | None = None


REHEARSAL_PRESETS = [
    {"id": "as-happened", "title": "Promote mq-bridge 3.1 to PROD", "subtitle": "What Friday 11:42 actually did",
     "environment": "prod", "changes": [{"component": "mq-bridge", "version": "3.1"}]},
    {"id": "cr-4471", "title": "Execute CR-4471 now", "subtitle": "legacy-ledger 7.0 + ledger-db V15",
     "environment": "prod", "changes": [{"component": "ledger-db", "version": "V15"},
                                        {"component": "legacy-ledger", "version": "7.0"}]},
    {"id": "ledger-only", "title": "Promote legacy-ledger 7.0 only", "subtitle": "Without the V15 migration",
     "environment": "prod", "changes": [{"component": "legacy-ledger", "version": "7.0"}]},
    {"id": "rollback-bridge", "title": "Roll mq-bridge back to 3.0", "subtitle": "Is the old version safe?",
     "environment": "prod", "changes": [{"component": "mq-bridge", "version": "3.0"}]},
]


@router.get("/rehearsals/presets")
def rehearsal_presets():
    versions = {}
    for comp in flows.get_components():
        commits = workspace.known_commits().get(comp["id"], {})
        versions[comp["id"]] = list(commits.keys())
    return {"presets": REHEARSAL_PRESETS, "versions": versions}


@router.post("/rehearsals")
def create_rehearsal(req: RehearsalRequest):
    if req.environment not in flows.environments():
        raise HTTPException(404, f"Unknown environment {req.environment}")
    return rehearse(req.environment, req.changes, run_probes=True, title=req.title)


# --------------------------------------------------------------------- documents & source

DOCS = {
    "change-request.pdf": ("application/pdf", "change-request-data.json", "CR-4471 · Change request"),
    "release-notes.docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           "release-notes-data.json", "R-26.9 · Release notes"),
    "interface-control.xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               "interface-control-data.json", "LEDG-ICD-007 · Interface control document"),
}


@router.get("/documents")
def documents():
    out = []
    for name, (mime, sidecar, title) in DOCS.items():
        path = DOCUMENTS / name
        out.append({"name": name, "title": title, "mime": mime, "exists": path.exists(),
                    "size": path.stat().st_size if path.exists() else 0,
                    "content": json.loads((DOCUMENTS / sidecar).read_text(encoding="utf-8"))
                    if (DOCUMENTS / sidecar).exists() else None})
    return out


@router.get("/documents/{name}")
def document_file(name: str):
    if name not in DOCS or not (DOCUMENTS / name).exists():
        raise HTTPException(404, name)
    return FileResponse(DOCUMENTS / name, media_type=DOCS[name][0], filename=name)


@router.get("/source/{component}")
def source(component: str, commit: str, path: str):
    try:
        text = workspace.show(component, commit, path)
    except workspace.SourceUnavailable as exc:
        raise HTTPException(404, str(exc))
    return {"component": component, "commit": commit, "path": path, "lines": text.splitlines()}


@router.get("/repos/{component}/log")
def repo_log(component: str):
    try:
        return workspace.log(component)
    except workspace.SourceUnavailable as exc:
        raise HTTPException(404, str(exc))


@router.get("/meta")
def meta():
    return {"generated": datetime.utcnow().isoformat() + "Z", "environments": flows.environments(),
            "promotion_path": flows.promotion_path(), "snapshot_time": flows.snapshot_time()}
