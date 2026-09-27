"""IBM Bob integration: configuration discovery, live guardrail test, agent activity."""

from __future__ import annotations

import json
import subprocess
import sys

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from engine.paths import AGENT_FINDINGS, MERIDIAN, ROOT

router = APIRouter()
BOB = ROOT / ".bob"


def _front_matter(text: str) -> dict:
    if text.startswith("---"):
        _, fm, _body = text.split("---", 2)
        return yaml.safe_load(fm) or {}
    return {}


@router.get("/bob")
def bob_config():
    modes = []
    modes_file = BOB / "custom_modes.yaml"
    if modes_file.exists():
        for m in (yaml.safe_load(modes_file.read_text(encoding="utf-8")) or {}).get("customModes", []):
            groups = []
            for g in m.get("groups", []):
                groups.append(g if isinstance(g, str) else f"{g[0]} ({g[1].get('fileRegex', '')})")
            modes.append({"slug": m["slug"], "name": m["name"], "groups": groups,
                          "when": " ".join(str(m.get("whenToUse", "")).split())})
    skills = []
    for path in sorted((BOB / "skills").glob("*/SKILL.md")):
        fm = _front_matter(path.read_text(encoding="utf-8"))
        skills.append({"name": fm.get("name", path.parent.name),
                       "description": " ".join(str(fm.get("description", "")).split()),
                       "path": path.relative_to(ROOT).as_posix(),
                       "files": sorted(p.name for p in path.parent.iterdir())})
    agents = [{"name": p.stem, "path": p.relative_to(ROOT).as_posix()}
              for p in sorted((BOB / "agents").glob("*.md"))]
    rules = [p.relative_to(ROOT).as_posix() for p in sorted((BOB / "rules-meridian").glob("*.md"))]
    mcp = json.loads((BOB / "mcp.json").read_text(encoding="utf-8")) if (BOB / "mcp.json").exists() else {}
    settings = json.loads((BOB / "settings.json").read_text(encoding="utf-8")) if (BOB / "settings.json").exists() else {}

    sys.path.insert(0, str(ROOT / "mcp-server"))
    try:
        from meridian_mcp import TOOL_CATALOG  # type: ignore
        tools = TOOL_CATALOG
    except Exception as exc:  # noqa: BLE001
        tools = [{"name": "unavailable", "description": str(exc)}]
    finally:
        sys.path.pop(0)

    return {"modes": modes, "skills": skills, "agents": agents, "rules": rules, "mcp": mcp,
            "hooks": settings.get("hooks", {}), "tools": tools,
            "agents_md": (ROOT / "AGENTS.md").exists()}


class HookTest(BaseModel):
    command: str


@router.post("/bob/hook-test")
def hook_test(req: HookTest):
    """Run the real PreToolUse guard exactly as Bob would, with a tool-call payload on stdin."""
    payload = json.dumps({"tool_name": "execute_command", "tool_input": {"command": req.command}})
    proc = subprocess.run([sys.executable, str(BOB / "hooks" / "guard.py")], input=payload,
                          capture_output=True, text=True, timeout=10, cwd=ROOT)
    return {"command": req.command, "exit_code": proc.returncode, "blocked": proc.returncode == 2,
            "stderr": proc.stderr.strip(), "hook": ".bob/hooks/guard.py (PreToolUse · execute_command)"}


@router.get("/bob/activity")
def activity(limit: int = 60):
    log = MERIDIAN / "bob-activity.jsonl"
    entries = []
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    findings = []
    if AGENT_FINDINGS.exists():
        for path in sorted(AGENT_FINDINGS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                findings.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
    return {"hook_log": list(reversed(entries)), "agent_findings": findings}
