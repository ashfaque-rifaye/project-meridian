"""
"Why this happened": the organisational promotion pattern.

Compares the release's documented rollout order with the order in which the
environment actually received the release, and with scheduled changes. The
point is to show how independent promotion cadences assembled the
composition, not to blame a person or a team.
"""

from __future__ import annotations

from engine.domain import flows
from engine.reconciliation import history
from engine.reconciliation.reconciler import parse_ts


def promotion_pattern(environment: str, release_id: str | None = None) -> dict:
    release = flows.get_release(release_id or flows.default_release_id())
    target = release["target"]
    expected = []
    for step, entry in enumerate(release["rollout_order"], 1):
        component, version = entry.rsplit(" ", 1)
        expected.append({"step": step, "component": component, "version": version})

    actual = [e for e in history.events(environment) if target.get(e["component"]) == e["to_version"]]
    done = {e["component"] for e in actual}
    pending = []
    for change in history.scheduled_changes(environment):
        for c in change["changes"]:
            if c["component"] not in done and target.get(c["component"]) == c["to_version"]:
                pending.append({**c, "change_request": change["change_request"],
                                "window_start": change["window_start"], "window_end": change["window_end"],
                                "status": change["status"]})

    deviations = []
    for event in actual:
        step = next((s for s in expected if s["component"] == event["component"]), None)
        if not step:
            continue
        prerequisites = [s for s in expected if s["step"] < step["step"] and s["component"] not in done]
        missing_before = [s for s in prerequisites
                          if not any(a["component"] == s["component"] and parse_ts(a["deployed_at"]) <= parse_ts(event["deployed_at"])
                                     for a in actual)]
        if missing_before:
            deviations.append({
                "event": event,
                "runbook_step": step["step"],
                "ahead_of": [f"{s['component']} {s['version']} (step {s['step']})" for s in missing_before],
            })

    cadences = []
    for comp in flows.get_components():
        if comp["id"] in target:
            cadences.append({"component": comp["id"], "team": comp["team"], "deployed_by": comp["deploy_tool"],
                             "platform": comp["platform"], "cloud": comp["cloud"]})

    story = []
    if deviations:
        d = deviations[-1]
        e = d["event"]
        story.append(f"{e['component']} {e['to_version']} reached {environment.upper()} at {e['deployed_at']} "
                     f"via {e['tool']} ({e['trigger']}).")
        story.append("The runbook says it should go at step %d, after %s." % (d["runbook_step"], ", ".join(d["ahead_of"])))
    for p in pending:
        story.append(f"{p['component']} {p['to_version']} is scheduled in {p['change_request']} "
                     f"for {p['window_start']} ({p['status']}).")
    if deviations:
        story.append("No single deployment failed. Teams deploying on different schedules produced a set of versions "
                     "that no earlier environment ever tested.")

    return {
        "environment": environment,
        "release": release["id"],
        "expected_order": expected,
        "actual_order": [{"component": e["component"], "version": e["to_version"], "deployed_at": e["deployed_at"],
                          "tool": e["tool"], "trigger": e["trigger"], "note": e.get("note")} for e in actual],
        "pending": pending,
        "deviations": deviations,
        "cadences": cadences,
        "story": story,
    }
