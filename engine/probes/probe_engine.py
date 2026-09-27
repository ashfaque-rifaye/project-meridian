"""
Compatibility probe engine.

PROVE step. A probe takes the producer and the consumer at their exact
deployed commits, feeds the Stage validation fixtures through both in an
isolated subprocess, and evaluates the observations deterministically.

The probe is the only way Meridian reports FAILED or VERIFIED_BY_PROBE.
No model output can change a probe result.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from engine.domain.models import ProbeOutcome
from engine.paths import PROBES, ROOT, RUNS, SANDBOX, ensure_dirs
from engine.probes import workspace

RUNNER = Path(__file__).with_name("runner.py")
TIMEOUT_SECONDS = 20


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _sandbox_env(sandbox: Path) -> dict:
    env = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "MERIDIAN_SANDBOX": "1",
        "TEMP": str(sandbox), "TMP": str(sandbox),
        "PATH": str(Path(sys.executable).parent),
    }
    if os.name == "nt":
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
    return env


def _money(value) -> Decimal | None:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return None


def evaluate_fixture(fixture: dict, observation: dict | None) -> dict:
    """Deterministically judge one fixture from the runner's observations."""
    base = {"fixture": fixture["id"], "label": fixture["label"], "event": fixture["event"]}
    if observation is None:
        return base | {"outcome": "NOT_RUN", "passed": None, "silent": False,
                       "note": "The runner produced no observation for this fixture."}
    if "producer_error" in observation:
        return base | {"outcome": "PRODUCER_ERROR", "passed": None, "silent": False,
                       "note": observation["producer_error"]}
    produced = observation["producer"]
    if produced.get("outcome") == "HOLD":
        return base | {"outcome": "HELD", "passed": True, "silent": False, "queue": produced.get("queue"),
                       "producer_layout": produced.get("layout"),
                       "note": f"Held explicitly on {produced.get('queue')}: {produced.get('reason')}"}
    record = produced.get("record") or ""
    common = base | {"record": record, "record_length": len(record), "producer_layout": produced.get("layout"),
                     "queue": produced.get("queue")}
    if "consumer_error" in observation:
        return common | {"outcome": "CONSUMER_ERROR", "passed": False, "silent": False,
                         "note": observation["consumer_error"]}
    consumed = observation.get("consumer") or {}
    infrastructure = {
        "status": consumed.get("status"), "http_status": consumed.get("http_status"),
        "mq_ack": consumed.get("mq_ack"), "db_commit": consumed.get("db_commit"),
    }
    if consumed.get("status") != "POSTED":
        return common | {"outcome": "REJECTED", "passed": False, "silent": False, "infrastructure": infrastructure,
                         "note": consumed.get("reason", "Consumer rejected the record (visible failure).")}
    expect = fixture["expect"]
    assertions = [
        {"field": "customer_id", "expected": expect["customer_id"], "actual": consumed.get("customer_id"),
         "passed": consumed.get("customer_id") == expect["customer_id"]},
        {"field": "currency", "expected": expect["currency"], "actual": consumed.get("currency"),
         "passed": consumed.get("currency") == expect["currency"]},
        {"field": "amount", "expected": expect["amount"], "actual": consumed.get("amount"),
         "passed": _money(consumed.get("amount")) == _money(expect["amount"])},
    ]
    passed = all(a["passed"] for a in assertions)
    silent = (not passed) and bool(consumed.get("mq_ack")) and bool(consumed.get("db_commit"))
    return common | {"outcome": "POSTED", "passed": passed, "silent": silent, "assertions": assertions,
                     "consumer_layout": consumed.get("layout"), "infrastructure": infrastructure}


def _transcript(spec: dict, run_id: str, sandbox: Path, steps: dict, fixtures: list[dict],
                outcome: str, exit_code: int, stderr: str) -> list[dict]:
    p, c = spec["producer"], spec["consumer"]
    lines = [
        {"kind": "cmd", "text": f"$ meridian probe run {spec['probe_id']}"},
        {"kind": "meta", "text": f"sandbox   {_rel(sandbox)}  (python -I, no credentials, no network endpoints)"},
        {"kind": "meta", "text": f"producer  {p['component']} {p['label']} @ {p['commit']}  (git archive)"},
        {"kind": "meta", "text": f"consumer  {c['component']} {c['version']} @ {c['commit']}  (git archive)"},
        {"kind": "meta", "text": f"fixtures  {len(spec['fixtures'])} · {spec['fixture_source']}"},
    ]
    if p.get("config"):
        lines.append({"kind": "meta", "text": "config    " + ", ".join(f"{k}={v}" for k, v in p["config"].items())})
    lines.append({"kind": "step", "text": "[1/4] Load producer at deployed commit",
                  "status": steps.get("load-producer", "error")})
    lines.append({"kind": "step", "text": "[2/4] Load consumer at deployed commit",
                  "status": steps.get("load-consumer", "error")})
    ran = [f for f in fixtures if f["outcome"] != "NOT_RUN"]
    lines.append({"kind": "step", "text": f"[3/4] Produce and consume {len(spec['fixtures'])} fixtures",
                  "status": "ok" if ran else "error"})
    for f in fixtures:
        if f["outcome"] == "POSTED":
            infra = f["infrastructure"]
            lines.append({"kind": "detail", "text": (
                f"      {f['fixture']:<26} {f['record']!r} ({f['record_length']} B) -> POSTED · "
                f"HTTP {infra['http_status']} · MQ ACK · DB COMMIT")})
        else:
            lines.append({"kind": "detail", "text": f"      {f['fixture']:<26} {f['outcome']} · {f.get('note', '')}"})
    failed_assertions = [a for f in fixtures for a in f.get("assertions", []) if not a["passed"]]
    total_assertions = sum(len(f.get("assertions", [])) for f in fixtures)
    rejected = [f for f in fixtures if f["outcome"] in ("REJECTED", "CONSUMER_ERROR")]
    held = [f for f in fixtures if f["outcome"] == "HELD"]
    status = "FAIL" if (failed_assertions or rejected) else ("ok" if outcome == "PASS" else "inconclusive")
    summary = f"[4/4] Semantic assertions ({total_assertions - len(failed_assertions)}/{total_assertions} passed"
    summary += f", {len(held)} held explicitly)" if held else ")"
    lines.append({"kind": "step", "text": summary, "status": status})
    for f in fixtures:
        for a in f.get("assertions", []):
            if not a["passed"]:
                lines.append({"kind": "assert", "text": (
                    f"      {f['fixture']:<26} {a['field']:<12} expected {a['expected']!r:<16} observed {a['actual']!r}")})
    if stderr.strip():
        lines.append({"kind": "stderr", "text": stderr.strip()[:800]})
    silent = any(f.get("silent") for f in fixtures)
    if outcome == "FAIL" and silent:
        text = "Result: FAILED · silent semantic failure (HTTP 200, MQ ACK, DB COMMIT, wrong business data)"
    elif outcome == "FAIL":
        text = "Result: FAILED · records rejected by the consumer"
    elif outcome == "PASS":
        text = "Result: PASS · every delivered record round-trips exactly" + (
            f"; {len(held)} held explicitly" if held else "")
    else:
        text = f"Result: INCONCLUSIVE · probe could not establish compatibility (exit code {exit_code})"
    lines.append({"kind": "result", "text": text, "status": outcome})
    return lines


def run_probe(spec: dict) -> dict:
    """Execute a probe spec in isolation, evaluate it, persist the evidence."""
    ensure_dirs()
    started = _now()
    run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}-{spec['probe_id'][-8:]}"
    sandbox = SANDBOX / run_id
    p, c = spec["producer"], spec["consumer"]
    records: list[dict] = []
    stdout = stderr = ""
    exit_code = -1
    setup_error = None
    t0 = time.perf_counter()
    try:
        workspace.materialize(p["component"], p["commit"], sandbox / "producer")
        workspace.materialize(c["component"], c["commit"], sandbox / "consumer")
        (sandbox / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        shutil.copyfile(RUNNER, sandbox / "runner.py")
        proc = subprocess.run(
            [sys.executable, "-I", str(sandbox / "runner.py"), str(sandbox)],
            cwd=sandbox, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, env=_sandbox_env(sandbox),
        )
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
        for line in stdout.splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except subprocess.TimeoutExpired:
        setup_error = f"Probe exceeded {TIMEOUT_SECONDS}s and was terminated."
    except workspace.SourceUnavailable as exc:
        setup_error = str(exc)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    steps = {r["step"]: r.get("status") for r in records if r.get("step") in ("load-producer", "load-consumer", "load")}
    observations = {r["fixture"]: r for r in records if r.get("step") == "fixture"}
    fixtures = [evaluate_fixture(f, observations.get(f["id"])) for f in spec["fixtures"]]

    if setup_error or exit_code != 0 or not observations:
        outcome = ProbeOutcome.INCONCLUSIVE
    elif any(f["passed"] is False for f in fixtures):
        outcome = ProbeOutcome.FAIL
    elif any(f["passed"] is None for f in fixtures):
        outcome = ProbeOutcome.INCONCLUSIVE
    else:
        outcome = ProbeOutcome.PASS

    if setup_error:
        stderr = (stderr + "\n" + setup_error).strip()
    result = {
        "run_id": run_id,
        "probe_id": spec["probe_id"],
        "evidence_id": f"ev-{run_id}",
        "edge_id": spec["edge_id"],
        "interface": spec["interface"],
        "producer": p, "consumer": c,
        "result": outcome.value,
        "silent_failure": any(f.get("silent") for f in fixtures),
        "fixtures": fixtures,
        "assertions_total": sum(len(f.get("assertions", [])) for f in fixtures),
        "assertions_failed": sum(1 for f in fixtures for a in f.get("assertions", []) if not a["passed"]),
        "held": sum(1 for f in fixtures if f["outcome"] == "HELD"),
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "started_at": started,
        "finished_at": _now(),
        "duration_ms": duration_ms,
        "sandbox": _rel(sandbox),
        "isolation": spec.get("isolation"),
        "transcript": _transcript(spec, run_id, sandbox, steps, fixtures, outcome.value, exit_code, stderr),
        "spec": spec,
    }
    (RUNS / f"{run_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (PROBES / f"{spec['probe_id']}.json").write_text(json.dumps({
        "probe_id": spec["probe_id"], "spec": spec,
        "latest_run": {k: result[k] for k in ("run_id", "result", "silent_failure", "finished_at", "evidence_id")},
    }, indent=2), encoding="utf-8")
    return result


def all_runs() -> list[dict]:
    if not RUNS.exists():
        return []
    runs = []
    for path in RUNS.glob("run-*.json"):
        try:
            runs.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return sorted(runs, key=lambda r: r["run_id"])


def get_run(run_id: str) -> dict | None:
    path = RUNS / f"{run_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def latest_result(edge_id: str, producer_commit: str | None, consumer_commit: str | None,
                  producer_config: dict | None = None) -> dict | None:
    """Most recent probe run for this exact edge, commits and producer config."""
    matches = [
        r for r in all_runs()
        if r["edge_id"] == edge_id
        and r["producer"]["commit"] == producer_commit
        and r["consumer"]["commit"] == consumer_commit
        and (r["producer"].get("config") or {}) == (producer_config or {})
    ]
    return matches[-1] if matches else None
