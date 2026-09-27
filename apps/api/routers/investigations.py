"""Investigation runs, streamed live to the UI with Server-Sent Events."""

from __future__ import annotations

import asyncio
import json
import queue

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from engine.investigation import AGENTS, Investigation, latest_investigation, load_investigation

router = APIRouter()
_RUNNING: dict[str, Investigation] = {}


class InvestigationRequest(BaseModel):
    environment: str = "prod"
    reference: str = "stage"
    pace_ms: int = 450


@router.get("/investigations/agents")
def agents():
    return AGENTS


@router.post("/investigations")
def start(req: InvestigationRequest):
    inv = Investigation(req.environment, req.reference, pace_ms=max(0, min(req.pace_ms, 2000))).start()
    _RUNNING[inv.id] = inv
    return {"investigation_id": inv.id}


@router.get("/investigations/latest")
def latest():
    inv = latest_investigation()
    if not inv:
        raise HTTPException(404, "No investigation has run yet.")
    return inv


@router.get("/investigations/{investigation_id}")
def get(investigation_id: str):
    inv = load_investigation(investigation_id)
    if inv:
        return inv
    running = _RUNNING.get(investigation_id)
    if running:
        return {"investigation_id": investigation_id, "result": running.result, "events": list(running.events)}
    raise HTTPException(404, investigation_id)


@router.get("/investigations/{investigation_id}/events")
async def stream(investigation_id: str):
    inv = _RUNNING.get(investigation_id)
    if inv is None:
        stored = load_investigation(investigation_id)
        if not stored:
            raise HTTPException(404, investigation_id)

        async def replay():
            for event in stored["events"]:
                yield f"data: {json.dumps(event)}\n\n"
            yield "event: end\ndata: {}\n\n"
        return StreamingResponse(replay(), media_type="text/event-stream")

    async def live():
        while True:
            try:
                event = inv.queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"
        yield "event: end\ndata: {}\n\n"
        _RUNNING.pop(investigation_id, None)

    return StreamingResponse(live(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
