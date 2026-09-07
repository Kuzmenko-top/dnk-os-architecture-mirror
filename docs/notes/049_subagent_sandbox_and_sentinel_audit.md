---
title: "049 Subagent Sandbox Isolation and Sentinel Trajectory Audit"
created_at: "2026-09-07"
updated_at: "2026-09-07"
tags: ["#architecture", "#swarm", "#subagents", "#sentinel", "#sandbox", "#handshake"]
aliases: ["Subagent Sandbox Isolation", "Sentinel Trajectory Audit"]
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/049_subagent_sandbox_and_sentinel_audit.md"
purpose: "Documentation of Subagent Sandbox Isolation, zero-loss artifact handshake, and Sentinel multi-session trajectory audit."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-07"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🛡️ 049 Subagent Sandbox Isolation and Sentinel Trajectory Audit

## 📌 Executive Summary
Впроваджено ізольований пісочничний шар виконання для субагентів рою DNK OS — **Subagent Sandbox Isolation** (`core/orchestrator/subagent_sandbox.py`) та протокол безвтратного обміну артефактами (**Zero-Loss Artifact Handshake**). Одночасно проведено комплексний аудит та реконсиляцію сесій за допомогою **[[Session Sentinel v2.0]]**, усунено дев'яносто шість залишкових осиротілих сесій та розгорнуто плани самовідновлення для марафонських сесій.

---

## 🏗️ 1. Subagent Sandbox Architecture (`core/orchestrator/subagent_sandbox.py`)

### 1.1. Ізоляція середовища та контракти
Для кожного субагента, запущеного в режимі `autonomous_subagent`, створюється ізольований контекст змінних середовища та файлові артефакти вхідних/вихідних даних:
- **`DNK_SWARM_WORKER` = `1`**: ідентифікатор запуску в ролі підлеглого процесу.
- **`DNK_INPUT_ARTIFACT`**: шлях до `data/swarm_artifacts/<task_id>_input.json`.
- **`DNK_OUTPUT_ARTIFACT`**: шлях до `data/swarm_artifacts/<task_id>_output.json`.
- **`DNK_AGENT_ID` & `DNK_TASK_ID`**: точні координати в просторі рою.

### 1.2. Zero-Loss Artifact Handshake
1. Оркестратор серіалізує цільові файли (`target_files`), таймаут та параметри завдання у вхідний JSON-артефакт.
2. Субагент через `get_subagent_context()` десеріалізує структурований контекст без ризику втрати аргументів командного рядка.
3. По завершенні субагент викликає `emit_subagent_output()`, що гарантує збереження звіту, модифікованих файлів та статусу.
4. Оркестратор через `harvest_subagent_output()` безпечно збирає результати та синхронізує стан у DAG Canvas.

---

## 🔍 2. Sentinel Multi-Session Trajectory Audit

Проведено поглиблений аналіз траєкторій інтерактивних сесій у локальній базі `state.db`:
- **Сесія `20260906_201203_fab5b6` ("Огляд репозиторію Graphify-Labs/graphify")**:
  - 3,877 повідомлень, 1,864 виклики інструментів.
  - Виявлено 56 аномалій (повторні читання без змін, порушення бюджету MASE).
  - Створено план самовідновлення `TASK-DNK-SELFHEAL-20260907-001025.md` та зареєстровано вузол у Canvas Graph.
- **Сесія `20260906_172052_5dcd93` ("DNK OS Agent Swarm dashboard")**:
  - Виявлено авторизаційну аномалію, автоматично згенеровано та передано задачу `dnk_dev_fullstack`.
- **Сесія `bg_181029_83211a` ("Перехід до фази 3")**:
  - Автоматично передано на аудит `gerych_auditor`.
- **Реконсиляція осиротілих процесів**:
  - `session_sentinel.py --reconcile-orphaned` успішно проаналізував та фіналізував 96 завислих/осиротілих сесій без втрати даних.

---

## 🧪 3. Quality & Verification Gates
- `tests/verification/test_subagent_sandbox.py`: **2/2 PASSED**
- `tests/verification/test_subagent_sandbox_handshake.py`: **3/3 PASSED**
- `bash scripts/verify_all.sh --affected`: **100% Green (16/16 blast-radius tests)**
- TypeScript Type-Check: **Clean (0 errors)**
- Git Hygiene Guard: **No untracked files, zero drift**
