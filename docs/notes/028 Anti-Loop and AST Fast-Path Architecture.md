---
title: "Anti-Loop & AST Fast-Path Architecture (Sentinel Telemetry)"
tags:
  - architecture
  - anti-loop
  - sentinel
  - ast-fast-path
  - zero-waste
  - mase
date: 2026-09-06
status: Active
author: DNK-e.com Maksym & Gerych Prime
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/014_Anti_Loop_and_AST_Fast_Path_Architecture.md"
purpose: "Architectural documentation of AST Fast-Path, Anti-Search-Loop, Unverified Churn, and MASE Hard Budget Guards"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# ⚡ Anti-Loop & AST Fast-Path Architecture (Sentinel Telemetry)

## 📌 Context & Motivation
Під час аналізу аудиту виконання рою (`AUDIT_20260906_143924_78ecd0.md`) було виявлено серйозне вузьке місце:
- Воркер рою виконав **51 інструментальний виклик** (при ліміті MASE ≤ 25 на слайс).
- Витрачено 9 важких викликів `search_files` на пошук класів та інтерфейсів через повільне сканування файлів на диску замість використання pre-indexed AST-кешу.
- Здійснено 11 повторних викликів `read_file` та 16 викликів `patch` над одним і тим самим файлом (`apps/web/store/nodeTasksStore.ts`) без запуску тестів між правками (Unverified Mutation Churn).

## 🛡️ Реалізовані механізми захисту

### 1. AST Fast-Path Guard (`scripts/system/hermes_pre_tool_hook.py`)
- **Перехоплення regex-пошуку визначень**: коли агент викликає `search_files` із патерном на кшталт `class `, `def `, `interface `, `type `, `function `, пре-тул хук блокує виклик та скеровує на:
  `dnk_resolve_symbol(symbol="<name>")`
- **Швидкість**: `dnk_resolve_symbol` повертає точні файли, номери рядків, сигнатури та типи за **< 20 мс**, заощаджуючи десятки секунд та тисячі токенів контексту.

### 2. Anti-Search-Loop Guard
- Якщо агент виконує 4 послідовні виклики `search_files` без мутацій або верифікації, спрацьовує захисний контур, який примушує перейти до таргетної інспекції через AST або тестування.

### 3. Unverified Rewrite Churn Guard (Invariant 10)
- Забороняє багаторазове (≥ 3 разів) сліпе переписування одного й того самого файлу без прогону тестів (`pytest`, `verify_all.sh`, `npm test`).
- Скидається лише тоді, коли агент дійсно запускає команду тестування.

### 4. MASE Hard Budget Guard (Invariant 2)
- При досягненні 30 викликів інструментів на слайс усі дослідницькі та мутаційні операції зупиняються.
- Дозволено виключно команди верифікації (`pytest`, `verify_all.sh`, `git commit`).

### 5. Sentinel Anomaly Detection (`core/orchestrator/session_sentinel.py`)
- Виявляє аномалію `TOOL_LOOP`:
  - `Missing AST Fast-Path`: якщо `search_files` викликано ≥ 3 разів без жодного виклику `dnk_resolve_symbol`.
  - `Unverified File Modification Churn`: якщо файл змінювався ≥ 3 разів без верифікації.
  - `Read Loop`: якщо файл читався ≥ 3 разів поспіль без змін.

## 🔗 Пов'язані компоненти
- [[Task Spec v2.5 Specification]]
- [[Zero-Touch Inception Gateway]]
- [[Session Sentinel Telemetry]]
- [[Task Forest Architecture]]
