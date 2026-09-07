---
title: "015 Gerych System Architecture Audit, SOTA Assimilation & Strategic Evolution Blueprint"
type: "architecture_audit"
status: "active"
tags:
  - "architecture"
  - "audit"
  - "sota"
  - "swarm"
  - "memory"
  - "orchestration"
  - "roadmap"
created: "2026-09-05"
author: "Gerych Prime & Antigravity Mentor"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/015 Gerych System Architecture Audit, SOTA Assimilation & Strategic Evolution Blueprint.md"
purpose: "Comprehensive Architectural Audit of Gerych Prime & DNK OS, Global GitHub SOTA Reverse Engineering, and Strategic Improvement Roadmap."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym, Gerych Prime & Mentor"
--- END DNK-MRH-HEADER -->

# 🏛️ Повний архітектурний аудит Gerych Prime & DNK OS, SOTA-асиміляція та стратегічний план еволюції

**Дата аудиту:** 5 вересня 2026 р.  
**Ролі:** Ментор з архітектури (Head of Orchestration) + Команда Senior Fullstack/Swarm інженерів.  
**Об'єкт аудиту:** Екосистема `DNK_HUB`: ядро (`core/`), оркестратор (`core/orchestrator/`), пам'ять (`SCONES`), інструментарій, шлюзи та Swarm-агенти.

---

## 📌 Зміст
1. [Вступне слово Ментора та Команди](#1-вступне-слово-ментора-та-команди)
2. [Глибокий аудит поточної архітектури: Сильні сторони, Проблеми та Невідповідності](#2-глибокий-аудит-поточної-архітектури)
3. [Світові SOTA Open Source орієнтири на GitHub та їхня логіка](#3-світові-sota-open-source-орієнтири-на-github)
4. [Детальний порівняльний аналіз: Gerych проти SOTA індустрії](#4-детальний-порівняльний-аналіз)
5. [Стратегічні рекомендації та Дорожня карта покращення (Roadmap)](#5-стратегічні-рекомендації-та-дорожня-карта-покращення)
6. [Висновки](#6-висновки)

---

## 1. Вступне слово Ментора та Команди

### Погляд Ментора (Head of System Architecture)
> "Gerych — це унікальна надбудова, яка еволюціонувала з простого агента-виконавця у багаторівневу інженерну платформу. Головне досягнення проекту — **Zero-Waste Protocol v4.3.0**, атомарне квантування задач (MASE) та жорсткі Quality Gates (100% Green).  
> Проте швидке екстенсивне масштабування призвело до класичної хвороби росту: **архітектурної седиментації** (нашарування старих та нових підсистем без повної консолідації), розпорошення шару пам'яті та змішування статичних конфігурацій агентів із динамічним runtime-станом."

### Погляд Команди розробників (Core Engineers)
> "Щодня ми стикаємося з тим, що розмір `core/` розрісся до 3+ ГБ за рахунок дублікатів та локальних SQLite-баз; системний промпт перевантажений інструментами, які не потрібні для конкретного таску; а координація агентів відбувається частково через евристики, частково через Hermes subagents, а частково через кастомні FastMCP-ендпоінти.  
> Нам потрібен єдиний уніфікований **Control Plane**, динамічне звуження контексту (Dynamic LOD) та перехід на перевірені світові патерни (LangGraph, Letta, Aider, Agno)."

---

## 2. Глибокий аудит поточної архітектури

### 2.1. Сильні сторони та конкурентні переваги Gerych Core
1. **Zero-Waste High-Velocity Protocol (v4.3.0)**:
   - Автоматичний пре-триаж задач (`dnk_triage_task`): розподіл на `SOLO`, `SWARM_PARALLEL` та `SWARM_SEQUENTIAL`.
   - Жорсткий ліміт на кількість викликів інструментів (≤ 25 tools per turn), що запобігає нескінченним галюцинаційним циклам та вичерпанню лімітів.
2. **Two-Track SOTA Repository Assimilation Engine**:
   - Чіткий поділ ліцензій (Track 1: MIT/Apache — пряма асиміляція; Track 2: GPL/AGPL — чиста реверс-інженерія Clean-Room).
3. **Fail-Closed Quality Gates**:
   - `scripts/verify_all.sh` (понад 1350 тестів), `adversarial_gate_runner.py` (Red Team vs Blue Team), що гарантує захист від регресій перед коммітом.
4. **MRH Invariant (Machine-Readable Headers)**:
   - Повна простежуваність версійності та цілей файлів (`DNK-STD-0075`).

---

### 2.2. Критичні проблеми та невідповідності (Architectural Debt)

#### 🔴 Проблема 1: Витік Runtime-стану та надлишковий дисковий баласт (2.5+ GB)
* **Факт:** Каталоги агентів `core/orchestrator/agents/gerych_prime/` та `herich_librarian/` містять важкі бази даних `state.db` (понад 600 MB), кеші мовних серверів `lsp/` (168 MB), директорії `checkpoints/` (196 MB), `bin/` (62 MB).
* **Невідповідність:** Специфікація агента (`agent_card.yaml`, `SOUL.md`) має бути незмінною (stateless декларацією), а runtime-стан має жити в ізольованому каталозі (`~/.hermes/` або `.runtime_cache/`).
* **Зомбі-архіви:** Каталоги `core/hermes_agent.backup...`, `core/hermes_agent_staging/`, `core/hermes_versions/` займають понад 1.36 ГБ і 77,000 файлів.

#### 🟠 Проблема 2: Фрагментація шару оркестрації та Swarm-координації
* **Факт:** Логіка управління агентами розпорошена між 6 компонентами:
  1. `core/orchestrator/swarm_coordinator.py`
  2. `core/swarm_engine.py`
  3. `core/swarm_orchestrator.py`
  4. `core/workflow_orchestrator.py`
  5. `core/coordinators/agent_coordinator.py`
  6. `core/hermes_agent/` (субпроцеси `delegate_task`).
* **Невідповідність:** Немає єдиного авторитетного State Machine або Directed Acyclic Graph (DAG) двигуна. Різні модулі по-різному трактують поняття таску, черги та статусу виконання.

#### 🟡 Проблема 3: Дисперсія пам'яті (Memory Dispersion)
* **Факт:** У системі співіснують 4 незалежні сховища знань:
  1. **L1 (Hermes Memory)**: текстові записи `memory(action='add')`.
  2. **L2/L3 (SCONES)**: `core/scones_memory.py` та `scones_l3_memory.py` (JSON-фолбек + pgvector).
  3. **Session FTS5 DB**: локальна SQLite база сесій Hermes (`session_search`).
  4. **Obsidian Vault**: Markdown-нотатки в `docs/notes/`.
* **Невідповідність:** Відсутній єдиний шар **Memory Router / Unified Retrieval**. Агент часто не "знає", куди саме дивитися в першу чергу, або читає файли заново замість швидкого RAG-пошуку.

#### 🟡 Проблема 4: Context Window Tax (Податок на розмір контексту)
* **Факт:** Кожен запит до моделі несе в собі повний масив із 60+ інструментів та великий системний промпт (15,000–25,000 токенів ще до початку розмови).
* **Невідповідність:** Навіть якщо задача стосується суто виправлення помилки в Python-скрипті, модель отримує описи інструментів для Shopify Liquid, Remotion Video, Notion, Twitter, Philips Hue тощо. Це збільшує час генерації (latency), витрати коштів та ризик галюцинацій.
* **Рішення:** Деталізовано у [[018 Dynamic Context Budgeting and Toolset Pruning Architecture|ADR 018: Dynamic Context Budgeting and Toolset Pruning Architecture]].

---

## 3. Світові SOTA Open Source орієнтири на GitHub

| Репозиторій | Ключова технологічна інновація | Чому це найкраще рішення |
| :--- | :--- | :--- |
| **`langchain-ai/langgraph`** | **Cyclic StateGraph + Checkpointing** | Формальні графи переходів станів, Time-Travel дебаг, Human-in-the-Loop переривання, збереження стану у PostgreSQL. |
| **`letta-ai/letta` (раніше MemGPT)** | **OS-Style Hierarchical Memory** | Розподіл пам'яті за аналогією з ОС: Core/Working Context, Recall Memory (FTS/Vector) та Archival Memory. Саморедагування пам'яті агентом. |
| **`agno-agi/agno` (раніше Phidata)** | **Ultra-Low Latency Agent Core** | Мінімалістична архітектура без оверхеду, pure Python, пряме асинхронне виконання, вбудована підтримка pgvector та multi-modal. |
| **`paul-gauthier/aider`** | **Tree-Sitter RepoMap & Git-Centric Commits** | Побудова компактної карти символів репозиторію через Tree-Sitter AST (1-2k токенів замість зчитування всього репозиторію), миттєве попадання у потрібний файл. |
| **`geekan/MetaGPT`** | **SOP (Standard Operating Procedures) Engine** | Передача структурованих артефактів між агентами (PRD -> Design -> Code -> Review) замість неструктурованого чату. |
| **`crewAIInc/crewAI`** | **Hierarchical Swarm with Smart Caching** | Ієрархічні процеси, кешування важких інструментів (Tool Cache), рольова взаємодія. |

---

## 4. Детальний порівняльний аналіз: Gerych проти SOTA

### 4.1. Оркестрація: Gerych vs LangGraph vs MetaGPT
* **У Gerych зараз:** Гібридний підхід: евристичний `task_triage.py` + `swarm_coordinator.py` + субпроцеси Hermes. Складно відновити виконання графа після збою на кроці 3 з 5 без повторного старту всього ланцюжка.
* **SOTA-підхід:** У **LangGraph** граф є детермінованим скінченним автоматом. Кожен вузол записує свій стан у PostgreSQL-чекпоінт. Якщо стається збій, агент перезапускається точно з точки збою (durable state).

### 4.2. Навігація кодом: Gerych vs Aider
* **У Gerych зараз:** Пошук через `search_files` (ripgrep) або `dnk_resolve_symbol` (regex/ctags парсинг). Іноді агент витрачає 2-4 виклики на з'ясування структури директорій та типів.
* **SOTA-підхід:** В **Aider** використовується **RepoMap на основі Tree-Sitter**. Створюється граф визначень та викликів (pagerank репозиторію). За 1 запит агент отримує точний список сигнатур саме тих класів, які пов'язані з поточною задачею, вкладаючись у 1024 токени.

### 4.3. Робота з пам'яттю: SCONES vs Letta (MemGPT)
* **У SCONES зараз:** Потужна система з pgvector та локальним JSON-фолбеком, але вона відокремлена від швидкої пам'яті сесій Hermes.
* **SOTA-підхід:** У **Letta** агент володіє спеціалізованими інструментами самокерування: `core_memory_replace`, `archival_memory_insert`, `archival_memory_search`. Модель сама підтримує актуальність своєї робочої пам'яті, стискаючи старі факти.

---

## 5. Стратегічні рекомендації та Дорожня карта покращення

### 🚀 Рівень 1 (P0): Негайна санація та видалення баласту (Day 1–2)
1. **Quarantine & Prune зомбі-директорій**:
   - Безпечно вилучити `core/hermes_agent.backup.pre-0.21.0/`, `core/hermes_agent_staging/`, `core/hermes_versions/`. Це звільнить **1.36 ГБ** та прискорить повний лінтинг на 40%.
2. **Винесення runtime-станів агентів**:
   - Перенести `state.db`, `checkpoints/`, `lsp/`, `bin/` з `core/orchestrator/agents/*/` у `~/.hermes/runtime/` або додати у `.gitignore`. Папки агентів мають містити лише версіоновані конфігураційні картки та SOUL.
3. **Виправлення імпортів у `core/tests`**:
   - Додати безпечні моки для `langfuse` у `core/accounting_engine.py`, забезпечивши 100% запуск тестів у підкаталозі `core/tests`.

### ⚡ Рівень 2 (P1): Консолідація Swarm Control Plane (Week 1)
1. **Єдиний Orchestrator Interface**:
   - Злити дублюючі модулі `core/swarm_engine.py`, `core/swarm_orchestrator.py` та `core/coordinators/` у єдине ядро `core/orchestrator/SwarmControlPlane.py`.
2. **Впровадження Tree-Sitter AST RepoMap (Aider Pattern)**:
   - Розширити `scripts/system/repo_map.py` та `dnk_resolve_symbol` підтримкою повноцінного синтаксичного дерева AST через `tree-sitter`. Формувати динамічну мапу релевантних символів за 10 мс.

### 🧠 Рівень 3 (P2): Уніфікація когнітивної пам'яті (Knowledge Fabric) (Week 2)
1. **Unified Memory Broker**:
   - Створити єдиний абстрактний шар над L1 (Hermes Session/Memory), L2/L3 (SCONES / pgvector) та Obsidian Vault.
2. **Автоматична двостороння синхронізація з Obsidian Vault**:
   - Після кожного великого таску зберігати структурований звіт у `./docs/notes/` з перехресними посиланнями `[[wikilinks]]`.

### 🎯 Рівень 4 (P3): Dynamic Toolset LOD & Context Pruning (Week 3)
1. **Контекстне звуження інструментів на базі Triage**:
   - Якщо `task_triage` класифікував задачу як `backend_api`, автоматично обмежувати набір доступних інструментів до `terminal`, `file`, `web`, `github`, вимикаючи інструменти `shopify`, `video_ai`, `smart_home`. Це заощадить 10-15k токенів на кожному виклику.
2. **Artifact-Driven A2A Handshake**:
   - Перехід передачі результатів між агентами на типізовані Pydantic-контракти (MetaGPT / LangGraph pattern) замість неструктурованого тексту.

---

## 6. Висновки

Gerych Prime та DNK OS уже сьогодні є передовою автономною системою з найсуворішим контролем якості коду (MASE + Zero-Waste Protocol + Quality Gates).  
Реалізація цієї дорожньої карти дозволить:
1. **Знизити споживання дискового простору на ~2.5 ГБ**.
2. **Скоротити навантаження на контекст на 40–60%** завдяки динамічному LOD та Tree-Sitter RepoMap.
3. **Збільшити швидкість проходження тестів та рефакторингу в 2-3 рази**.
4. **Забезпечити детерміновану відмовостійкість Swarm-оркестрації** на рівні світових лідерів індустрії (LangGraph, Letta, Aider).

---
*Документ створено та ратифіковано у рамках спільної сесії Mentorship & Architecture Review.*
