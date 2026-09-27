"""
Adapter contract.

An adapter reads raw state from one kind of system (Kubernetes, WebSphere
Liberty, Flyway, Schema Registry, IBM MQ, ...) and returns normalized
observations. Adapters are strictly read-only: they never call anything that
changes the target environment.

For the hackathon every adapter reads a recorded response from
environments/<env>/adapters/*.json. A live adapter only has to produce the same
document shape (for example by running `kubectl get deployments -A -o json`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RawObservation:
    component: str | None          # flow component id, or None for unrelated workloads
    name: str                      # workload name as the platform reports it
    key: str                       # environment-independent identity used for diffs
    version: str | None
    commit: str | None
    artifact: str | None
    digest: str | None
    deployed_at: str | None
    platform: str
    location: str
    runtime_target: str
    health: str
    pointer: str                   # JSON pointer into the source document
    attributes: dict[str, str] = field(default_factory=dict)


class Adapter(Protocol):
    name: str

    def observe(self, document: dict, source_file: str) -> list[RawObservation]:
        ...


def flatten(value, prefix: str = "") -> dict[str, str]:
    """Flatten nested JSON into dotted leaf paths (used for raw diffs)."""
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            label = v.get("name") if isinstance(v, dict) and "name" in v else str(i)
            out.update(flatten(v, f"{prefix}[{label}]"))
    else:
        out[prefix] = "" if value is None else str(value)
    return out
