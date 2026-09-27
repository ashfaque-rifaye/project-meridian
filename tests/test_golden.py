"""
Meridian Golden End-to-End Test

Asserts the complete critical chain using the current engine API:
  Stage: bridge 3.1 + ledger 7.0 → VERIFIED
  Prod:  bridge 3.1 + ledger 6.9 → UNTESTED/FAILED
  First Demonstrated Divergence: mq-bridge 3.1 -> legacy-ledger 6.9
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_stage_validated():
    """Stage: mq-bridge 3.1 + legacy-ledger 7.0 should have VERIFIED evidence."""
    from engine.domain import flows
    from engine.domain.models import EvidenceTier
    from engine.validation import memory

    edge = next(e for e in flows.get_edges() if e.id == "mq-bridge--legacy-ledger")
    ev = memory.edge_evidence(edge, "3.1", "7.0")
    assert ev.tier == EvidenceTier.VERIFIED, (
        f"Expected VERIFIED for mq-bridge 3.1 + legacy-ledger 7.0, got {ev.tier}"
    )
    assert len(ev.verified) >= 1, "Should have at least one verified run"


def test_prod_combination_untested():
    """Prod: mq-bridge 3.1 + legacy-ledger 6.9 should have no verification evidence."""
    from engine.domain import flows
    from engine.domain.models import EvidenceTier
    from engine.validation import memory

    edge = next(e for e in flows.get_edges() if e.id == "mq-bridge--legacy-ledger")
    ev = memory.edge_evidence(edge, "3.1", "6.9")
    assert ev.tier != EvidenceTier.VERIFIED, (
        f"mq-bridge 3.1 + legacy-ledger 6.9 must NOT be VERIFIED — got {ev.tier}"
    )


def test_prod_divergence_found():
    """Prod evaluation must find mq-bridge 3.1 → legacy-ledger 6.9 as diverged or untested."""
    from engine.divergence.first_divergence import evaluate_environment
    from engine.domain.models import Verdict

    result = evaluate_environment("prod", run_probes=False)
    verdict = result["verdict"]
    # Prod must not be CONVERGED — there is an unvalidated edge
    assert verdict in (Verdict.DIVERGED.value, Verdict.UNVALIDATED.value), (
        f"Prod verdict should be DIVERGED or UNVALIDATED, got {verdict}"
    )


def test_prod_running_correct_versions():
    """Prod must be running mq-bridge 3.1 and legacy-ledger 6.9."""
    from engine.divergence.first_divergence import evaluate_environment

    result = evaluate_environment("prod", run_probes=False)
    comp = result.get("composition", {})
    mqb = comp.get("mq-bridge", {}).get("version")
    ll = comp.get("legacy-ledger", {}).get("version")
    assert mqb == "3.1", f"Expected mq-bridge 3.1 in prod, got {mqb}"
    assert ll == "6.9", f"Expected legacy-ledger 6.9 in prod, got {ll}"


def test_stage_versions_correct():
    """Stage must be running mq-bridge 3.1 and legacy-ledger 7.0."""
    from engine.divergence.first_divergence import evaluate_environment

    result = evaluate_environment("stage", run_probes=False)
    comp = result.get("composition", {})
    mqb = comp.get("mq-bridge", {}).get("version")
    ll = comp.get("legacy-ledger", {}).get("version")
    assert mqb == "3.1", f"Expected mq-bridge 3.1 in stage, got {mqb}"
    assert ll == "7.0", f"Expected legacy-ledger 7.0 in stage, got {ll}"


if __name__ == "__main__":
    print("Running Meridian Golden Tests...")

    test_stage_validated()
    print("  [PASS] Stage: mq-bridge 3.1 + legacy-ledger 7.0 -> VERIFIED")

    test_prod_combination_untested()
    print("  [PASS] Prod: mq-bridge 3.1 + legacy-ledger 6.9 -> not VERIFIED")

    test_prod_divergence_found()
    print("  [PASS] Prod verdict: DIVERGED or UNVALIDATED (not CONVERGED)")

    test_prod_running_correct_versions()
    print("  [PASS] Prod: mq-bridge=3.1, legacy-ledger=6.9")

    test_stage_versions_correct()
    print("  [PASS] Stage: mq-bridge=3.1, legacy-ledger=7.0")

    print()
    print("ALL GOLDEN TESTS PASSED")
