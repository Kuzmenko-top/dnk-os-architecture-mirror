# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/agno/RN-043_agno_architecture_and_infinite_canvas_audit.md"
# purpose: "Comprehensive Research Digest & Technical Reverse-Engineering Audit of Agno (formerly Phidata) for DNK OS Infinite Canvas."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-AGNO-ASSIMILATION"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🔬 RN-043: Agno Framework, AgentOS Runtime & Infinite Canvas Substrate Deep-Dive Audit

## 📋 1. Executive Summary & Product DNA
**Agno** (`github.com/agno-agi/agno`, 42,000+ ⭐, ліцензія **Apache 2.0**) — ультрашвидкий multi-agent фреймворк, рантайм та control plane для побудови, запуску та моніторингу автономних агентних систем виробничого рівня.

У контексті **DNK OS Infinite Canvas** (Робочого Безкінечного Полотна) Agno надає фундаментальні патерни:
1. **Multi-Agent Teams & Workflows as Graph Nodes**: Перетворення абстрактних агентів і кроків виконання у візуальні інтерактивні вузли полотна.
2. **Stateless Session Checkpointing**: Можливість паузи/відновлення складних агентних ланцюгів на полотні без блокування потоків виконання.
3. **First-Class Human-in-the-Loop (HITL)**: Механізм запиту дозволів на небезпечні дії (виклики інструментів, мутації бази даних, деплой) безпосередньо через UI-вузли полотна.
4. **Agentic Memory & LearningMachine**: Довгострокова пам'ять агентів із семантичним пошуком, ізоляцією воркспейсів та оновленням профілів користувача на льоту.
5. **Model Context Protocol (MCP) & 100+ Toolkits**: Стандартизована інтеграція зовнішніх інструментів через stdio/SSE/Streamable-HTTP.

---

## 🏛️ 2. Трьохрівнева Архітектура Agno (Three-Tier Stack)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGNO PLATFORM STACK                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. FRAMEWORK LAYER:                                                         │
│    - Agent (Model agnostic, Tools, Instructions, Reasoning, Guardrails)     │
│    - Team (Leader, Route, Broadcast, Tasks, Debate/Consensus)               │
│    - Workflow (Step, Parallel, Condition, Loop, Router DAGs)                │
│    - Memory (Agentic Memory, User Preferences, Session History)             │
│    - Storage (PostgreSQL, SQLite, Redis, DynamoDB, MongoDB)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. AGENTOS RUNTIME LAYER:                                                   │
│    - Stateless FastAPI Server with Session-Scoped Checkpoints               │
│    - Server-Sent Events (SSE) & WebSocket Streaming                         │
│    - Schema Enforcement (`input_schema` & `output_schema` Pydantic DTOs)   │
│    - Asynchronous Human-in-the-Loop (HITL) Signal Routing                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. CONTROL PLANE & CANVAS BRIDGE:                                           │
│    - Real-time Observability, Session Telemetry & Step Metrics              │
│    - Spatial Infinite Canvas Bridge (2D Reactive Node Visualizer)           │
│    - Dynamic Tool Sandbox & Token Budget Enforcement                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧬 3. Деконструкція Ключових Патернів та Адаптація для DNK OS

### 3.1 Патерн Мульти-Агентної Координації (Agent & Team)
У Agno агент інкапсулює:
- `Model`: інтерфейс взаємодії з LLM (Claude, Gemini, OpenAI, Ollama, DeepSeek).
- `Tools`: набір callable інструментів з автогенерацією JSON-схем або клієнти MCP.
- `Instructions`: динамічні системні промпти, що підтримують ін'єкцію контексту в рантаймі.
- `Team`: режим координатора, де агент-лідер аналізує запит і маршрутизує його до профільних воркерів (Route), розсилає паралельно (Broadcast) або керує послідовним консенсусом.

**Адаптація для DNK Canvas**:
Кожен воркер DNK Swarm (`gerych_builder`, `dnk_shopify`, `dnk_video_ai_creator`, `dnk_dev_fullstack`, `gerych_auditor`) представляється як інтерактивний реактивний `AgentNode` або `TeamNode` на нескінченному полотні з візуальними портами введення/виведення даних.

### 3.2 Патерн Декларативних Воркфлоу (Workflow DAG)
Воркфлоу Agno будується з композиції вузлів:
- `Step`: одинична дія або виклик агента.
- `Parallel`: паралельне виконання гілок із об'єднанням результатів.
- `Condition`: умовне розгалуження на основі предикату чи оцінки моделі.
- `Loop`: ітеративне доопрацювання до виконання умови зупинки.
- `Router`: динамічний семантичний вибір наступного кроку.

**Адаптація для DNK Canvas**:
Воркфлоу Agno транслюється 1:1 у Canvas AST Graph (`WorkflowNode`, `BranchNode`, `ParallelJoinNode`), що дозволяє користувачеві візуально з'єднувати вузли лініями зв'язку (Edges) та запускати їх топологічним сортуванням.

### 3.3 Патерн Асинхронного Human-in-the-Loop (HITL)
Коли агент викликає дію з прапорцем `requires_confirmation=True`:
1. Виконання не блокує потік або сокет; стан агентної сесії зберігається як `PAUSED_FOR_APPROVAL` у Storage.
2. На Infinite Canvas генерується візуальна картка затвердження (`ApprovalCardNode`) із деталями запланованої дії, диффом змін або вартістю операції.
3. Користувач натискає `Approve` або `Reject` (або вносить правки в промпт/параметри).
4. Запит відновлює виконання з точної точки збереження (`resume_checkpoint`).

### 3.4 Патерн Агентної Пам'яті (SCONES + LearningMachine)
Agno використовує багаторівневу структуру пам'яті:
- **Short-term Memory**: останні $K$ повідомлень та викликів інструментів поточної сесії.
- **Session Summaries**: стиснуті резюме попередніх розмов.
- **Agentic Memory**: агент самостійно вирішує, коли зберігати або видаляти знання про уподобання користувача.
- **Vector Knowledge Base**: гібридний пошук (BM25 + Dense Vectors) по вбудованій базі знань.

**Адаптація для DNK OS**:
Синхронізація з **DNK SCONES Memory Engine** (`ws-alpha-001`), де кожен Canvas Workspace має свій ізольований простір пам'яті та базу знань, доступну всім вузлам полотна.

---

## ⚖️ 4. Аудит Ліцензії та Безпеки (Track 1 Permissive)
- **Ліцензія**: Apache License 2.0 (дозволяє комерційне використання, модифікацію, патентування та вільну дистрибуцію).
- **Track 1**: Повне пряме запозичення інтерфейсів, структур даних (DTOs) та створення нативного гексагонального адаптера в `adapters/dnk_agno_canvas_adapter.py`.
- **Безпека**: Необхідна ізоляція динамічного виконання коду через DNK Security Sandbox (`DNK-SEC-043`), валідація схем вводу/виводу через Pydantic v2 та блокування витоку API-ключів у клієнтський браузер.

---

## 🎯 5. Архітектурні Рекомендації для Впровадження
1. Створити `adapters/dnk_agno_canvas_adapter.py`, який реалізує єдиний API між Canvas AST та Agno Agent/Team/Workflow.
2. Описати специфікації `DNK-ARCH-043_agno_infinite_canvas_patterns.md`, `DNK-COMP-043_agno_canvas_contracts.md`, `DNK-SEC-043_agno_execution_sandbox.md`.
3. Створити скіл `skills/agno_assimilated/SKILL.md` для автоматичного використання патернів агентами рою.
4. Покрити адаптер 100% тестами в `tests/test_agno_canvas_assimilation.py`.
