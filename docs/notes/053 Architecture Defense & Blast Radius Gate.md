---
title: "053 Architecture Defense & Blast Radius Gate"
date: "2026-09-06"
tags:
  - architecture
  - quality-gate
  - blast-radius
  - import-cycles
  - graphify
  - ci-cd
aliases:
  - "015 Architecture Defense & Blast Radius Gate"
status: "active"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/053 Architecture Defense & Blast Radius Gate.md"
purpose: "ADR and architecture documentation for Graphify-driven architectural refactoring, import cycle breaking, God Component decomposition, and deterministic blast radius CI gate"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

E3 Architecture Defense & Blast Radius Gate

## 1. Контекст та Передумови
Під час глибокого аналізу репозиторію інструментом **Graphify** було виявлено чотири критичні вузькі місця архітектурного графа:
1. **Layer Leakage (Витік шарів)**: Прямий імпорт внутрішніх помилок та хелпера `err()` з `visual_shell` у `apps/web` порушував ізоляцію Two-Tier Clean Architecture.
2. **Circular Dependencies (Циклічні імпорти)**:
   - У `visual_shell/.../providers/` (`openai-compatible.ts` ↔ `anthropic.ts`, `api-proxy.ts` ↔ `anthropic.ts`, `utils/apiProtocol.ts` ↔ `providers`).
   - У `visual_shell/.../updater/` (`updater.ts` ↔ `payload.ts` / `scheduler.ts`).
3. **God Component**: `ProjectView.tsx` (12 148 LOC, >31 залежність), який акумулював бізнес-логіку сплітів, нормалізацію повідомлень, буферизацію стрімінгу та аналіз артефактів.
4. **Відсутність детермінованого захисту в CI**: Відсутність швидкого аналізу зачепленої поверхні (blast radius) та автоматичної зупинки регресій циклічності перед комітом.

---

## 2. Реалізоване Архітектурне Рішення

### 2.1. Ізоляція шарів (Layer Isolation)
- Створено чистий шар інтерфейсів `apps/web/types/apiProtocol.ts` (дзеркальний чистий контракт без залежності від `visual_shell`).
- Усунено пряму зв'язність між `apps/web` та внутрішніми реалізаціями `visual_shell`.
- Закріплено регресійним тестом `tests/test_web_layer_isolation.py`.

### 2.2. Розрив циклічних залежностей (Cycle Defense)
- Виділено чисті типи конфігурації провайдерів у `visual_shell/.../providers/types.ts`.
- Створено `visual_shell/.../updater/types.ts` для розриву зв'язку між `updater.ts`, `payload.ts` та `scheduler.ts`.
- Впроваджено DFS/Tarjan алгоритм детекції циклів імпорту в `scripts/system/architecture_and_cycle_guard.py` та `tests/test_import_cycles.py`.

### 2.3. Декомпозиція God Component `ProjectView`
Створено модульний пакет `visual_shell/open_design/apps/web/src/components/project-view/`:
- `layoutUtils.ts` — розрахунки панелей, сплітів, зберігання у `localStorage`.
- `conversationUtils.ts` — нормалізація повідомлень, життєвий цикл ранів, буферизація стрімінгу (`createBufferedTextUpdates`).
- `artifactRecoveryUtils.ts` — виявлення зачеплених файлів, відновлення артефактів.
- `index.ts` — єдиний публічний фасад.
- Клієнтські хуки (`useConversationChat.ts`) та Vitest тести переведені на ізольований пакет.
- Закріплено `tests/test_project_view_decomposition.py`.

### 2.4. Детермінований Blast Radius Analyzer (`blast_radius_analyzer.py`)
- Визначає зачеплені домени за зміненими файлами (`git diff` / `git status`).
- Розраховує оцінку ризику (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- Динамічно формує мінімальний необхідний набір таргетних тестів (Pytest та Vitest) для миттєвої валідації без потреби щоразу виконувати 30-хвилинний монолітний тест-ран.
- Підтримує CLI режими `--json`, `--staged`, `--all`.

### 2.5. Вбудований захист у Pre-commit та CI Gate
- `scripts/system/architecture_and_cycle_guard.py` додано як обов'язковий крок перевірки (0.05с).
- `scripts/system/auto_precommit_guard.py` тепер включає:
  - Check 3.2: Architecture Isolation & Import Cycles Guard.
  - Check 3.3: Deterministic Blast Radius Assessment.
- `scripts/verify_all.sh` отримав кроки:
  - `[2.6/4] Verifying Architecture Isolation & Import Cycles`
  - `[2.7/4] Calculating Blast Radius & Affected Surface`
  - Автоматичне виявлення верхньорівневих `tests/test_*.py` у кроці `[3/4]`.

---

## 3. Зв'язки з іншими артефактами (Graphify Links)
- [[026 Graphify Assimilation & Test Report]] — первинний звіт про дефекти та рекомендації.
- [[DNK_HUB_Core_Architecture.canvas]] — оновлений інтерактивний Canvas архітектури системи.
- `tests/test_architecture_guard_and_blast_radius.py` — тести надійності blast radius та циклічного захисту.
