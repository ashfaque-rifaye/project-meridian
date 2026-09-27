"""Flows router"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import APIRouter
router = APIRouter()


@router.get("/{flow_id}")
def get_flow(flow_id: str):
    from engine.domain.flows import FLOWS, COMPONENTS
    flow = FLOWS.get(flow_id)
    if not flow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found")
    return {
        "flow_id": flow_id,
        "name": "Order-to-Ledger",
        "description": "The complete order-to-ledger business flow from web checkout through to Db2 ledger",
        "edges": [
            {
                "edge_id": e.edge_id,
                "producer": e.producer,
                "consumer": e.consumer,
                "interface": e.interface,
                "order": e.order,
            }
            for e in sorted(flow, key=lambda x: x.order)
        ],
        "components": COMPONENTS,
    }


@router.get("/{flow_id}/edges")
def get_flow_edges(flow_id: str):
    from engine.domain.flows import FLOWS
    flow = FLOWS.get(flow_id, [])
    return [
        {"edge_id": e.edge_id, "producer": e.producer, "consumer": e.consumer,
         "interface": e.interface, "order": e.order}
        for e in sorted(flow, key=lambda x: x.order)
    ]
