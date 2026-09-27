# Meridian: lablab.ai submission copy

Paste each block into the matching field of the lablab.ai form. Numbers come from the demo engine (`python demo/run_demo.py`), not from estimates.

## Project title

Meridian: The System Nobody Tested

If the form rejects punctuation or anything over 32 characters, use: Meridian Release Convergence

## Short description (max 255 characters)

Every component passed its tests. The system in production didn't. Meridian runs inside IBM Bob to find the version pair nobody tested together, rebuild its hidden contract and prove the break in a sandbox before customers see it.

## Long description: Problem & Solution Statement (max 500 words)

In a hybrid enterprise, a release is never deployed as one thing. Our sample checkout flow crosses eight components owned by eight teams, from a storefront on GKE through AWS, Azure and Kafka to an IBM MQ bridge on OpenShift, a WebSphere ledger and Db2. They ship through seven pipelines, and each team tests its own change. Nobody tests the exact mix of versions that ends up in production.

In our demo, release R-26.9 widens customer IDs from 10 to 12 characters and adds a currency code. On Thursday, Stage passes with mq-bridge 3.1 and legacy-ledger 7.0. On Friday at 11:42 UTC an Argo CD auto-sync pushes mq-bridge 3.1 to production. The ledger upgrade that can read the new 25-byte record is booked for Sunday 02:00 UTC under CR-4471. For the 38 hours in between, pipelines are green, pods are healthy, MQ acknowledges every message and Db2 commits every row. Meanwhile customer CUST12345678 is posted as CUST123456, $149.50 is posted as $780,000,149.00, and a €20.00 payment is booked in dollars.

Meridian answers a single question: has the exact combination running in this environment ever been validated together?

1. Reconstruct. Read-only adapters for Kubernetes, WebSphere Liberty, IBM MQ, Flyway and Schema Registry rebuild what actually runs in DEV, TEST, STAGE and PROD. The release manifest is context, not truth.
2. Understand. Validation memory keeps "observed together", "exercised" and "verified" apart, so a dev smoke test that sent one message and checked nothing does not count. The 149 raw differences between Stage and Prod narrow to 63 on the flow, 2 that touch a dependency boundary, and 1 version pair nobody validated.
3. Prove. For that pair, Meridian rebuilds the implicit contract from the deployed code, a COBOL copybook, an interface spreadsheet, the release notes and the change request. It then runs both sides at those exact commits in a sandbox with Stage's fixtures. Code decides PASS or FAIL, not a model. Here 3 of 9 assertions fail while the infrastructure reports success. That is the First Demonstrated Divergence, backed by an evidence packet.
4. Rehearse. Promotions are simulated, never deployed. Pulling CR-4471 forward brings all 7 edges back to verified. Rolling the bridge back to 3.0 looks safe, but it creates a different pair nobody tested either.
5. Remediate. Bob drafts a compatibility mode for the bridge on an isolated branch and the regression probe passes. Records the old ledger cannot represent wait on a hold queue instead of being corrupted.

Contract tests need every team to write contracts first, and drift tools list every difference. Meridian works from what already exists: running versions, test history, code and documents.

It is built for release managers, platform teams and SREs. They work in IBM Bob through Meridian's modes and MCP tools, or in the web workspace. The whole chain runs in about a second on a laptop and never writes to a target environment. All demo data is synthetic.

## IBM Bob Usage Statement (max 500 words)

Meridian is built for IBM Bob, and we built it with IBM Bob.

How Meridian runs inside Bob. Everything lives in the repository's `.bob/` folder, so opening the project in Bob IDE is the install.

- AGENTS.md gives Bob the mission, the evidence rules and the vocabulary. For example, Bob must report a "First Demonstrated Divergence" and never a "root cause".
- Four custom modes with different permissions. Meridian Investigator can read, call MCP tools, load skills and spawn subagents, but cannot edit files or run commands. Probe Engineer can only edit files under probes/, fixtures/, sample-system/ and tests/. Remediator drafts fixes. Demo runs the showcase.
- Five skills hold the procedure: release investigation, environment reconstruction, implicit contract discovery, probe generation and evidence review.
- An MCP server (`mcp-server/meridian_mcp.py`, stdio) exposes 22 tools. 17 are read-only, 3 execute only in the probe sandbox and 2 write only under `.meridian/`. Bob calls get_environment_snapshot, get_validation_history, discover_implicit_contract, run_probe, get_first_divergence, simulate_promotion and verify_remediation instead of guessing.
- Subagents run in parallel: one environment investigator each for DEV, TEST, STAGE and PROD, and a contract-discovery subagent for every unverified boundary. `record_agent_finding` puts their findings into the web UI.
- Document understanding: the implicit contract is spread across a PDF change request, a DOCX release note and an XLSX interface specification. Bob reads all three.
- Hooks: a PreToolUse guard on execute_command exits with code 2 on mutating kubectl, oc, helm, argocd, terraform, aws, az, gcloud, flyway, Db2, MQ admin and git push commands. A PostToolUse logger records Bob's tool calls so the UI can show what Bob did.
- Open in Bob: a failed probe produces a ready-made task for the Remediator mode, which drafts a compatibility fix in an isolated worktree that the engine then re-proves.

We drew one firm line. Bob reads, plans and drafts. The engine decides. Validation states, probe verdicts and the divergence are computed by code, so the same inputs always give the same answer.

How we used Bob to build it. We wrote a 12-phase build specification (`MERIDIAN_IBM_BOB_BUILD.md`) and worked through it with Bob, tracking the phases in Bob's to-do list: the sample enterprise system with real git history for 8 components, the adapters, validation memory, the divergence engine, the probe sandbox, the FastAPI backend, the MCP server and the React UI.

In the final session Bob renamed the project from LockStep to Meridian across the codebase, rebuilt the UI, rewrote the golden test suite against the current engine API and ran it, then set up the repository. When Bob tried to run git push, our own guard blocked it. Bob retried through PowerShell's Start-Process and slipped past the pattern. We tightened the guard so wrapped commands are caught as well.

Task session summary screenshots from each team member are in `bob_sessions/`.

We did not use watsonx.ai or watsonx Orchestrate. The background videos in the UI were generated with Google Flow (Veo 3.1).

## Technology & category tags

IBM Bob, MCP, Python, FastAPI, React, TypeScript, DevOps, Release Management, Hybrid Cloud, Developer Tools

## Links

- Public repository: https://github.com/ashfaque-rifaye/project-meridian
- Demo application platform: Local (Python + Node, runs from the repository)
- Application URL: https://github.com/ashfaque-rifaye/project-meridian (replace with a hosted URL if you deploy one)

## Slide presentation (PDF, 6 slides)

1. Every component passed. The system didn't.
   Eight components, eight teams, seven pipelines. Nobody tests the exact mix that ends up in production. Meridian finds it and proves what it does.
2. The week R-26.9 went wrong
   Thursday: Stage passes with bridge 3.1 + ledger 7.0. Friday 11:42 UTC: Argo CD auto-syncs bridge 3.1 to Prod. Sunday 02:00 UTC: the ledger upgrade is still waiting. 38 hours of green dashboards. CUST12345678 becomes CUST123456. $149.50 becomes $780,000,149.00.
3. 149 differences, 1 that matters
   149 raw Stage vs Prod differences, 63 on the flow, 2 on a dependency boundary, 1 unvalidated pair, 1 failed probe.
4. How it works
   Reconstruct, Understand, Prove, Rehearse, Remediate. Read-only adapters, validation memory, implicit contract from code and documents, sandbox probe at the exact deployed commits. Code decides the verdict.
5. Built into IBM Bob
   AGENTS.md, 4 custom modes, 5 skills, 22 MCP tools, parallel subagents per environment, PDF/DOCX/XLSX document reading, PreToolUse guard (exit 2), Open in Bob remediation handoff.
6. Result
   First Demonstrated Divergence found and proved in about a second. Rehearsal shows the rollback everyone would reach for creates a new untested pair. Bob's compatibility fix passes the regression probe. Nothing in any environment was touched.

## Video (MP4, 3:00 max, at least 90 seconds of the product running)

Shot list and full narration: `docs/demo-script.md` (2:55).

## Cover image

16:9, PNG or JPG. Capture the First Divergence screen (`/#/divergence`) at 1920×1080 with the headline visible.
