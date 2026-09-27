# MERIDIAN — Project Context for IBM Bob

> **Every component passed. The system didn't.**

Meridian is an AI-assisted release-convergence intelligence system for distributed enterprise applications.
It reconstructs the exact software composition running across environments, identifies unvalidated
version combinations, discovers implicit integration contracts, safely rehearses promotions, and
identifies the first demonstrated release divergence with executable proof.

---

## Product Mission

Answer one question: **Is the exact system currently running one that has actually been validated together?**

When the answer is no: **Which connection became unvalidated, can we reproduce its behavior safely, and what evidence proves the result?**

Core workflow: **RECONSTRUCT → UNDERSTAND → REHEARSE → PROVE → REMEDIATE**

---

## Repository Structure

```
meridian/
├── AGENTS.md                     ← this file (Bob project context)
├── README.md
├── Makefile
├── docker-compose.yml
├── .bob/                         ← IBM Bob configuration
│   ├── mcp.json                  ← MCP server registration
│   ├── custom_modes.yaml         ← Meridian-specific Bob modes
│   ├── settings.json             ← Hooks and safety guardrails
│   ├── hooks/                    ← PreToolUse safety hooks
│   ├── skills/                   ← Bob skills (5 specialist skills)
│   ├── agents/                   ← Reusable agent prompts
│   └── rules-meridian/           ← Standing rules for Bob
├── apps/
│   ├── api/                      ← FastAPI backend (Python)
│   └── web/                      ← React + TypeScript + Vite frontend
├── engine/                       ← Deterministic reconciliation engine (Python)
│   ├── domain/                   ← Core data models
│   ├── reconciliation/           ← Environment state normalization
│   ├── validation/               ← Validation memory
│   ├── divergence/               ← First Divergence algorithm
│   ├── evidence/                 ← Evidence packet assembly
│   ├── rehearsal/                ← Counterfactual promotion rehearsal
│   └── probes/                   ← Probe engine
├── mcp/server/                   ← Python MCP server
├── adapters/                     ← Adapter layer (synthetic + base)
├── sample-system/                ← 8-component enterprise demo system
│   ├── mq-bridge/                ← v3.0 and v3.1 (the key component)
│   ├── legacy-ledger/            ← v6.9 and v7.0 (fixed-width parser)
│   └── ...
├── environments/                 ← Environment snapshots (dev/test/stage/prod)
├── documents/                    ← Enterprise artifacts (PDF/DOCX/XLSX)
├── probes/                       ← Generated probe files
├── fixtures/                     ← Test fixtures and synthetic data
├── .meridian/                    ← Runtime evidence and results (write-allowed)
├── demo/                         ← Demo scripts (reset/seed/run/benchmark)
├── tests/                        ← Unit, integration, golden tests
└── docs/                         ← Architecture, decisions, threat model
```

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Backend | Python 3.11+, FastAPI, SQLite (SQLAlchemy) |
| Engine | Pure Python (deterministic, no LLM calls) |
| MCP Server | Python, mcp SDK |
| Probe Runtime | Python subprocess isolation |
| Documents | PDF (fpdf2), DOCX (python-docx), XLSX (openpyxl) |

---

## Safety Rules — CRITICAL

**Meridian is read-only against target environments.**

Bob must NEVER run:
- `kubectl apply`, `kubectl delete`, `kubectl scale`, `kubectl rollout`
- `helm upgrade`, `helm install`
- `terraform apply`
- `aws create/update/delete/deploy`
- `az create/update/delete/deployment/webapp deploy`
- `gcloud create/update/delete/deploy`

Bob MAY:
- Read files anywhere in the repository
- Read project data via MCP tools
- Run isolated probes under `probes/` and `.meridian/`
- Write evidence under `.meridian/`
- Modify test fixtures in `fixtures/` and `tests/`
- Run demo scripts in `demo/`
- Execute backend/frontend builds and tests

Probe execution always runs in subprocess isolation — never against real infrastructure.

---

## Testing Rules

Run tests with:
```bash
cd apps/api && python -m pytest tests/ -v
```

Golden end-to-end test (must always pass):
```bash
python -m pytest tests/test_golden.py -v
```

The golden test asserts the complete chain:
- Stage: bridge 3.1 + ledger 7.0 → VERIFIED
- Prod: bridge 3.1 + ledger 6.9 → UNTESTED → probe FAILED
- First Demonstrated Divergence: mq-bridge 3.1 → legacy-ledger 6.9

---

## Demo Path

```bash
./demo/reset.sh    # wipe .meridian/ and reset SQLite DB
./demo/seed.sh     # load synthetic environment data
./demo/run-demo.sh # execute the end-to-end demonstration
./demo/benchmark.sh # collect timing and evidence metrics
```

Expected output chain:
```
Stage validated → Production partial promotion → System Nobody Tested
→ Implicit Contract Discovery → Executable Probe → Semantic Failure
→ First Demonstrated Divergence → Counterfactual Promotion Rehearsal
→ Bob Remediation → Regression Probe → PASS
```

---

## Core Terminology

| Term | Meaning |
|---|---|
| Environment Reality | What is actually running (not what was intended) |
| Validation Evidence | Proof that a specific combination was exercised successfully |
| Implicit Contract | Compatibility assumption existing only in code/docs, not formal spec |
| Compatibility Probe | Isolated executable test of a specific version boundary |
| Release Convergence | All components running the combination that was validated together |
| First Demonstrated Divergence | Earliest boundary where running versions lack evidence AND probe fails |
| Promotion Rehearsal | Simulate a deployment to predict its validation impact (no actual deploy) |
| Evidence Packet | Traceable bundle of all facts behind a First Divergence finding |

---

## Evidence Requirements

- Every finding must have an evidence ID.
- Never claim VERIFIED without actual passing validation records.
- Never claim FAILED without a deterministic probe result.
- INCONCLUSIVE is a valid and important state — never suppress it.
- Separate observed co-existence from exercised integration from verified behavior.
- Never use the phrase "root cause" — use "First Demonstrated Divergence."

---

## MCP Tools Available to Bob

All tools are in the `meridian` MCP server:

- `get_release_intent` — release scope and expected versions
- `get_environment_snapshot` — actual running versions per environment
- `get_environment_history` — deployment timeline
- `get_component_versions` — version history for a component
- `get_business_flow` — ordered component flow definition
- `get_dependency_edges` — edges for a flow
- `get_validation_history` — validation evidence records
- `get_untested_edges` — edges lacking sufficient evidence
- `get_interface_document` — fixed-width interface specification
- `get_change_request` — CAB/change request metadata
- `get_release_notes` — release notes content
- `discover_implicit_contract` — LLM-assisted contract inference (returns probe spec)
- `create_probe_spec` — build a runnable probe specification
- `run_probe` — execute probe in isolation (never against production)
- `get_probe_result` — retrieve probe execution result
- `get_first_divergence` — deterministic First Divergence for a flow+environment
- `get_evidence_packet` — full traceable evidence bundle
- `simulate_promotion` — counterfactual promotion rehearsal

---

## Commands to Run the Project

```bash
# Backend
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd apps/web
npm install
npm run dev

# MCP server
cd mcp/server
pip install -r requirements.txt
python server.py

# Full stack (Docker Compose)
docker-compose up

# Tests
cd apps/api && python -m pytest tests/ -v
```

---

*All data in this repository is synthetic and fictional. Environment snapshots, deployment
timestamps, component versions, and validation records are created for demonstration purposes only.*
