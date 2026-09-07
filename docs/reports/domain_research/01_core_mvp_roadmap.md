# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/domain_research/01_core_mvp_roadmap.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "projects/01_DNK_OS_Core/planning/DNK_OS_MVP_ROADMAP.md"
purpose: "Офіційний roadmap DNK OS MVP з фазами, задачами та критеріями завершення."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-08-05"
--- END DNK-MRH-HEADER --- -->

---
document_id: DNK-PLAN-0001
file_name: DNK_OS_MVP_ROADMAP.md
title: DNK OS MVP Roadmap
category: PLAN
type: Roadmap
owner: Maxim
status: Active
version: 1.0.0
created_at: 2026-08-05
updated_at: 2026-08-05
parent_id: DNK-GOV-0024
related_ids: [DNK-DEV-2001]
tags:

  - roadmap
  - mvp
  - planning
  - dnk-os

storage_type: git
path: projects/01_DNK_OS_Core/planning/DNK_OS_MVP_ROADMAP.md
access_level: write
---

# DNK OS MVP — Офіційний Roadmap

> **Source of truth**: `planning/dnk_mvp_tasks.json`  
> **Візуалізація**: `planning/dnk_task_graph.html` (відкрити у браузері)  
> **Архітектурна основа**: `docs/product/CORE_VISION.md`

---

## Ключовий принцип: Thin Thread

Ми не будуємо все і одразу. Один бізнес-кейс проводиться крізь **усі 3 шари**:

```
Запит Максима
  → omni_router.py (Kernel)
    → hub_memory (PostgreSQL)
      → Gerych Agent (Spoke)
        → Результат у Visual Shell (UI)
```

---

## Фазова Структура

| Фаза | Назва | Тривалість | Статус |
|------|-------|-----------|--------|
| **P0** | Architecture Lock | 1 тиждень | `done` |
| **P1** | Core Kernel MVP | 2 тижні | `in_progress` |
| **P2** | Visual Shell Alpha | 2 тижні | `todo` |
| **P3** | Agent Fleet v1 | 2 тижні | `todo` |
| **P4** | Integration & Thin Thread | 1 тиждень | `in_progress` |

---

## P0 — Architecture Lock (DONE)

**Мета**: Зафіксувати архітектуру перед розробкою. Ніяких змін Core Vision після цього.

- [x] `CORE_VISION.md` — затверджено (DNK-GOV-0024)
- [x] `DECISIONS.md` — зафіксовано ключові рішення
- [x] Структура `projects/01_DNK_OS_Core/planning/` — створено
- [x] `dnk_mvp_tasks.json` — source of truth задач
- [x] `dnk_task_graph.html` — інтерактивна візуалізація

**Definition of Done**: Граф задач відкривається у браузері та відображає повну архітектуру MVP.

---

## P1 — Core Kernel MVP

**Мета**: Серце DNK OS — усе, що потрібно для того, щоб система думала та маршрутизувала.

### Компоненти

| ID | Задача | Агент | Статус |
|----|--------|-------|--------|
| T1_HUB_MEMORY | hub_memory PostgreSQL backend | gerych | `done` |
| T1_MEMORY_TASKS_TABLE | tasks table schema | gerych | `done` |
| T1_MEMORY_VECTOR_INDEX | pgvector ivfflat index | gerych | `done` |
| T1_OMNI_ROUTER | omni_router.py | gerych | `in_progress` |
| T1_ROUTER_INTENT | Intent Classifier (LLM) | gerych | `todo` |
| T1_ROUTER_DISPATCH | Task Dispatcher | gerych | `in_progress` |
| T1_MCP_BRIDGE | MCP Protocol Bridge | gerych | `in_progress` |
| T1_AGENT_REGISTRY | Agent Registry (hub_memory) | gerych | `todo` |

**Definition of Done**: `omni_router.py` приймає текстовий запит, класифікує intent і успішно dispatch-ить до `dnk_git_research`.

---

## P2 — Visual Shell Alpha

**Мета**: Єдиний UI — Максим бачить задачі, агентів, результати.

| ID | Задача | Агент | Статус |
|----|--------|-------|--------|
| T2_TASK_GRAPH | Task Graph Visualizer (D3.js) | antigravity | `in_progress` |
| T2_TG_HTML | dnk_task_graph.html | antigravity | `in_progress` |
| T2_TG_JSON | dnk_mvp_tasks.json | antigravity | `done` |
| T2_TG_PG_SYNC | PostgreSQL Sync Script | gerych | `todo` |
| T2_CANVAS_UI | Canvas UI (xyflow / React) | antigravity | `todo` |
| T2_TELEGRAM_BOT | Telegram Interface | gerych | `todo` |

**Пріоритет**: Спочатку `T2_TG_PG_SYNC` — щоб Gerych читав задачі з БД.

**Definition of Done**: Відкриття `dnk_task_graph.html` показує актуальний стан задач з live-даних PostgreSQL.

---

## P3 — Agent Fleet v1

**Мета**: 3 активних spoke-агенти зареєстровані в Agent Registry.

| ID | Задача | Агент | Статус |
|----|--------|-------|--------|
| T3_GIT_RESEARCH | dnk_git_research MCP | gerych | `done` |
| T3_SHOPIFY | dnk_shopify Liquid Compiler | gerych | `in_progress` |
| T3_YOUTUBE | dnk_youtube_analyst | gerych | `todo` |

**Definition of Done**: `omni_router.py` може dispatch-ити до кожного з 3-х агентів і повертати результат.

---

## P4 — Infrastructure (Parallel Track)

**Мета**: Стабільна інфраструктура для всіх фаз.

| ID | Задача | Статус |
|----|--------|--------|
| T4_DOCKER | Docker Compose (dnk_postgres + dnk_bridge) | `done` |
| T4_UV_WORKSPACE | uv Workspace (root pyproject.toml) | `done` |
| T4_MRH | MRH Standard (DNK-STD-0075) | `in_progress` |
| T4_PATH_GUARD | path_guard.py (no absolute paths) | `done` |

---

## Наступний крок (зараз)

1. Відкрити `planning/dnk_task_graph.html` у браузері — переконатись у коректності
2. Реалізувати `T2_TG_PG_SYNC` — sync JSON → PostgreSQL tasks
3. Завершити `T1_ROUTER_INTENT` — Intent Classifier для omni_router

---

## Залежності (Critical Path)

```
T1_HUB_MEMORY → T1_OMNI_ROUTER → T1_MCP_BRIDGE → T2_CANVAS_UI
T1_HUB_MEMORY → T1_AGENT_REGISTRY → T3_* (Fleet)
T2_TG_JSON → T2_TG_PG_SYNC → [Agent-readable task graph]
```

---

*DNK OS MVP Roadmap · Antigravity Architect · 2026-08-05*