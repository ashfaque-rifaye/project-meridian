# Architecture Decisions

All decisions made during the Meridian build. Recorded per the execution directive.

## D-001: Python + FastAPI for backend

**Decision**: Python 3.11+ with FastAPI.
**Reason**: Fastest path to a working deterministic engine. Python's subprocess module is ideal for isolated probe execution. FastAPI provides auto-docs and typed responses.

## D-002: React + TypeScript + Vite for frontend

**Decision**: Standard React 18 SPA with TypeScript.
**Reason**: Fast build, type safety, widely understood. Vite provides instant HMR for demo iteration.

## D-003: SQLite for persistence (hackathon)

**Decision**: SQLite / JSON files for environment fixtures and evidence.
**Reason**: Zero infrastructure to provision. The adapter model means this can be replaced with a real DB without changing the engine interface.

## D-004: Subprocess isolation for probes

**Decision**: Python subprocess (not Docker) for probe execution.
**Reason**: Docker requires the daemon to be running. Subprocess provides sufficient isolation for the demo scenario. The interface can be swapped for Docker without changing the engine.

## D-005: Deterministic engine owns PASS/FAIL

**Decision**: The Python assertion evaluator, not the LLM, determines probe results.
**Reason**: This is the core product differentiation. LLM-generated compatibility opinions are not proof. Executable assertion evaluation is proof.

## D-006: Unicode arrows in edge IDs

**Decision**: Use `→` (U+2192) in edge IDs for readability.
**Reason**: Matches the spec visual language. All file I/O uses UTF-8 encoding explicitly.

## D-007: Validation evidence scoped to all environments

**Decision**: Single validation-evidence.json covers all environments (indexed by environment field).
**Reason**: Simplifies loading; a real implementation would have per-environment stores with separate credentials.

## D-008: Probe script generation (not subprocess import)

**Decision**: Generate a complete Python script in a temp file and execute it as a subprocess.
**Reason**: Ensures the probe runs in an isolated Python namespace, separate from the engine process. Import isolation prevents engine state from contaminating probe results.

## D-009: mq-bridge source in both `mq-bridge/` and `mq_bridge/` dirs

**Decision**: Copy source files to Python-importable `mq_bridge/src/` package name.
**Reason**: Python cannot import from directories with hyphens. The hyphenated form is the enterprise naming convention for the component; the underscored form is the Python package. Both are kept in sync.

## D-010: Static UI data for screens without active backend

**Decision**: UI screens use embedded static data matching the demo scenario, with API fetch as a fallback.
**Reason**: Ensures the UI is fully demonstrable without a running backend. When the backend is running, the UI fetches live data.
