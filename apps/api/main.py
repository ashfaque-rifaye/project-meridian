"""
Meridian API.

Thin HTTP layer over the deterministic engine. Every response is computed from
adapter outputs, validation runs, git repositories, documents and persisted
probe evidence; nothing in here is hard-coded demo state.

    uvicorn apps.api.main:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from apps.api.routers import bob, core, investigations, remediation  # noqa: E402

app = FastAPI(
    title="Meridian API",
    description="Release convergence verification: actual composition + validation evidence + "
                "implicit contract discovery + executable rehearsal.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core.router, prefix="/api")
app.include_router(investigations.router, prefix="/api")
app.include_router(remediation.router, prefix="/api")
app.include_router(bob.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "meridian-api"}


# Ambient videos generated with Google Flow (Veo 3.1), served outside the build output.
MEDIA = ROOT / "apps" / "web" / "media"
if MEDIA.exists():
    app.mount("/media", StaticFiles(directory=MEDIA), name="media")

# Serve the built UI (apps/web/dist) when present, so one process runs the demo.
DIST = ROOT / "apps" / "web" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        target = DIST / path
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(DIST / "index.html")
