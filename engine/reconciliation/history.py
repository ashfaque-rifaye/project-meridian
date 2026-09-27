"""
Deployment history and composition timelines.

Replays deployment events (pipelines, GitOps syncs, CAB changes) to answer
"which exact versions were running together, when, and which deployment
created that combination".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from engine.domain import flows
from engine.paths import ENVIRONMENTS
from engine.reconciliation.reconciler import parse_ts


@lru_cache(maxsize=1)
def _history_doc() -> dict:
    return json.loads((ENVIRONMENTS / "deployment-events.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _scheduled_doc() -> dict:
    path = ENVIRONMENTS / "scheduled-changes.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"changes": []}


def reload() -> None:
    _history_doc.cache_clear()
    _scheduled_doc.cache_clear()


def events(environment: str | None = None) -> list[dict]:
    items = _history_doc()["events"]
    if environment:
        items = [e for e in items if e["environment"] == environment]
    return sorted(items, key=lambda e: e["deployed_at"])


def baseline(environment: str) -> dict:
    return _history_doc()["baseline"][environment]


def scheduled_changes(environment: str | None = None) -> list[dict]:
    items = _scheduled_doc()["changes"]
    return [c for c in items if environment is None or c["environment"] == environment]


@dataclass
class Segment:
    """An interval during which an environment ran one exact composition."""

    environment: str
    start: str
    end: str | None                       # None = still running
    versions: dict[str, str]
    commits: dict[str, str | None]
    started_by: dict | None               # deployment event that created it (None = baseline)

    def to_dict(self) -> dict:
        return {
            "environment": self.environment, "start": self.start, "end": self.end,
            "versions": self.versions, "commits": self.commits, "started_by": self.started_by,
        }


def segments(environment: str, until: str | None = None) -> list[Segment]:
    until = until or flows.snapshot_time()
    base = baseline(environment)
    versions = {c: v["version"] for c, v in base.items()}
    commits = {c: v.get("commit") for c, v in base.items()}
    start = max(v["deployed_at"] for v in base.values())
    out: list[Segment] = []
    current = Segment(environment, start, None, dict(versions), dict(commits), None)
    for event in events(environment):
        if parse_ts(event["deployed_at"]) > parse_ts(until):
            break
        if parse_ts(event["deployed_at"]) <= parse_ts(start):
            continue  # already reflected in the baseline
        current.end = event["deployed_at"]
        out.append(current)
        versions[event["component"]] = event["to_version"]
        commits[event["component"]] = event.get("commit")
        current = Segment(environment, event["deployed_at"], None, dict(versions), dict(commits), event)
    out.append(current)
    return out


def pair_windows(environment: str, producer: str, consumer: str,
                 producer_version: str, consumer_version: str, until: str | None = None) -> list[dict]:
    """Intervals in which the exact pair co-existed in an environment."""
    windows: list[dict] = []
    for seg in segments(environment, until):
        if seg.versions.get(producer) == producer_version and seg.versions.get(consumer) == consumer_version:
            if windows and windows[-1]["end"] == seg.start:
                windows[-1]["end"] = seg.end
            else:
                windows.append({"environment": environment, "start": seg.start, "end": seg.end,
                                "started_by": seg.started_by})
    for w in windows:
        end = parse_ts(w["end"] or (until or flows.snapshot_time()))
        w["duration_seconds"] = int((end - parse_ts(w["start"])).total_seconds())
        w["ongoing"] = w["end"] is None
    return windows


def combination_created(environment: str, producer: str, consumer: str,
                        producer_version: str, consumer_version: str) -> dict | None:
    """The window (and deployment event) that created the currently running pair."""
    windows = pair_windows(environment, producer, consumer, producer_version, consumer_version)
    ongoing = [w for w in windows if w["ongoing"]]
    return ongoing[-1] if ongoing else None
