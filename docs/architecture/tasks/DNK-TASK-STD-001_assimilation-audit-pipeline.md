---
mrh_id: DNK-TASK-STD-001
title: Assimilation & Mentor Audit Pipeline
author: Maxim
license: MIT
version: 1.0.0
---

# DNK-TASK-STD-001: Assimilation & Mentor Audit Pipeline

## 1. Purpose

Define a standard workflow for agents (Gerych, Antigravity subagents, etc.) to:
- Perform assimilation and architecture work in DNK OS.
- Export artifacts to the mentor audit repo.
- Apply mentor feedback back into DNK OS.

## 2. Required Artifacts per Assimilation Task

For each external repo or architecture topic, agents MUST produce:

- `RN-XXX_<repo>-research.md` — Research & Evidence Trail.
- `DNK-ARCH-XXX_<topic>.md` — Architecture spec.
- `DNK-COMP-XXX_<topic>.md` — Component interfaces & contracts.
- `DNK-SEC-XXX_<topic>.md` — Security / sandbox / egress spec.
- `skills/<repo>_assimilated/SKILL.md` — Index skill pointing to the 4 artifacts.

All of these live **locally in** `docs` and `skills`.

## 3. Export to Mentor Audit Repo

To export artifacts for mentor review:

1. Ensure files are saved and committed locally in `DNK_HUB`.
2. Run the export script:
   ```bash
   cd /Users/<username>/Kuzmenko/MY_LIFE_WORK/DNK_HUB/DNK OS
   ./scripts/export-assimilation.sh
   ```
3. The script copies `docs` and `skills` into a temporary workspace and pushes Markdown-only files to:
   - `https://github.com/Kuzmenko-top/dnk-os-mvp-assimilation` (branch `main`).

## 4. Mentor Review Protocol

After export:

1. Supervisor (Maxim) notifies Mentor:
   - Example:
     > "Перевір RN-002, DNK-ARCH-002, DNK-COMP-002, DNK-SEC-002, SKILL.md у dnk-os-mvp-assimilation."

2. Mentor (Antigravity / Perplexity) reads artifacts via GitHub MCP.
3. Mentor returns:
   - PASS / WARN / FAIL status per file.
   - Concrete changes and improvements.

## 5. Applying Feedback to DNK OS

Agents MUST:

1. Apply all approved changes **directly in** `docs` and `skills`.
2. Optionally re-export to `dnk-os-mvp-assimilation` to keep the audit view in sync.
3. Use DNK OS as the **single source of truth** for specs and tasks.

## 6. Guardrails

- DNK_HUB git ignores `DNK_HUB/`.
- DNK OS `.gitignore` protects:
  - `.venv/`, `__pycache__/`, `.next/`, `node_modules/`, logs, telemetry, `.env`.
- dnk-os-mvp-assimilation:
  - Enforces Markdown-only content via `.gitignore` and CI (`validate-artifacts.yml`).
  - Contains no application code.

## 7. Single Next Action (for any agent)

When you finish an assimilation task:

1. Save & commit RN, DNK-ARCH, DNK-COMP, DNK-SEC, SKILL in DNK OS.
2. Run `./scripts/export-assimilation.sh`.
3. Supervisor notifies Mentor with the list of artifacts to audit.
4. Apply mentor feedback back into DNK OS.
