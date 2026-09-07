<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260907-001040.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 20260906_170225_84c16b."
# canonical_source: true
# alters_files: ["AGENTS.md", "apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx", "apps/web/store/nodeTasksStore.ts", "docs/plans/my_task/task_20260906_remotion_010_voice_ai_video_exporter.md"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-07"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Read Loop Detected on: nodeTasksStore.ts

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `20260906_170225_84c16b` виявлено 10 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260907-001040`
- **Title**: `[Self-Heal] Read Loop Detected on: nodeTasksStore.ts`
- **Domain / Bounded Context**: `apps/web`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `20260906_170225_84c16b`
- **Recursion Depth**: `1`

---

## ⚡ Zero-Waste Execution Contract

| Параметр | Вимога | Призначення |
| :--- | :--- | :--- |
| **Max Tool Calls** | **≤ 15 tool calls** | Швидкий точковий патч без зайвої розвідки. |
| **Virtualenv SSOT** | `.venv/bin/python3` та `.venv/bin/pytest` | Жодних системних інтерпретаторів. |
| **Path Invariant** | **Тільки відносні шляхи (`./`, `../`)** | 0 абсолютних шляхів `/Users/...`. |
| **MRH Invariant** | Обов'язковий MRH заголовок | `DNK-STD-0075` комплаєнс. |
| **Quality Gate** | **100% Green Pytest Suite** | Регресійне тестування перед фіксацією. |

---

## 💡 1. Problem Statement & Raw Evidence

### ⚠️ 1. Read Loop Detected on: nodeTasksStore.ts (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/store/nodeTasksStore.ts was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/web/store/nodeTasksStore.ts (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/web/store/nodeTasksStore.ts`

### ⚠️ 2. Read Loop Detected on: NodeTaskMarketingVideoViewer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx`

### ⚠️ 3. Unverified File Modification Churn: nodeTasksStore.ts (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/store/nodeTasksStore.ts was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/store/nodeTasksStore.ts (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/store/nodeTasksStore.ts`

### ⚠️ 4. Unverified File Modification Churn: NodeTaskMarketingVideoViewer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx`

### ⚠️ 5. Tool Execution or Test Failure in [terminal] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
[terminal] ran `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` -> exit 2, 1 lines output
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 6. Tool Execution or Test Failure in [search_files] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
{"total_count": 21, "matches_format": "path-grouped: each file path on its own line, followed by indented '<line>: <content>' rows for matches in that file", "matches_text": "docker-compose.yml\n  51:   frontend:\n  52:     build:\n  53:       context: .\n  54:       dockerfile: Dockerfile.frontend\
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 7. Error Loop: Repeated 'CalledProcessError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'CalledProcessError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"success": true, "mode": "discover", "query": "Slice 3 Standalone Build", "detail": "adaptive", "results": [{"session_id": "20260904_233524_1ba8bb", "when": "September 04, 2026 at 11:35 PM", "source": "cli", "model": "gemini-3.8-flash", "title": "Ау
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='CalledProcessError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 8. Unverified File Modification Churn: task_20260906_remotion_010_voice_ai_video_exporter.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/plans/my_task/task_20260906_remotion_010_voice_ai_video_exporter.md was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: docs/plans/my_task/task_20260906_remotion_010_voice_ai_video_exporter.md (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `docs/plans/my_task/task_20260906_remotion_010_voice_ai_video_exporter.md`

### ⚠️ 9. MASE Tool Budget Breached (246 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 246 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 246
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 10. Missing AST Fast-Path: Repeated search_files instead of dnk_resolve_symbol (`TOOL_LOOP` - MEDIUM)
- **Опис**: Agent performed 122 search_files calls without utilizing dnk_resolve_symbol (<20ms pre-indexed AST cache).
- **Лог / Стек**: ```text
Total search_files calls: 122, dnk_resolve_symbol calls: 0
```
- **Пропоноване лікування**: Invoke dnk_resolve_symbol(symbol=...) for sub-20ms AST symbol resolution instead of scanning files on disk.
- **Цільові файли**: N/A

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/store/nodeTasksStore.ts` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/plans/my_task/task_20260906_remotion_010_voice_ai_video_exporter.md` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx, apps/web/store/nodeTasksStore.ts, docs/plans/my_task/task_20260906_remotion_010_voice_ai_video_exporter.md`
- **Команда перевірки**:
  ```bash
  .venv/bin/pytest tests/verification/test_*.py -v
  ```
- **Бюджет**: ≤ 12 tool calls.

### 🔹 Slice 2: Evidence & SCONES Memory Confirmation
- **Ціль**: Перевірити відсутність регресій та оновити базу уроків.
- **Команда перевірки**:
  ```bash
  python3 scripts/system/session_sentinel.py --audit-latest
  ```
- **Бюджет**: ≤ 5 tool calls.

---

## ✅ 4. Definition of Done (DoD)

- [ ] Всі виявлені аномалії усунуто в коді цільових файлів.
- [ ] 0 абсолютних шляхів у змінених файлах.
- [ ] Тести проходять на 100% Green.
- [ ] Звіт передано ментору Antigravity та зафіксовано в git.
