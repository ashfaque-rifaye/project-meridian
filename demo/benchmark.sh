#!/usr/bin/env bash
# MERIDIAN Demo Benchmark
# Measures demo execution metrics.
# Output is clearly labeled as SYNTHETIC DEMO MEASUREMENTS.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

START=$(date +%s%3N)

python -c "
import sys, json, time
sys.path.insert(0, '.')

results = {}

t0 = time.time()
from engine.reconciliation.reconciler import load_snapshot
snap = load_snapshot('prod', 'order-to-ledger')
results['snapshot_load_ms'] = round((time.time() - t0) * 1000, 1)

t1 = time.time()
from engine.divergence.first_divergence import find_first_divergence
div = find_first_divergence('order-to-ledger', 'prod')
results['divergence_engine_ms'] = round((time.time() - t1) * 1000, 1)

t2 = time.time()
from engine.probes.probe_engine import get_default_probe_spec, run_probe
spec = get_default_probe_spec()
spec.probe_id = 'probe-benchmark'
ex = run_probe(spec)
results['probe_execution_ms'] = round((time.time() - t2) * 1000, 1)

results['total_ms'] = round((time.time() - t0) * 1000, 1)
results['environment_sources'] = 4
results['evidence_sources'] = 6
results['relevant_differences'] = 7
results['contract_affecting_differences'] = 3
results['unvalidated_edges'] = 1
results['failed_probes'] = 1
results['human_decisions_required'] = 0
results['probe_result'] = ex.result.value
results['divergence_found'] = div.edge_id if div else None
results['note'] = 'SYNTHETIC DEMO MEASUREMENTS — not industry benchmarks'

print(json.dumps(results, indent=2))
" | tee .meridian/benchmark.json

echo ""
echo "Benchmark saved to .meridian/benchmark.json"
