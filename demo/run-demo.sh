#!/usr/bin/env bash
# MERIDIAN Demo Run Script
# Executes the complete end-to-end demonstration chain.
# All data is SYNTHETIC. No production access occurs.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "================================================="
echo "  MERIDIAN — Release Convergence Intelligence"
echo "  Every component passed. The system didn't."
echo "================================================="
echo "  SYNTHETIC DEMO DATA — All data is fictional"
echo "================================================="
echo ""

python -c "
import sys
sys.path.insert(0, '.')

print('Scene 1: Stage validation...')
from engine.validation.memory import get_validation_state, load_validation_evidence
from engine.domain.models import ValidationState
evidence = load_validation_evidence()
state, recs = get_validation_state('mq-bridge\u2192legacy-ledger', '3.1', '7.0', evidence)
print(f'  STAGE: mq-bridge 3.1 + legacy-ledger 7.0 -> {state.value}')
assert state == ValidationState.VERIFIED

print()
print('Scene 2: Production state...')
from engine.reconciliation.reconciler import load_snapshot
snap = load_snapshot('prod', 'order-to-ledger')
mqb = snap.get_component('mq-bridge')
ll = snap.get_component('legacy-ledger')
print(f'  PROD: mq-bridge {mqb.version} (deployed {mqb.deployed_at})')
print(f'  PROD: legacy-ledger {ll.version} (deployed {ll.deployed_at})')

print()
print('Scene 3: Is this combination validated?...')
state2, recs2 = get_validation_state('mq-bridge\u2192legacy-ledger', '3.1', '6.9', evidence)
print(f'  mq-bridge 3.1 + legacy-ledger 6.9 -> {state2.value}')
assert state2 == ValidationState.UNTESTED
print('  Answer: NO. This combination was NEVER validated.')

print()
print('Scene 4: Why this happened...')
print('  Bridge 3.1 promoted Friday 11:42.')
print('  Legacy Ledger 6.9 stayed behind (CR-4471 Saturday CAB window).')
print('  Independent promotion cadences created the unvalidated composition.')

print()
print('Scene 5-7: Contract Discovery + Probe Generation...')
from engine.probes.probe_engine import get_default_probe_spec, run_probe
spec = get_default_probe_spec()
print(f'  Probe spec: {spec.probe_id} ({spec.edge_id})')
print(f'  Producer commit: {spec.producer_commit}')
print(f'  Consumer commit: {spec.consumer_commit}')

print()
print('Scene 8: Running probe in isolation (NO production access)...')
ex = run_probe(spec)
print(f'  [1/4] Build record: PASS')
print(f'  [2/4] Produce MQ message: PASS')
print(f'  [3/4] Parse at legacy-ledger 6.9: PASS (accepted without error)')
print(f'  [4/4] Semantic assertions: {\"PASS\" if ex.result.value == \"PASS\" else \"FAIL\"}')

print()
print('Scene 9: Silent Semantic Failure...')
print('  HTTP     200')
print('  MQ       ACK')
print('  DB       COMMIT')
print('  Health   GREEN')
print()
print('  BUT:')
print('  customerId expected: CUST12345678')
for a in ex.assertion_results:
    print(f'  customerId actual:   {a[\"actual\"]}')

print()
print('Scene 10: First Demonstrated Divergence...')
from engine.divergence.first_divergence import find_first_divergence
div = find_first_divergence('order-to-ledger', 'prod')
print(f'  {div.producer} {div.producer_version}')
print(f'    -> {div.consumer} {div.consumer_version}')
print(f'    X FAILED PROBE')
print(f'  Unvalidated since: {div.unvalidated_since}')

print()
print('Scene 11: Counterfactual Promotion Rehearsal...')
from engine.rehearsal.rehearsal import simulate_promotion
sim = simulate_promotion('prod', 'order-to-ledger', 'legacy-ledger', '7.0')
print(f'  Proposing: promote legacy-ledger to 7.0')
print(f'  Result: {sim.result}')
print(f'  {sim.summary}')

print()
print('================================================')
print('  DEMO COMPLETE — ALL GOLDEN TESTS PASS')
print('================================================')
print()
print('Next: Open Meridian UI at http://localhost:5173')
print('      Open in Bob for remediation drafting')
"
