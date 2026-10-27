# Using the Coworker from other chat apps (MCP)

The Coworker is also an MCP server, `onboarding-coworker`, so a person can work with it from another chat app instead of the web app. It runs on `127.0.0.1` only and uses synthetic data only.

## What it can do

| Tool | What it does |
|---|---|
| `start_onboarding(text, sender)` | Starts a case from a start email or message and returns the first question |
| `answer_question(case_id, text)` | Answers the Coworker's next open question |
| `case_status(ref)` | How a case is going and who must act, from the case record only |
| `open_questions(case_id)` | The fields still missing or in conflict |
| `my_alerts(limit)` | The latest alerts for the server's role |

It acts as one role, `COWORKER_MCP_ROLE` (default `recruiter`), so FLSA, visa and sponsorship values stay hidden. **It cannot approve, return or reject a package, assign an owner or act on any system**: those decisions stay with people in the web app (BR-002), and a test checks that no such tool is registered. Every call goes through the same orchestrator, governance and audit log as the web app, with the channel recorded as `mcp`.

## Connect a client

Start the Coworker first, from `code/` (Git Bash):

```bash
./scripts/start.sh      # with AGENT_TRANSPORT=mcp it also starts onboarding-coworker on 127.0.0.1:8110
```

**Claude Code** (in this repository): `.mcp.json` at the repository root already points to `http://127.0.0.1:8110/mcp`. Approve the `onboarding-coworker` server when Claude Code asks.

**VS Code** (Copilot or Claude extension): add to `.vscode/mcp.json` in your workspace:

```json
{ "servers": { "onboarding-coworker": { "type": "http", "url": "http://127.0.0.1:8110/mcp" } } }
```

**Claude Desktop**: add to `claude_desktop_config.json` (Settings, Developer, Edit config). Claude Desktop starts the server itself over stdio; it reads `code/.env` for the database settings. Adjust the paths to your clone:

```json
{
  "mcpServers": {
    "onboarding-coworker": {
      "command": "C:\\repo\\Hackaton\\Movers-OnBoarding\\code\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_servers.coworker.server", "--stdio"],
      "cwd": "C:\\repo\\Hackaton\\Movers-OnBoarding\\code"
    }
  }
}
```

PostgreSQL must be running (`./scripts/start.sh` or `docker compose up -d postgres`).

## Try it

> "Start an onboarding case from this email: Candidate ID: SYN-0950, Position: QA Engineer, Start date: 2026-12-21, ..."
>
> "What does the Coworker still need for SYN-0950?" / "The bill rate is 61.00 USD/h" / "How is SYN-0950 doing?"

Then open the web app (http://127.0.0.1:3000) as the Approver to review and approve the package.

## Coworker Tray (Windows notifications)

The tray is an MCP client too. It starts `onboarding-coworker` over stdio with the role picked in its menu (`COWORKER_MCP_ROLE`) and calls only `my_alerts`, every 5 seconds. A new alert shows a Windows notification and a red dot on the icon; **Open latest alert** (or a click on the icon) opens the Coworker window docked above the clock, as that role. The chat is its main view, on the alert's case; Approval, Dashboard, Status and the other views are tabs, with the same controls as the web app (`?mode=desktop`). **Open in the browser** opens it in the browser instead.

```bash
.venv/Scripts/python -m pip install -e ".[tray]"   # once
./scripts/tray.sh                                   # after ./scripts/start.sh
```

`COWORKER_TRAY_ROLE` sets the first role (default `recruiter`).

## Microsoft Teams (pilot)

Teams does not use MCP directly. In the pilot, a Copilot Studio agent in Teams can connect to this MCP server. That needs the server published over HTTPS with Entra ID authentication, which the hackathon rules exclude (everything on `127.0.0.1`, no Teams bot, TC-005).
