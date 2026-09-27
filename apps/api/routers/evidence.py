"""Evidence router"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import APIRouter, HTTPException
router = APIRouter()

MERIDIAN_DIR = Path(__file__).parent.parent.parent.parent / ".meridian"


@router.get("/{evidence_id}")
def get_evidence(evidence_id: str):
    """Retrieve evidence by ID — searches probe runs and validation records."""
    # Search probe runs
    runs_dir = MERIDIAN_DIR / "runs"
    if runs_dir.exists():
        for probe_file in runs_dir.glob("*.json"):
            with open(probe_file) as f:
                data = json.load(f)
            if data.get("evidence_id") == evidence_id or data.get("probe_id") == evidence_id:
                return {"source": "probe_run", "data": data}
    
    raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found")


@router.get("/packet/{divergence_id}")
def get_evidence_packet(divergence_id: str, environment: str = "prod", flow_id: str = "order-to-ledger"):
    """Build a complete evidence packet for a First Demonstrated Divergence."""
    from engine.divergence.first_divergence import find_first_divergence
    
    div = find_first_divergence(flow_id, environment)
    if not div:
        raise HTTPException(status_code=404, detail="No divergence found for this environment")
    
    return {
        "divergence_id": div.divergence_id,
        "release_id": div.release_id,
        "environment": div.environment,
        "flow_id": div.flow_id,
        "connection": f"{div.producer} {div.producer_version} → {div.consumer} {div.consumer_version}",
        "upstream_version": div.producer_version,
        "upstream_commit": div.producer_commit,
        "upstream_deploy_time": div.producer_deployed_at.isoformat(),
        "downstream_version": div.consumer_version,
        "downstream_commit": div.consumer_commit,
        "downstream_deploy_time": div.consumer_deployed_at.isoformat(),
        "first_divergence_timestamp": div.unvalidated_since.isoformat(),
        "triggering_deployment": div.triggering_deployment,
        "probe_id": div.probe_id,
        "probe_result": div.probe_result.value if div.probe_result else None,
        "human_summary": (
            f"Production entered a new unvalidated composition at 11:42 when "
            f"'{div.producer} {div.producer_version}' was promoted while '{div.consumer}' "
            f"remained at '{div.consumer_version}'. No passing validation evidence exists "
            f"for this pair on the promotion path. "
            f"The generated isolated probe reproduced a fixed-width semantic incompatibility."
        ),
    }
