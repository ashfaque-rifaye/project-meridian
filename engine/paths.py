"""Filesystem layout used by the Meridian engine."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENVIRONMENTS = ROOT / "environments"
DOCUMENTS = ROOT / "documents"
PROBES_SOURCE = ROOT / "probes"
FIXTURES = ROOT / "fixtures"
SOURCE_MERIDIAN = ROOT / ".meridian"

# Vercel bundles are read-only. Generated evidence and probe sandboxes must use
# its writable temporary filesystem, while the generated Git repositories stay
# in the deployed source tree for read-only source inspection.
SERVERLESS = bool(os.environ.get("VERCEL")) or str(ROOT).startswith("/var/task")
MERIDIAN = Path(os.environ.get("MERIDIAN_HOME") or (Path("/tmp") / "meridian" if SERVERLESS else SOURCE_MERIDIAN))
REPOS = SOURCE_MERIDIAN / "repos"
RUNS = MERIDIAN / "runs"
SANDBOX = MERIDIAN / "sandbox"
WORKTREES = MERIDIAN / "worktrees"
CANDIDATES = MERIDIAN / "candidates"
EVIDENCE = MERIDIAN / "evidence"
INVESTIGATIONS = MERIDIAN / "investigations"
HANDOFF = MERIDIAN / "handoff"
AGENT_FINDINGS = MERIDIAN / "agent-findings"
CONTRACTS = MERIDIAN / "contracts"
REHEARSALS = MERIDIAN / "rehearsals"
PROBES = MERIDIAN / "probes" if SERVERLESS else PROBES_SOURCE


def _seed_runtime_files() -> None:
    """Copy read-only seeded evidence into a fresh serverless runtime volume."""
    if MERIDIAN == SOURCE_MERIDIAN:
        return
    for name in ("evidence", "validation-memory", "agent-findings"):
        source = SOURCE_MERIDIAN / name
        target = MERIDIAN / name
        if source.exists():
            shutil.copytree(source, target, dirs_exist_ok=True)


def ensure_dirs() -> None:
    _seed_runtime_files()
    for d in (RUNS, SANDBOX, WORKTREES, CANDIDATES, EVIDENCE, INVESTIGATIONS,
              HANDOFF, AGENT_FINDINGS, CONTRACTS, REHEARSALS, PROBES):
        d.mkdir(parents=True, exist_ok=True)


# Initialize the writable runtime volume before request handlers read from it.
ensure_dirs()
