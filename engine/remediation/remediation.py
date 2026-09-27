"""
Remediation.

REMEDIATE step: "What is the smallest safe change that restores compatibility?"

Every strategy is rehearsed, never deployed:

  A  converge-forward     pull CR-4471 forward: legacy-ledger 7.0 + ledger-db V15
  B  bridge-compat-mode   candidate mq-bridge build that never truncates (HOLD instead)
  C  hold-bridge          put mq-bridge back to 3.0

Strategy B needs code. IBM Bob drafts it in the `meridian-remediator` mode
(the candidate lands in .meridian/candidates/mq-bridge/). If Bob has not
produced one yet, the reference candidate from fixtures/reference-remediation
is used and labelled as such. Either way the candidate is committed to an
isolated branch in a separate worktree and proven by a regression probe.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone

from engine.domain import flows
from engine.paths import CANDIDATES, FIXTURES, HANDOFF, ROOT, WORKTREES, ensure_dirs
from engine.probes import workspace
from engine.rehearsal.rehearsal import rehearse

CANDIDATE_BRANCH = "meridian/remediation-compat-mode"
CANDIDATE_LABEL = "3.1.1-compat"
CANDIDATE_FILE = "src/ledger_record.py"
COMPAT_CONFIG = {"ledger.recordLayout": "v6-compat"}

STRATEGIES = [
    {
        "id": "converge-forward",
        "letter": "A",
        "title": "Deploy the CR-4471 upgrade now",
        "action": "Deploy legacy-ledger 7.0 and ledger-db V15 (the versions Stage tested) now instead of on Sunday.",
        "owner": "Core Ledger team + change board (emergency change)",
        "changes": [{"component": "ledger-db", "version": "V15"}, {"component": "legacy-ledger", "version": "7.0"}],
        "tradeoff": "Brings production back to exactly what Stage tested. Needs emergency approval for an on-prem change.",
    },
    {
        "id": "bridge-compat-mode",
        "letter": "B",
        "title": "Compatibility mode in mq-bridge",
        "action": "Ship an mq-bridge build that sends the old record format when an event fits it exactly, and holds everything else on the LEDGER.HOLD queue.",
        "owner": "Integration Services",
        "changes": None,  # candidate-specific
        "tradeoff": "Stops the bad data straight away. New 12-character and non-USD records wait on LEDGER.HOLD until CR-4471 is deployed.",
    },
    {
        "id": "hold-bridge",
        "letter": "C",
        "title": "Roll mq-bridge back to 3.0",
        "action": "Go back to the mq-bridge version production ran before Friday 11:42.",
        "owner": "Integration Services",
        "changes": [{"component": "mq-bridge", "version": "3.0"}],
        "tradeoff": "Looks safe, but billing-service 7.2 → mq-bridge 3.0 has never been tested together either.",
    },
]


def _git(cwd, *args, env=None) -> str:
    result = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args],
                            cwd=cwd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def candidate_source() -> tuple[str, str]:
    """(file content, author) for the compat-mode candidate."""
    bob = CANDIDATES / "mq-bridge" / CANDIDATE_FILE
    if bob.exists():
        return bob.read_text(encoding="utf-8").replace("\r\n", "\n"), "IBM Bob (meridian-remediator mode)"
    ref = FIXTURES / "reference-remediation" / "mq-bridge" / CANDIDATE_FILE
    return ref.read_text(encoding="utf-8").replace("\r\n", "\n"), "Reference candidate (fixtures/reference-remediation)"


def create_candidate() -> dict:
    """Commit the compat-mode candidate to an isolated branch in its own worktree."""
    ensure_dirs()
    repo = workspace.repo_path("mq-bridge")
    base = workspace.commit_for("mq-bridge", "3.1")
    tree = WORKTREES / "mq-bridge-remediation"
    content, author = candidate_source()

    branches = _git(repo, "branch", "--list", CANDIDATE_BRANCH)
    if not tree.exists():
        if branches:
            _git(repo, "worktree", "prune")
            _git(repo, "worktree", "add", "--force", str(tree), CANDIDATE_BRANCH)
        else:
            _git(repo, "worktree", "add", "-b", CANDIDATE_BRANCH, str(tree), base)

    target = tree / CANDIDATE_FILE
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if current != content:
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        name = "Meridian Remediator" if author.startswith("IBM Bob") else "Meridian Reference"
        env = {**os.environ, "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": "meridian@acme.example",
               "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": "meridian@acme.example"}
        _git(tree, "add", CANDIDATE_FILE, env=env)
        _git(tree, "commit", "-q", "-m",
             "MERIDIAN: mq-bridge compatibility mode for legacy-ledger < 7.0\n\n"
             "Emit LEDGREC rev 6 only when the event is exactly representable; route everything\n"
             "else to LEDGER.HOLD instead of truncating. Candidate only - not a release.\n\n"
             f"Author: {author}", env=env)
    commit = _git(tree, "rev-parse", "--short=7", "HEAD")
    diff = workspace.diff("mq-bridge", base, commit, CANDIDATE_FILE)
    return {
        "component": "mq-bridge",
        "label": CANDIDATE_LABEL,
        "branch": CANDIDATE_BRANCH,
        "base_commit": base,
        "commit": commit,
        "worktree": tree.relative_to(ROOT).as_posix(),
        "author": author,
        "authored_by_bob": author.startswith("IBM Bob"),
        "config": COMPAT_CONFIG,
        "diff": diff,
        "files_changed": [CANDIDATE_FILE],
    }


def rehearse_strategy(strategy_id: str, environment: str = "prod") -> dict:
    strategy = next(s for s in STRATEGIES if s["id"] == strategy_id)
    candidate = None
    if strategy_id == "bridge-compat-mode":
        candidate = create_candidate()
        changes = [{"component": "mq-bridge", "version": CANDIDATE_LABEL, "label": CANDIDATE_LABEL,
                    "commit": candidate["commit"], "config": COMPAT_CONFIG}]
    else:
        changes = strategy["changes"]
    result = rehearse(environment, changes, run_probes=True, title=f"{strategy['letter']} · {strategy['title']}")
    focus = next((e for e in result["edges"] if e["edge_id"] == "mq-bridge--legacy-ledger"), None)
    return {**strategy, "environment": environment, "candidate": candidate, "rehearsal": result,
            "critical_edge": focus}


def list_strategies() -> list[dict]:
    return [{k: v for k, v in s.items()} for s in STRATEGIES]


def write_handoff(packet: dict | None, evaluation: dict) -> dict:
    """Prepare the 'Open in Bob' task: a prompt plus the evidence packet on disk."""
    ensure_dirs()
    fd = evaluation.get("first_divergence")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    name = f"handoff-{stamp}"
    packet_path = HANDOFF / f"{name}.evidence.json"
    packet_path.write_text(json.dumps(packet or {}, indent=2), encoding="utf-8")
    edge = f"{fd['producer']} {fd['producer_version']} → {fd['consumer']} {fd['consumer_version']}" if fd else "n/a"
    prompt = f"""/mode meridian-remediator

Meridian found a First Demonstrated Divergence in {evaluation['environment'].upper()} ({flows.default_release_id()}):

  {edge}
  interface: {fd['interface'] if fd else ''}
  probe: {fd['probe']['result'] if fd and fd.get('probe') else 'n/a'} (run {fd['probe']['run_id'] if fd and fd.get('probe') else 'n/a'})

Evidence packet: {packet_path.relative_to(ROOT).as_posix()}

Task:
1. Read the evidence packet and call the meridian MCP tools get_first_divergence and get_evidence_packet.
2. Use the implicit-contract-discovery skill to confirm the LEDGREC layouts at the deployed commits
   (mq-bridge {fd['producer_commit'] if fd else ''}, legacy-ledger {fd['consumer_commit'] if fd else ''}).
3. Draft strategy B: an mq-bridge compatibility mode. Write the full file to
   .meridian/candidates/mq-bridge/{CANDIDATE_FILE}. Events that LEDGREC rev 6 cannot represent exactly
   (customerId > 10 characters, currency other than USD) must be routed to LEDGER.HOLD, never truncated.
4. Call the MCP tool verify_remediation with strategy "bridge-compat-mode" and report the regression probe result.

Do not deploy anything. Do not touch environments/. The human owns the release decision.
"""
    (HANDOFF / f"{name}.prompt.md").write_text(prompt, encoding="utf-8")
    return {"handoff_id": name, "prompt": prompt,
            "prompt_file": (HANDOFF / f"{name}.prompt.md").relative_to(ROOT).as_posix(),
            "evidence_file": packet_path.relative_to(ROOT).as_posix()}


def reset_candidate() -> None:
    """Remove the candidate worktree/branch (used by demo reset)."""
    try:
        repo = workspace.repo_path("mq-bridge")
    except workspace.SourceUnavailable:
        return
    tree = WORKTREES / "mq-bridge-remediation"
    if tree.exists():
        try:
            _git(repo, "worktree", "remove", "--force", str(tree))
        except RuntimeError:
            shutil.rmtree(tree, ignore_errors=True)
    _git(repo, "worktree", "prune")
    if _git(repo, "branch", "--list", CANDIDATE_BRANCH):
        _git(repo, "branch", "-D", CANDIDATE_BRANCH)
