"""
Drift relevance.

A naive diff between two environments reports every attribute that differs.
Meridian narrows that to what matters for release convergence:

  raw differences
    -> on the selected business flow
    -> change a dependency boundary (a version on either side of an edge)
    -> create a version pair with no passing validation evidence
    -> fail an executable compatibility probe
"""

from __future__ import annotations

from engine.domain import flows
from engine.domain.models import EvidenceTier
from engine.probes import probe_engine
from engine.reconciliation.reconciler import reconstruct_environment
from engine.validation import memory

VERSION_MARKERS = (
    "labels.app.kubernetes.io/version", "image", "annotations.org.opencontainers.image.revision",
    "annotations.org.opencontainers.image.version", "manifest.Implementation-Version",
    "manifest.Implementation-Build", "archive", "subject.version", "subject.id", "subject.schema_git_commit",
)
# Fields that name the environment itself; a diff tool keyed by environment ignores them.
IDENTITY = ("labels.app.kubernetes.io/managed-by",)


def _is_version_attr(attr: str) -> bool:
    return attr.startswith("history.V") or any(attr == m or attr.startswith(m + ".") for m in VERSION_MARKERS)


def raw_diff(reference: str, target: str, flow_id: str | None = None) -> list[dict]:
    ref = reconstruct_environment(reference, flow_id)
    tgt = reconstruct_environment(target, flow_id)
    ref_w = {w.key: w for w in ref.workloads}
    tgt_w = {w.key: w for w in tgt.workloads}
    diffs = []
    for key in sorted(set(ref_w) | set(tgt_w)):
        a, b = ref_w.get(key), tgt_w.get(key)
        if a is None or b is None:
            present = a or b
            diffs.append({"workload": key, "name": present.name, "component": present.component,
                          "attribute": "(workload)", "reference": "present" if a else "absent",
                          "target": "present" if b else "absent", "adapter": present.adapter})
            continue
        for attr in sorted(set(a.attributes) | set(b.attributes)):
            if attr in IDENTITY:
                continue
            va, vb = a.attributes.get(attr), b.attributes.get(attr)
            if va != vb:
                diffs.append({"workload": key, "name": a.name, "component": a.component or b.component,
                              "attribute": attr, "reference": va, "target": vb, "adapter": a.adapter})
    return diffs


def relevance(reference: str = "stage", target: str = "prod", flow_id: str | None = None) -> dict:
    flow_id = flow_id or flows.default_flow_id()
    diffs = raw_diff(reference, target, flow_id)
    ref = reconstruct_environment(reference, flow_id)
    tgt = reconstruct_environment(target, flow_id)
    flow_components = {c["id"] for c in flows.get_components(flow_id)}

    on_flow = [d for d in diffs if d["component"] in flow_components]
    version_changed = sorted({d["component"] for d in on_flow if _is_version_attr(d["attribute"])})

    boundary, unvalidated, failed = [], [], []
    for edge in flows.get_edges(flow_id):
        rp, rc = ref.components.get(edge.producer), ref.components.get(edge.consumer)
        tp, tc = tgt.components.get(edge.producer), tgt.components.get(edge.consumer)
        if not (rp and rc and tp and tc):
            continue
        if (rp.version, rc.version) == (tp.version, tc.version):
            continue
        item = {
            "edge_id": edge.id, "label": edge.label, "interface": edge.interface,
            "reference_pair": [rp.version, rc.version], "target_pair": [tp.version, tc.version],
        }
        boundary.append(item)
        ev = memory.edge_evidence(edge, tp.version, tc.version)
        item["target_evidence"] = ev.tier.value
        if ev.tier != EvidenceTier.VERIFIED:
            unvalidated.append(item)
            probe = probe_engine.latest_result(edge.id, tp.commit, tc.commit)
            item["probe"] = probe["result"] if probe else None
            if probe and probe["result"] == "FAIL":
                failed.append(item)

    for d in diffs:
        if d["component"] not in flow_components:
            d["classification"] = "irrelevant"
            d["why"] = "Workload is not part of the selected business flow."
        elif not _is_version_attr(d["attribute"]):
            d["classification"] = "relevant"
            d["why"] = "Operational difference on a flow component; does not change an interface."
        elif any(d["component"] in (u["label"].split(" → ")) for u in unvalidated):
            d["classification"] = "release-convergence-risk"
            d["why"] = "Version change that leaves a boundary without validation evidence."
        else:
            d["classification"] = "contract-affecting"
            d["why"] = "Version change on a flow component; its boundaries still have validation evidence."

    by_class: dict[str, int] = {}
    for d in diffs:
        by_class[d["classification"]] = by_class.get(d["classification"], 0) + 1

    funnel = [
        {"stage": "raw", "label": "raw environment differences", "count": len(diffs),
         "detail": f"attribute-level diff of every workload in {reference.upper()} vs {target.upper()}"},
        {"stage": "flow", "label": "on the Order-to-Ledger flow", "count": len(on_flow),
         "detail": f"{len(on_flow)} differences across {len({d['component'] for d in on_flow})} flow components"},
        {"stage": "boundary", "label": "change a dependency boundary", "count": len(boundary),
         "detail": f"version changes on {', '.join(version_changed) or 'no components'}"},
        {"stage": "unvalidated", "label": "create an unvalidated version pair", "count": len(unvalidated),
         "detail": ", ".join(u["label"] + f" ({u['target_pair'][0]} → {u['target_pair'][1]})" for u in unvalidated) or "none"},
        {"stage": "failed", "label": "fail executable validation", "count": len(failed),
         "detail": ", ".join(f["label"] for f in failed) or ("probe not run yet" if unvalidated else "none")},
    ]
    return {
        "reference": reference, "target": target, "flow_id": flow_id,
        "funnel": funnel, "by_classification": by_class,
        "boundary_changes": boundary, "differences": diffs,
        "note": "Counts are computed from this demo's synthetic adapter data. They are not industry benchmarks.",
    }
