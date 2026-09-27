#!/usr/bin/env bash
# MERIDIAN Demo Seed Script
# Generates all necessary demo documents and verifies environment fixtures.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "MERIDIAN Demo Seed"
echo "=================="
echo ""

# Generate document fixtures
echo "Generating document fixtures..."
cd "$PROJECT_ROOT"
python documents/generate_docs.py

# Verify environment snapshots exist
echo ""
echo "Verifying environment snapshots..."
for env in dev test stage prod; do
  if [ -f "environments/$env/snapshot.json" ]; then
    echo "  [OK] environments/$env/snapshot.json"
  else
    echo "  [MISSING] environments/$env/snapshot.json"
    exit 1
  fi
done

# Verify validation evidence
if [ -f "environments/stage/validation-evidence.json" ]; then
  echo "  [OK] environments/stage/validation-evidence.json"
else
  echo "  [MISSING] environments/stage/validation-evidence.json"
  exit 1
fi

# Verify sample system source
echo ""
echo "Verifying sample system..."
for f in "sample-system/mq-bridge/src/record_builder.py" "sample-system/legacy-ledger/src/record_parser_v69.py" "sample-system/legacy-ledger/src/record_parser.py"; do
  if [ -f "$f" ]; then
    echo "  [OK] $f"
  else
    echo "  [MISSING] $f"
    exit 1
  fi
done

echo ""
echo "Seed complete. Run ./demo/run-demo.sh to start the demo."
