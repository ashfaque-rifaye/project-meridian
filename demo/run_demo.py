#!/usr/bin/env python3
"""
Meridian end-to-end demo chain in the terminal.

Calls the same functions the MCP server exposes to IBM Bob, in workflow order:
RECONSTRUCT -> UNDERSTAND -> PROVE -> REHEARSE -> REMEDIATE.
Nothing is deployed; probes run in the .meridian/sandbox only.

    python demo/run_demo.py              # full chain
    python demo/run_demo.py --benchmark  # timings, saved to .meridian/benchmark.json
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mcp-server"))
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import meridian_mcp as m  # noqa: E402
from engine.rehearsal.rehearsal import rehearse  # noqa: E402

EDGE = "mq-bridge--legacy-ledger"


def timed(label: str, fn, *args, **kwargs):
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)["data"]
    return out, round((time.perf_counter() - t0) * 1000, 1)


def main() -> int:
    timings: dict[str, float] = {}

    print("RECONSTRUCT")
    for env in ("dev", "test", "stage", "prod"):
        ev, ms = timed(env, m.get_dependency_edges, env)
        timings[f"reconstruct_{env}_ms"] = ms
        print(f"  {env.upper():<6} {ev['verdict']}")

    print("\nUNDERSTAND")
    drift, timings["drift_relevance_ms"] = timed("drift", m.get_drift_relevance, "stage", "prod")
    for step in drift["funnel"]:
        print(f"  {step['count']:>4}  {step['label']}")
    untested, _ = timed("untested", m.get_untested_edges, "prod")
    for e in untested:
        print(f"  not verified: {e['edge_id']} {e.get('producer_version')} -> {e.get('consumer_version')}")

    print("\nPROVE")
    probe, timings["probe_ms"] = timed("probe", m.run_probe, EDGE, "prod")
    print(f"  probe {probe['result']}  silent={probe['silent_failure']}  "
          f"assertions failed {probe['assertions_failed']}/{probe['assertions_total']}")
    for fx in probe["fixtures"]:
        for a in fx["assertions"]:
            if not a["passed"]:
                print(f"    {fx['fixture']:<26} {a['field']:<12} expected {a['expected']!r:<16} got {a['actual']!r}")
    fd, timings["first_divergence_ms"] = timed("fd", m.get_first_divergence, "prod")
    d = fd["first_divergence"]
    if d:
        print(f"  First Demonstrated Divergence: {d['producer']} {d['producer_version']} -> "
              f"{d['consumer']} {d['consumer_version']}, unvalidated since {d['unvalidated_since']}")

    print("\nREHEARSE")
    plans = {
        "CR-4471 now (ledger-db V15 + legacy-ledger 7.0)": [{"component": "ledger-db", "version": "V15"},
                                                             {"component": "legacy-ledger", "version": "7.0"}],
        "roll mq-bridge back to 3.0": [{"component": "mq-bridge", "version": "3.0"}],
    }
    for label, changes in plans.items():
        t0 = time.perf_counter()
        r = rehearse("prod", changes, run_probes=True)
        timings[f"rehearse {label}_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        extra = f"  newly unvalidated: {', '.join(r['newly_unvalidated'])}" if r["newly_unvalidated"] else ""
        print(f"  {label}: {r['verdict']} (deployed anything: {r['deployed_anything']}){extra}")

    print("\nREMEDIATE")
    for strategy in ("converge-forward", "bridge-compat-mode", "hold-bridge"):
        r, ms = timed("rem", m.verify_remediation, strategy, "prod")
        timings[f"remediate_{strategy}_ms"] = ms
        print(f"  {strategy:<20} {r['rehearsal'].get('verdict'):<12} {r['tradeoff']}")

    if "--benchmark" in sys.argv:
        out = ROOT / ".meridian" / "benchmark.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {"timings_ms": timings, "note": "Synthetic demo measurements on this machine, not industry benchmarks."}
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("\n" + json.dumps(payload, indent=2))
        print(f"\nSaved to {out.relative_to(ROOT)}")
    return 0 if d else 1


if __name__ == "__main__":
    sys.exit(main())
