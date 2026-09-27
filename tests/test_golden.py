"""
Meridian golden end-to-end test.

Asserts the complete critical chain on the synthetic R-26.9 scenario:

  Stage:  mq-bridge 3.1 + legacy-ledger 7.0  -> VERIFIED
  Prod:   mq-bridge 3.1 + legacy-ledger 6.9  -> not validated (EXERCISED in DEV, OBSERVED in TEST, never VERIFIED)
  Probe:  exact deployed commits, isolated   -> FAIL, silent (HTTP 200 / MQ ACK / DB COMMIT, wrong data)
  First Demonstrated Divergence              -> mq-bridge 3.1 -> legacy-ledger 6.9, created by the 11:42 Argo CD sync
  Rehearsal: CR-4471 (ledger 7.0 + V15)      -> CONVERGED
  Remediation B (bridge compatibility mode)  -> regression probe PASS

    python -m pytest tests/test_golden.py -v
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EDGE = "mq-bridge--legacy-ledger"


@pytest.fixture(scope="session", autouse=True)
def scenario():
    from engine.paths import REPOS
    if not (REPOS / "mq-bridge" / ".git").exists():
        from fixtures.build_scenario import build
        build(quiet=True)


def _edge(edge_id):
    from engine.domain import flows
    return flows.get_edge(edge_id)


def test_stage_pair_is_verified():
    from engine.domain.models import EvidenceTier
    from engine.validation.memory import edge_evidence
    ev = edge_evidence(_edge(EDGE), "3.1", "7.0")
    assert ev.tier == EvidenceTier.VERIFIED
    assert any(v["environment"] == "stage" for v in ev.verified)


def test_prod_pair_was_never_validated():
    from engine.domain.models import EvidenceTier
    from engine.validation.memory import edge_evidence
    ev = edge_evidence(_edge(EDGE), "3.1", "6.9")
    assert ev.tier == EvidenceTier.EXERCISED, "smoke test crossed the edge without semantic assertions"
    assert not ev.verified
    assert {w["environment"] for w in ev.observed} >= {"dev", "test"}


def test_prod_reality_comes_from_adapters():
    from engine.reconciliation.reconciler import reconstruct_environment
    prod = reconstruct_environment("prod")
    assert prod.components["mq-bridge"].version == "3.1"
    assert prod.components["legacy-ledger"].version == "6.9"
    assert prod.components["legacy-ledger"].adapter == "websphere-liberty"
    assert not prod.missing


def test_probe_demonstrates_silent_failure():
    from engine.contracts import discovery
    from engine.divergence.first_divergence import members_from_reality
    from engine.probes.probe_engine import run_probe
    from engine.reconciliation.reconciler import reconstruct_environment
    edge = _edge(EDGE)
    m = members_from_reality(reconstruct_environment("prod"))
    contract = discovery.discover(edge, "3.1", m["mq-bridge"].commit, "6.9", m["legacy-ledger"].commit)
    assert contract["status"] == "DISCOVERED"
    assert {c["field"] for c in contract["constraints"] if not c["compatible"]} == {"customer_id", "currency_code", "amount"}
    result = run_probe(contract["probe_spec"])
    assert result["result"] == "FAIL"
    assert result["silent_failure"] is True
    new_customer = next(f for f in result["fixtures"] if f["fixture"] == "fx-new-customer-usd")
    posted = {a["field"]: a["actual"] for a in new_customer["assertions"]}
    assert posted["customer_id"] == "CUST123456"
    assert new_customer["infrastructure"]["db_commit"] is True


def test_first_demonstrated_divergence():
    from engine.divergence.first_divergence import evaluate_environment
    ev = evaluate_environment("prod", run_probes=True)
    assert ev["verdict"] == "DIVERGED"
    fd = ev["first_divergence"]
    assert fd["edge_id"] == EDGE
    assert (fd["producer_version"], fd["consumer_version"]) == ("3.1", "6.9")
    assert fd["unvalidated_since"] == "2026-09-25T11:42:00Z"
    assert fd["triggering_deployment"]["tool"].startswith("Argo CD")


def test_lower_environments_converged():
    from engine.divergence.first_divergence import evaluate_environment
    for env in ("dev", "test", "stage"):
        assert evaluate_environment(env)["verdict"] == "CONVERGED", env


def test_rehearsal_of_cr_4471_converges():
    from engine.rehearsal.rehearsal import rehearse
    r = rehearse("prod", [{"component": "ledger-db", "version": "V15"}, {"component": "legacy-ledger", "version": "7.0"}])
    assert r["verdict"] == "CONVERGED"
    assert r["deployed_anything"] is False


def test_remediation_compat_mode_passes_regression_probe():
    from engine.remediation import remediation
    out = remediation.rehearse_strategy("bridge-compat-mode")
    assert out["critical_edge"]["state"] == "VERIFIED_BY_PROBE"
    assert out["candidate"]["branch"].endswith("compat-mode")


def test_guard_blocks_environment_mutation():
    import subprocess
    guard = ROOT / ".bob" / "hooks" / "guard.py"
    blocked = subprocess.run([sys.executable, str(guard), "kubectl --context ocp-prod-dc2 apply -f bridge.yaml"])
    allowed = subprocess.run([sys.executable, str(guard), "kubectl get deployments -A -o json"])
    assert blocked.returncode == 2
    assert allowed.returncode == 0
