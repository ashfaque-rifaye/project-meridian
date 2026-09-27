"""Remediation strategies, Open-in-Bob handoff, and demo reset."""

from __future__ import annotations

import shutil

from fastapi import APIRouter, HTTPException

from engine.divergence.first_divergence import evaluate_environment
from engine.evidence import packet as packets
from engine.paths import (
    AGENT_FINDINGS, CANDIDATES, CONTRACTS, EVIDENCE, HANDOFF, INVESTIGATIONS, PROBES, REHEARSALS, RUNS, SANDBOX,
)
from engine.remediation import remediation

router = APIRouter()


@router.get("/remediation/strategies")
def strategies():
    return remediation.list_strategies()


@router.post("/remediation/{strategy_id}/rehearse")
def rehearse_strategy(strategy_id: str, environment: str = "prod"):
    if strategy_id not in {s["id"] for s in remediation.STRATEGIES}:
        raise HTTPException(404, strategy_id)
    return remediation.rehearse_strategy(strategy_id, environment)


@router.get("/remediation/candidate")
def candidate_status():
    source, author = remediation.candidate_source()
    return {"author": author, "authored_by_bob": author.startswith("IBM Bob"),
            "bob_candidate_path": ".meridian/candidates/mq-bridge/src/ledger_record.py",
            "lines": source.count("\n")}


@router.post("/handoff")
def handoff(environment: str = "prod"):
    evaluation = evaluate_environment(environment)
    if not evaluation["first_divergence"]:
        raise HTTPException(409, "No First Demonstrated Divergence to hand off. Run an investigation first.")
    return remediation.write_handoff(packets.latest_packet(), evaluation)


@router.post("/demo/reset")
def reset():
    """Remove generated evidence so the demo starts from a clean state. Scenario data is untouched."""
    removed = 0
    for directory in (RUNS, SANDBOX, EVIDENCE, INVESTIGATIONS, REHEARSALS, HANDOFF, CONTRACTS):
        if directory.exists():
            for item in directory.iterdir():
                if item.name == ".gitkeep":
                    continue
                shutil.rmtree(item) if item.is_dir() else item.unlink()
                removed += 1
    if PROBES.exists():
        for item in PROBES.glob("probe-*.json"):
            item.unlink()
            removed += 1
    remediation.reset_candidate()
    return {"status": "reset", "removed": removed,
            "kept": [str(p) for p in (AGENT_FINDINGS, CANDIDATES)],
            "note": "Bob-authored candidates and agent findings are kept."}
