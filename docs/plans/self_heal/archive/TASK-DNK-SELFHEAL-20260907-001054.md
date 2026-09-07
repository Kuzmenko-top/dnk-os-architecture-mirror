<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260907-001054.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 20260906_201203_fab5b6."
# canonical_source: true
# alters_files: ["AGENTS.md", "apps/api/routers/canvas_v3_ws.py", "apps/api/routers/node_tasks_router.py", "apps/api/services/self_healing_distiller.py", "apps/web/app/tasks/page.tsx", "apps/web/components/stitch/StitchBiAnalystDrawer.tsx", "apps/web/components/stitch/StitchShopifyPreviewDrawer.tsx", "apps/web/components/stitch/StitchSmartInspector.tsx", "apps/web/components/stitch/index.ts", "apps/web/components/workspace/DNKStudioWorkspace.tsx", "apps/web/components/workspace/WorkspaceShell.tsx", "core/hermes_agent/tools/dnk_swarm_tool.py", "core/obsidian/export_canvas.py", "core/occ_merge.py", "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md", "core/orchestrator/swarm_coordinator.py", "core/orchestrator/swarm_health.py", "docs/notes/014 Graphify Assimilation & Test Report.md", "docs/notes/060 System Architecture & Agent Bottlenecks Audit.md", "docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md", "docs/notes/tasks_and_ideas/gate-canvas-qa.md", "docs/notes/tasks_and_ideas/task-distiller-patch.md", "docs/notes/tasks_and_ideas/task-node-system.md", "docs/notes/tasks_and_ideas/task-occ-merge.md", "scripts/system/blast_radius_analyzer.py", "scripts/system/gerych.sh", "scripts/system/gerych_swarm.sh", "scripts/system/repo_map.py", "tests/core/test_occ_merge.py", "tests/verification/test_canvas_bridge_router.py", "tests/verification/test_swarm_autonomous_subagent_bridge.py", "visual_shell/open_design/apps/web/src/components/ProjectView.tsx", "visual_shell/open_design/apps/web/src/components/project-view/conversationUtils.ts", "visual_shell/open_design/apps/web/src/components/project-view/layoutUtils.ts", "visual_shell/open_design/apps/web/src/components/stitch/StitchBiAnalystDrawer.tsx", "visual_shell/open_design/apps/web/src/components/stitch/StitchShopifyPreviewDrawer.tsx", "visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx", "visual_shell/open_design/apps/web/src/components/stitch/StitchSwarmCommandCenter.tsx", "visual_shell/open_design/apps/web/src/components/stitch/StitchTaskForestDrawer.tsx"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-07"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Error Loop: Repeated 'ValueError' Without Distillation

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `20260906_201203_fab5b6` виявлено 56 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260907-001054`
- **Title**: `[Self-Heal] Error Loop: Repeated 'ValueError' Without Distillation`
- **Domain / Bounded Context**: `apps/api`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `20260906_201203_fab5b6`
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

### ⚠️ 1. Error Loop: Repeated 'ValueError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'ValueError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"content": "1|# --- DNK-MRH-HEADER ---\n2|# mrh_id: \"core/obsidian/export_canvas.py\"\n3|# purpose: \"Export Canvas nodes and edges into Markdown files and Obsidian .canvas format with canonical Vault path validation and deterministic revision/cont
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='ValueError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 2. Read Loop Detected on: repo_map.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/repo_map.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: scripts/system/repo_map.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `scripts/system/repo_map.py`

### ⚠️ 3. Read Loop Detected on: export_canvas.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/obsidian/export_canvas.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/obsidian/export_canvas.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/obsidian/export_canvas.py`

### ⚠️ 4. Error Loop: Repeated 'HTTPException' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'HTTPException' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"content": "1|# --- DNK-MRH-HEADER ---\n2|# mrh_id: \"apps/api/routers/canvas_bridge.py\"\n3|# purpose: \"FastAPI REST endpoints for bidirectional Obsidian Canvas ↔ React Flow SSOT synchronization.\"\n4|# canonical_source: true\n5|# alters_files: []
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='HTTPException') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 5. Absolute Path Invariant Violation (/Users/...) (`PATH_VIOLATION` - HIGH)
- **Опис**: Agent passed an absolute system path in tool arguments instead of mandatory relative path.
- **Лог / Стек**: ```text
{"command": "head -n 2 $HOME/.local/bin/graphify"}
```
- **Пропоноване лікування**: Enforce relative path sanitization (./ or ../) before dispatching tool calls.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 6. Tool Execution or Test Failure in [terminal] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
[terminal] ran `graphify extract . --code-only` -> exit 124, 1 lines output
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 7. Unverified File Modification Churn: 014 Graphify Assimilation & Test Report.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/014 Graphify Assimilation & Test Report.md was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: docs/notes/014 Graphify Assimilation & Test Report.md (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `docs/notes/014 Graphify Assimilation & Test Report.md`

### ⚠️ 8. Error Loop: Repeated 'ApiError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'ApiError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"total_count": 2, "matches": [{"path": "visual_shell/open_design/apps/daemon/src/http/types.ts", "line": 5, "content": "  | { ok: false; error: E };"}, {"path": "visual_shell/open_design/apps/daemon/src/http/types.ts", "line": 8, "content": "export
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='ApiError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 9. Error Loop: Repeated 'setError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'setError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"content": "90|  const [loading, setLoading] = useState<boolean>(true);\n91|  const [error, setError] = useState<string | null>(null);\n92|\n93|  const fetchConfigs = useCallback(async () => {\n94|    try {\n95|      setLoading(true);\n96|      cons
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='setError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 10. Error Loop: Repeated 'onError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'onError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"success": true, "diff": "--- a/$HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/visual_shell/open_design/apps/web/src/providers/anthropic.ts\n+++ b/$HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/visual_shell/open_design/apps/web/src/providers/a
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='onError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 11. Error Loop: Repeated 'reconcileConversationRecoveryGlobalError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'reconcileConversationRecoveryGlobalError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "Total lines: 12148\n382: export function mergeSavedPreviewComment(current: PreviewComment[], saved: PreviewComment): PreviewComment[] {\n388: function wait(ms: number): Promise<void> {\n426: function mergeServerMessageWithLocal(server: Ch
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='reconcileConversationRecoveryGlobalError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 12. Read Loop Detected on: ProjectView.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/ProjectView.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/ProjectView.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/ProjectView.tsx`

### ⚠️ 13. Error Loop: Repeated 'lastError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'lastError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "};\n\nexport function mergeSavedPreviewComment(current: PreviewComment[], saved: PreviewComment): PreviewComment[] {\n  const existingIndex = current.findIndex((comment) => comment.id === saved.id);\n  if (existingIndex < 0) return [...cu
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='lastError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 14. Unverified File Modification Churn: layoutUtils.ts (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/project-view/layoutUtils.ts was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/project-view/layoutUtils.ts (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/project-view/layoutUtils.ts`

### ⚠️ 15. Unverified File Modification Churn: conversationUtils.ts (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/project-view/conversationUtils.ts was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/project-view/conversationUtils.ts (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/project-view/conversationUtils.ts`

### ⚠️ 16. Error Loop: Repeated 'nError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'nError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "RUN  v4.1.6 $HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/visual_shell/open_design/apps/web\n\n ❯ tests/components/ProjectView.shared-non-owner-chat-default.test.ts (0 test)\n ❯ tests/components/ProjectView.questionFormKey.test.ts (0
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='nError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 17. Error Loop: Repeated 'nAssertionError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'nAssertionError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "RUN  v4.1.6 $HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/visual_shell/open_design/apps/web\n\n ❯ tests/components/ProjectView.questionFormKey.test.ts (6 tests | 1 failed) 16ms\n     × restores a user turn that was persisted after its
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='nAssertionError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 18. Error Loop: Repeated 'CalledProcessError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'CalledProcessError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"content": "75|                results[\"fast_syntax_check\"] = True\n76|        except subprocess.CalledProcessError as exc:\n77|            results[\"fast_syntax_check\"] = False\n78|            errors.append(f\"Fast Syntax Check failed: {exc.stde
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='CalledProcessError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 19. Unverified File Modification Churn: blast_radius_analyzer.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/blast_radius_analyzer.py was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: scripts/system/blast_radius_analyzer.py (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `scripts/system/blast_radius_analyzer.py`

### ⚠️ 20. Error Loop: Repeated 'nImportError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'nImportError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "⚡ [TARGETED MODE] --affected flag enabled: running focused tests based on blast radius.\n🔍 [1/4] Running Preflight Sanitizer...\n========================================================\n🧹 DNK OS Process Hygiene & Resource Watchdog\n=====
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='nImportError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 21. Read Loop Detected on: swarm_health.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/swarm_health.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/orchestrator/swarm_health.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/orchestrator/swarm_health.py`

### ⚠️ 22. Read Loop Detected on: StitchSwarmCommandCenter.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/stitch/StitchSwarmCommandCenter.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/stitch/StitchSwarmCommandCenter.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/stitch/StitchSwarmCommandCenter.tsx`

### ⚠️ 23. Read Loop Detected on: WorkspaceShell.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/workspace/WorkspaceShell.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/web/components/workspace/WorkspaceShell.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/web/components/workspace/WorkspaceShell.tsx`

### ⚠️ 24. Unverified File Modification Churn: WorkspaceShell.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/workspace/WorkspaceShell.tsx was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/workspace/WorkspaceShell.tsx (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/workspace/WorkspaceShell.tsx`

### ⚠️ 25. Read Loop Detected on: StitchSmartInspector.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx`

### ⚠️ 26. Read Loop Detected on: StitchShopifyPreviewDrawer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/stitch/StitchShopifyPreviewDrawer.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/stitch/StitchShopifyPreviewDrawer.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/stitch/StitchShopifyPreviewDrawer.tsx`

### ⚠️ 27. Read Loop Detected on: StitchBiAnalystDrawer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/stitch/StitchBiAnalystDrawer.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/stitch/StitchBiAnalystDrawer.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/stitch/StitchBiAnalystDrawer.tsx`

### ⚠️ 28. Read Loop Detected on: StitchTaskForestDrawer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File visual_shell/open_design/apps/web/src/components/stitch/StitchTaskForestDrawer.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: visual_shell/open_design/apps/web/src/components/stitch/StitchTaskForestDrawer.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `visual_shell/open_design/apps/web/src/components/stitch/StitchTaskForestDrawer.tsx`

### ⚠️ 29. Unverified File Modification Churn: StitchSmartInspector.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/stitch/StitchSmartInspector.tsx was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/stitch/StitchSmartInspector.tsx (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/stitch/StitchSmartInspector.tsx`

### ⚠️ 30. Unverified File Modification Churn: StitchShopifyPreviewDrawer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/stitch/StitchShopifyPreviewDrawer.tsx was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/stitch/StitchShopifyPreviewDrawer.tsx (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/stitch/StitchShopifyPreviewDrawer.tsx`

### ⚠️ 31. Unverified File Modification Churn: StitchBiAnalystDrawer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/stitch/StitchBiAnalystDrawer.tsx was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/stitch/StitchBiAnalystDrawer.tsx (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/stitch/StitchBiAnalystDrawer.tsx`

### ⚠️ 32. Unverified File Modification Churn: index.ts (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/stitch/index.ts was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/stitch/index.ts (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/stitch/index.ts`

### ⚠️ 33. Read Loop Detected on: 000_DNK_TASK_AND_IDEAS_INDEX.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md`

### ⚠️ 34. Read Loop Detected on: 060 System Architecture & Agent Bottlenecks Audit.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/060 System Architecture & Agent Bottlenecks Audit.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/notes/060 System Architecture & Agent Bottlenecks Audit.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/notes/060 System Architecture & Agent Bottlenecks Audit.md`

### ⚠️ 35. Read Loop Detected on: occ_merge.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/occ_merge.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/occ_merge.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/occ_merge.py`

### ⚠️ 36. Read Loop Detected on: task-occ-merge.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/tasks_and_ideas/task-occ-merge.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/notes/tasks_and_ideas/task-occ-merge.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/notes/tasks_and_ideas/task-occ-merge.md`

### ⚠️ 37. Read Loop Detected on: test_canvas_bridge_router.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File tests/verification/test_canvas_bridge_router.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: tests/verification/test_canvas_bridge_router.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `tests/verification/test_canvas_bridge_router.py`

### ⚠️ 38. Read Loop Detected on: task-node-system.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/tasks_and_ideas/task-node-system.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/notes/tasks_and_ideas/task-node-system.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/notes/tasks_and_ideas/task-node-system.md`

### ⚠️ 39. Read Loop Detected on: node_tasks_router.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/api/routers/node_tasks_router.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/api/routers/node_tasks_router.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/api/routers/node_tasks_router.py`

### ⚠️ 40. Read Loop Detected on: test_occ_merge.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File tests/core/test_occ_merge.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: tests/core/test_occ_merge.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `tests/core/test_occ_merge.py`

### ⚠️ 41. Read Loop Detected on: page.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/app/tasks/page.tsx was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/web/app/tasks/page.tsx (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/web/app/tasks/page.tsx`

### ⚠️ 42. Read Loop Detected on: gate-canvas-qa.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/tasks_and_ideas/gate-canvas-qa.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/notes/tasks_and_ideas/gate-canvas-qa.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/notes/tasks_and_ideas/gate-canvas-qa.md`

### ⚠️ 43. Read Loop Detected on: task-distiller-patch.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/notes/tasks_and_ideas/task-distiller-patch.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/notes/tasks_and_ideas/task-distiller-patch.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/notes/tasks_and_ideas/task-distiller-patch.md`

### ⚠️ 44. Read Loop Detected on: self_healing_distiller.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/api/services/self_healing_distiller.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/api/services/self_healing_distiller.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/api/services/self_healing_distiller.py`

### ⚠️ 45. Error Loop: Repeated 'JSONDecodeError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'JSONDecodeError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"total_count": 18, "matches_format": "path-grouped: each file path on its own line, followed by indented '<line>: <content>' rows for matches in that file", "matches_text": "./config/audit_exclusions.yaml\n  70:     - \"visual_shell_db.json\"\n./doc
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='JSONDecodeError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 46. Read Loop Detected on: canvas_v3_ws.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/api/routers/canvas_v3_ws.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/api/routers/canvas_v3_ws.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/api/routers/canvas_v3_ws.py`

### ⚠️ 47. Unverified File Modification Churn: DNKStudioWorkspace.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/workspace/DNKStudioWorkspace.tsx was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: apps/web/components/workspace/DNKStudioWorkspace.tsx (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `apps/web/components/workspace/DNKStudioWorkspace.tsx`

### ⚠️ 48. Error Loop: Repeated 'RuntimeError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'RuntimeError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"success": true, "diff": "--- a/$HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md\n+++ b/$HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_I
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='RuntimeError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 49. Read Loop Detected on: swarm_coordinator.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/swarm_coordinator.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/orchestrator/swarm_coordinator.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/orchestrator/swarm_coordinator.py`

### ⚠️ 50. Read Loop Detected on: gerych_swarm.sh (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/gerych_swarm.sh was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: scripts/system/gerych_swarm.sh (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `scripts/system/gerych_swarm.sh`

### ⚠️ 51. Tool Execution or Test Failure in [read_file] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
{"content": "240|print(code)\n241|\"\n242|    exit 0\n243|fi\n244|\n245|# Adversarial Review Debate Mode\n246|if [ \"$RUN_ADVERSARIAL\" -eq 1 ]; then\n247|    echo \"⚔️  Launching Adversarial AI Review Debate (Auditor ⚔️  Builder)...\"\n248|    ./.venv/bin/python3 -c \"\n249|import sys\n250|from cor
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 52. Read Loop Detected on: test_swarm_autonomous_subagent_bridge.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File tests/verification/test_swarm_autonomous_subagent_bridge.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: tests/verification/test_swarm_autonomous_subagent_bridge.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `tests/verification/test_swarm_autonomous_subagent_bridge.py`

### ⚠️ 53. Read Loop Detected on: gerych.sh (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/gerych.sh was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: scripts/system/gerych.sh (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `scripts/system/gerych.sh`

### ⚠️ 54. Read Loop Detected on: solo_agent_syndrome_cure_and_subagent_spawning_protocol.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md`

### ⚠️ 55. Read Loop Detected on: dnk_swarm_tool.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/hermes_agent/tools/dnk_swarm_tool.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/hermes_agent/tools/dnk_swarm_tool.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/hermes_agent/tools/dnk_swarm_tool.py`

### ⚠️ 56. MASE Tool Budget Breached (1939 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 1939 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 1939
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/api/routers/canvas_v3_ws.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/api/routers/node_tasks_router.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/api/services/self_healing_distiller.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/app/tasks/page.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/stitch/StitchBiAnalystDrawer.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/stitch/StitchShopifyPreviewDrawer.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/stitch/StitchSmartInspector.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/stitch/index.ts` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/workspace/DNKStudioWorkspace.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/workspace/WorkspaceShell.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/hermes_agent/tools/dnk_swarm_tool.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/obsidian/export_canvas.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/occ_merge.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/swarm_coordinator.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/swarm_health.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/014 Graphify Assimilation & Test Report.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/060 System Architecture & Agent Bottlenecks Audit.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/tasks_and_ideas/gate-canvas-qa.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/tasks_and_ideas/task-distiller-patch.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/tasks_and_ideas/task-node-system.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/notes/tasks_and_ideas/task-occ-merge.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `scripts/system/blast_radius_analyzer.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `scripts/system/gerych.sh` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `scripts/system/gerych_swarm.sh` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `scripts/system/repo_map.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `tests/core/test_occ_merge.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `tests/verification/test_canvas_bridge_router.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `tests/verification/test_swarm_autonomous_subagent_bridge.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/ProjectView.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/project-view/conversationUtils.ts` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/project-view/layoutUtils.ts` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/stitch/StitchBiAnalystDrawer.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/stitch/StitchShopifyPreviewDrawer.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/stitch/StitchSwarmCommandCenter.tsx` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `visual_shell/open_design/apps/web/src/components/stitch/StitchTaskForestDrawer.tsx` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, apps/api/routers/canvas_v3_ws.py, apps/api/routers/node_tasks_router.py, apps/api/services/self_healing_distiller.py, apps/web/app/tasks/page.tsx, apps/web/components/stitch/StitchBiAnalystDrawer.tsx, apps/web/components/stitch/StitchShopifyPreviewDrawer.tsx, apps/web/components/stitch/StitchSmartInspector.tsx, apps/web/components/stitch/index.ts, apps/web/components/workspace/DNKStudioWorkspace.tsx, apps/web/components/workspace/WorkspaceShell.tsx, core/hermes_agent/tools/dnk_swarm_tool.py, core/obsidian/export_canvas.py, core/occ_merge.py, core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md, core/orchestrator/swarm_coordinator.py, core/orchestrator/swarm_health.py, docs/notes/014 Graphify Assimilation & Test Report.md, docs/notes/060 System Architecture & Agent Bottlenecks Audit.md, docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md, docs/notes/tasks_and_ideas/gate-canvas-qa.md, docs/notes/tasks_and_ideas/task-distiller-patch.md, docs/notes/tasks_and_ideas/task-node-system.md, docs/notes/tasks_and_ideas/task-occ-merge.md, scripts/system/blast_radius_analyzer.py, scripts/system/gerych.sh, scripts/system/gerych_swarm.sh, scripts/system/repo_map.py, tests/core/test_occ_merge.py, tests/verification/test_canvas_bridge_router.py, tests/verification/test_swarm_autonomous_subagent_bridge.py, visual_shell/open_design/apps/web/src/components/ProjectView.tsx, visual_shell/open_design/apps/web/src/components/project-view/conversationUtils.ts, visual_shell/open_design/apps/web/src/components/project-view/layoutUtils.ts, visual_shell/open_design/apps/web/src/components/stitch/StitchBiAnalystDrawer.tsx, visual_shell/open_design/apps/web/src/components/stitch/StitchShopifyPreviewDrawer.tsx, visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx, visual_shell/open_design/apps/web/src/components/stitch/StitchSwarmCommandCenter.tsx, visual_shell/open_design/apps/web/src/components/stitch/StitchTaskForestDrawer.tsx`
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
