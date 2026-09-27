#!/usr/bin/env python3
"""
Meridian PostToolUse logger for IBM Bob.

Appends one line per Bob tool call to .meridian/bob-activity.jsonl so the
Meridian UI can show what Bob actually did during an investigation.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent.parent / ".meridian" / "bob-activity.jsonl"


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"raw": raw[:500]}
    tool_input = payload.get("tool_input") or {}
    entry = {
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hook": "PostToolUse",
        "tool": payload.get("tool_name") or payload.get("tool"),
        "summary": {k: (str(v)[:200]) for k, v in tool_input.items()} if isinstance(tool_input, dict) else None,
        "mode": payload.get("mode"),
    }
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
