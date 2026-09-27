#!/usr/bin/env python3
"""
Meridian PreToolUse guard for IBM Bob.

Bob runs this before `execute_command`. The tool call arrives as JSON on stdin
(`{"tool_name": ..., "tool_input": {"command": ...}}`); a command can also be
passed as argv for manual testing:

    python .bob/hooks/guard.py "kubectl apply -f prod.yaml"

Exit code 2 blocks the tool call and Bob continues the session. Meridian is
read-only against target environments; compatibility checks run only as
isolated probes.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED = [
    (r"\bkubectl\b.*[\s\"'(,](apply|delete|scale|rollout|patch|edit|replace|set|annotate|label|cordon|drain|create)\b", "kubectl mutation"),
    (r"\boc\b.*[\s\"'(,](apply|delete|scale|rollout|patch|edit|replace|set|create)\b", "OpenShift mutation"),
    (r"\bhelm\b.*[\s\"'(,](upgrade|install|uninstall|rollback)\b", "Helm release change"),
    (r"\bargocd\b.*[\s\"'(,](sync|set|delete|rollback)\b", "Argo CD sync"),
    (r"\bterraform\b.*[\s\"'(,](apply|destroy|import)\b", "Terraform change"),
    (r"\baws\b.*[\s\"'(,](create|update|delete|deploy|put|modify|register|start|stop|terminate)[\w-]*", "AWS mutation"),
    (r"\baz\b.*[\s\"'(,](create|update|delete|deploy|deployment|set|start|stop|restart)\b", "Azure mutation"),
    (r"\bgcloud\b.*[\s\"'(,](create|update|delete|deploy|set|start|stop|resize)\b", "Google Cloud mutation"),
    (r"\bflyway\b.*[\s\"'(,](migrate|clean|repair|undo)\b", "database migration"),
    (r"\bdb2\b.*\b(update|delete|insert|drop|alter)\b", "Db2 write"),
    (r"\b(runmqsc|setmqaut|endmqm|strmqm)\b", "IBM MQ administration"),
    (r"\bgit\b.*[\s\"'(,]push\b", "git push"),
]
# The verb may follow a quote or comma, not only whitespace, so wrapped forms such as
# Start-Process -FilePath "git" -ArgumentList "push" are caught as well.

LOG = Path(__file__).resolve().parent.parent.parent / ".meridian" / "bob-activity.jsonl"


def command_from_input() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw.strip():
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    return str(tool_input.get("command") or payload.get("command") or "")


def record(entry: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def main() -> int:
    command = command_from_input()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for pattern, label in BLOCKED:
        if re.search(pattern, command, re.IGNORECASE):
            message = (f"MERIDIAN GUARD: blocked {label}: `{command}`. Meridian is read-only against target "
                       "environments. Run compatibility checks as isolated probes (MCP tool run_probe).")
            print(message, file=sys.stderr)
            record({"at": now, "hook": "PreToolUse", "decision": "BLOCKED", "rule": label, "command": command})
            return 2
    record({"at": now, "hook": "PreToolUse", "decision": "ALLOWED", "command": command})
    return 0


if __name__ == "__main__":
    sys.exit(main())
