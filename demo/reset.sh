#!/usr/bin/env bash
# MERIDIAN Demo Reset Script
# Wipes all runtime evidence and resets the system to a clean demo state.
# Run this before every demo to ensure reproducibility.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "MERIDIAN Demo Reset"
echo "==================="
echo ""

# Remove probe run artifacts
echo "Removing probe run artifacts..."
rm -f "$PROJECT_ROOT/.meridian/runs/"*.json

# Remove investigation log
echo "Clearing investigation log..."
rm -f "$PROJECT_ROOT/.meridian/investigation.log"

# Ensure directories exist
mkdir -p "$PROJECT_ROOT/.meridian/runs"
mkdir -p "$PROJECT_ROOT/.meridian/evidence"
mkdir -p "$PROJECT_ROOT/.meridian/validation-memory"

echo ""
echo "Reset complete. System is ready for demo."
echo "Run: ./demo/seed.sh to load demo data"
