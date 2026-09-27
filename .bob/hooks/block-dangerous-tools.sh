#!/usr/bin/env bash
# Meridian PreToolUse safety hook
# Blocks dangerous environment-mutation commands.
# Exit code 2 = block the tool call.

COMMAND="${1:-}"

BLOCKED_PATTERNS=(
  "kubectl apply"
  "kubectl delete"
  "kubectl scale"
  "kubectl rollout"
  "helm upgrade"
  "helm install"
  "terraform apply"
  "aws create"
  "aws update"
  "aws delete"
  "aws deploy"
  "az create"
  "az update"
  "az delete"
  "az deployment"
  "az webapp deploy"
  "gcloud create"
  "gcloud update"
  "gcloud delete"
  "gcloud deploy"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qi "$pattern"; then
    echo "MERIDIAN SAFETY: Command blocked — '${pattern}' is not permitted in investigation mode." >&2
    echo "Meridian is read-only against target environments. Use probe isolation for all compatibility tests." >&2
    exit 2
  fi
done

exit 0
