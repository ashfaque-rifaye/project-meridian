"""
Meridian MCP Server
Exposes read-only tools for IBM Bob to investigate release convergence.

All tools return structured JSON. All environment access is read-only.
Probe execution is isolated in subprocess. No production mutation possible.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: mcp package not installed. Install with: pip install mcp", file=sys.stderr)

ENVIRONMENTS_DIR = PROJECT_ROOT / "environments"
DOCUMENTS_DIR = PROJECT_ROOT / "documents"


def load_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)


# ─────────────────────────── Tool implementations ────────────────────────────

def tool_get_release_intent(release_id: str = "R-26.9") -> dict:
    notes_path = DOCUMENTS_DIR / "release-notes-data.json"
    cr_path = DOCUMENTS_DIR / "change-request-data.json"
    
    result = {"release_id": release_id, "evidence": []}
    
    if notes_path.exists():
        notes = load_json(notes_path)
        result["title"] = notes.get("release_title")
        result["changed_services"] = notes.get("changed_services", [])
        result["deployment_dependencies"] = notes.get("deployment_dependencies", [])
        result["rollout_order"] = notes.get("expected_rollout_order", [])
        result["compatibility_notes"] = notes.get("compatibility_notes", [])
        result["validated_combination"] = notes.get("validated_combination")
        result["evidence"].append({"source": "release-notes-data.json", "id": "ev-doc-rn-001"})
    
    if cr_path.exists():
        cr = load_json(cr_path)
        result["change_request"] = cr
        result["evidence"].append({"source": "change-request-data.json", "id": "ev-doc-cr-001"})
    
    return result


def tool_get_environment_snapshot(environment: str, flow_id: str = "order-to-ledger") -> dict:
    snap_path = ENVIRONMENTS_DIR / environment / "snapshot.json"
    if not snap_path.exists():
        return {"error": f"No snapshot for environment '{environment}'", "state": "INCONCLUSIVE"}
    
    data = load_json(snap_path)
    return {
        "environment": data["environment"],
        "flow": flow_id,
        "snapshot_id": data["snapshot_id"],
        "snapshot_time": data.get("snapshot_time"),
        "components": [
            {
                "name": d["component"],
                "version": d["version"],
                "commit": d.get("commit"),
                "deployed_at": d.get("deployed_at"),
                "config_fingerprint": d.get("config_fingerprint"),
                "schema_version": d.get("schema_version"),
                "evidence_id": d.get("evidence_id"),
            }
            for d in data.get("deployments", [])
        ],
        "evidence": [{"source": f"environments/{environment}/snapshot.json", "id": data["snapshot_id"]}],
    }


def tool_get_environment_history(environment: str, flow_id: str = "order-to-ledger") -> dict:
    history_path = ENVIRONMENTS_DIR / environment / "deployment-history.json"
    if not history_path.exists():
        return {"environment": environment, "history": [], "note": "No deployment history file found"}
    
    return {
        "environment": environment,
        "history": load_json(history_path),
        "evidence": [{"source": f"environments/{environment}/deployment-history.json"}],
    }


def tool_get_validation_history(edge_id: str = None) -> dict:
    all_evidence = []
    for env_dir in ENVIRONMENTS_DIR.iterdir():
        if not env_dir.is_dir():
            continue
        ev_path = env_dir / "validation-evidence.json"
        if ev_path.exists():
            records = load_json(ev_path)
            for r in records:
                if r.get("_comment"):
                    continue
                if edge_id is None or r.get("edge_id") == edge_id:
                    all_evidence.append(r)
    
    return {
        "edge_id": edge_id,
        "records": all_evidence,
        "count": len(all_evidence),
        "evidence": [{"source": "environments/*/validation-evidence.json"}],
    }


def tool_get_untested_edges(environment: str, flow_id: str = "order-to-ledger") -> dict:
    from engine.divergence.first_divergence import get_all_edge_states
    states = get_all_edge_states(flow_id, environment)
    untested = [s for s in states if s["state"] in ("UNTESTED", "FAILED", "INCONCLUSIVE")]
    return {
        "environment": environment,
        "flow_id": flow_id,
        "untested_edges": untested,
        "count": len(untested),
    }


def tool_get_interface_document(interface_name: str = "BILL.OUT") -> dict:
    doc_path = DOCUMENTS_DIR / "interface-control-data.json"
    if not doc_path.exists():
        return {"error": "Interface document not found", "state": "INCONCLUSIVE"}
    
    fields = load_json(doc_path)
    return {
        "interface": interface_name,
        "document": "interface-control.xlsx (synthetic)",
        "fields": fields,
        "evidence": [{"source": "documents/interface-control-data.json", "id": "ev-doc-ic-001"}],
    }


def tool_get_change_request(cr_id: str = "CR-4471") -> dict:
    cr_path = DOCUMENTS_DIR / "change-request-data.json"
    if not cr_path.exists():
        return {"error": "Change request not found", "state": "INCONCLUSIVE"}
    
    cr = load_json(cr_path)
    if cr.get("cr_id") != cr_id:
        return {"error": f"CR {cr_id} not found", "available": cr.get("cr_id")}
    
    return {**cr, "evidence": [{"source": "documents/change-request-data.json", "id": "ev-doc-cr-001"}]}


def tool_get_release_notes(release_id: str = "R-26.9") -> dict:
    notes_path = DOCUMENTS_DIR / "release-notes-data.json"
    if not notes_path.exists():
        return {"error": "Release notes not found", "state": "INCONCLUSIVE"}
    
    notes = load_json(notes_path)
    return {**notes, "evidence": [{"source": "documents/release-notes-data.json", "id": "ev-doc-rn-001"}]}


def tool_get_business_flow(flow_id: str = "order-to-ledger") -> dict:
    from engine.domain.flows import FLOWS, COMPONENTS
    flow = FLOWS.get(flow_id)
    if not flow:
        return {"error": f"Flow '{flow_id}' not found"}
    return {
        "flow_id": flow_id,
        "name": "Order-to-Ledger",
        "edges": [
            {"edge_id": e.edge_id, "producer": e.producer, "consumer": e.consumer,
             "interface": e.interface, "order": e.order}
            for e in sorted(flow, key=lambda x: x.order)
        ],
        "components": COMPONENTS,
    }


def tool_get_first_divergence(environment: str = "prod", flow_id: str = "order-to-ledger") -> dict:
    from engine.divergence.first_divergence import find_first_divergence
    div = find_first_divergence(flow_id, environment)
    if not div:
        return {"environment": environment, "divergence": None, "status": "VERIFIED"}
    
    return {
        "divergence_id": div.divergence_id,
        "environment": environment,
        "edge_id": div.edge_id,
        "producer": div.producer,
        "producer_version": div.producer_version,
        "producer_commit": div.producer_commit,
        "producer_deployed_at": div.producer_deployed_at.isoformat(),
        "consumer": div.consumer,
        "consumer_version": div.consumer_version,
        "consumer_commit": div.consumer_commit,
        "consumer_deployed_at": div.consumer_deployed_at.isoformat(),
        "unvalidated_since": div.unvalidated_since.isoformat(),
        "triggering_deployment": div.triggering_deployment,
        "probe_id": div.probe_id,
        "probe_result": div.probe_result.value if div.probe_result else None,
        "status": "DIVERGED",
    }


def tool_run_probe(probe_id: str = "probe-001") -> dict:
    from engine.probes.probe_engine import get_default_probe_spec, run_probe
    spec = get_default_probe_spec()
    spec.probe_id = probe_id
    
    execution = run_probe(spec)
    return {
        "probe_id": execution.probe_id,
        "connection": execution.connection,
        "result": execution.result.value,
        "assertion_results": execution.assertion_results,
        "stdout": execution.stdout[:2000],
        "exit_code": execution.exit_code,
        "executed_at": execution.executed_at.isoformat(),
        "evidence_id": execution.evidence_id,
    }


def tool_simulate_promotion(
    environment: str = "prod",
    flow_id: str = "order-to-ledger",
    proposed_component: str = "legacy-ledger",
    proposed_version: str = "7.0",
) -> dict:
    from engine.rehearsal.rehearsal import simulate_promotion
    sim = simulate_promotion(environment, flow_id, proposed_component, proposed_version)
    return {
        "simulation_id": sim.simulation_id,
        "result": sim.result,
        "summary": sim.summary,
        "predicted_composition": sim.predicted_composition,
        "edge_results": sim.edge_results,
    }


# ─────────────────────────── MCP server registration ─────────────────────────

TOOLS_MAP = {
    "get_release_intent": tool_get_release_intent,
    "get_environment_snapshot": tool_get_environment_snapshot,
    "get_environment_history": tool_get_environment_history,
    "get_validation_history": tool_get_validation_history,
    "get_untested_edges": tool_get_untested_edges,
    "get_interface_document": tool_get_interface_document,
    "get_change_request": tool_get_change_request,
    "get_release_notes": tool_get_release_notes,
    "get_business_flow": tool_get_business_flow,
    "get_first_divergence": tool_get_first_divergence,
    "run_probe": tool_run_probe,
    "simulate_promotion": tool_simulate_promotion,
}


def main():
    if not MCP_AVAILABLE:
        print("ERROR: mcp package required. Install: pip install mcp", file=sys.stderr)
        sys.exit(1)
    
    server = Server("meridian")
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="get_release_intent", description="Get release intent, changed components, and deployment dependencies for a release", inputSchema={"type": "object", "properties": {"release_id": {"type": "string", "default": "R-26.9"}}}),
            Tool(name="get_environment_snapshot", description="Get the actual running component versions in an environment", inputSchema={"type": "object", "properties": {"environment": {"type": "string", "enum": ["dev","test","stage","prod"]}, "flow_id": {"type": "string", "default": "order-to-ledger"}}, "required": ["environment"]}),
            Tool(name="get_environment_history", description="Get deployment history for an environment", inputSchema={"type": "object", "properties": {"environment": {"type": "string"}, "flow_id": {"type": "string", "default": "order-to-ledger"}}, "required": ["environment"]}),
            Tool(name="get_validation_history", description="Get validation evidence records for a dependency edge", inputSchema={"type": "object", "properties": {"edge_id": {"type": "string"}}}),
            Tool(name="get_untested_edges", description="Get all unvalidated dependency edges in an environment", inputSchema={"type": "object", "properties": {"environment": {"type": "string"}, "flow_id": {"type": "string", "default": "order-to-ledger"}}, "required": ["environment"]}),
            Tool(name="get_interface_document", description="Get the interface control document specifying fixed-width field layout", inputSchema={"type": "object", "properties": {"interface_name": {"type": "string", "default": "BILL.OUT"}}}),
            Tool(name="get_change_request", description="Get the CAB change request document", inputSchema={"type": "object", "properties": {"cr_id": {"type": "string", "default": "CR-4471"}}}),
            Tool(name="get_release_notes", description="Get release notes including compatibility warnings and rollout order", inputSchema={"type": "object", "properties": {"release_id": {"type": "string", "default": "R-26.9"}}}),
            Tool(name="get_business_flow", description="Get the business flow definition with ordered dependency edges", inputSchema={"type": "object", "properties": {"flow_id": {"type": "string", "default": "order-to-ledger"}}}),
            Tool(name="get_first_divergence", description="Get the First Demonstrated Divergence for an environment — deterministic result", inputSchema={"type": "object", "properties": {"environment": {"type": "string", "default": "prod"}, "flow_id": {"type": "string", "default": "order-to-ledger"}}}),
            Tool(name="run_probe", description="Execute a compatibility probe in isolation. SAFE — never accesses production", inputSchema={"type": "object", "properties": {"probe_id": {"type": "string", "default": "probe-001"}}}),
            Tool(name="simulate_promotion", description="Rehearse a promotion without deploying — predicts validation impact", inputSchema={"type": "object", "properties": {"environment": {"type": "string", "default": "prod"}, "flow_id": {"type": "string", "default": "order-to-ledger"}, "proposed_component": {"type": "string"}, "proposed_version": {"type": "string"}}, "required": ["proposed_component", "proposed_version"]}),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        handler = TOOLS_MAP.get(name)
        if not handler:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
        
        try:
            result = handler(**arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}))]
    
    import asyncio
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
