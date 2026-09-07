# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🌸 Офіційний реєстр агентних патернів (Agentic Patterns Registry)

Цей реєстр містить канонічні паттерни взаємодії та покращення агентних систем, які впроваджені в екосистемі **DNK OS**. Всі нові паттерни повинні відповідно відповідати схемі `docs/schemas/agentic_pattern_schema.json`.

---

## 📖 Словник технологічних покращень агентів (Agentic Technological Improvements Dictionary)

Місія словника полягає у фіксації, структуризації та стандартизації технологічних покращень, які дозволяють оптимізувати роботу великих та малих мовних моделей, що виступають у ролі агентів (воркерів чи оркестраторів) в екосистемі **DNK OS**. Словник забезпевує уніфікований підхід до підвищення когнітивних здатностей агентів через збагачення промптів, контекстів та інструкцій.

---

### 📘 Картка DNK-AGNT-001: Agent Prompt & Task Enrichment Engine (Двигун збагачення промптів)

- **ID**: DNK-AGNT-001
- **Назва**: Agent Prompt & Task Enrichment Engine (Двигун збагачення промптів)
- **Тип**: Task Enrichment
- **Ролі**: Enrichment Orchestrator, Prompt Optimizer
- **Тригери**: Task starting, Agent initialization, Worker LLM call
- **Опис**: Конвеєр динамічного збагачення контексту, який перетворює лаконічні запити користувача у надзвичайно деталізовані інструкції.
- **Методи верифікації**: Prompt parsing tests, Enriched context checks


#### 🌊 1. Архітектура 3-хвильового збагачення (3-Wave Enrichment Architecture)

Двигун збагачення працює за трьома послідовними хвилями для забезпечення максимальної якості когнітивного результату:

```
[Вхідна задача]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 🌊 Wave 1: Context Harvesting & Intent Alignment        │
│    - Збір метаданих проекту та оточення                │
│    - Визначення меж робочого простору (DNK OS/)      │
│    - Синхронізація з SOUL та поточною пам'яттю          │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 🌊 Wave 2: Capability & Tool Synthesis                 │
│    - Динамічне підключення релевантних навичок (skills) │
│    - Ін'єкція архітектурних інваріантів та безпеки     │
│    - Вибір оптимальної LLM за допомогою matrix роутингу │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 🌊 Wave 3: Meta-cognitive Optimization & Verification │
│    - Додавання контурів самокорекції (Evaluator-Opt)   │
│    - Визначення Definition of Done (DoD)               │
│    - Специфікація точних команд верифікації (pytest/cli)│
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
[Збагачена SOTA-інструкція для Агента]
```

* **Wave 1: Context Harvesting & Intent Alignment (Перша хвиля: Збір контексту та вирівнювання намірів)**: Збирає всі необхідні метадані середовища виконання, сканує межі робочого простору (наприклад, конфігурацію папки `DNK_HUB/`), підтягує активні сесії та файли пам'яті. Зіставляє намір користувача з місією та філософією (SOUL) конкретного воркера для вирівнювання розуміння кінцевої мети.
* **Wave 2: Capability & Tool Synthesis (Друга хвиля: Синтез спроможностей та інструментів)**: На основі доступного набору інструментів та навичок (skills) динамічно збагачує промпт точними покроковими інструкціями з відповідних навичок. Додає системні обмеження безпеки (zero host pollution, використання виключно Docker-контейнерів для важких середовищ, відносні шляхи) та обирає модель за матрицею роутингу (GLM для UI чи Mistral для коду).
* **Wave 3: Meta-cognitive Optimization & Verification (Третя хвиля: Мета-когнітивна оптимізація та верифікація)**: Вбудовує в інструкцію когнітивні шаблони поведінки типу "Оцінювач-Оптимізатор", які змушують модель валідувати проміжні результати. Чітко визначає критерії успіху (DoD) та автоматично генерує точні CLI-команди для запуску верифікаційних скриптів або pytest-суїтів.

#### 📊 2. Таблиця універсального застосування (Universal Application Table)

| Агент / Роль | Сценарій використання | Очікуваний ефект збагачення | Метод верифікації |
| :--- | :--- | :--- | :--- |
| **Gerych (herich_librarian)** | Оркестрація мультиагентних робіт, аналіз R&D репозиторіїв | 100% точність визначення меж та розподілу підзадач | Автоматичний запуск pytest суїтів |
| **dnk_koder** | Написання, оптимізація та рефакторинг складного коду | Скорочення синтаксичних помилок та галюцинацій на 95% | Pytest, лінтування, AST парсинг |
| **dnk-dev-01** | Створення FastAPI ендпоінтів та React UI компонентів | Чиста гексагональна архітектура, надійне підключення до БД | Docker-compose інтеграційні тести |
| **dnk_governance_companion**| Перевірка standards коду, MRH-хедерів та лімітів токенів | Гарантія 100% дотримання архітектурних інваріантів | Автоматичний audit перед мержем |

### 📘 Картка DNK-AGNT-002: FastMCP Micro-Tooling Protocol

- **ID**: DNK-AGNT-002
- **Назва**: FastMCP Micro-Tooling Protocol
- **Тип**: Task Enrichment
- **Ролі**: MCP Server, MCP Client, Tool Coordinator
- **Тригери**: API integration expansion, Worker tools extension request
- **Опис**: Протокол швидкого розгортання мікросервісних MCP-інструментів на базі FastMCP для забезпечення інтеграції агентів з локальними та хмарними API.
- **Методи верифікації**: MCP tool listing check, FastMCP execution liveness tests

---

## 🧬 Опис патернів

### 1. Orchestrator-Workers (Оркестратор - Воркери)
- **ID**: DNK-PAT-001
- **Тип**: Multi-Agent System
- **Ролі**: Orchestrator, Worker
- **Тригери**: Complex multi-step tasks, Specialized domain requests
- **Опис**: Розподіл складних задач від головного оркестратора (Герич) до спеціалізованих воркерів (Rick, Yuriy, Cas, Tiffany, Morgan).
- **Методи верифікації**: Subagent execution reports, Integration tests

### 2. Evaluator-Optimizer (Оцінювач - Оптимізатор)
- **ID**: DNK-PAT-002
- **Тип**: Optimization Loop
- **Ролі**: Generator, Evaluator
- **Тригери**: Code writing, Refactoring, Infrastructure changes
- **Опис**: Двокрокова петля зворотного зв'язку, де один агент генерує рішення, а інший оцінює його та надає детальні вказівки для виправлення помилок перед здачею.
- **Методи верифікації**: Pytest execution, Linter status, Review response

### 3. Autonomous Reflection & Learning Loop (Автономна рефлексія та навчання)
- **ID**: DNK-PAT-003
- **Тип**: Cognitive Memory
- **Ролі**: Reflection Agent, Knowledge Consolidation Agent
- **Тригери**: Development cycle completion, Complex bug resolution
- **Опис**: Збір результатів виконаного циклу (execution blueprint), формування звітів про помилки/успіхи та автоматичне оновлення бази знань або навичок (skills) для майбутнього використання.
- **Методи верифікації**: Updated skill files, Successful future runs

### 4. Context-Compacted Memory (Контекстно-компактна пам'ять)
- **ID**: DNK-PAT-004
- **Тип**: Cognitive Memory
- **Ролі**: Memory Manager, Vector Store Connector
- **Тригери**: Token limit warnings, Historical session requests
- **Опис**: Динамічне стиснення контексту користувача та середовища для ефективного використання вікон контексту LLM через RAG та семантичне кешування.
- **Методи верифікації**: Context size checks, Retrieval accuracy

### 5. Standardized Skill Architecture (Модульна архітектура навичок)
- **ID**: DNK-PAT-005
- **Тип**: Procedural Knowledge
- **Ролі**: Skill Author, Skill Loader
- **Тригери**: New repeatable workflows
- **Опис**: Оформлення процедурних знань у стандартизовані директорії навичок, що містять інструкції, автоматичні скріпти, шаблони конфігурацій та верифікаційні тести.
- **Методи верифікації**: Structure audits, Skill load tests

### 6. Task Forest Engine / DAG Workflows (Дерево задач)
- **ID**: DNK-PAT-006
- **Тип**: State Machine / Workflow
- **Ролі**: Task Engine Controller, State Checker
- **Тригери**: New epic starting, Feature development kickoff
- **Опис**: Ієрархічне відстеження стану виконання задач (від Поля до Квітки Задач) за допомогою спрямованих ациклічних графів, що дозволяє робити чекпоінти та відновлення після збоїв.
- **Методи верифікації**: Graph export validation, State recovery tests

### 7. Dynamic SOTA Model Routing (Динамічний роутинг SOTA моделей)
- **ID**: DNK-PAT-007
- **Тип**: Dynamic Routing
- **Ролі**: Router Gateway, LLM Proxy
- **Тригери**: Agent invocation, Code generation tasks
- **Опис**: Інтелектуальний підбір та роутинг запитів до найбільш оптимальних спеціалізованих LLM/SLM моделей відповідно до ролі воркера для забезпечення швидкості та економії токенів.
- **Методи верифікації**: Routing matrix checks, Cost & latency audits
---

## 📇 Офіційний JSON-список патернів для валідації (Pattern Cards JSON)

У наведеному нижче блоці містяться машинозчитувані картки патернів, які використовуються автоматизованими тестами для валідації відповідності JSON-схемі.

```json
[
  {
    "id": "DNK-PAT-001",
    "name": "Orchestrator-Workers (Оркестратор - Воркери)",
    "description": "Розподіл складних задач від головного оркестратора (Герич) до спеціалізованих воркерів (Rick, Yuriy, Cas, Tiffany, Morgan).",
    "type": "Multi-Agent System",
    "roles": [
      "Orchestrator",
      "Worker"
    ],
    "triggers": [
      "Complex multi-step tasks",
      "Specialized domain requests"
    ],
    "validation_methods": [
      "Subagent execution reports",
      "Integration tests"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-PAT-002",
    "name": "Evaluator-Optimizer (Оцінювач - Оптимізатор)",
    "description": "Двокрокова петля зворотного зв'язку, де один агент генерує рішення, а інший оцінює його та надає детальні вказівки для виправлення помилок перед здачею.",
    "type": "Optimization Loop",
    "roles": [
      "Generator",
      "Evaluator"
    ],
    "triggers": [
      "Code writing",
      "Refactoring",
      "Infrastructure changes"
    ],
    "validation_methods": [
      "Pytest execution",
      "Linter status",
      "Review response"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-PAT-003",
    "name": "Autonomous Reflection & Learning Loop (Автономна рефлексія та навчання)",
    "description": "Збір результатів виконаного циклу (execution blueprint), формування звітів про помилки/успіхи та автоматичне оновлення бази знань або навичок (skills) для майбутнього використання.",
    "type": "Cognitive Memory",
    "roles": [
      "Reflection Agent",
      "Knowledge Consolidation Agent"
    ],
    "triggers": [
      "Development cycle completion",
      "Complex bug resolution"
    ],
    "validation_methods": [
      "Updated skill files",
      "Successful future runs"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-PAT-004",
    "name": "Context-Compacted Memory (Контекстно-компактна пам'ять)",
    "description": "Динамічне стиснення контексту користувача та середовища для ефективного використання вікон контексту LLM через RAG та семантичне кешування.",
    "type": "Cognitive Memory",
    "roles": [
      "Memory Manager",
      "Vector Store Connector"
    ],
    "triggers": [
      "Token limit warnings",
      "Historical session requests"
    ],
    "validation_methods": [
      "Context size checks",
      "Retrieval accuracy"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-PAT-005",
    "name": "Standardized Skill Architecture (Модульна архітектура навичок)",
    "description": "Оформлення процедурних знань у стандартизовані директорії навичок, що містять інструкції, автоматичні скріпти, шаблони конфігурацій та верифікаційні тести.",
    "type": "Procedural Knowledge",
    "roles": [
      "Skill Author",
      "Skill Loader"
    ],
    "triggers": [
      "New repeatable workflows"
    ],
    "validation_methods": [
      "Structure audits",
      "Skill load tests"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-PAT-006",
    "name": "Task Forest Engine / DAG Workflows (Дерево задач)",
    "description": "Ієрархічне відстеження стану виконання задач (від Поля до Квітки Задач) за допомогою спрямованих ациклічних графів, що дозволяє робити чекпоінти та відновлення після збоїв.",
    "type": "State Machine / Workflow",
    "roles": [
      "Task Engine Controller",
      "State Checker"
    ],
    "triggers": [
      "New epic starting",
      "Feature development kickoff"
    ],
    "validation_methods": [
      "Graph export validation",
      "State recovery tests"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-PAT-007",
    "name": "Dynamic SOTA Model Routing (Динамічний роутинг SOTA моделей)",
    "description": "Інтелектуальний підбір та роутинг запитів до найбільш оптимальних спеціалізованих LLM/SLM моделей відповідно до ролі воркера для забезпечення швидкості та економії токенів.",
    "type": "Dynamic Routing",
    "roles": [
      "Router Gateway",
      "LLM Proxy"
    ],
    "triggers": [
      "Agent invocation",
      "Code generation tasks"
    ],
    "validation_methods": [
      "Routing matrix checks",
      "Cost & latency audits"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-AGNT-001",
    "name": "Agent Prompt & Task Enrichment Engine (Двигун збагачення промптів)",
    "description": "Конвеєр динамічного збагачення контексту, який перетворює лаконічні запити користувача у надзвичайно деталізовані інструкції.",
    "type": "Task Enrichment",
    "roles": [
      "Enrichment Orchestrator",
      "Prompt Optimizer"
    ],
    "triggers": [
      "Task starting",
      "Agent initialization",
      "Worker LLM call"
    ],
    "validation_methods": [
      "Prompt parsing tests",
      "Enriched context checks"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  },
  {
    "id": "DNK-AGNT-002",
    "name": "FastMCP Micro-Tooling Protocol",
    "description": "Протокол швидкого розгортання мікросервісних MCP-інструментів на базі FastMCP для забезпечення інтеграції агентів з локальними та хмарними API.",
    "type": "Task Enrichment",
    "roles": [
      "MCP Server",
      "MCP Client",
      "Tool Coordinator"
    ],
    "triggers": [
      "API integration expansion",
      "Worker tools extension request"
    ],
    "validation_methods": [
      "MCP tool listing check",
      "FastMCP execution liveness tests"
    ],
    "metadata": {
      "status": "Active",
      "version": "1.0.0"
    }
  }
]
```