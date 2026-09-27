#!/usr/bin/env bash
# MERIDIAN demo benchmark: times every step of the chain and saves .meridian/benchmark.json.
# These are SYNTHETIC DEMO MEASUREMENTS on the local machine, not industry benchmarks.
set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

python demo/run_demo.py --benchmark
