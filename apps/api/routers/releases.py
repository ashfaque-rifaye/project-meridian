"""Releases router"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import APIRouter
router = APIRouter()

RELEASES = {
    "R-26.9": {
        "release_id": "R-26.9",
        "title": "Customer ID Expansion and Currency Code Support",
        "tagline": "Increase customerId capacity from 10 to 12 characters and introduce mandatory currencyCode support.",
        "status": {
            "dev": "VERIFIED",
            "test": "VERIFIED",
            "stage": "VERIFIED",
            "prod": "DIVERGED",
        },
        "component_count": 7,
        "edge_count": 6,
        "unvalidated_edges": 1,
        "failed_probes": 1,
        "first_divergence": {
            "producer": "mq-bridge",
            "producer_version": "3.1",
            "consumer": "legacy-ledger",
            "consumer_version": "6.9",
        },
    }
}


@router.get("/")
def list_releases():
    return list(RELEASES.values())


@router.get("/{release_id}")
def get_release(release_id: str):
    if release_id not in RELEASES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Release {release_id} not found")
    return RELEASES[release_id]


@router.get("/{release_id}/journey")
def get_release_journey(release_id: str):
    """Return the timeline of events for a release."""
    return {
        "release_id": release_id,
        "timeline": [
            {
                "event_id": "ev-1",
                "timestamp": "2026-09-20T08:00:00Z",
                "type": "commit",
                "component": "mq-bridge",
                "description": "Add 12-character customer ID support",
                "commit": "8f7a91",
                "environment": None,
            },
            {
                "event_id": "ev-2",
                "timestamp": "2026-09-20T09:00:00Z",
                "type": "commit",
                "component": "legacy-ledger",
                "description": "New v7 parser with currencyCode support",
                "commit": "c88d10",
                "environment": None,
            },
            {
                "event_id": "ev-3",
                "timestamp": "2026-09-22T09:00:00Z",
                "type": "deploy",
                "component": "all",
                "description": "R-26.9 deployed to DEV",
                "environment": "dev",
                "validation_state": "VERIFIED",
            },
            {
                "event_id": "ev-4",
                "timestamp": "2026-09-23T10:00:00Z",
                "type": "deploy",
                "component": "all",
                "description": "R-26.9 deployed to TEST — integration tests pass",
                "environment": "test",
                "validation_state": "VERIFIED",
            },
            {
                "event_id": "ev-5",
                "timestamp": "2026-09-24T14:30:00Z",
                "type": "validation",
                "component": "mq-bridge + legacy-ledger",
                "description": "Stage E2E validation — mq-bridge 3.1 + legacy-ledger 7.0 VERIFIED",
                "environment": "stage",
                "validation_state": "VERIFIED",
                "evidence_id": "val-stage-mqb31-ll70-001",
            },
            {
                "event_id": "ev-6",
                "timestamp": "2026-09-25T06:00:00Z",
                "type": "deploy",
                "component": "web-checkout, order-api, payment-service, billing-service",
                "description": "R-26.9 first wave deployed to PROD",
                "environment": "prod",
                "validation_state": "VERIFIED",
            },
            {
                "event_id": "ev-7",
                "timestamp": "2026-09-26T11:42:00Z",
                "type": "deploy",
                "component": "mq-bridge",
                "description": "mq-bridge 3.1 promoted to PROD — legacy-ledger stays at 6.9",
                "environment": "prod",
                "validation_state": "UNVALIDATED",
                "significance": "THIS EVENT CREATED THE UNVALIDATED PRODUCTION COMPOSITION",
                "note": "legacy-ledger 7.0 upgrade scheduled for Saturday CAB window (CR-4471)",
            },
            {
                "event_id": "ev-8",
                "timestamp": "2026-09-26T11:42:05Z",
                "type": "divergence",
                "component": "mq-bridge 3.1 + legacy-ledger 6.9",
                "description": "UNVALIDATED PRODUCTION COMBINATION CREATED",
                "environment": "prod",
                "validation_state": "UNTESTED",
            },
        ]
    }
