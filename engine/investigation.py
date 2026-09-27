"""
Investigation pipeline.

Runs the Meridian workflow end to end and emits an event for every step, so
the UI can show real agent activity as it happens:

  RECONSTRUCT  release investigator · environment investigators (4, in parallel)
  UNDERSTAND   validation memory · drift relevance · contract discovery (per unvalidated edge)
  PROVE        probe engineer (per edge, in parallel) · first divergence · evidence review

The same steps are exposed to IBM Bob as MCP tools and skills; inside Bob the
lanes are Bob subagents. Here the engine executes them directly. Measured
durations are real. `pace_ms` only adds presentation spacing between steps and
is reported separately.
"""

from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from engine.contracts import discovery
from engine.divergence.first_divergence import evaluate_environment, members_from_reality
from engine.domain import flows
from engine.drift.relevance import relevance
from engine.evidence.packet import build_packet
from engine.paths import INVESTIGATIONS, ensure_dirs
from engine.reconciliation.reconciler import reconstruct_environment

AGENTS = [
    {"id": "release-investigator", "name": "Release reader", "stage": "RECONSTRUCT",
     "skill": "release-investigation", "bob": "subagent · general"},
    {"id": "env-dev", "name": "Environment reader · DEV", "stage": "RECONSTRUCT",
     "skill": "environment-reconstruction", "bob": "subagent · explore"},
    {"id": "env-test", "name": "Environment reader · TEST", "stage": "RECONSTRUCT",
     "skill": "environment-reconstruction", "bob": "subagent · explore"},
    {"id": "env-stage", "name": "Environment reader · STAGE", "stage": "RECONSTRUCT",
     "skill": "environment-reconstruction", "bob": "subagent · explore"},
    {"id": "env-prod", "name": "Environment reader · PROD", "stage": "RECONSTRUCT",
     "skill": "environment-reconstruction", "bob": "subagent · explore"},
    {"id": "validation-memory", "name": "Test history", "stage": "UNDERSTAND",
     "skill": "release-investigation", "bob": "MCP get_untested_edges"},
    {"id": "drift-relevance", "name": "Difference filter", "stage": "UNDERSTAND",
     "skill": "release-investigation", "bob": "MCP get_drift_relevance"},
    {"id": "contract-discovery", "name": "Message format finder", "stage": "UNDERSTAND",
     "skill": "implicit-contract-discovery", "bob": "subagent · general (one per connection)"},
    {"id": "probe-engineer", "name": "Compatibility tester", "stage": "PROVE",
     "skill": "probe-generation", "bob": "mode meridian-probe-engineer"},
    {"id": "first-divergence", "name": "Failing connection finder", "stage": "PROVE",
     "skill": "release-investigation", "bob": "MCP get_first_divergence"},
    {"id": "evidence-reviewer", "name": "Evidence reviewer", "stage": "PROVE",
     "skill": "evidence-review", "bob": "subagent · general"},
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Investigation:
    def __init__(self, environment: str = "prod", reference: str = "stage", pace_ms: int = 0):
        self.id = f"inv-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
        self.environment = environment
        self.reference = reference
        self.pace = pace_ms / 1000
        self.events: list[dict] = []
        self.queue: queue.Queue = queue.Queue()
        self.t0 = time.perf_counter()
        self.done = threading.Event()
        self.result: dict | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ events
    def emit(self, kind: str, **data) -> None:
        event = {"type": kind, "t_ms": int((time.perf_counter() - self.t0) * 1000), "at": _now(), **data}
        with self._lock:
            self.events.append(event)
        self.queue.put(event)

    def agent(self, agent_id: str, status: str, summary: str = "", **detail) -> None:
        self.emit("agent", agent=agent_id, status=status, summary=summary, detail=detail)

    def log(self, agent_id: str, text: str) -> None:
        self.emit("log", agent=agent_id, text=text)

    def _pace(self) -> None:
        if self.pace:
            time.sleep(self.pace)

    def _timed(self, agent_id: str, fn, *args):
        self.agent(agent_id, "running")
        start = time.perf_counter()
        value = fn(*args)
        return value, int((time.perf_counter() - start) * 1000)

    # ------------------------------------------------------------------ steps
    def _release(self):
        release = flows.get_release()
        cr = discovery.change_request()
        notes = discovery.release_note_facts()
        icd = discovery.icd_layouts()
        self.log("release-investigator", f"Release {release['id']}: {release['title']}")
        self.log("release-investigator", f"Target: " + ", ".join(f"{k} {v}" for k, v in release["target"].items()))
        self.log("release-investigator", f"release-notes.docx: {len(notes)} compatibility statements about legacy-ledger")
        self.log("release-investigator", f"interface-control.xlsx: sheets {', '.join(icd.get('sheets', {}))}")
        if cr:
            self.log("release-investigator", f"change-request.pdf: {cr['id']} · {cr['status']} · {cr['window']}")
        return {"release": release, "change_request": cr, "notes": notes}

    def _env(self, env: str):
        self._pace()
        reality = reconstruct_environment(env)
        for src in reality.sources:
            self.log(f"env-{env}", f"read {src['file']} ({src['adapter']}, {src.get('records', 0)} records)")
        return reality

    # ------------------------------------------------------------------ run
    def run(self) -> dict:
        ensure_dirs()
        try:
            self.emit("start", investigation_id=self.id, environment=self.environment,
                      reference=self.reference, agents=AGENTS, pace_ms=int(self.pace * 1000))
            for a in AGENTS:
                self.agent(a["id"], "queued")

            # RECONSTRUCT --------------------------------------------------
            self.emit("stage", stage="RECONSTRUCT", title="Which versions are live?")
            intent, ms = self._timed("release-investigator", self._release)
            self.agent("release-investigator", "done",
                       f"{intent['release']['id']} changes {sum(1 for c, v in intent['release']['target'].items() if intent['release']['baseline'][c] != v)} components; "
                       f"{intent['change_request']['id'] if intent['change_request'] else 'no CR'} pending",
                       duration_ms=ms)
            self._pace()

            realities = {}
            with ThreadPoolExecutor(max_workers=4) as pool:
                starts = {}
                futures = {}
                for env in flows.environments():
                    self.agent(f"env-{env}", "running")
                    starts[env] = time.perf_counter()
                    futures[env] = pool.submit(self._env, env)
                for env, fut in futures.items():
                    reality = fut.result()
                    realities[env] = reality
                    ms = int((time.perf_counter() - starts[env]) * 1000)
                    comp = ", ".join(f"{c} {o.version}" for c, o in reality.components.items()
                                     if c in ("mq-bridge", "legacy-ledger", "ledger-db"))
                    self.agent(f"env-{env}", "done",
                               f"{len(reality.components)}/8 services found · {len(reality.sources)} sources · {comp}",
                               duration_ms=ms, snapshot_id=reality.snapshot_id, missing=reality.missing)
            self._pace()

            # UNDERSTAND ---------------------------------------------------
            self.emit("stage", stage="UNDERSTAND", title="What changed since the tested versions?")
            self.agent("validation-memory", "running")
            start = time.perf_counter()
            pre = {env: evaluate_environment(env, run_probes=False) for env in flows.environments()}
            for env, ev in pre.items():
                self.log("validation-memory", f"{env.upper():5} {ev['verdict']:<11} " +
                         " · ".join(f"{k}={v}" for k, v in ev["counts"].items() if v))
            target_pre = pre[self.environment]
            untested = [e for e in target_pre["edges"] if e["state"] not in ("VERIFIED",)]
            for e in untested:
                self.log("validation-memory", f"{e['producer']} {e['producer_version']} → {e['consumer']} "
                                              f"{e['consumer_version']}: {e['reason']}")
            self.agent("validation-memory", "done",
                       f"{self.environment.upper()}: {len(untested)} of {len(target_pre['edges'])} connections have no passing test",
                       duration_ms=int((time.perf_counter() - start) * 1000),
                       untested=[e["edge_id"] for e in untested])
            self._pace()

            self.agent("drift-relevance", "running")
            start = time.perf_counter()
            drift = relevance(self.reference, self.environment)
            for step in drift["funnel"][:4]:
                self.log("drift-relevance", f"{step['count']:>4}  {step['label']}")
            self.agent("drift-relevance", "done",
                       " → ".join(str(s["count"]) for s in drift["funnel"][:4]) + " (all differences → ones that matter)",
                       duration_ms=int((time.perf_counter() - start) * 1000))
            self._pace()

            self.agent("contract-discovery", "running")
            start = time.perf_counter()
            reality = realities[self.environment]
            members = members_from_reality(reality)
            contracts = {}
            probe_targets = []
            for e in untested:
                edge = flows.get_edge(e["edge_id"])
                p, c = members[edge.producer], members[edge.consumer]
                contract = discovery.discover(edge, p.version, p.commit, c.version, c.commit, p.config)
                contracts[edge.id] = contract
                self.log("contract-discovery", f"{edge.label}: {contract['status']} · {contract['summary']}")
                for constraint in contract.get("constraints", []):
                    mark = "ok " if constraint["compatible"] else "!! "
                    self.log("contract-discovery", f"  {mark}{constraint['field']:<14} sender {constraint['producer']:<18} "
                                                   f"receiver {constraint['consumer']}")
                if contract.get("probe_spec"):
                    probe_targets.append(contract["probe_spec"])
            self.agent("contract-discovery", "done",
                       f"{sum(1 for c in contracts.values() if c['status'] == 'DISCOVERED')} message format(s) rebuilt "
                       f"from code, the interface spreadsheet, release notes and the change request",
                       duration_ms=int((time.perf_counter() - start) * 1000),
                       contracts=list(contracts))
            self._pace()

            # PROVE --------------------------------------------------------
            self.emit("stage", stage="PROVE", title="Does the connection actually work?")
            from engine.probes.probe_engine import run_probe
            self.agent("probe-engineer", "running")
            start = time.perf_counter()
            probe_results = []
            with ThreadPoolExecutor(max_workers=4) as pool:
                for result in pool.map(run_probe, probe_targets):
                    probe_results.append(result)
                    for line in result["transcript"]:
                        self.log("probe-engineer", line["text"])
            self.agent("probe-engineer", "done",
                       ", ".join(f"{r['producer']['component']} → {r['consumer']['component']}: {r['result']}"
                                 + (" (no error raised)" if r["silent_failure"] else "") for r in probe_results) or "no tests needed",
                       duration_ms=int((time.perf_counter() - start) * 1000),
                       runs=[r["run_id"] for r in probe_results])
            self._pace()

            self.agent("first-divergence", "running")
            start = time.perf_counter()
            final = evaluate_environment(self.environment, run_probes=False)
            fd = final["first_divergence"]
            if fd:
                self.log("first-divergence", f"FAILING CONNECTION {fd['producer']} {fd['producer_version']} → "
                                             f"{fd['consumer']} {fd['consumer_version']}")
                self.log("first-divergence", f"untested since {fd['unvalidated_since']} · started by "
                                             f"{(fd['triggering_deployment'] or {}).get('event_id')}")
            self.agent("first-divergence", "done",
                       (f"Failing connection: {fd['producer']} {fd['producer_version']} → {fd['consumer']} {fd['consumer_version']}"
                        if fd else {"CONVERGED": "All connections tested", "UNVALIDATED": "Untested connections, no failure found"}
                        .get(final["verdict"], final["verdict"])),
                       duration_ms=int((time.perf_counter() - start) * 1000))
            self._pace()

            self.agent("evidence-reviewer", "running")
            start = time.perf_counter()
            contract = contracts.get(fd["edge_id"]) if fd else None
            packet = build_packet(final, contract) if fd else None
            if packet:
                for check in packet["review"]["checks"]:
                    self.log("evidence-reviewer", f"{'PASS' if check['passed'] else 'FAIL'}  {check['label']}")
            self.agent("evidence-reviewer", "done",
                       f"{'CONFIRMED' if packet['review']['verdict'] == 'SUPPORTED' else 'NEEDS REVIEW'} · {len(packet['evidence_items'])} evidence items · {packet['packet_id']}"
                       if packet else "nothing to review",
                       duration_ms=int((time.perf_counter() - start) * 1000))

            self.result = {
                "investigation_id": self.id,
                "environment": self.environment,
                "verdict": final["verdict"],
                "first_divergence": fd,
                "packet_id": packet["packet_id"] if packet else None,
                "probe_runs": [r["run_id"] for r in probe_results],
                "funnel": drift["funnel"],
                "duration_ms": int((time.perf_counter() - self.t0) * 1000),
                "pace_ms": int(self.pace * 1000),
            }
            self.emit("complete", result=self.result)
        except Exception as exc:  # noqa: BLE001 - surface every failure to the UI
            self.emit("error", message=f"{type(exc).__name__}: {exc}")
            self.result = {"investigation_id": self.id, "error": str(exc)}
        finally:
            (INVESTIGATIONS / f"{self.id}.json").write_text(
                json.dumps({"investigation_id": self.id, "result": self.result, "events": self.events}, indent=2),
                encoding="utf-8")
            self.done.set()
            self.queue.put(None)
        return self.result

    def start(self) -> "Investigation":
        threading.Thread(target=self.run, daemon=True).start()
        return self


def run_investigation(environment: str = "prod", pace_ms: int = 0) -> dict:
    inv = Investigation(environment, pace_ms=pace_ms)
    inv.run()
    return {"result": inv.result, "events": inv.events}


def load_investigation(investigation_id: str) -> dict | None:
    path = INVESTIGATIONS / f"{investigation_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def latest_investigation() -> dict | None:
    if not INVESTIGATIONS.exists():
        return None
    paths = sorted(INVESTIGATIONS.glob("inv-*.json"), key=lambda p: p.stat().st_mtime)
    return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else None
