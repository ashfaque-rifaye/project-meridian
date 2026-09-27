"""Rehearsals router"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()


class RehearsalRequest(BaseModel):
    environment: str = "prod"
    flow_id: str = "order-to-ledger"
    proposed_component: str
    proposed_version: str


@router.post("/")
def create_rehearsal(req: RehearsalRequest):
    from engine.rehearsal.rehearsal import simulate_promotion
    sim = simulate_promotion(
        req.environment,
        req.flow_id,
        req.proposed_component,
        req.proposed_version,
    )
    return {
        "simulation_id": sim.simulation_id,
        "environment": sim.environment,
        "proposed_component": sim.proposed_component,
        "proposed_version": sim.proposed_version,
        "predicted_composition": sim.predicted_composition,
        "affected_edges": [
            {"edge_id": e.edge_id, "producer": e.producer, "consumer": e.consumer}
            for e in sim.affected_edges
        ],
        "edge_results": sim.edge_results,
        "result": sim.result,
        "summary": sim.summary,
        "first_divergence": {
            "edge_id": sim.first_divergence.edge_id,
            "producer": sim.first_divergence.producer,
            "producer_version": sim.first_divergence.producer_version,
            "consumer": sim.first_divergence.consumer,
            "consumer_version": sim.first_divergence.consumer_version,
        } if sim.first_divergence else None,
    }


@router.get("/{simulation_id}")
def get_rehearsal(simulation_id: str):
    return {"simulation_id": simulation_id, "status": "Use POST /api/rehearsals to create a new simulation"}
