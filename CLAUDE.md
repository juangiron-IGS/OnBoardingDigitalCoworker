# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Hackathon project building the **Onboarding Digital Coworker** for INSPYR on **Velocity 2.0**. The design and scope were delivered at the 2026-10-14 checkpoint. Final submission is due **2026-10-22**. No application code exists yet: the repo holds requirement and design documents plus one utility script. There are no build, lint or test commands until source code lands.

## Documents and which one wins

Read these in this order of authority when they disagree:

1. [Documents/CheckPoint/14October/checkpoint-deliverable.md](Documents/CheckPoint/14October/checkpoint-deliverable.md): the approved design (agents, case states, data model, integrations, governance, acceptance criteria, plan). `checkpoint-deliverable-no-images.md` is the same content with the diagrams written out as tables, which is easier to read as text. Use the checkpoint as the baseline when reviewing other project documents.
2. [Documents/Velocity/01. Understanding/](Documents/Velocity/01.%20Understanding/): Velocity stage-01 Source of Truth (SOT-001). It uses ID catalogs (CAP capabilities, BR business rules, UR user roles, INT integrations, OQ open questions) that later Velocity stages (Strategic Intake, Functional Spec, Backlog) trace back to; its Glossary defines them. Two versions exist: `(offline)` is v1.1, edited by hand to match the checkpoint, and is the one aligned with it; the other is a later Velocity regeneration (v1.0) that drops several of those fixes. Velocity rebuilds the SOT from its own Answers record, so regenerating it discards manual edits. `Documents/Velocity/sot-001-*-considerations.md` record the alignment facts used for v1.1.
3. [Documents/Employee Onboarding Digital Coworker - Solution Intake.md](Documents/Employee%20Onboarding%20Digital%20Coworker%20-%20Solution%20Intake.md): the original problem statement. Its agent list (Employee Information, Policy and Classification, ...) is superseded by the checkpoint. It was generated from the `.docx` next to it; if the `.docx` changes, regenerate the `.md` instead of editing it by hand.
4. [Documents/HackatonDocuments/](Documents/HackatonDocuments/): hackathon rules. `TechnicalRequirements.md` (platform and security), `GitHubSubmisionPackage.md` (required repo contents and README sections), `evaluationCriteria.md` (scoring weights), `expectedvalue.md`.

[README.md](README.md) already contains every required submission section. Sections marked *Planned* must be filled in as code lands (install, run, demo commands, `.env.example`, license).

## Target architecture (from the checkpoint)

To users it is one Coworker reached through a local web app (chat, simulated inbox, approval, alerts and status views); Velocity 2.0 has no chat UI, so the web app is required. Inside, an **Onboarding Orchestrator** owns the case and routes work to specialized agents that share one context:

- Must: Intake and Validation, Policy and Case Setup, JobDiva and Workflow
- Should: Access and Equipment, Candidate Follow-up, Onboarding Knowledge
- Could: Culture and Belonging (IGS)

Notifications (email, Teams) are a shared tool, not an agent. The demo must show at least three specialized agents collaborating on one case.

Design rules that cut across components:
- **Single writer.** Only the JobDiva and Workflow agent writes to (simulated) systems, and only with an approval ID for the *current* package version. A returned package goes back to Validated and needs a new approval.
- **Case states:** Received → Validated (or Needs clarification) → Case set up → Ready for review → Approval gate → Approved / Rejected / returned → Actions executed, then the Should/Could states (documents, verification, payroll, IGS handoff) → Closed. Duplicate (same person and start date) blocks at Received.
- **Rules and knowledge are data, not code.** Paperwork path, forms by state/city/client, owner, 2%/5% equipment overhead and bill-back live in a rules catalog the business maintains. Every package line carries a label (source, inferred, recommended, exception) and the source or rule ID.
- **Every enterprise system is a mock** exposed as a tool or MCP server: JobDiva, Outlook mailbox, Teams, IT and equipment (Chelsea Tech), payroll (Paychex), LDC tracker (SharePoint).
- **JobDiva connector has two modes** behind one interface: `JOBDIVA_MODE=mock` (default, read/write on synthetic data) and `JOBDIVA_MODE=sandbox` (read-only; the Coworker never writes to real JobDiva). Sandbox credentials come from `.env`; the token stays in memory and is never logged.
- The entities (case, package line, approval, document checklist, business rule, cultural follow-up, knowledge record, audit log) are listed in the checkpoint's Data model section.

## Hard constraints

- Human approval before any action on a system, access, equipment or purchase. Never place real orders or provision production access.
- The Coworker never decides FLSA, worker classification, compensation or legal employment questions; it escalates them.
- Synthetic or anonymized data only; no connection to client production environments.
- No credentials in the repo. Ship `.env.example` with variable names only (`.env` and `.env.*` are git-ignored).
- Log every agent action with its agent, case, data and rules used.

## Repo conventions

- `.gitignore` keeps internal material out of the public repo: `Documents/Meetings Transcript/`, `Documents/Team Ideas/` and `.pptx` files in `Documents/HackatonDocuments/`. Do not add those paths.
- The final repo must also contain Velocity config, source, agent definitions/prompts/skills, integration scripts, DB schemas and migrations, seed data, tests and evidence, architecture diagram, final presentation, backup demo video, and license/dependency info (see `GitHubSubmisionPackage.md`).
- Put helper scripts in `tools/`. `python tools/docx_to_md.py <input.docx> [output.md]` converts Word to Markdown (needs `python-docx`; output defaults to next to the input).
