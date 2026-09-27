"""
File-backed adapters.

Each adapter parses the exact document shape the real system returns
(kubectl JSON, Liberty admin export, flyway_schema_history rows, Schema
Registry REST, IBM MQ REST). In the demo the documents are recorded fixtures;
pointing the same parsers at live read-only APIs is the only change needed.
"""

from __future__ import annotations

from adapters.base import RawObservation, flatten

FLOW_LABEL = "app.kubernetes.io/part-of"


class KubernetesAdapter:
    """EKS, AKS, GKE and OpenShift all return the same Deployment objects."""

    name = "kubernetes"

    def observe(self, document: dict, source_file: str) -> list[RawObservation]:
        out = []
        for index, item in enumerate(document.get("items", [])):
            meta = item.get("metadata", {})
            labels = meta.get("labels", {})
            annotations = meta.get("annotations", {})
            spec = item.get("spec", {})
            pod = spec.get("template", {}).get("spec", {})
            container = (pod.get("containers") or [{}])[0]
            image = container.get("image", "")
            artifact, _, digest = image.partition("@")
            status = item.get("status", {})
            progressing = next(
                (c for c in status.get("conditions", []) if c.get("type") == "Progressing"), {}
            )
            desired = spec.get("replicas", 0)
            ready = status.get("readyReplicas", 0)
            name = meta.get("name", f"item-{index}")
            namespace = meta.get("namespace", "default")
            component = labels.get("app.kubernetes.io/name") if labels.get(FLOW_LABEL) else None
            attributes = flatten({
                "labels": labels,
                "annotations": annotations,
                "replicas": desired,
                "nodeSelector": pod.get("nodeSelector", {}),
                "image": image,
                "resources": container.get("resources", {}),
                "env": {e["name"]: e.get("value", "") for e in container.get("env", [])},
            })
            out.append(RawObservation(
                component=component,
                name=name,
                key=f"k8s:{document.get('platform')}:{namespace}/{name}",
                version=labels.get("app.kubernetes.io/version"),
                commit=annotations.get("org.opencontainers.image.revision"),
                artifact=artifact or None,
                digest=digest or None,
                deployed_at=progressing.get("lastUpdateTime"),
                platform=document.get("platform", "Kubernetes"),
                location=f"{document.get('cluster')} · ns/{namespace}",
                runtime_target=document.get("cluster", ""),
                health=f"{'HEALTHY' if ready >= desired and desired > 0 else 'DEGRADED'} · {ready}/{desired} ready",
                pointer=f"/items/{index}",
                attributes=attributes,
            ))
        return out


class LibertyAdapter:
    name = "websphere-liberty"

    def observe(self, document: dict, source_file: str) -> list[RawObservation]:
        out = []
        for s_index, server in enumerate(document.get("servers", [])):
            for a_index, app in enumerate(server.get("applications", [])):
                manifest = app.get("manifest", {})
                attributes = flatten({
                    "archive": app.get("archive"),
                    "manifest": manifest,
                    "liberty": server.get("liberty", {}),
                    "jvm": server.get("jvm", {}),
                    "vm": {k: v for k, v in server.get("vm", {}).items() if k not in ("vcenter",)},
                    "mq": app.get("mq", {}),
                })
                out.append(RawObservation(
                    component="legacy-ledger" if app.get("name") == "ldgpost" else None,
                    name=app.get("name", "app"),
                    key=f"liberty:{app.get('name')}",
                    version=manifest.get("Implementation-Version"),
                    commit=manifest.get("Implementation-Build"),
                    artifact=app.get("archive"),
                    digest=None,
                    deployed_at=app.get("deployed_at"),
                    platform="WebSphere Liberty",
                    location=f"{server.get('host')} · {server.get('vm', {}).get('cluster', '')}",
                    runtime_target=server.get("host", ""),
                    health=f"{'HEALTHY' if app.get('state') == 'STARTED' else 'DEGRADED'} · {app.get('state')}",
                    pointer=f"/servers/{s_index}/applications/{a_index}",
                    attributes=attributes,
                ))
        return out


class FlywayAdapter:
    name = "flyway"

    def observe(self, document: dict, source_file: str) -> list[RawObservation]:
        rows = [r for r in document.get("flyway_schema_history", []) if r.get("success")]
        if not rows:
            return []
        latest = max(rows, key=lambda r: r["installed_rank"])
        attributes = flatten({
            "history": {f"V{r['version']}": {"script": r["script"], "installed_on": r["installed_on"],
                                            "checksum": r.get("checksum")} for r in rows},
            "schema": document.get("schema"),
        })
        return [RawObservation(
            component="ledger-db",
            name=f"{document.get('database')}/{document.get('schema')}",
            key=f"flyway:{document.get('database')}/{document.get('schema')}",
            version=f"V{latest['version']}",
            commit=document.get("migrations_git_commit"),
            artifact=latest.get("script"),
            digest=None,
            deployed_at=latest.get("installed_on"),
            platform="Db2 LUW",
            location=f"{document.get('host')} · {document.get('database')}",
            runtime_target=document.get("host", ""),
            health=f"HEALTHY · {len(rows)} migrations applied",
            pointer=f"/flyway_schema_history/{rows.index(latest)}",
            attributes=attributes,
        )]


class SchemaRegistryAdapter:
    name = "schema-registry"

    def observe(self, document: dict, source_file: str) -> list[RawObservation]:
        out = []
        for index, subject in enumerate(document.get("subjects", [])):
            out.append(RawObservation(
                component="kafka-orders" if subject.get("subject") == "orders-value" else None,
                name=subject.get("subject", "subject"),
                key=f"kafka:{subject.get('subject')}",
                version=f"v{subject.get('version')}",
                commit=subject.get("schema_git_commit"),
                artifact=f"{subject.get('subject')} v{subject.get('version')} (schema id {subject.get('id')})",
                digest=None,
                deployed_at=subject.get("registered_at"),
                platform="Kafka",
                location=f"{document.get('cluster')} · topic {subject.get('topic')}",
                runtime_target=document.get("cluster", ""),
                health=f"HEALTHY · compatibility {subject.get('compatibility')}",
                pointer=f"/subjects/{index}",
                attributes=flatten({"subject": subject, "config": document.get("config", {})}),
            ))
        return out


class IbmMqAdapter:
    """Queue configuration. Not versioned, but real diffs are full of it."""

    name = "ibm-mq"

    def observe(self, document: dict, source_file: str) -> list[RawObservation]:
        out = []
        for q_index, qmgr in enumerate(document.get("queue_managers", [])):
            for index, queue in enumerate(qmgr.get("queues", [])):
                out.append(RawObservation(
                    component=None,
                    name=f"{qmgr['name']}/{queue['name']}",
                    key=f"mq:{qmgr['name']}/{queue['name']}",
                    version=None, commit=None, artifact=None, digest=None, deployed_at=None,
                    platform="IBM MQ",
                    location=qmgr.get("host", ""),
                    runtime_target=qmgr.get("host", ""),
                    health="HEALTHY",
                    pointer=f"/queue_managers/{q_index}/queues/{index}",
                    attributes=flatten(queue),
                ))
        return out


ADAPTERS = {a.name: a for a in (
    KubernetesAdapter(), LibertyAdapter(), FlywayAdapter(), SchemaRegistryAdapter(), IbmMqAdapter(),
)}
