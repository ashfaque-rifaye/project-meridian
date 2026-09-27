# IBM Bob Hackathon 2.0 — Complete Project Context

> **Event URL:** https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon  
> **Organizers:** lablab.ai × IBM  
> **Format:** Online / Global  
> **Theme:** Build the next generation of AI-powered developer tools using IBM Bob

---

## Table of Contents

1. [What Is IBM Bob?](#1-what-is-ibm-bob)
2. [IBM Bob IDE — Core Architecture](#2-ibm-bob-ide--core-architecture)
3. [Modes — Built-in & Custom](#3-modes--built-in--custom)
4. [Tools — Complete Taxonomy](#4-tools--complete-taxonomy)
5. [Skills (SKILL.md)](#5-skills-skillmd)
6. [Custom Rules & AGENTS.md](#6-custom-rules--agentsmd)
7. [MCP (Model Context Protocol)](#7-mcp-model-context-protocol)
8. [Context Mentions](#8-context-mentions)
9. [Slash Commands](#9-slash-commands)
10. [Bob Tips — Real-time Code Analysis](#10-bob-tips--real-time-code-analysis)
11. [Code Reviews](#11-code-reviews)
12. [Subtasks & Subagents](#12-subtasks--subagents)
13. [Context Window Management](#13-context-window-management)
14. [Context Poisoning](#14-context-poisoning)
15. [Auto-Approve System](#15-auto-approve-system)
16. [Bob Shell](#16-bob-shell)
17. [Bob Marketplace](#17-bob-marketplace)
18. [Security & Best Practices](#18-security--best-practices)
19. [The 5 Extensibility Surfaces](#19-the-5-extensibility-surfaces)
20. [Hackathon — Rules & Requirements](#20-hackathon--rules--requirements)
21. [Hackathon — Judging Criteria](#21-hackathon--judging-criteria)
22. [Hackathon — Prizes](#22-hackathon--prizes)
23. [What Makes a Winning Submission](#23-what-makes-a-winning-submission)
24. [Brainstorm Seed Ideas](#24-brainstorm-seed-ideas)
25. [Quick Reference Cheatsheet](#25-quick-reference-cheatsheet)
26. [Bob Plans, Billing & Bobcoins](#26-bob-plans-billing--bobcoins)
27. [Authentication & API Keys](#27-authentication--api-keys)
28. [Code Actions & Literate Coding](#28-code-actions--literate-coding)
29. [Keyboard Shortcuts — Full Reference](#29-keyboard-shortcuts--full-reference)
30. [Bob Shell Sandboxing](#30-bob-shell-sandboxing)
31. [Bobalytics — Enterprise Analytics](#31-bobalytics--enterprise-analytics)

---

## 1. What Is IBM Bob?

IBM Bob is an **AI SDLC (Software Development Lifecycle) partner** — an agentic integrated development environment (IDE) that helps you write, test, upgrade, and secure software across the entire software development lifecycle.

### One-sentence summary
> "IBM Bob is an AI SDLC partner that augments your existing workflows and helps you understand, plan, improve, and work confidently with real codebases while offering proactive insights that keep you in control every step."

### What makes it different from a code copilot
- It is not just autocomplete — it is a full **reasoning agent**
- It can read your files, plan multi-step work, execute commands, and maintain project context across sessions
- It operates through **tools** (read, write, execute, MCP, skill, mode, subtask)
- It is stateless by design — project context is re-injected via `AGENTS.md` on each conversation
- Built on VS Code; also available as **Bob Shell** (terminal/CLI version)

### Platforms
- **Bob IDE** — VS Code extension (primary)
- **Bob Shell** — terminal-based CLI interface for headless / CI/CD use

---

## 2. IBM Bob IDE — Core Architecture

```
IBM Bob IDE
├── Chat Interface (agentic sidebar)
│   ├── Natural language prompts
│   ├── Slash commands (/init, /review, /memory, /bug, custom)
│   └── Context mentions (@file, @problems, @terminal, @git-changes)
├── Modes (Agent | Plan | Ask | Orchestrator | Custom)
├── Tools
│   ├── Read tools  (read_file, glob, grep, list_files, symbol tools)
│   ├── Write tools (write_file, apply_diff, insert_content, search_and_replace)
│   ├── Command tools (execute_command)
│   ├── MCP tools   (external servers via Model Context Protocol)
│   ├── Skill tools (use_skill)
│   ├── Mode tools  (switch_mode)
│   └── Subtask tools (start_subtask, spawn_subagent)
├── Skills (.bob/skills/<name>/SKILL.md)
├── Custom Rules (.bob/rules/, .bob/rules-{mode}/)
├── AGENTS.md (persistent project context)
├── MCP Server Connections (local STDIO or remote HTTP/SSE)
├── Bob Tips (real-time code quality analysis)
├── Code Reviews (/review command)
├── Bob Marketplace (community MCP servers + custom modes)
└── Settings (auto-approve, MCP, modes, shortcuts)
```

### Context Window
- **Total capacity:** 270,000 tokens (model provides 200,000 tokens per conversation)
- **Reserved for response:** ~20,000 tokens
- **Breakdown categories:** System prompt | Tool definitions | MCP Tools | Rules | Skills | Messages
- **Baseline overhead (empty project):** ~8,500 tokens before you type anything

---

## 3. Modes — Built-in & Custom

### Built-in Modes

| Mode | Purpose | Tool Access | Best For |
|------|---------|-------------|---------|
| **Agent** | Write, modify, refactor code | Full (read + write + execute + MCP) | Implementing features, fixing bugs |
| **Plan** | Design, architect, specify | Read-heavy, no writes by default | Planning before coding |
| **Ask** | Q&A, explanations | Read-only | Understanding code, no changes |
| **Orchestrator** | Coordinate multi-task work | Full + subtask/subagent tools | Complex multi-step projects |

### Switching Modes
- **Dropdown menu** — click selector left of chat input
- **Keyboard shortcut** — `Ctrl + .` (Windows/Linux) or `⌘ + .` (macOS) — cycles through modes
- **Slash command** — `/agent`, `/plan`, `/ask`
- **Mid-task switching** — Bob switches autonomously when work evolves
- **Suggestions** — Bob offers switch suggestions when appropriate

### Custom Modes

Custom modes are defined in `.bob/custom_modes.yaml` (project-level) or `~/.bob/custom_modes.yaml` (global).

**Schema:**
```yaml
customModes:
  - slug: my-mode              # unique identifier, used for rules-{slug}/ directory
    name: 🔒 Security Auditor  # display name in UI
    roleDefinition: >          # core identity and expertise
      You are an expert security engineer...
    whenToUse: >               # guidance for Orchestrator & mode switching
      Use this mode when reviewing code for security vulnerabilities...
    customInstructions: >      # additional behavioral guidelines
      Always reference OWASP Top 10. Provide severity levels (Critical/High/Medium/Low).
    description: >             # short summary shown in mode picker
      Security-focused code review and vulnerability detection
    groups:                    # tool permission groups
      - read
      - mcp
      - skill
    allowedSubagents:          # optional: restrict subagent presets
      - explore
```

**Tool permission groups:**
- `read` — read files, symbols, grep, glob
- `edit` — write files, apply diffs
- `execute` — run terminal commands
- `mcp` — use connected MCP servers
- `skill` — activate skills

**Override rules:**
- Project-scope (`project/.bob/`) > Global (`~/.bob/`) > Default built-ins
- A custom mode with the same `slug` as a built-in overrides it
- Custom modes do **not** bypass custom rules — rules always apply

**Mode-specific rules files:**
- `.bob/rules/` — applies to all modes
- `.bob/rules-agent/` — applies only to Agent mode
- `.bob/rules-plan/` — applies only to Plan mode
- `.bob/rules-ask/` — applies only to Ask mode
- `.bob/rules-{custom-slug}/` — applies to that custom mode

---

## 4. Tools — Complete Taxonomy

Bob automatically selects and uses the appropriate tool. Users approve or reject each tool invocation.

### Read Tools
| Tool | Description | Use Case |
|------|------------|----------|
| `read_file` | Read file contents with optional line ranges | View config, examine source |
| `glob` | Find files by name pattern (`**/*.ts`) | Locate test files, find all components |
| `grep` | Search file content with regex | Find function definitions, locate TODOs |
| `list_files` | List files/dirs in a directory | Browse directory structure |
| `GetSymbolsOverview` | Get top-level symbols in a file | Understand file structure |
| `FindSymbol` | Look up symbol by name path + optional depth | Navigate to class/method/function |
| `FindReferencingSymbols` | Find all references to a symbol | Understand where a function/type is used |

### Write Tools
| Tool | Description | Use Case |
|------|------------|----------|
| `write_file` | Create or fully rewrite a file | Generate new components, config files |
| `apply_diff` | Precise targeted changes to specific parts | Update function logic, fix bugs |
| `insert_content` | Insert new lines at a specific position | Add imports, insert new functions |
| `search_and_replace` | Find/replace text or regex across file | Rename variables, update repeated patterns |

### Command Tools
| Tool | Description | Use Case |
|------|------------|----------|
| `execute_command` | Run CLI commands in workspace | Install deps, run tests, build projects |

### MCP Tools
- Provided by connected MCP servers
- Access external APIs, databases, services
- Defined per-server — Bob discovers available tools automatically
- Can be enabled/disabled per tool per server

### Skill Tools
| Tool | Description |
|------|------------|
| `use_skill` | Load a named skill's instructions into current context |

### Mode Tools
| Tool | Description |
|------|------------|
| `switch_mode` | Switch to Agent, Plan, Ask, or custom mode |

### Subtask / Subagent Tools
| Tool | Description |
|------|------------|
| `start_subtask` | Create a new visible task with its own conversation thread in the UI |
| `spawn_subagent` | Spawn a silent background worker that returns a summary |

### Tool Approval Workflow
1. Bob selects the appropriate tool based on request
2. Approval prompt appears **one at a time** — user reviews parameters
3. Large tool details collapsed into preview by default (click to expand)
4. **Editable commands:** Terminal commands can be edited in the approval prompt before approving
5. **Task-level approvals:** Approve all reads/edits/executes for the entire current task at once

---

## 5. Skills (SKILL.md)

Skills are reusable instruction sets stored as `SKILL.md` files that Bob loads on demand.

### How Skills Work
1. You define a skill with a `SKILL.md` file
2. Bob reads the `description` field to decide when to activate
3. When a request matches, Bob activates the skill (once per conversation)
4. Bob receives the skill's full instructions and supporting files
5. Bob follows those instructions to complete the task

### File Structure
```
your-project/
└── .bob/
    └── skills/
        └── code-review/
            ├── SKILL.md          # required
            ├── checklist.md      # supporting file
            ├── severity-guide.md # supporting file
            └── scripts/
                ├── analyze.sh
                └── report-generator.py
```

### SKILL.md Format
```markdown
---
name: code-review
description: Review code for bugs, security issues, and best practices
---

When reviewing code, check for:
- Security vulnerabilities
- Performance issues
- Missing error handling at API boundaries
- Unused imports and dead code

Provide a summary with severity levels for each finding.
```

**Required front-matter fields:**
- `name` — display name used in Bob interface
- `description` — **critical**: helps Bob decide when to activate. Skills without descriptions are **ignored**

**Instructions section:** Everything below the `---` delimiter is the instructions Bob receives when activated.

### Skill Locations & Priority
| Location | Scope |
|----------|-------|
| `<project>/.bob/skills/` | Project-specific workflows |
| `~/.bob/skills/` | Global / personal / org-wide workflows |

Project-level skills take precedence over global ones when names conflict.

### Activation
- **Auto-activation** — Bob determines relevance from description + request context
- **Manual activation** — Call `use_skill` directly in your prompt or code
- **Approval** — Bob asks permission before activating by default
- **Auto-approve skills** — Enable in Settings → Auto-Approve → Skills toggle

### Supporting Files
Skills can include supporting files (checklists, templates, scripts, style guides, reference docs). Bob reads these automatically once the skill is activated.

---

## 6. Custom Rules & AGENTS.md

### AGENTS.md
Auto-generated by the `/init` command. Provides persistent project context across all conversations.

**Typical contents:**
- Project overview and purpose
- Directory structure and key file locations
- Technology stack and dependencies
- Architectural patterns and conventions
- Development workflows (test commands, build commands)

**Hierarchy:**
1. `~/.bob/AGENTS.md` — global context (all projects)
2. `<project-root>/AGENTS.md` — project context
3. `<subdirectory>/AGENTS.md` — component-specific context

Bob automatically applies AGENTS.md to new conversations.

### Custom Rules Files

**Placement:**
```
.bob/
├── rules/              # General — applies to ALL modes
├── rules-agent/        # Only Agent mode
├── rules-plan/         # Only Plan mode
├── rules-ask/          # Only Ask mode
└── rules-{custom-slug}/  # Only the named custom mode
```

**Supported file extensions:** `.md`, `.txt`, `.xml`

**Common rule types:**
- Coding style preferences (indentation, naming conventions)
- Documentation formats and standards
- Testing methodologies and requirements
- Project workflows and processes
- Team-specific conventions
- Communication style (verbosity, tone)
- Internal monologue / audit trail logging

**Example rule: Internal monologue**
```markdown
Write a summary of every interaction into the folder `internal-monologue/`.
Name the file starting with a timestamp, followed by a concise description.
Example: 2026-01-15_update-readme.md
```
This creates a persistent audit trail across all sessions — who did what with Bob and when.

**Reload rules:** Use `/memory refresh` to reload all context files.  
**Verify rules:** Use `/memory show` to verify the current context.

---

## 7. MCP (Model Context Protocol)

### What Is MCP?
MCP is the "USB-C" protocol for AI tools — a standardized way for Bob to connect to external services. Any compatible service can expose tools that Bob can discover and call.

### What MCP Provides
- **Tool discovery** — available tools with descriptions and parameters
- **Tool invocation** — calling specific tools with arguments and receiving structured responses
- **Resource access** — reading data from specific resources

### Transport Types

#### STDIO (Local)
- Runs on same machine as Bob
- Lower latency, no network overhead
- Better security (no network exposure)
- Server starts/stops with Bob (child process lifecycle)

**Configuration in `settings.json`:**
```json
{
  "mcpServers": {
    "local-server": {
      "command": "node",
      "args": ["server.js"],
      "cwd": "/path/to/project/root",
      "env": {
        "API_KEY": "your_api_key"
      },
      "alwaysAllow": ["tool1", "tool2"],
      "disabled": false
    }
  }
}
```

#### Streamable HTTP (Remote — Modern Standard)
- Hosted on different machines
- Supports multiple client connections
- Centralized deployment
- Supports both request-response and streaming

```json
{
  "mcpServers": {
    "remote-server": {
      "type": "streamable-http",
      "url": "https://your-server-url.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token"
      },
      "alwaysAllow": ["tool3"],
      "disabled": false
    }
  }
}
```

#### SSE (Legacy Remote)
- Same as Streamable HTTP but older standard
- Use `url` property (no `type` field)
- Avoid for new implementations — prefer Streamable HTTP

### Configuration Properties (all transports)
| Property | Required | Description |
|----------|----------|-------------|
| `command` | STDIO only | Executable to run (node, python, npx) |
| `url` / `httpURL` | HTTP/SSE only | Endpoint URL |
| `args` | Optional | Array of command-line arguments |
| `cwd` | Optional | Working directory for STDIO |
| `env` | Optional | Environment variables |
| `headers` | Optional | Custom HTTP headers (auth tokens) |
| `timeout` | Optional | Request timeout in ms (default: 600,000ms) |
| `alwaysAllow` | Optional | Tool names to auto-approve |
| `disabled` | Optional | Set `true` to disable server |

### Managing MCP Servers in Bob
- Settings → MCP tab → Add/remove/configure servers
- Enable/disable individual tools per server (fine-grained control)
- Disabling unused tools reduces context window overhead

### Building an MCP Server With Bob
Bob can scaffold MCP servers from natural language:
1. Enable **"Enable MCP Server Creation"** setting
2. Ask Bob: `"Create an MCP tool that gets the current Bitcoin price"`
3. Bob scaffolds a TypeScript project, implements the tool, prompts for API keys, adds config to settings.json, and connects automatically

### MCP Auto-approve
- Disabled by default
- Global setting: Auto-approve → MCP toggle
- Per-tool setting: Settings → MCP → server → tool → "Always allow"
- Global setting takes precedence over per-tool setting

---

## 8. Context Mentions

Reference project elements directly in chat instead of copy-pasting.

| Mention | Provides |
|---------|---------|
| `@/path/to/file.ts` | Complete file contents with line numbers |
| `@/path/to/file.ts:10-20` | Specific line range only |
| `@/path/to/folder` | All files in directory |
| `@problems` | Bob Findings panel diagnostics |
| `@terminal` | Recent terminal output |
| `@git-changes` | Current git diff |
| `@<commit-hash>` | Specific git commit contents |
| `@issues` | Bob Findings (from /review) |
| `@https://...` | URL content |

**Keyboard shortcut:** Highlight code in editor → `Ctrl+L` (Win/Linux) or `⌘+L` (macOS) to send to chat.

**Supported file types:** Text files, PDFs, DOCX, XLSX (text extracted for non-text formats).

**Ignore rules behavior:**
- `@mentions` **bypass** `.bobignore` — you can reference ignored files directly
- `@mentions` do **not** respect `.gitignore`
- `@git-changes`, `@<commit-hash>` **do** respect `.gitignore` (rely on git commands)

---

## 9. Slash Commands

Type `/` in the input field to see all available commands.

### Built-in Commands
| Command | Description |
|---------|-------------|
| `/init` | Scan project, generate AGENTS.md + .bob folder structure |
| `/review` | Run AI-powered code review, populate Bob Findings panel |
| `/memory refresh` | Reload all context files (AGENTS.md, rules) |
| `/memory show` | Verify what context is currently loaded |
| `/bug` | Report issues to IBM Bob feedback |
| `/agent` | Switch to Agent mode |
| `/plan` | Switch to Plan mode |
| `/ask` | Switch to Ask mode |

### Custom Commands
- Create `.bob/commands/<command-name>.md` (project-level)
- Create `~/.bob/commands/<command-name>.md` (global)
- Markdown file content becomes the command instructions
- Appears in the `/` menu alongside built-in commands
- Used for automating team-specific workflows

---

## 10. Bob Tips — Real-time Code Analysis

Continuous AI-powered static analysis running in the background on all open files.

### Metrics Analyzed
| Metric | Threshold | Description |
|--------|-----------|-------------|
| **Cyclomatic complexity** | ≥ 10 = high | Number of independent paths through code |
| **Maintainability index** | ≤ 70 = low | Ease of reading, testing, and extending |

### How It Works
1. Runs automatically as you write/modify code — no manual scans needed
2. When a function exceeds thresholds: purple underline appears in editor
3. Finding added to **Bob Findings panel**
4. AI-powered refactoring suggestion generated
5. Hover over purple underline: tooltip shows issue + suggestions + "Discuss with Bob" option

### Benefits
- Real-time detection — catch issues during development, before code review
- Reduce technical debt as it emerges
- Improve code readability and testability
- Reduce deeply nested logic and excessive branching

---

## 11. Code Reviews

Built-in AI-powered code review workflow.

### Running a Review
```
/review
```

Bob analyzes your changes and flags potential issues before you commit.

### Findings Panel
- All findings appear in the **Bob Findings panel**
- Click a finding to see full details
- Navigate to the file to see inline annotations
- Reference findings with `@issues` in chat for discussion

---

## 12. Subtasks & Subagents

### Subtasks (`start_subtask`)
- Fully visible and interactive in the UI
- Own breadcrumb and conversation thread
- Can be given: title, message, todo list, starting mode
- You can follow progress, review output, continue conversation within it
- Best for: complex, trackable, multi-step work that benefits from dedicated UI thread

### Subagents (`spawn_subagent`)
- Run silently in the background
- Only return a summary when done
- Own isolated context window
- Best for: self-contained side work whose result can be summarized back

### When to Use Which
| Use Subagent | Use Subtask |
|-------------|-------------|
| Research task that only needs a summary | Complex feature implementation |
| Independent lookup or analysis | Work you want to track in UI |
| Side work irrelevant to main context | Work that may need follow-up |
| Single-tool operations | Multi-step tracked task |

### Subagent Types
- `"explore"` — codebase exploration (read tools, explorer model)
- `"general"` — inherits current mode tools, default model
- `fork_context: true` — pass parent conversation history into subagent

---

## 13. Context Window Management

### Token Budget
- **Total:** 270,000 tokens (some models: 200,000 per conversation)
- **Reserved for response:** ~20,000 tokens
- **Available:** 270,000 - 20,000 = 250,000 usable

### What Fills the Window (Categories)
| Category | What It Is | Typical Size |
|----------|------------|-------------|
| **System prompt** | Bob's core instructions | ~1,500 tokens |
| **Tool definitions** | Built-in tool schemas + MCP definitions | ~5,100 tokens |
| **MCP Tools** | Connected MCP server tool descriptions | Varies |
| **Rules** | AGENTS.md + custom rules files | ~830 tokens |
| **Skills** | Loaded skill instructions | ~454 tokens (per skill) |
| **Messages** | Prompts, responses, tool activity transcript | Grows with conversation |

### Best Practices
- Keep AGENTS.md and rules short — only setup, test, and style commands
- Connect only MCP servers needed for current work
- Use subagents/subtasks for isolated work (own context window)
- Use `GetSymbolsOverview` / `FindSymbol` instead of `@` mentioning entire large files
- Break large tasks into smaller separate conversations
- Include only the log lines/errors Bob needs — not full dumps
- When Messages grows large → start new conversation (`+` New task button)

### When Context Gets Full
- Bob automatically summarizes the oldest content to free space
- Summaries may lose nuance — start a new task for critical long work
- Token usage indicator in top-right of chat panel (hover to see breakdown)

---

## 14. Context Poisoning

### What It Is
Context poisoning occurs when wrong or irrelevant information enters the context window and stays in the transcript. Bob treats it as fact on follow-up prompts, causing outputs to drift.

### Symptoms
- Suggestions repeat, wander, or stop matching the repo
- Tool steps no longer match what was asked
- Long multi-prompt flows loop or stall
- A corrective prompt helps once, then problem returns
- Bob misuses tools even though tool definitions didn't change

### Recovery
- Start a new task (`+` New task) — clears poisoned Messages while keeping Rules/files on disk
- Paste less — send only the specific log lines or errors needed
- Split the work goal — use separate tasks for unrelated steps
- Check tool output — if a tool returns garbage, stop and reset
- Trust tests over text — point Bob at runnable checks

---

## 15. Auto-Approve System

Controls whether Bob needs permission before each action.

### Available Actions & Risk Levels
| Action | What It Does | Risk Level |
|--------|-------------|------------|
| **Read** | View files and directory content | Medium |
| **Edit** | Create, edit, save files | **High** |
| **Execute** | Run commands in terminal | **High** |
| **MCP** | Use configured MCP servers | Medium-High |
| **Skill** | Activate defined skills | Medium |
| **Todo** | Update todo list | Low |
| **Subtask** | Create and complete subtasks | Low |
| **Subagent** | Spawn subagents | Low |
| **Mode** | Switch modes | Low |

### Approval Modes
- **Global auto-approve** — Settings → Auto-Approve → toggle per action type
- **Task-level approval** — "Approve all [read/edit/execute] for this task" button in approval UI
- **Per-tool MCP approve** — Settings → MCP → server → tool → "Always allow"

> **Warning:** Auto-approve bypasses confirmation prompts. Edit and Execute are particularly dangerous — they can cause data loss, file corruption, or run harmful operations.

---

## 16. Bob Shell

Terminal-based interface delivering the same AI capabilities in a command-line context.

### Key Capabilities
- Same reasoning, MCP, modes, rules as Bob IDE
- Workspace awareness (recent files + cursor position)
- Native diff viewing in editor's diff tool
- Seamless file editing (accept changes directly in editor)
- Sandboxing support (Docker/Podman container isolation)

### CLI Arguments
```bash
bob                                         # start interactive session
bob -p "Explain this code"                  # non-interactive prompt
bob -i "Help me debug"                      # interactive with initial prompt
bob -s                                      # sandbox mode
bob -d                                      # debug mode
bob --yolo                                  # auto-approve ALL tool calls
bob --approval-mode auto_edit               # set approval mode
bob --allowed-tools "git status"            # specify auto-approved tools
bob --include-directories=../lib            # add directories to workspace
bob --chat-mode=my-mode                     # choose mode
bob --hide-intermediary-output              # final output only
bob --instance-id=my-instance               # specify instance ID
bob --team-id=my-team                       # specify team ID
```

### Trusted Folders
Bob Shell uses trusted folders to control project access:
- **Trust folder** — full trust to current folder
- **Trust parent folder** — trust to parent + all subdirectories
- **Don't trust** — restricted safe mode

**Untrusted folder restrictions:**
- Project settings and env vars ignored
- Tool auto-approval disabled
- MCP servers do not connect
- Custom commands not loaded

### Bob Shell Slash Commands
- Custom commands in `.bob/commands/` or `~/.bob/commands/`
- `/memory` — context management
- Mode commands for switching modes

---

## 17. Bob Marketplace

Community-contributed extensions integrated directly into Bob's Settings UI.

### What's Available
- **MCP Servers** — connect Bob to external tools, APIs, services
  - Examples: database clients, cloud platform integrations, specialized dev tools
- **Custom Modes** — pre-configured specialized personas
  - Examples: React development, documentation writing, security reviews

### How to Access
1. Click settings icon (⚙️) in Bob panel
2. Navigate to **MCP** or **Modes** tab
3. Browse and install directly from the unified interface

### Install / Uninstall
- **Install** — click item in marketplace view → Install
- **Uninstall** — click installed item → Uninstall (removes from config immediately)

---

## 18. Security & Best Practices

### `.bobignore`
- Uses `.gitignore` syntax
- Restricts which files Bob can read/modify through its tools
- Configure as first security measure in a new workspace
- **Note:** `@mentions` bypass `.bobignore` when directly referenced

### Security Checklist
- Configure `.bobignore` to restrict file access
- Review and limit auto-approve settings
- Keep secrets out of prompts, code snippets, and accessible files
- Use MCP servers with authentication, encryption, and access controls
- Review Bob's output before applying changes or running generated commands
- Store secrets in environment variable files (covered by `.gitignore` AND `.bobignore`)
- Use secret management tools (principle of least privilege)

### Best Practices for Working with Bob
1. **Use Plan mode first** for new projects or complex features
2. **Use Agent mode** for implementing features and file modifications
3. **Use Ask mode** when you need explanations without making changes
4. **Be specific** — use file paths and function names, not vague references
5. **Use context mentions** — more efficient than copy-pasting code
6. **Break down tasks** — smaller, focused subtasks keep context lean
7. **Run `/init`** at the start of every project — gives Bob persistent context
8. **Keep AGENTS.md lean** — only setup, test, and style commands
9. **Start a new conversation** when Messages category grows very large
10. **Use subagents** for isolated self-contained research or analysis work

---

## 19. The 5 Extensibility Surfaces

These are the primary ways to extend Bob's capabilities — what hackathon submissions should build:

### Surface 1: Custom MCP Server ⭐ (Highest Impact)
Connect Bob to any external API, database, or service.

**What you build:**
- TypeScript or Python server using the Model Context Protocol SDK
- Exposes any external service as Bob tools
- Deployable locally (STDIO) or as a hosted service (Streamable HTTP)
- Can be published to Bob Marketplace for community use

**Bob can scaffold it for you:**
- Ask: `"Create an MCP tool that queries our company database"`
- Bob writes the TypeScript, sets up the config, connects automatically

**Examples:**
- GitHub / GitLab / Jira / Linear integration
- Database query tool (PostgreSQL, MongoDB, Redis)
- Cloud platform tool (AWS, GCP, Azure CLI wrapper)
- Internal company knowledge base search
- Monitoring/alerting system (PagerDuty, Datadog)
- Any REST/GraphQL API wrapper

### Surface 2: Custom Mode ⭐ (High Impact)
Define a specialized AI persona with tailored role, tool access, and behavior.

**What you build:**
- `custom_modes.yaml` configuration
- Specialized role definition (the "who Bob is" in this mode)
- Targeted tool group permissions
- Custom instructions (the "how Bob behaves")
- `whenToUse` guidance for Orchestrator coordination

**Examples:**
- Security Auditor mode (read-only, OWASP focus)
- Product Manager mode (plan mode, no code writes)
- DevOps Engineer mode (execute permissions, infra focus)
- Technical Writer mode (docs-only writes)
- Junior Developer Guardrails mode (limited permissions)

### Surface 3: Custom Skill Pack ⭐ (High Impact)
Package domain-specific workflows as portable, reusable instruction sets.

**What you build:**
- One or more `SKILL.md` files in `.bob/skills/`
- Supporting files (checklists, templates, scripts, reference docs)
- Auto-activating based on description match

**Examples:**
- Security review skill (OWASP checklist + severity guide)
- Database migration skill (migration runbook + rollback scripts)
- API documentation skill (OpenAPI template + style guide)
- Onboarding skill (project tour + team conventions)
- Performance optimization skill (profiling checklist + patterns)

### Surface 4: Rules & AGENTS.md Templates (Medium Impact)
Opinionated project configuration templates for teams.

**What you build:**
- AGENTS.md templates for specific frameworks/stacks
- Mode-specific rule packs
- Team convention enforcement rules
- Internal monologue / audit trail setups

### Surface 5: Bob Shell Automation (Medium Impact)
CI/CD pipeline integrations and workflow automation.

**What you build:**
- Non-interactive pipeline scripts using `bob -p "..."`
- Custom slash command libraries (`.bob/commands/`)
- Sandbox-mode automated quality/security gates
- Pre-commit hooks powered by Bob Shell

---

## 20. Hackathon — Rules & Requirements

### Core Requirement
- Project **must meaningfully use IBM Bob** as a core component
- Must use Bob's extensibility layer (MCP, Skills, Modes, Rules) — not just basic chat
- Project must be built (or substantially enhanced) during the hackathon window

### Submission Requirements
- **Public GitHub repository** — open source expected
- **Working prototype** — not just a concept
- **Demo video** — typically 2-3 minutes showing the extension in action
- **README** — setup instructions, architecture explanation

### Team Rules
- Teams or individuals permitted
- Check official lablab.ai event page for maximum team size

### Technology Requirements
- IBM Bob (IDE or Shell) must be central to the project
- Any additional tech stack is allowed (Node.js, Python, TypeScript, etc.)
- MCP server can be in any language that supports STDIO or HTTP

---

## 21. Hackathon — Judging Criteria

| Criterion | Weight | What Judges Look For |
|-----------|--------|---------------------|
| **Use of IBM Bob** | Required | Meaningful, deep use of Bob's extensibility APIs |
| **Innovation & Originality** | High | Novel idea, creative use of Bob's features |
| **Technical Implementation** | High | Works end-to-end, clean code, proper use of MCP/Skills/Modes |
| **Practical Usefulness** | High | Solves a real developer pain point people actually have |
| **Presentation & Demo** | Medium | Clear before/after, 3-minute demo, articulate explanation |

### What Deep Integration Looks Like
Submissions that combine multiple surfaces score higher:
- `MCP Server + Custom Mode + Skill` = Deep integration
- `Just a custom mode` = Surface-level
- A working MCP server that Bob can use to solve real problems = Strong

---

## 22. Hackathon — Prizes

| Place | Prize |
|-------|-------|
| 🥇 1st Place | IBM Bob Enterprise subscription + lablab.ai credits + IBM swag |
| 🥈 2nd Place | IBM Bob Pro subscription + lablab.ai credits |
| 🥉 3rd Place | IBM Bob Pro subscription + community recognition |
| 🌟 Special Mentions | lablab.ai credits + community recognition |

> **Note:** Verify exact prize details on the official event page at https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon — prizes may be updated.

**Potential special category awards:**
- Best MCP Server
- Most Creative Use
- Best Custom Mode
- Most Practical / Highest Usefulness

---

## 23. What Makes a Winning Submission

### Must-Haves
- ✅ Bob is **central** — the extension is useless without Bob
- ✅ **Works end-to-end** — not a prototype, a real functional tool
- ✅ **Solves a real pain point** — something developers actually suffer with daily
- ✅ **Demo-able in 3 minutes** — clear before/after showing Bob + your extension in action
- ✅ **Documented** — AGENTS.md, README, setup instructions present
- ✅ **Uses multiple surfaces** — MCP + Mode + Skill together, not just one

### Differentiators
- 🌟 **Composable** — other teams can reuse/fork your MCP server or mode
- 🌟 **Polished UX** — the Bob experience feels natural and intuitive
- 🌟 **Surprising use case** — unexpected but obviously useful application
- 🌟 **Published to Bob Marketplace** — already available for community use
- 🌟 **Bob Shell integration** — works in CI/CD pipelines, not just IDE

### Common Pitfalls to Avoid
- ❌ Using Bob only for basic chat (no extensibility)
- ❌ Building something that could work without Bob at all
- ❌ Demo that doesn't work live (pre-record a backup)
- ❌ No AGENTS.md or setup docs — judges can't evaluate what they can't run
- ❌ Single-surface project (just a skill, nothing else)

---

## 24. Brainstorm Seed Ideas

### 1. Legacy Code Modernizer Agent
**Surfaces:** MCP + Custom Mode + Skill  
**Pain point:** Teams stuck on Node 14, Python 2, jQuery 1.x  
**Concept:** A custom "Modernizer" mode + skills containing upgrade playbooks (Node.js 22, Python 3.12, React 18) + MCP server that queries npm/PyPI for latest compatible versions and checks for breaking changes. Bob orchestrates: detect → plan → migrate → test.

### 2. Security Hardening Suite
**Surfaces:** Skills + Custom Mode + Rules  
**Pain point:** Security reviews are ad-hoc and inconsistent  
**Concept:** A "Security Auditor" mode (read-only) + skills for OWASP Top 10, secrets scanning (patterns for common secret formats), dependency CVE checking. Activates automatically when touching auth, crypto, or API boundary files.

### 3. Issue Tracker MCP Bridge
**Surfaces:** MCP + Custom Mode  
**Pain point:** Context-switching between IDE and project management tools  
**Concept:** MCP server connecting to GitHub Issues + Jira + Linear. Bob can create, assign, comment, close tickets from chat. Custom "PM" mode interprets code changes into user story updates automatically.

### 4. Team Onboarding Autopilot
**Surfaces:** Bob Shell + Rules + Skills  
**Pain point:** New developer onboarding takes days and is inconsistent  
**Concept:** Bob Shell pipeline: `/init` → generates customized onboarding docs → bootstraps AGENTS.md templates for the stack → creates a guided tour conversation. Skill pack that knows the team's conventions.

### 5. Database Migration Agent
**Surfaces:** MCP + Custom Mode + Skill  
**Pain point:** Schema migrations are risky and poorly documented  
**Concept:** MCP server connects to database (PostgreSQL, MySQL). Custom mode that plans migrations step-by-step, generates SQL + ORM code, runs validation tests, and handles rollback on failure. Migration skill includes the runbook.

### 6. Documentation-as-Code Engine
**Surfaces:** Skills + Custom Mode + Rules  
**Pain point:** Docs always get out of date immediately after writing  
**Concept:** "Docs Keeper" mode + skills that enforce: README reflects code, API docs match OpenAPI spec, CHANGELOG updated from git commits. Rules trigger doc checks on every Agent session.

### 7. Bob-Powered DevOps Copilot
**Surfaces:** MCP + Bob Shell + Custom Mode  
**Pain point:** Infra operations require deep CLI knowledge  
**Concept:** MCP server wrapping AWS/GCP/Azure CLI. "DevOps Engineer" mode in Bob Shell. Bob can describe infrastructure, plan changes, apply with approval, monitor deployment status — all from a chat prompt.

### 8. Test Coverage Enforcer
**Surfaces:** Skills + Rules + Bob Shell  
**Pain point:** Test coverage drops over time with no enforcement  
**Concept:** Bob Shell CI gate — runs coverage analysis, creates GitHub Issues for functions below threshold, generates test stubs for uncovered code. Skills contain testing patterns per framework (Jest, pytest, JUnit).

### 9. Code Review Copilot for PRs
**Surfaces:** MCP + Skill  
**Pain point:** PR reviews are bottlenecks and inconsistent  
**Concept:** MCP server connecting to GitHub PRs. Skill containing review checklist. Bob fetches PR diff, runs `/review`, posts structured findings as GitHub PR comments — auto-labeling severity.

### 10. Internal Knowledge Base Connector
**Surfaces:** MCP + Skill  
**Pain point:** Developers can't find internal docs, runbooks, or past decisions  
**Concept:** MCP server indexing Confluence, Notion, or internal wikis. Skill that knows how to search and cite internal knowledge. Bob answers "how do we handle auth in this company?" from internal docs, not just web knowledge.

---

## 25. Quick Reference Cheatsheet

### File Locations
```
<project>/
├── AGENTS.md                     # project context (run /init to generate)
├── .bobignore                    # file access restrictions (gitignore syntax)
└── .bob/
    ├── custom_modes.yaml         # custom mode definitions
    ├── rules/                    # general rules (all modes)
    ├── rules-agent/              # agent mode rules
    ├── rules-plan/               # plan mode rules
    ├── rules-ask/                # ask mode rules
    ├── rules-{custom-slug}/      # custom mode rules
    ├── skills/
    │   └── <skill-name>/
    │       └── SKILL.md          # skill definition + supporting files
    └── commands/
        └── <command-name>.md     # custom slash commands

~/.bob/                           # global scope (same structure)
├── custom_modes.yaml
├── AGENTS.md
├── skills/
└── commands/
```

### Key Commands
```
/init           # bootstrap project context
/review         # AI code review
/memory show    # verify loaded context
/memory refresh # reload context files
/bug            # report feedback
```

### MCP Config Snippet
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["dist/server.js"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

### Custom Mode Snippet
```yaml
customModes:
  - slug: security-auditor
    name: 🔒 Security Auditor
    roleDefinition: You are an expert security engineer...
    whenToUse: Use for security reviews and vulnerability detection
    customInstructions: Always reference OWASP. Provide severity levels.
    groups:
      - read
      - mcp
      - skill
```

### SKILL.md Snippet
```markdown
---
name: security-review
description: Review code for security vulnerabilities and best practices
---

Check for:
- SQL injection, XSS, auth/authz issues
- Sensitive data exposure
- Input validation and output encoding

Provide findings with severity (Critical/High/Medium/Low) and recommended fix.
```

### Context Window Tips
| Problem | Solution |
|---------|---------|
| Context getting full | Start new conversation (+) |
| Bob drifting/ignoring rules | Context poisoning — start fresh |
| Slow responses on large files | Use FindSymbol instead of @file |
| Need parallel work | Use spawn_subagent |
| Need tracked complex work | Use start_subtask |

---

*Last updated for IBM Bob Hackathon 2.0 context brief. Official event details at https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon*

---

## 26. Bob Plans, Billing & Bobcoins

### Plans Overview

| Plan | Bobcoins/Month | Notes |
|------|---------------|-------|
| **Free Trial** | 40 Bobcoins | Trial access |
| **Pro** | 40 Bobcoins | Individual paid |
| **Pro+** | 160 Bobcoins | Individual paid |
| **Ultra** | 500 Bobcoins | Individual paid |
| **Enterprise** | Purchased in packs | Centralized team pool |

- **1 Bobcoin = $0.50 USD**
- **Overage rate:** $0.50 USD per Bobcoin, automatic billing
- Bobcoin allocation resets at the start of each billing cycle

### Enterprise Plan
- **Shared Bobcoin pool** — distribute from a centralized budget to the entire team
- **Admin dashboard** — control spending, manage users, track usage
- **Teams** — each team's spending tracked separately against its allocated budget
- **Enterprise support** — dedicated IBM Bob specialists
- **Bobcoin packs:** 1,000 Bobcoins per pack at $500 USD — expire 1 year after purchase
- Manage via `bob.ibm.com/admin` → Users & Teams → assign premium packages per user

### What Are Bobcoins?
Bobcoins are IBM's billing metric abstracting raw token usage into a predictable cost structure.
- **Tokens** = raw units of text the AI model processes (input prompt + output response)
- **Bobcoins** = standardized billing unit across all models and operations
- Different models have varying token costs — Bobcoins unify this into one metric
- Bob automatically converts model usage to Bobcoins for transparent billing
- You do not need to track tokens directly

### Premium Packages
Optional add-ons that extend IBM Bob with specialized capabilities. Assignable per-user by Enterprise admins via the Administration page.

---

## 27. Authentication & API Keys

### Authentication Methods

| Method | Use Case | Requires |
|--------|---------|---------|
| **SSO / IBMid** | Interactive IDE and Shell sessions | IBMid or corporate SSO + browser |
| **API Key** | Automation, CI/CD, non-interactive sessions | API key from Bob web portal + env var |

### SSO / IBMid
- Login entry point: `bob.ibm.com/login`
- First run or expired session → Bob opens browser automatically
- Corporate SSO configured → redirected to company login page
- Otherwise → redirected to IBMid
- Session established automatically after browser auth

### API Key Authentication (for Bob Shell / CI/CD)
1. Create an API key in the Bob web portal with **Scope: Inference**
2. Download/copy the key — **you cannot view it again**
3. Set environment variable:
   ```bash
   # macOS/Linux
   export BOBSHELL_API_KEY="your-api-key-here"

   # Windows PowerShell
   $env:BOBSHELL_API_KEY="your-api-key-here"
   ```
4. Run Bob Shell with API key:
   ```bash
   bob --auth-method api-key -p "Explain this project"
   ```

### When to Use API Keys
- Authenticate Bob Shell in non-interactive sessions
- Run Bob in CI/CD pipelines or scheduled automation
- Avoid browser-based sign-in for scripted workflows
- Authenticate inference requests programmatically

### Non-interactive Session Setup
```bash
# First time: accept license agreement
bob --accept-license -p "Explain this project"

# Subsequent non-interactive runs
bob -p "Your task here"
```
> **Note:** Non-interactive sessions require API key authentication. Pre-configure `~/.bob/trustedFolders.json` for security-sensitive CI environments.

---

## 28. Code Actions & Literate Coding

### Code Actions
AI-powered actions accessible directly in the editor via:
- **Lightbulb icon** — appears in the gutter when you select code
- **Context menu** — right-click selected code → Bob → select action
- **Keyboard shortcuts** (see Section 29)

**Available code actions:**
- **Inline Chat** — opens a chat interface at cursor position; respond directly in editor
- **Move to Chat** — sends selected code to the main chat panel with file path + line numbers
- **Explain** — explains selected code in plain language
- **Fix** — AI-suggests fixes for selected code/errors
- **Generate** — generate code from a selection/instruction

### Inline Chat
```
Select code → Ctrl+K (Win/Linux) or Cmd+K (macOS)
```
- Opens chat directly in the editor (no switching to panel)
- Respond and accept/reject changes without leaving the file
- Useful for quick, focused edits

### Move to Chat
```
Select code → Ctrl+L (Win/Linux) or Cmd+L (macOS)
```
- Sends selection to the main chat panel with full context
- File path and line numbers included automatically
- For detailed multi-turn conversations about the code

### Literate Coding Mode
Write natural language instructions **directly in your source file** — Bob converts them to code.

**How it works:**
1. Toggle mode: `Ctrl+I` (Win/Linux) or `Cmd+I` (macOS) — or click the magic wand icon
2. Write instructions in plain English, pseudocode, or annotations in the file
3. Instructions appear **highlighted in blue**
4. Press `Cmd/Ctrl + Enter` or click **Generate**
5. Bob analyzes the file + surrounding context, replaces instructions with real code
6. Shows an **inline diff** — review before accepting

**Accept/Reject diff:**
- Accept: `Cmd/Ctrl + Enter`
- Reject: `Cmd/Ctrl + Shift + Backspace`
- Changes are written to file before acceptance — you can test them before deciding

**Use cases:**
- Write pseudocode and convert it to implementation
- Annotate what a function should do and generate it
- Describe a change in plain language without opening the chat panel
- Great for staying focused in the file without context-switching

---

## 29. Keyboard Shortcuts — Full Reference

| Command | macOS | Windows/Linux | Description |
|---------|-------|---------------|-------------|
| **Inline Chat** | `Cmd + K` | `Ctrl + K` | Open inline chat at cursor in editor |
| **Move to Chat** | `Cmd + L` | `Ctrl + L` | Send selected code to chat panel |
| **Literate Coding** | `Cmd + I` | `Ctrl + I` | Toggle literate coding mode |
| **Open Bob Panel** | `Option + Cmd + B` | `Ctrl + Alt + B` | Show/focus Bob chat panel |
| **Mode Toggle** | `Cmd + .` | `Ctrl + .` | Cycle through available modes |
| **Bob.acceptInput** | configurable | configurable | Submit text or accept primary suggestion |
| **Bob.focus** | configurable | configurable | Focus the Bob input box |

> Configure custom shortcuts: Bob Settings → General → Keyboard Shortcuts

---

## 30. Bob Shell Sandboxing

Sandboxing isolates potentially dangerous operations from the host system using container-based isolation.

### Sandboxing Methods

| Method | Technology | Use Case |
|--------|-----------|---------|
| **Native** | OS-level isolation | Default, no deps needed |
| **Container-based** | Docker or Podman | Full process isolation, cross-platform |

### Enable Sandbox Mode
```bash
bob -s "your task here"
# or
bob --sandbox "your task here"
```

### Container-based Sandboxing (Docker/Podman)
- Requires Docker or Podman installed
- Builds sandbox image locally (or uses org registry image)
- Complete process isolation from host
- Custom flags via `SANDBOX_FLAGS` environment variable:
  ```bash
  # Single flag example
  export SANDBOX_FLAGS="--security-opt label=disable"
  bob -s "analyze this script"

  # Multiple flags (memory + CPU limits)
  export SANDBOX_FLAGS="--memory=4g --cpus=2"
  bob -s "analyze this script"
  ```

### Useful For
- Disabling SELinux labeling on Podman
- Setting resource limits (memory, CPU)
- Configuring custom network settings
- Adding custom volume mounts

### Limitations
- Not a complete security solution — always review Bob's actions
- Container-based sandboxing has minimal overhead after initial image build
- GUI/graphical applications do not work inside sandboxes (display isolation)

---

## 31. Bobalytics — Enterprise Analytics

Enterprise-only analytics dashboard measuring Bob's value across an organization.

### Three Core KPIs

#### 1. Adoption Rate
> How many people are actively using Bob?

- **Formula:** Average daily active users ÷ total licensed seats
- A user is "active" on a day when they accept ≥1 code completion OR complete a chat conversation
- **Charts:** Team onboarding %, daily active users over time, usage level breakdown (multiple/day, daily, weekly, occasional, inactive)
- **Tip:** Low adoption → check usage levels, identify inactive users, review onboarding

#### 2. Bob Factor
> How much of your shipped code did Bob actually write?

- **Formula:** Lines of code committed by Bob ÷ total lines of code committed
- **Charts:** Impact vs. cost per team, Bob-assisted commits over time, team trends
- **Tip:** High Bob Factor + low spend = efficient use. High spend + low Bob Factor = review usage patterns

#### 3. Bobcoin Spend
> What is Bob costing us?

- Total Bobcoins consumed over selected period
- **Charts:** Impact and cost (Bob factor vs. spend), daily spend, team details and trends
- **Tip:** High spend + high adoption + strong Bob factor = effective use. High spend + low Bob factor = opportunity to review

### Using All Three Together

| Goal | KPI Focus |
|------|-----------|
| How many people use Bob actively? | Adoption rate |
| How much code did Bob contribute? | Bob factor |
| What did it cost? | Bobcoin spend |
| Is it worth the money? | Bob factor + Bobcoin spend together |

> Bobalytics is available on the Enterprise plan via `bob.ibm.com/admin`.
