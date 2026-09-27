"""
Environment reconciliation.

RECONSTRUCT step: turn raw, read-only adapter outputs into one normalized
EnvironmentReality per environment. Nothing here is inferred: a value the
adapters did not report stays missing and is surfaced as such.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from adapters.synthetic import ADAPTERS
from engine.domain import flows
from engine.domain.models import EnvironmentReality, Observation, Workload
from engine.paths import ENVIRONMENTS


def _evidence_id(env: str, component: str, source: str, pointer: str) -> str:
    digest = hashlib.sha1(f"{source}#{pointer}".encode()).hexdigest()[:6]
    return f"obs-{env}-{component}-{digest}"


def reconstruct_environment(environment: str, flow_id: str | None = None) -> EnvironmentReality:
    flow_id = flow_id or flows.default_flow_id()
    adapter_dir = ENVIRONMENTS / environment / "adapters"
    if not adapter_dir.exists():
        raise FileNotFoundError(f"No adapter outputs for environment '{environment}' in {adapter_dir}")

    flow_components = {c["id"] for c in flows.get_components(flow_id)}
    components: dict[str, Observation] = {}
    workloads: list[Workload] = []
    sources: list[dict] = []
    collected = []

    for path in sorted(adapter_dir.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        adapter = ADAPTERS.get(document.get("adapter", ""))
        rel = path.relative_to(ENVIRONMENTS.parent).as_posix()
        if adapter is None:
            sources.append({"file": rel, "adapter": document.get("adapter"), "status": "UNSUPPORTED"})
            continue
        raw = adapter.observe(document, rel)
        collected.append(document.get("collected_at", ""))
        sources.append({
            "file": rel,
            "adapter": adapter.name,
            "command": document.get("source"),
            "collected_at": document.get("collected_at"),
            "records": len(raw),
            "status": "READ",
        })
        for r in raw:
            workloads.append(Workload(key=r.key, name=r.name, adapter=adapter.name,
                                      component=r.component, attributes=r.attributes))
            if r.component and r.component in flow_components:
                components[r.component] = Observation(
                    component=r.component,
                    environment=environment,
                    version=r.version,
                    commit=r.commit,
                    artifact=r.artifact,
                    digest=r.digest,
                    deployed_at=r.deployed_at,
                    platform=r.platform,
                    location=r.location,
                    runtime_target=r.runtime_target,
                    health=r.health,
                    adapter=adapter.name,
                    source=rel,
                    source_pointer=r.pointer,
                    evidence_id=_evidence_id(environment, r.component, rel, r.pointer),
                )

    collected_at = max(collected) if collected else ""
    stamp = collected_at.replace("-", "").replace(":", "").replace("T", "-").rstrip("Z")[:13]
    return EnvironmentReality(
        environment=environment,
        snapshot_id=f"snap-{environment}-{stamp}",
        collected_at=collected_at,
        components=components,
        workloads=workloads,
        sources=sources,
        missing=sorted(flow_components - set(components)),
    )


def reconstruct_all(flow_id: str | None = None) -> dict[str, EnvironmentReality]:
    return {env: reconstruct_environment(env, flow_id) for env in flows.environments()}


def parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
