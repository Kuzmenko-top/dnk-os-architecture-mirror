---
title: "048 Closed-Loop Self-Healing & Interactive Canvas Bridge Architecture"
type: "architecture_specification"
created_at: "2026-09-06"
updated_at: "2026-09-06"
status: "active"
tags:
  - architecture
  - self-healing
  - obsidian-canvas
  - react-flow
  - swarm-orchestration
  - sentinel
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/048_closed_loop_self_healing_and_interactive_canvas_bridge.md"
purpose: "Comprehensive Architecture Guide for Closed-Loop Self-Healing, Live Canvas Post-Tool Hooks, and Bidirectional Obsidian-ReactFlow Bridge"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 048 Closed-Loop Self-Healing & Interactive Canvas Bridge Architecture

## 📌 Executive Summary

Цей документ фіксує промислову архітектуру **трьох інтегрованих контурів автоматизації DNK OS**, реалізованих у вересні 2026 року:
1. **Live Zero-Code Obsidian Canvas Dashboard**: фонова реактивність через `scripts/system/hermes_post_tool_hook.py`, яка оновлює прогрес виконання задач у реальному часі без опитування (zero polling overhead).
2. **Sentinel Closed-Loop Self-Healing**: замкнений цикл діагностики аномалій, інтелектуального роутингу агентів (`gerych_auditor`, `dnk_dev_fullstack`), автоматичного пошуку та ін'єкції дистильованих рішень зі **SCONES** (`docs/scones/error_distillations.json`).
3. **SSOT Bidirectional Bridge (Obsidian Canvas ↔ React Flow)**: математично точна трансляція просторових координат, розмірів карток та реляційних зв'язків між десктопним Obsidian Canvas та веб-інтерфейсом DNK OS.

Споріднені вузли: [[000 DNK HUB Index]], [[017_Swarm_TaskDNA_Control_Panel.canvas]], [[046_docs_notes_vault_system_audit_and_strategic_evolution]], [[047_taskade_ecosystem_sota_audit_and_dnk_os_architecture]].

---

## 🏗️ 1. Системна архітектура трьох контурів

```
                          ┌────────────────────────┐
                          │   Gerych Prime Tool    │
                          │      Execution         │
                          └───────────┬────────────┘
                                      │
                         (Tool Result Emitted)
                                      ▼
                    ┌──────────────────────────────────┐
                    │  hermes_post_tool_hook.py        │
                    │  (Intercepts status, path, diff) │
                    └───────┬──────────────────┬───────┘
                            │                  │
           [Live Canvas HUD]│                  │[Telemetry & Anomalies]
                            ▼                  ▼
              ┌─────────────────────┐  ┌─────────────────────────┐
              │ visual_canvas_      │  │ session_sentinel.py     │
              │ control.py          │  │ (Anomaly Detector)      │
              │ (record_live_tool)  │  └───────────┬─────────────┘
              └──────────┬──────────┘              │
                         │             [Anomaly Detected & Classifed]
                         │                         │
                         │                         ▼
                         │             ┌─────────────────────────┐
                         │             │ SCONES Knowledge Recall │
                         │             │ (Find Distilled Remedy) │
                         │             └───────────┬─────────────┘
                         │                         │
                         │                         ▼
                         │             ┌─────────────────────────┐
                         │             │ Swarm Worker Dispatch   │
                         │             │ (auditor / fullstack)   │
                         │             └───────────┬─────────────┘
                         │                         │
                         │    (Self-Healing Plan)  │
                         └──────────────┬──────────┘
                                        ▼
             ┌───────────────────────────────────────────────────┐
             │   Master Obsidian Canvas (017 Swarm Dashboard)    │
             │   - Blue: Active Modification (in_progress)       │
             │   - Green: Verification Passed (done)             │
             │   - Red: Error / Remediation Required             │
             │   - Interactive Triggers: - [x] Run Tests         │
             └──────────────────────────┬────────────────────────┘
                                        │
                         (SSOT Bidirectional Sync)
                                        ▼
             ┌───────────────────────────────────────────────────┐
             │       Web React Flow Visual Graph Canvas          │
             │   (apps/web React Flow JSON ↔ Obsidian Canvas)    │
             └───────────────────────────────────────────────────┘
```

---

## ⚡ 2. Live Zero-Code Canvas Sync через Post-Tool Hook

### 2.1. Принцип роботи без опитування (Zero-Polling)
Замість запуску важких циклічних демонів, які сканують файлову систему, кожен виклик інструменту агентом перехоплюється середовищем виконання у файлі `scripts/system/hermes_post_tool_hook.py`.

* **Аналіз модифікацій файлів**:
  Коли інструмент `write_file` або `patch` змінює файл у поточному слайсі задачі, хук викликає `record_live_tool_execution(tool_name, tool_args, tool_result)`.
* **Автоматична зміна кольору вузла**:
  * Нода задачі переходить у стан `in_progress` із кольором `5` (Небесно-блакитний).
  * Лічильник викликів інструментів у заголовку картки оновлюється: `🔧 Tools: N/25 (MASE Bound)`.
* **Реакція на верифікацію**:
  * Якщо викликано `terminal` із командою `pytest` і отримано `exit_code: 0`, колір картки стає `4` (Зелений `done`), а індикатор змінюється на `🟢 100% Green`.
  * Якщо `exit_code != 0`, колір миттєво стає `1` (Червоний `failure`), фіксуючи помилку на полотні.

---

## 🛡️ 3. Sentinel Closed-Loop Self-Healing Protocol

### 3.1. Інтелектуальна матриця роутингу аномалій

| Категорія аномалії | Ознаки помилки | Призначений ройовий агент | Стратегія самозцілення |
|---|---|---|---|
| `TEST_FAILURE` | Падіння тестів, assert mismatch, tracebacks | `gerych_auditor` | Запуск виправлення у пісочниці, перевірка лінтера, повторна верифікація |
| `SYNTAX_ERROR` / `IMPORT_ERROR` | SyntaxError, ImportError, ModuleNotFoundError | `dnk_dev_fullstack` | Аналіз AST-дерева, перевірка маніфесту залежностей `pyproject.toml`, виправлення імпортів |
| `AUTH_ERROR` | 401 Unauthorized, 403 Forbidden, token expired | `gerych_auditor` | Перевірка системних змінних середовища `$GH_TOKEN`, оновлення конфігурації безпеки |
| `FALSE_COMPLIANCE` | Заява про виконання без артефактів/файлів | `gerych_auditor` | Блокування комміту, примусове створення валідних файлів і тестів |
| `READ_LOOP` | 3+ читань незміненого файлу підряд | `gerych_auditor` | Активація Circuit-Breaker, скидання контексту |

### 3.2. Автоматична ін'єкція рішень SCONES
Перед тим, як створити нову задачу самозцілення, `SessionSentinel` виконує семантичний запит до бази `docs/scones/error_distillations.json`:
1. Якщо знайдено точний патерн помилки (наприклад, `fastapi_testclient_thread_safety` або `sqlite_busy_timeout`), відоме рішення додається безпосередньо в поле `Remedy Injection` задачі.
2. Воркер отримує чітку інструкцію та код виправлення на першому кроці, що виключає повторні галюцинації та скорочує час відновлення до <5 секунд.

---

## 🔄 4. Двостороння тригеризація Canvas ↔ Swarm

Користувач може керувати роєм прямо з інтерфейсу Obsidian Canvas, змінюючи текстовий вміст нод:

* **Тригер тестування**:
  Якщо користувач ставить позначку `- [x] Run Tests` або `- [x] Verify All`:
  1. Фоновий вочдог виявляє зміну чекбоксу.
  2. Запускається відповідна тестова команда (`pytest` або `scripts/verify_all.sh`).
  3. Чекбокс автоматично повертається у стан `- [ ]` із бейджем результату `✅ [Tests Passed (06:45:12)]`.
* **Тригер виклику воркера**:
  Якщо встановлено чекбокс `- [x] Dispatch Worker`:
  1. З картки зчитується призначений агент (`Assigned Agent: gerych_auditor`).
  2. Викликається `dnk_swarm_dispatch(agent, task_description)`.
  3. Картка оновлює свій статус на `in_progress`.

---

## 🌉 5. SSOT Bridge: Obsidian Canvas ↔ React Flow

Модуль `core/orchestrator/visual_canvas_control.py` забезпечує точне відображення структур даних:

```python
# Конвертація Obsidian Canvas JSON у React Flow
flow_data = canvas_to_react_flow(canvas_data)

# Зворотна трансляція React Flow у Obsidian Canvas
canvas_data = react_flow_to_canvas(flow_data)
```

### Специфікація узгодження типів:
* **Координати**: Obsidian Canvas `(x, y)` ➔ React Flow `node.position: {x, y}`.
* **Розміри**: Obsidian `(width, height)` ➔ React Flow `node.dimensions: {width, height}` або `node.style: {width, height}`.
* **Зв'язки (Edges)**: Obsidian `fromNode / toNode` ➔ React Flow `source / target` із маркерами стрілок та підписами залежностей (`TaskDNA Dependency`).

---

## 🚀 6. Наступні кроки еволюції (Roadmap)

1. **FastAPI Canvas Bridge Router** (`apps/api/routers/canvas_bridge.py`):
   * Публікація ендпоінтів `/api/v1/canvas/sync/obsidian-to-web` та `/api/v1/canvas/sync/web-to-obsidian`.
2. **WebSocket Live Heartbeat**:
   * Трансляція подій Post-Tool хука та Sentinel у реальному часі на фронтенд-дашборд через `/ws/orchestrator/events`.
3. **Daemon Service Launcher**:
   * Створення скрипта `scripts/system/start_canvas_watchdog.sh` для фонового демона на базі launchd/systemd.
