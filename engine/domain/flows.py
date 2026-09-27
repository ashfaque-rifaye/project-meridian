"""
Business-flow and release catalog.

Flow definitions live in environments/flows.json and release manifests in
environments/releases.json, so the engine has no scenario data hard-coded.
"""

from __future__ import annotations

import json
from functools import lru_cache

from engine.domain.models import DependencyEdge
from engine.paths import ENVIRONMENTS


def _load(name: str) -> dict:
    path = ENVIRONMENTS / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python fixtures/build_scenario.py` (or ./demo/seed.sh) first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def catalog() -> dict:
    return _load("flows.json")


def reload() -> None:
    catalog.cache_clear()
    releases.cache_clear()


@lru_cache(maxsize=1)
def releases() -> dict:
    return _load("releases.json")


def get_release(release_id: str = "R-26.9") -> dict:
    for release in releases()["releases"]:
        if release["id"] == release_id:
            return release
    raise KeyError(f"Unknown release {release_id}")


def default_release_id() -> str:
    return releases()["releases"][0]["id"]


def get_flow(flow_id: str = "order-to-ledger") -> dict:
    for flow in catalog()["flows"]:
        if flow["id"] == flow_id:
            return flow
    raise KeyError(f"Unknown flow {flow_id}")


def default_flow_id() -> str:
    return catalog()["flows"][0]["id"]


def get_edges(flow_id: str = "order-to-ledger") -> list[DependencyEdge]:
    edges = [DependencyEdge(**e) for e in get_flow(flow_id)["edges"]]
    return sorted(edges, key=lambda e: e.order)


def get_edge(edge_id: str, flow_id: str = "order-to-ledger") -> DependencyEdge:
    for edge in get_edges(flow_id):
        if edge.id == edge_id:
            return edge
    raise KeyError(f"Unknown edge {edge_id}")


def get_components(flow_id: str = "order-to-ledger") -> list[dict]:
    return get_flow(flow_id)["components"]


def component_meta(component_id: str, flow_id: str = "order-to-ledger") -> dict:
    for c in get_components(flow_id):
        if c["id"] == component_id:
            return c
    raise KeyError(component_id)


def environments() -> list[str]:
    return catalog()["environments"]


def promotion_path() -> list[str]:
    return catalog()["promotion_path"]


def snapshot_time() -> str:
    return catalog()["snapshot_time"]
