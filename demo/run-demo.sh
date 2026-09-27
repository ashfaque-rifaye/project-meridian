#!/usr/bin/env bash
# MERIDIAN end-to-end demo: builds the scenario repos, then runs
# RECONSTRUCT -> UNDERSTAND -> PROVE -> REHEARSE -> REMEDIATE in the terminal.
# Nothing is deployed; probes run in .meridian/sandbox only.
set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

python fixtures/build_scenario.py
python demo/run_demo.py
