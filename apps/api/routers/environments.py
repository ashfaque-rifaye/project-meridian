"""Environments router"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import APIRouter, HTTPException
router = APIRouter()


@router.get("/{env}")
def get_environment(env: str, flow_id: str = "order-to-ledger"):
    try:
        from engine.reconciliation.reconciler import load_snapshot
        snapshot = load_snapshot(env, flow_id)
        return {
            "environment": snapshot.environment,
            "flow_id": snapshot.flow_id,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_time": snapshot.snapshot_time.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "version": c.version,
                    "commit": c.commit,
                    "deployed_at": c.deployed_at.isoformat() if c.deployed_at else None,
                    "config_fingerprint": c.config_fingerprint,
                    "schema_version": c.schema_version,
                    "evidence_id": c.evidence_id,
                }
                for c in snapshot.components
            ],
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No snapshot for environment '{env}'")


@router.get("/{env}/edges")
def get_edge_states(env: str, flow_id: str = "order-to-ledger"):
    from engine.divergence.first_divergence import get_all_edge_states
    return get_all_edge_states(flow_id, env)
