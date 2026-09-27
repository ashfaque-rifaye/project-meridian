"""Filesystem layout used by the Meridian engine."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENVIRONMENTS = ROOT / "environments"
DOCUMENTS = ROOT / "documents"
PROBES = ROOT / "probes"
FIXTURES = ROOT / "fixtures"

MERIDIAN = Path(os.environ.get("MERIDIAN_HOME", ROOT / ".meridian"))
REPOS = MERIDIAN / "repos"
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


def ensure_dirs() -> None:
    for d in (RUNS, SANDBOX, WORKTREES, CANDIDATES, EVIDENCE, INVESTIGATIONS,
              HANDOFF, AGENT_FINDINGS, CONTRACTS, REHEARSALS, PROBES):
        d.mkdir(parents=True, exist_ok=True)
