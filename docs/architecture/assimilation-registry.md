# --- DNK-MRH-HEADER ---
# mrh_id: "docs_architecture_assimilation_registry"
# purpose: "Master Assimilation Registry & Open Source Provenance Map for DNK OS"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-31"
# --- END DNK-MRH-HEADER ---

# 🗺️ DNK OS Master Assimilation Registry (DNK-ASSIM-REGISTRY-001)

Цей документ є офіційним реєстром походження (Provenance), класифікації та правил адаптації зовнішніх відкритих рішень (Open Source) у канонічну архітектуру **DNK OS**.

---

## 1. Рівні Асиміляції (Assimilation Levels)

* **R1 (Research Only)**: Вивчення документації, архітектурних ідей, UX-концепцій. Код у репозиторій не додається.
* **R2 (Protocol Compatibility)**: Підтримка відкритих стандартів (Shopify GraphQL, OTLP, W3C Trace Context, OAuth 2.0).
* **R3 (Pattern Adaptation) — ГОЛОВНИЙ ШЛЯХ**: Адаптація перевірених алгоритмів і патернів (Supervisor-Worker, Task DAG, State Graph) під власну доменну модель, Pydantic-схеми, базу даних та UI.
* **R4 (Isolated Component Reuse)**: Використання ліцензійно чистих, ізольованих NPM/PyPI бібліотек (Lucide React, Framer Motion, XYFlow).
* **R5 (Fork / Vendor)**: Винятковий режим для важких підсистем із суворим патч-менеджментом.

---

## 2. Каталог Джерел та Асиміляційна Карта

### 2.1. Оркестрація Агентів (Agent Orchestration & Swarm)

| Джерело / Репозиторій | Ліцензія | Рівень | Що адаптовано в DNK OS | Що відкинуто (Not Adopted) | Зона в DNK OS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LangGraph** (`langchain-ai/langgraph`) | MIT | **R3** | Патерн Supervisor-Worker, переривання для Human-in-the-Loop, граф станів задач | Чужий UI, важкий рантайм, прив'язка до хмари LangSmith | `core/orchestrator/`, `apps/api/routers/agent.py` |
| **AutoGen** (`microsoft/autogen`) | MIT | **R3** | A2A (Agent-to-Agent) конверти повідомлень, ролі спеціалістів | Неконтрольовані групові чати у продакшні | `core/coordinators/`, `apps/api/routers/a2a_mesh_router.py` |
| **CrewAI** (`crewAIInc/crewAI`) | MIT | **R3** | Декомпозиція задач (TaskDNA), рольові профілі агентів | Зовнішня жорстка залежність від фреймворку | `core/agent_factory/`, `services/agentswarms/` |
| **AgentSwarms** (`AgentSwarms-fyi/agentswarms`) | Elastic-2.0 | **R3** | 6-нодовий Swarm DAG (Agent, Router, Condition, Loop, Approval, Tool), DuckDB Lakehouse, AI Analyst (NL2SQL) | Чужа хмарна схема Supabase, монолітний сервер | `core/adapters/dnk_agentswarms_adapter.py`, `docs/reports/rd_assimilation/agentswarms/` |
| **Open-SWE / Hermes** | MIT / Apache 2.0 | **R3/R4** | Автономний інженерний цикл: Task ➔ Code ➔ Test ➔ Evidence PR | Прямі неконтрольовані коміти в `main` | `core/hermes_runtime.py`, `scripts/system/gerych_swarm.sh` |


---

### 2.2. Візуальний Робочий Простір (Infinite Canvas & Spatial UI)

| Джерело / Репозиторій | Ліцензія | Рівень | Що адаптовано в DNK OS | Що відкинуто (Not Adopted) | Зона в DNK OS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **XYFlow / React Flow** | MIT | **R4** | Інтерактивне полотно, ноди, з'єднання, мінімапа, zoom/pan | Стандартний вигляд, базова бізнес-логіка | `apps/web/components/canvas/`, `DNKStudioWorkspace.tsx` |
| **Archify Spatial Diagrams** | MIT | **R4** | Автономний компілятор JSON IR діаграм (архітектура, воркфлоу, послідовності, потоки даних, життєвий цикл), self-contained HTML/SVG | Зовнішній хмарний хостинг, нетипізовані схеми | `packages/archify/`, `core/adapters/dnk_archify_adapter.py`, `skills/archify_assimilated/` |
| **OpenDesign / CapCut UX** | MIT / Internal | **R3** | Ритм інтерфейсу, spatial dock, інспектор властивостей справа, live console знизу | Чужі демо-ассети, монолітні демо-сервери | `apps/web/components/workspace/` |

---

### 2.3. E-Commerce & Shopify Engine

| Джерело / Репозиторій | Ліцензія | Рівень | Що адаптовано в DNK OS | Що відкинуто (Not Adopted) | Зона в DNK OS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Shopify Theme Tools / AST** | MIT | **R2/R3** | Парсинг Liquid AST, валідація секцій OS 2.0, генерація коду | Небезпечні прямі записи на живий магазин | `packages/shopify-theme/`, `services/dnk_shopify/` |
| **ReBurn E-Com Patterns** | Proprietary | **R3** | Секції з високою конверсією, чекаути, післяпокупкова аналітика | Жорстко закодовані статичні шаблони | `apps/api/routers/shopify.py`, `apps/shopify/` |

---

### 2.4. Мультимодальні Медіа та Відео (Media Studio)

| Джерело / Репозиторій | Ліцензія | Рівень | Що адаптовано в DNK OS | Що відкинуто (Not Adopted) | Зона в DNK OS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Remotion / FFmpeg Pipeline** | MIT / GPL / Custom | **R3** | 9:16 та 16:9 просторові відео-шаблони, таймлайн рендерингу | Важкі локальні синхронні рендери без черг | `services/dnk_video_ai_creator/`, `apps/api/routers/video_router.py` |

---

### 2.5. Пам'ять, Знання та RAG (Knowledge Engine)

| Джерело / Репозиторій | Ліцензія | Рівень | Що адаптовано в DNK OS | Що відкинуто (Not Adopted) | Зона в DNK OS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SCONES L3 Memory** | MIT (DNK Core) | **R3** | Корпоративна пам'ять, посилання на рішення, еволюція правил | Не замінює канонічну реляційну БД | `core/scones_l3_memory.py`, `core/scones_memory.py` |
| **Qdrant / pgvector** | Apache 2.0 / PostgreSQL | **R2** | Гібридний векторний пошук, фільтрація за метаданими клієнта (Tenant Scoped) | Змішування контекстів різних клієнтів | `apps/api/routers/vector_search.py`, `core/memory/` |

---

## 3. Заборонені Режими (Forbidden Invariants)

1. **Жодного неконтрольованого запису**: Агенти не мають права виконувати зовнішні дії з запису (Shopify publish, списання коштів, деплой) без явного схвалення користувача (Human-in-the-Loop Gate).
2. **Нульовий витік секретів**: Секрети, API-ключі та дані клієнтів заборонено передавати у відкритому вигляді у фронтенд-бандл, Git-історію чи необмежений LLM-промпт.
3. **Ізоляція ареалів (Tenant Isolation)**: Дані одного клієнта суворо ізольовані та ніколи не змішуються у векторній чи реляційній пам'яті з іншими.
