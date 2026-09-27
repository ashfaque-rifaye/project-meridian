# Threat Model

## Security Boundaries

### What Meridian can access (read-only)
- Repository files (source code, fixtures, documents)
- Environment snapshots (synthetic adapter outputs)
- `.meridian/` directory (evidence writes only)

### What Meridian cannot do
- Connect to real production infrastructure
- Deploy, scale, or modify any Kubernetes/cloud resource
- Access production credentials
- Execute arbitrary code outside the probe sandbox

## Probe Sandbox

Probes execute in Python subprocess isolation:
- Separate process, separate namespace
- No network access to production
- Timeout: 30 seconds
- All output captured and persisted as evidence

## Hook Enforcement

The `block-dangerous-tools.sh` PreToolUse hook blocks:
- `kubectl apply/delete/scale/rollout`
- `helm upgrade/install`
- `terraform apply`
- `aws/az/gcloud` create/update/delete/deploy commands

Exit code 2 causes IBM Bob to cancel the tool call.

## Data Classification

All environment data in this repository is:
- Synthetic (fictional)
- For demonstration purposes only
- Does not represent any real organization's infrastructure

No real credentials, IPs, hostnames, or customer data appear anywhere in the repository.

## Evidence Trust

- Environment state is backed by adapter evidence records with IDs
- Validation states are backed by evidence records (never inferred)
- Probe results are deterministic (not LLM-generated opinions)
- INCONCLUSIVE is surfaced explicitly, never silently suppressed
