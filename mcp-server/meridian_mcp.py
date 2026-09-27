#!/usr/bin/env python3
"""
Meridian MCP server for IBM Bob.

Exposes the deterministic Meridian engine to Bob as MCP tools (stdio).
Registered in .bob/mcp.json. Every environment-facing tool is read-only;
the only tools that execute code run isolated probes inside .meridian/sandbox.

    python mcp-server/meridian_mcp.py          # stdio transport (what Bob launches)
    python mcp-server/meridian_mcp.py --list   # print the tool catalogue
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Append (not insert) so the installed `mcp` SDK is never shadowed by a local folder.
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from engine.contracts import discovery  # noqa: E402
from engine.divergence import why  # noqa: E402
from engine.divergence.first_divergence import evaluate_environment, members_from_reality  # noqa: E402
from engine.domain import flows  # noqa: E402
from engine.drift.relevance import relevance  # noqa: E402
from engine.evidence import packet as packets  # noqa: E402
from engine.paths import AGENT_FINDINGS, DOCUMENTS, ensure_dirs  # noqa: E402
from engine.probes import probe_engine, workspace  # noqa: E402
from engine.reconciliation import history  # noqa: E402
from engine.reconciliation.reconciler import reconstruct_environment  # noqa: E402
from engine.rehearsal.rehearsal import rehearse  # noqa: E402
from engine.remediation import remediation  # noqa: E402
from engine.validation import memory  # noqa: E402


def _envelope(data, evidence: list | None = None, note: str | None = None) -> dict:
    out = {"data": data, "evidence": evidence or [], "generated_at": datetime.now(timezone.utc).isoformat()}
    if note:
        out["note"] = note
    return out


# --------------------------------------------------------------------------- tools

def get_release_intent(release_id: str = "R-26.9") -> dict:
    """Release scope, target versions, rollout order and dependencies (release manifest + documents)."""
    release = flows.get_release(release_id)
    return _envelope({
        "release": release,
        "change_request": discovery.change_request(),
        "release_note_facts": discovery.release_note_facts(),
    }, evidence=["environments/releases.json", "documents/release-notes.docx", "documents/change-request.pdf"],
        note="Release intent is contextual evidence, not proof of what is running.")


def get_environment_snapshot(environment: str) -> dict:
    """What is actually running in an environment, normalized from read-only adapter outputs."""
    reality = reconstruct_environment(environment)
    data = reality.to_dict()
    data.pop("workloads", None)
    return _envelope(data, evidence=[c["evidence_id"] for c in data["components"].values()],
                     note="Values come from adapters only. Missing values are listed in `missing`.")


def get_environment_history(environment: str) -> dict:
    """Deployment events and every composition the environment has run, with timestamps."""
    return _envelope({
        "events": history.events(environment),
        "segments": [s.to_dict() for s in history.segments(environment)],
        "scheduled": history.scheduled_changes(environment),
    }, evidence=["environments/deployment-events.json", "environments/scheduled-changes.json"])


def get_component_versions(component: str) -> dict:
    """Released versions, commits and recent git history for a component."""
    return _envelope({"versions": workspace.known_commits().get(component, {}),
                      "log": workspace.log(component)}, evidence=[f".meridian/repos/{component}"])


def get_business_flow(flow_id: str = "order-to-ledger") -> dict:
    """Ordered components and dependency edges of a business flow."""
    return _envelope(flows.get_flow(flow_id), evidence=["environments/flows.json"])


def get_dependency_edges(environment: str = "prod") -> dict:
    """Every edge of the flow with running versions and validation state in an environment."""
    ev = evaluate_environment(environment)
    return _envelope({"verdict": ev["verdict"], "edges": ev["edges"]},
                     evidence=[e["edge_id"] for e in ev["edges"]])


def get_validation_history(edge_id: str, producer_version: str, consumer_version: str) -> dict:
    """Validation memory for one exact version pair: verified / exercised / observed together / failed."""
    edge = flows.get_edge(edge_id)
    ev = memory.edge_evidence(edge, producer_version, consumer_version)
    return _envelope({"evidence": ev.to_dict(), "summary": memory.describe(ev), "ledger": memory.edge_ledger(edge)},
                     evidence=[v["evidence_id"] for v in ev.verified + ev.exercised] + [w["evidence_id"] for w in ev.observed],
                     note="Observed together is not validated together.")


def get_untested_edges(environment: str = "prod") -> dict:
    """Edges whose running version pair lacks passing validation evidence."""
    ev = evaluate_environment(environment)
    return _envelope([e for e in ev["edges"] if e["state"] != "VERIFIED"])


def get_drift_relevance(reference: str = "stage", target: str = "prod") -> dict:
    """Naive environment diff narrowed to the differences that affect release convergence."""
    r = relevance(reference, target)
    r["differences"] = r["differences"][:40]
    return _envelope(r, note="Only the first 40 raw differences are included; counts cover all of them.")


def get_interface_document() -> dict:
    """LEDG-ICD-007 interface control document (read from documents/interface-control.xlsx)."""
    return _envelope(discovery.icd_layouts(), evidence=["documents/interface-control.xlsx"])


def get_change_request() -> dict:
    """CR-4471 metadata (the PDF is at documents/change-request.pdf)."""
    return _envelope(json.loads((DOCUMENTS / "change-request-data.json").read_text(encoding="utf-8")),
                     evidence=["documents/change-request.pdf"])


def get_release_notes() -> dict:
    """R-26.9 release notes (the DOCX is at documents/release-notes.docx)."""
    return _envelope(json.loads((DOCUMENTS / "release-notes-data.json").read_text(encoding="utf-8")),
                     evidence=["documents/release-notes.docx"])


def read_source(component: str, commit: str, path: str) -> dict:
    """Read a file from a component repository at an exact commit (git show)."""
    return _envelope({"component": component, "commit": commit, "path": path,
                      "content": workspace.show(component, commit, path)},
                     evidence=[f"{component}@{commit}:{path}"])


def discover_implicit_contract(edge_id: str, environment: str = "prod") -> dict:
    """Reconstruct the implicit contract of an edge from deployed code + ICD + release notes + CR. Returns a probe spec."""
    edge = flows.get_edge(edge_id)
    members = members_from_reality(reconstruct_environment(environment))
    p, c = members[edge.producer], members[edge.consumer]
    contract = discovery.discover(edge, p.version, p.commit, c.version, c.commit, p.config)
    return _envelope(contract, note="The contract proposes a probe. It never decides compatibility.")


def create_probe_spec(edge_id: str, environment: str = "prod") -> dict:
    """Build the runnable probe specification for an edge's running version pair."""
    contract = discover_implicit_contract(edge_id, environment)["data"]
    return _envelope(contract.get("probe_spec"), note=contract.get("summary"))


def run_probe(edge_id: str, environment: str = "prod") -> dict:
    """Run the compatibility probe for an edge in an isolated sandbox (never against an environment)."""
    spec = create_probe_spec(edge_id, environment)["data"]
    if not spec:
        return _envelope(None, note="No executable probe for this interface. Result: NEEDS_HUMAN.")
    result = probe_engine.run_probe(spec)
    result.pop("stdout", None)
    return _envelope(result, evidence=[result["evidence_id"]])


def get_probe_result(run_id: str) -> dict:
    """A persisted probe run with fixtures, assertions and transcript."""
    return _envelope(probe_engine.get_run(run_id), evidence=[run_id])


def get_first_divergence(environment: str = "prod") -> dict:
    """Deterministic First Demonstrated Divergence for the flow in an environment."""
    ev = evaluate_environment(environment)
    return _envelope({"verdict": ev["verdict"], "first_divergence": ev["first_divergence"],
                      "promotion_pattern": why.promotion_pattern(environment)["story"]},
                     note="A factual observation about an unvalidated boundary, not a causal claim.")


def get_evidence_packet(environment: str = "prod") -> dict:
    """Build (or rebuild) the evidence packet behind the First Demonstrated Divergence."""
    ev = evaluate_environment(environment)
    fd = ev["first_divergence"]
    if not fd:
        return _envelope(None, note="No First Demonstrated Divergence. Run run_probe on untested edges first.")
    edge = flows.get_edge(fd["edge_id"])
    p = members_from_reality(reconstruct_environment(environment))[edge.producer]
    contract = discovery.discover(edge, fd["producer_version"], fd["producer_commit"],
                                  fd["consumer_version"], fd["consumer_commit"], p.config)
    return _envelope(packets.build_packet(ev, contract))


def simulate_promotion(environment: str, component: str, version: str) -> dict:
    """Counterfactual promotion rehearsal. Deploys nothing; probes run in the sandbox."""
    return _envelope(rehearse(environment, [{"component": component, "version": version}], run_probes=True))


def verify_remediation(strategy: str = "bridge-compat-mode", environment: str = "prod") -> dict:
    """Rehearse a remediation strategy (converge-forward | bridge-compat-mode | hold-bridge) with regression probes."""
    return _envelope(remediation.rehearse_strategy(strategy, environment),
                     note="Candidate fixes live on an isolated branch/worktree. Nothing is deployed.")


def record_agent_finding(agent: str, kind: str, target_edge_id: str, summary: str,
                         details_json: str = "{}", producer_version: str = "", consumer_version: str = "") -> dict:
    """Record a Bob subagent finding (e.g. kind='contract') so it appears in the Meridian UI and evidence."""
    ensure_dirs()
    try:
        details = json.loads(details_json or "{}")
    except json.JSONDecodeError:
        details = {"raw": details_json}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    finding = {
        "finding_id": f"finding-{stamp}-{agent}",
        "agent": agent, "kind": kind, "summary": summary, "details": details,
        "target": {"edge_id": target_edge_id, "producer_version": producer_version or None,
                   "consumer_version": consumer_version or None},
        "recorded_at": datetime.now(timezone.utc).isoformat(), "author": "IBM Bob",
    }
    (AGENT_FINDINGS / f"{finding['finding_id']}.json").write_text(json.dumps(finding, indent=2), encoding="utf-8")
    return _envelope(finding, note="Findings are attached as context. They never change a probe result.")


TOOLS = [
    get_release_intent, get_environment_snapshot, get_environment_history, get_component_versions,
    get_business_flow, get_dependency_edges, get_validation_history, get_untested_edges, get_drift_relevance,
    get_interface_document, get_change_request, get_release_notes, read_source, discover_implicit_contract,
    create_probe_spec, run_probe, get_probe_result, get_first_divergence, get_evidence_packet,
    simulate_promotion, verify_remediation, record_agent_finding,
]
EXECUTES_IN_SANDBOX = {"run_probe", "simulate_promotion", "verify_remediation"}
WRITES_MERIDIAN_ONLY = {"record_agent_finding", "get_evidence_packet"}

TOOL_CATALOG = [
    {"name": t.__name__, "description": (t.__doc__ or "").strip(),
     "access": "sandbox execution" if t.__name__ in EXECUTES_IN_SANDBOX
     else ("writes .meridian/ only" if t.__name__ in WRITES_MERIDIAN_ONLY else "read-only")}
    for t in TOOLS
]


def main() -> None:
    if "--list" in sys.argv:
        for tool in TOOL_CATALOG:
            print(f"{tool['name']:<28} {tool['access']:<22} {tool['description']}")
        return
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(
        "meridian",
        instructions=(
            "Meridian verifies release convergence: whether the exact composition running in an environment "
            "was ever validated together. Environment tools are read-only. Probes run only in an isolated "
            "sandbox. Never call a compatibility result PASS or FAIL yourself; run_probe decides. Use the term "
            "'First Demonstrated Divergence', never 'root cause'."
        ),
    )
    for tool in TOOLS:
        server.add_tool(tool)
    server.run("stdio")


if __name__ == "__main__":
    main()
