"""
Meridian domain model.

Plain dataclasses with a `to_dict()` helper. The deterministic engine owns
every state in here; no model output is ever stored as a fact.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EdgeState(str, Enum):
    """User-facing validation state of one dependency edge in one environment."""

    VERIFIED = "VERIFIED"                    # exact pair has passing validation evidence
    VERIFIED_BY_PROBE = "VERIFIED_BY_PROBE"  # previously untested, isolated probe passed
    UNTESTED = "UNTESTED"                    # insufficient evidence, no probe result yet
    FAILED = "FAILED"                        # isolated probe (or validation run) failed
    INCONCLUSIVE = "INCONCLUSIVE"            # compatibility cannot be established
    NEEDS_HUMAN = "NEEDS_HUMAN"              # contract could not be discovered


class EvidenceTier(str, Enum):
    """Strongest kind of historical evidence for a version pair."""

    VERIFIED = "VERIFIED"                    # exercised with semantic assertions that passed
    EXERCISED = "EXERCISED"                  # traffic crossed the edge, no semantic assertions
    OBSERVED_TOGETHER = "OBSERVED_TOGETHER"  # both versions were deployed at the same time
    FAILED = "FAILED"                        # a validation run failed for this pair
    NONE = "NONE"                            # the pair never existed on the promotion path


class ProbeOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class Verdict(str, Enum):
    """Environment-level release convergence verdict."""

    CONVERGED = "CONVERGED"      # every edge on the flow is VERIFIED
    UNVALIDATED = "UNVALIDATED"  # some edges lack evidence; nothing demonstrated to fail
    DIVERGED = "DIVERGED"        # a First Demonstrated Divergence exists


class Serializable:
    def to_dict(self) -> dict[str, Any]:
        def convert(value):
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [convert(v) for v in value]
            return value

        return convert(asdict(self))  # type: ignore[arg-type]


@dataclass
class Observation(Serializable):
    """One flow component as reported by a read-only adapter."""

    component: str
    environment: str
    version: str | None
    commit: str | None
    artifact: str | None
    digest: str | None
    deployed_at: str | None
    platform: str
    location: str
    runtime_target: str
    health: str
    adapter: str
    source: str
    source_pointer: str
    evidence_id: str


@dataclass
class Workload(Serializable):
    """Any workload an adapter reported, used for raw environment diffs."""

    key: str
    name: str
    adapter: str
    component: str | None
    attributes: dict[str, str]


@dataclass
class EnvironmentReality(Serializable):
    environment: str
    snapshot_id: str
    collected_at: str
    components: dict[str, Observation]
    workloads: list[Workload]
    sources: list[dict]
    missing: list[str] = field(default_factory=list)


@dataclass
class DependencyEdge(Serializable):
    id: str
    order: int
    producer: str
    consumer: str
    interface: str
    protocol: str
    contract: dict
    probe_type: str | None = None
    producer_entrypoint: str | None = None
    consumer_entrypoint: str | None = None

    @property
    def label(self) -> str:
        return f"{self.producer} → {self.consumer}"


@dataclass
class EdgeEvidence(Serializable):
    """Everything validation memory knows about one exact version pair."""

    edge_id: str
    producer_version: str
    consumer_version: str
    tier: EvidenceTier
    verified: list[dict]
    exercised: list[dict]
    observed: list[dict]
    failed: list[dict]


@dataclass
class EdgeEvaluation(Serializable):
    edge_id: str
    order: int
    producer: str
    consumer: str
    producer_version: str | None
    consumer_version: str | None
    producer_commit: str | None
    consumer_commit: str | None
    interface: str
    contract: dict
    state: EdgeState
    evidence: EdgeEvidence | None
    probe: dict | None
    reason: str
    combination_since: str | None = None
    created_by_event: dict | None = None
