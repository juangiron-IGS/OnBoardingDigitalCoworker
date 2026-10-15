# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Hackathon project (three weeks) building the **Employee Onboarding Digital Coworker** for INSPYR. No application code exists yet; the repo currently holds requirement documents and one utility script. The checkpoint deliverable (design and scope, not code) is due **2026-10-14**.

## Source of truth for requirements

- [Documents/Employee Onboarding Digital Coworker - Solution Intake.md](Documents/Employee%20Onboarding%20Digital%20Coworker%20-%20Solution%20Intake.md): the problem, MVP scope, capabilities (Must/Should/Could), agent roles, demo scenario, success metrics, guardrails, out-of-scope items and definition of done. It was generated from the `.docx` next to it. If the `.docx` changes, regenerate the `.md` instead of editing it by hand.
- [Documents/HackatonDocuments/](Documents/HackatonDocuments/): hackathon rules. `TechnicalRequirements.md` covers the platform and security rules, `GitHubSubmisionPackage.md` lists the required repo contents and README sections, `checkPoint.md` lists the Oct 14 deliverable, and `evaluationCriteria.md` gives the scoring weights.

## Intended architecture (from the Solution Intake)

The MVP has two core journeys plus one optional journey:
1. **Onboarding Intake**: a manager starts with a simple request ("hire X starting Oct 1"). The coworker adapts its questions to the onboarding path (employee or contractor, location, client assignment) until all mandatory data is collected.
2. **Approval and Action Package**: the coworker builds a structured package. A human approves it, rejects it or returns it for correction. Only after approval does the coworker create or simulate the JobDiva placement record, the IT access request, the equipment request and the task list.
3. Optional: a personalized information package for the new employee (company, client and role).

An **Onboarding Orchestrator** coordinates specialized agents that share context:
- Employee Information
- Policy and Classification
- Access and Equipment
- JobDiva and Workflow
- Onboarding Content (optional)

The demo must show at least three agents working together.

## Hard constraints

- **Platform**: Velocity 2.0 is mandatory. Local demos are acceptable. Simulated services, connectors and MCP servers are allowed and expected: mock JobDiva, mock IT access and equipment services, and synthetic employee scenarios.
- **Human-in-the-loop**: every action on an enterprise system, access, equipment or purchase needs explicit approval. Never place real orders or provision production access.
- **No autonomous legal decisions**: the coworker does not decide worker classification, compensation or legal employment questions on its own. Unclear cases are escalated.
- **Data**: use synthetic or anonymized data only, and never connect to client production environments.
- **Secrets**: no credentials in the repo. Provide an example env file (for example `.env.example`) that lists the required variable names.
- **Traceability**: every recommendation must cite the information, rule or user response that supports it. Log agent activity and approvals.
- Prevent duplicate onboarding requests and records.

## Submission requirements that shape the repo layout

The final repo must contain:
- Velocity config files
- Application source
- Agent definitions, prompts and skills
- Integration scripts
- DB schemas and migrations
- Seed data
- Tests and test evidence
- Architecture diagram
- Final presentation
- Backup demo video
- License and dependency information

The README must include these sections:
- Business problem and expected outcome
- Coworker responsibilities
- Agent architecture
- Prerequisites and installation
- Configuration
- How to run the solution
- How to run the demo
- Security and governance
- Known limitations
- Reusable components

## Tools

`tools/` holds helper scripts. Put any new utility there.

- `python tools/docx_to_md.py <input.docx> [output.md]`: converts Word documents to Markdown. Requires `python-docx`. By default the output goes next to the input.
