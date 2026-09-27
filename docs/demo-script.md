# Meridian — demo guide and video transcript

Target length: **2 min 55 s** (lablab limit is 3:00; at least 90 s must show the product working).

## Before you record (10 minutes)

1. Build the scenario and start the app (one process serves API + UI + videos):

   ```bash
   python fixtures/build_scenario.py
   python -m uvicorn apps.api.main:app --port 8010
   ```

   Open http://localhost:8010 in Chrome, full screen, 1440×900 or larger. Theme: **NEON**.
2. Click **Reset demo evidence** (bottom of the sidebar) so PROD starts as *UNVALIDATED* and the investigation happens live.
3. Open IBM Bob IDE on this folder. Check the MCP server `meridian` is connected (Settings → MCP) and the custom modes appear.
4. Have two browser tabs ready: `/#/` (home) and `/#/command`.
5. Optional: press **S** in the app for story mode; ← → steps through the scenes with captions.

## Shot list and narration

| Time | Screen | What to do | Narration |
|---|---|---|---|
| 0:00–0:14 | Home `/#/` | Let the hero video play, slow scroll | “Every component passed. The system didn’t. In big companies nobody deploys a release any more. Production assembles itself from dozens of independent deployments, and nobody tests the exact mix that ends up running.” |
| 0:14–0:28 | Home, incident section | Scroll to “The release passed Stage on Thursday” | “Here’s the case. Release R-26.9 passed Stage on Thursday. On Friday at 11:42 an Argo CD auto-sync pushed the new MQ bridge to production, while the legacy ledger that can read its new record format waits for Sunday’s change window.” |
| 0:28–0:42 | Command center `/#/command` | Point at the green stats, then the PROD lane | “Every pod is healthy, every pipeline is green. Meridian asks one question: is the exact combination running in production one that anybody validated together? Here, it isn’t.” |
| 0:42–1:05 | IBM Bob IDE | Mode **Meridian Investigator**, paste the prompt below, let Bob call the MCP tools and spawn subagents | “This is IBM Bob. Meridian ships as a Bob plugin: custom modes, skills, an MCP server and safety hooks. Bob’s subagents reconstruct all four environments in parallel and read the change request, the release notes and the interface spreadsheet.” |
| 1:05–1:20 | Live investigation `/#/investigate` | Click **Start investigation** (top right of the banner) | “The same lanes run here, live. Release investigator, four environment investigators, validation memory, contract discovery, then the probe engineer.” |
| 1:20–1:38 | Implicit contract `/#/contract` | Hover the red bytes in the byte map | “There’s no formal contract on this queue, just a COBOL copybook and an Excel sheet. Meridian rebuilt it from the code at the exact deployed commits. The bridge now writes 25 bytes. The old ledger reads 23 and never checks the length.” |
| 1:38–2:00 | Probe console `/#/probe` | Scroll to “Infrastructure is green” | “So Meridian doesn’t guess. It runs both components in a sandbox with the fixtures Stage used. HTTP 200, MQ ACK, DB commit. And customer CUST12345678 is booked as CUST123456, with 149 dollars 50 turned into 780 million.” |
| 2:00–2:15 | First divergence `/#/divergence` | Point at the edge, the timestamp and “Evidence review: SUPPORTED” | “That’s the first demonstrated divergence: bridge 3.1 to ledger 6.9, created at 11:42 by that auto-sync. It’s a fact with evidence behind every line, not a root-cause guess.” |
| 2:15–2:30 | Promotion rehearsal `/#/rehearse` | Click **Execute CR-4471 now**, then **Roll mq-bridge back to 3.0** | “Before anyone touches production, we rehearse. Pulling the ledger upgrade forward converges. Rolling the bridge back looks safe, but it creates another pair nobody ever tested.” |
| 2:30–2:50 | Remediation `/#/remediate` | Click **Open in Bob**, then B **Draft candidate + regression probe** | “Open in Bob hands the evidence to the remediator mode. Bob drafts a compatibility mode for the bridge on an isolated branch, and the regression probe passes: nothing is truncated, and anything the old ledger can’t represent is held, not corrupted.” |
| 2:50–2:58 | Home CTA or Command center | Hold | “We’re not monitoring whether your services are alive. We’re proving whether the system you assembled is the system you actually tested. That’s Meridian.” |

### Prompt to paste into IBM Bob (mode: Meridian Investigator)

```
Investigate release R-26.9 on the order-to-ledger flow in PROD.
Use the release-investigation skill. Reconstruct DEV, TEST, STAGE and PROD in parallel with
environment-investigator subagents through the meridian MCP tools, and read the change request,
release notes and interface-control documents. Hand every boundary without VERIFIED evidence to
contract discovery, run the probe with run_probe, then report the First Demonstrated Divergence
with its evidence packet. Do not modify any environment.
```

Remediation prompt (mode: Meridian Remediator) is generated for you by **Open in Bob** and saved in `.meridian/handoff/`.

## Full narration (read straight through, ~2:55)

Every component passed. The system didn’t.

In big companies, nobody deploys a release any more. Production assembles itself from dozens of independent deployments on different clouds and different schedules, and nobody tests the exact mix that ends up running.

Here’s the case. Release R-26.9 passed Stage on Thursday. On Friday at 11:42, an Argo CD auto-sync pushed the new MQ bridge to production, while the legacy ledger that understands its new record format is still waiting for Sunday’s change window.

Every pod is healthy. Every pipeline is green. Meridian asks a different question: is the exact combination running in production one that anybody actually validated together? Here, it isn’t.

This is IBM Bob. Meridian ships as a Bob plugin, with custom modes, skills, an MCP server and safety hooks. Bob’s subagents reconstruct all four environments in parallel and read the change request, the release notes and the interface spreadsheet.

The same lanes run live in the app: a release investigator, four environment investigators, validation memory, contract discovery and a probe engineer.

There’s no formal contract on this queue, only a COBOL copybook and an Excel sheet. Meridian rebuilt the contract from the code at the exact deployed commits. The bridge now writes twenty-five bytes. The old ledger reads twenty-three and never checks the length.

So Meridian doesn’t guess. It runs both components in an isolated sandbox with the same fixtures Stage used. HTTP 200. MQ acknowledged. Database committed. And customer CUST12345678 is booked as CUST123456, with a hundred and forty-nine dollars fifty turned into seven hundred and eighty million.

That’s the first demonstrated divergence: bridge 3.1 to ledger 6.9, created at 11:42 by that auto-sync. It’s a fact with evidence behind every line, not a root-cause guess.

Before anyone touches production, we rehearse. Pulling the ledger upgrade forward converges. Rolling the bridge back looks safe, but it creates another pair nobody ever tested.

Open in Bob hands the evidence to the remediator mode. Bob drafts a compatibility mode for the bridge on an isolated branch, and the regression probe passes. Nothing is truncated, and anything the old ledger can’t represent is held instead of corrupted.

We’re not monitoring whether your services are alive. We’re proving whether the system you assembled is the system you actually tested. That’s Meridian.

## If something goes wrong on camera

- PROD already shows DIVERGED: that’s fine, just say “we ran it once already” and continue; or click **Reset demo evidence**.
- A video background doesn’t load: the page still works; the aurora and 3D layers show through.
- Bob’s MCP server isn’t connected: record the Bob segment separately (Bob IDE → MCP settings → `meridian`), then cut it in.
