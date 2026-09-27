# Meridian Safety Rules

Meridian is **read-only against target environments**. These rules are non-negotiable.

## What Bob MAY do

- Read any file in this repository
- Call MCP tools (all are read-only against environments)
- Run `run_probe` — probes execute in subprocess isolation, never production
- Write to `.meridian/` — evidence, runs, logs
- Modify `fixtures/` and `tests/` — test data only
- Modify `probes/` and `sample-system/` — demo code, not live infrastructure
- Run `demo/` scripts — they operate on local data only
- Build and test backend/frontend code

## What Bob MUST NOT do

Never run commands that mutate target environments:

- `kubectl apply`, `kubectl delete`, `kubectl scale`, `kubectl rollout`
- `helm upgrade`, `helm install`, `helm delete`
- `terraform apply`, `terraform destroy`
- `aws *` commands that create/update/delete/deploy
- `az *` commands that create/update/delete/deploy
- `gcloud *` commands that create/update/delete/deploy
- Any command that connects to production systems

These patterns are also blocked by the PreToolUse hook in `.bob/settings.json`.

## Enforcement

The `block-dangerous-tools.sh` hook exits with code 2 (blocking) on any pattern match.

If a command seems necessary but appears blocked, describe the intended operation in text.
A human operator with appropriate credentials must perform environment mutations.
