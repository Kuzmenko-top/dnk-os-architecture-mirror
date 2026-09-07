---
title: "054 Task Execution Platform - Evidence Planner, Risk Gate and GitHub Research"
created: 2026-09-05
updated: 2026-09-05
tags:
  - architecture
  - task_execution_platform
  - evidence_planner
  - risk_gate
  - github_research
  - sota_assimilation
  - dnk_os
aliases:
  - "015 Task Execution Platform - Evidence Planner, Risk Gate and GitHub Research"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/054 Task Execution Platform - Evidence Planner, Risk Gate and GitHub Research.md"
purpose: "Architecture specification for Evidence Planner, Automated Risk Gate, and Two-Track GitHub Research Module."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

E4 DNK OS Task Execution Platform: Evidence Planner, Risk Gate & SOTA GitHub Research

## 📌 Огляд
Після впровадження **Auto-Task-Spec Generator** платформа DNK OS отримала три нові промислові підсистеми для перетворення агента з хаотичного кодера на прогнозовану виробничу платформу:
1. **Evidence Planner (`core/orchestrator/evidence_planner.py`)** — Емпіричний планувальник доказів та епістемічний класифікатор.
2. **Risk Gate (`core/orchestrator/risk_gate.py`)** — Автоматичний оцінювач ризиків (LOW/MEDIUM/HIGH) з вимогами погодження, бекапу та відкату.
3. **GitHub Research Module (`core/orchestrator/github_research.py`)** — Аналізатор ліцензій за протоколом Two-Track Assimilation (MIT/Apache vs GPL clean-room), витягування патернів та оцінки активності.

---

## 🔬 1. Evidence Planner & Epistemic Taxonomy
Для запобігання галюцинаціям та "голослівним твердженням" кожне твердження у завданні або специфікації класифікується за шкалою епістемічного статусу:
- **`OBSERVED`**: Факт, безпосередньо зафіксований перевіреними командами або файловою системою (розмір файлу, git статус, наявність коду в AST).
- **`INFERRED`**: Висновок, зроблений на основі сукупності спостережень.
- **`HYPOTHESIS`**: Припущення або гіпотеза, що потребує обов'язкової емпіричної перевірки.

### Типи доказів (Evidence Types):
- `filesystem`: перевірка наявності файлів, розміру (`du -sh`, `stat`).
- `git`: статус репозиторію, чистий робочий каталог, історія комітів (`git status --porcelain`).
- `test_gate`: автоматичні тести (`pytest`, `verify_all.sh`).
- `metrics`: часові або кількісні виміри.

---

## 🛡️ 2. Risk Gate & Safety Invariants
Автоматично аналізує запит та цільові файли на наявність небезпечних операцій:
- **`HIGH`** (85+ балів): видалення файлів (`delete`, `rm -rf`, `drop database`, `reset --hard`), зміна секретів (`.env`, `vault`, `SOUL.md`).
  - Вимагає: явного підтвердження людини (`requires_approval: True`), створення бекап-знімка (`backup_required: True`), план відкату (`rollback_required: True`).
- **`MEDIUM`** (50 балів): масовий рефакторинг, міграція баз даних, модифікація понад 5 файлів.
- **`LOW`** (15 балів): створення нового коду, читання, юніт-тести, аудит. Автономне виконання в межах ліміту MASE (≤ 25 tool calls).

---

## 🧬 3. Two-Track GitHub Research Module
Інтеграція з Two-Track SOTA Assimilation Protocol (`core/dna_assimilation.py`):
- **Track 1 (DIRECT: MIT / Apache 2.0 / BSD / ISC)**: Пряме запозичення компонентів, шаблонів та коду.
- **Track 2 (CLEAN_ROOM: GPL / AGPL / LGPL / SSPL / Non-Commercial)**: Реверс-інжиніринг, синтез нової архітектури без копіювання коду.
- Автоматичний збір метрик активності: зірки, форки, дата останнього коміту, ключові патерни та архітектурна застосовність для DNK OS.

---

## 🔗 Пов'язані модулі та нотатки
- [[024 Auto-Task-Spec Generation Protocol]]
- `core/orchestrator/task_spec_generator.py`
- `core/orchestrator/evidence_planner.py`
- `core/orchestrator/risk_gate.py`
- `core/orchestrator/github_research.py`
- `scripts/system/auto_task_spec.py`
- `scripts/system/hermes_pre_tool_hook.py`
