#!/usr/bin/env bash
# Meridian PostToolUse investigation log hook
# Appends a timestamped entry to .meridian/investigation.log

LOG_DIR=".meridian"
LOG_FILE="${LOG_DIR}/investigation.log"

mkdir -p "$LOG_DIR"
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] tool-use event" >> "$LOG_FILE"

exit 0
