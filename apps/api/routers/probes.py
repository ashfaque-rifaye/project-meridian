"""Probes router"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
router = APIRouter()


class RunProbeRequest(BaseModel):
    probe_id: str = "probe-001"
    edge_id: str = "mq-bridge→legacy-ledger"


@router.post("/")
def create_probe(req: RunProbeRequest):
    """Create a probe spec for an edge."""
    from engine.probes.probe_engine import get_default_probe_spec
    spec = get_default_probe_spec()
    return {
        "probe_id": spec.probe_id,
        "edge_id": spec.edge_id,
        "producer": spec.producer,
        "producer_version": spec.producer_version,
        "consumer": spec.consumer,
        "consumer_version": spec.consumer_version,
        "interface_type": spec.interface_type,
        "fixture": spec.fixture,
        "assertions": spec.assertions,
        "status": "PENDING",
    }


@router.post("/{probe_id}/run")
def run_probe(probe_id: str):
    """Execute a probe in isolation."""
    from engine.probes.probe_engine import get_default_probe_spec, run_probe as _run
    spec = get_default_probe_spec()
    spec.probe_id = probe_id
    
    try:
        execution = _run(spec)
        return {
            "probe_id": execution.probe_id,
            "connection": execution.connection,
            "result": execution.result.value,
            "assertion_results": execution.assertion_results,
            "stdout": execution.stdout,
            "stderr": execution.stderr,
            "exit_code": execution.exit_code,
            "executed_at": execution.executed_at.isoformat(),
            "evidence_id": execution.evidence_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{probe_id}")
def get_probe(probe_id: str):
    """Get a probe result by ID."""
    import json
    runs_dir = Path(__file__).parent.parent.parent.parent / ".meridian" / "runs"
    probe_file = runs_dir / f"{probe_id}.json"
    
    if not probe_file.exists():
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")
    
    with open(probe_file) as f:
        return json.load(f)
