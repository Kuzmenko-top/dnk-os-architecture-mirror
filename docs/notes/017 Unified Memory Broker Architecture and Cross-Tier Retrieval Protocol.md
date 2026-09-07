---
title: "017 Unified Memory Broker Architecture and Cross-Tier Retrieval Protocol"
tags: [memory, scones, l1_hermes, l3_scones, fts5, obsidian_vault, rag, tiered_retrieval]
status: "Accepted"
version: "1.0.0"
date: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/017 Unified Memory Broker Architecture and Cross-Tier Retrieval Protocol.md"
purpose: "Architectural Decision Record and Design Specification for the Unified Memory Broker (L1 Hermes, L2/L3 SCONES, SQLite FTS5 Session Store, and Obsidian Vault)."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🧠 017 Unified Memory Broker Architecture and Cross-Tier Retrieval Protocol

## 📌 Context & Problem Statement
У процесі розвитку DNK OS та агента Gerych виникла серйозна проблема **дисперсії пам'яті (Memory Dispersion)**:
У системі паралельно існували 4 ізольованих сховища знань:
1. **L1 Hermes Memory**: Швидкі текстові контекстні файли (`MEMORY.md`, `USER.md`), орієнтовані на інваріанти та персоналізовані правила користувача.
2. **L2/L3 SCONES Cognitive Engine (`core/scones_memory.py`, `core/scones_l3_memory.py`)**: Структуровані епізодичні спогади, база дистильованих рішень помилок (`Error Distillation`) та векторний HNSW/pgvector шар із часовим згасанням (recency decay).
3. **Session Store SQLite FTS5 (`~/.hermes/state.db`)**: Повнотекстовий індекс минулих діалогів, повідомлень та системних дій (`session_search`).
4. **Obsidian Knowledge Vault (`./docs/notes/`)**: Глибинні системні нотатки, архітектурні рішення (ADRs), специфікації компонентів та граф взаємозв'язків [[wikilinks]].

### ⚠️ Головні Невідповідності До Рефакторингу
- **Відсутність єдиного роутера (Unified Broker)**: Агент не знав, куди звертатися першочергово, або вдавався до повільного сканування файлової системи (`find`, `grep`, читання файлів з нуля) замість блискавичного RAG-запиту.
- **Відсутність раннього виходу (Early-Exit Optimization)**: Запити перевіряли всі шари підряд, що збільшувало час очікування (latency).
- **Відсутність зворотного поширення (Backpropagation)**: Знання, виявлені або виправлені під час діалогу (нові інваріанти, знайдені фікси помилок, прийняті архітектурні рішення), залишалися замкненими у поточному вікні контексту і не консолідувалися автоматично у довготривалі сховища.

---

## 🏛️ Рішення: Unified Memory Broker (`core/memory/unified_memory_broker.py`)

Створено централізований брокер пам'яті **`UnifiedMemoryBroker`** та провайдер сумісності **`UnifiedMemoryProvider`**, які інтегрують усі 4 шари знань в єдиний ієрархічний конвеєр (Tiered Memory Mesh).

```
                      ┌──────────────────────────────────────┐
                      │        UnifiedMemoryBroker           │
                      │  (Intent Classifier & Cascader)      │
                      └──────────────────┬───────────────────┘
                                         │
        ┌──────────────┬─────────────────┼────────────────┬──────────────┐
        ▼              ▼                 ▼                ▼              ▼
   ┌─────────┐   ┌───────────┐    ┌─────────────┐   ┌───────────┐  ┌───────────┐
   │ Tier 1  │   │  Tier 2   │    │   Tier 3    │   │  Tier 4   │  │  Tier 5   │
   │L1 Hermes│   │ L2 SCONES │    │  L3 SCONES  │   │ Obsidian  │  │ SQLite    │
   │ Memory  │   │ Episodic/ │    │  Recency/   │   │  Vault    │  │ FTS5      │
   │<5ms     │   │ Distill   │    │  Vector     │   │ docs/notes│  │ Sessions  │
   │         │   │ <20ms     │    │  <50ms      │   │ <30ms     │  │ <30ms     │
   └─────────┘   └───────────┘    └─────────────┘   └───────────┘  └───────────┘
```

### 1. Ешелони Пам'яті (Tiers)
| Tier | Назва | Сховище | Цільовий Latency | Тип Знань |
|------|-------|---------|------------------|-----------|
| **Tier 1** | `L1_HERMES` | In-memory / `MEMORY.md`, `USER.md` | **< 5ms** | Незмінні правила, інваріанти, персоналізований стиль користувача |
| **Tier 2** | `L2_SCONES` | JSON Dual-Write / pgvector | **< 20ms** | Епізодичні навички, дистиляція помилок (`Error Distillation`) |
| **Tier 3** | `L3_SCONES` | Векторний індекс із часовим згасанням | **< 50ms** | Довготривалий асоціативний контекст, патерни завдань |
| **Tier 4** | `OBSIDIAN_VAULT` | Markdown `./docs/notes/` | **< 30ms** | ADR, системні специфікації, Canvas-архітектура |
| **Tier 5** | `SESSION_FTS5` | SQLite FTS5 (`~/.hermes/state.db`) | **< 30ms** | Історія діалогів, команди та логи попередніх сеансів |

---

### 2. Інтелектуальний Каскадний Роутинг (Intent-Driven Routing)
Брокер аналізує запит через евристичний токенний класифікатор намірів (`MemoryIntent`) менш ніж за 1 мс:

1. **`INVARIANT`** (`правило`, `інваріант`, `preference`, `стиль`):
   - **Пріоритет**: `L1_HERMES -> L2_SCONES -> OBSIDIAN_VAULT`
   - Якщо в L1 знайдено відповідність з високим скором (≥ 0.70), спрацьовує **Early-Exit**: нижчі повільні рівні не опитуються взагалі. Затримка: **< 2ms**!
2. **`ERROR_SOLUTION`** (`error`, `traceback`, `exception`, `помилка`, `crash`, `500`):
   - **Пріоритет**: `L2_SCONES (Error Distillation) -> L3_SCONES -> OBSIDIAN_VAULT`
   - Миттєво знаходить готові рецепти виправлення без повторного дебагу.
3. **`ARCHITECTURE`** (`architecture`, `adr`, `blueprint`, `canvas`, `дизайн`, `специфікація`):
   - **Пріоритет**: `OBSIDIAN_VAULT -> L2_SCONES -> L1_HERMES`
   - Сканує YAML Frontmatter (теги, заголовки) та вміст нотаток, генеруючи релевантний сніппет.
4. **`CONVERSATION`** (`session`, `yesterday`, `минулий`, `сесія`, `що ми робили`):
   - **Пріоритет**: `SESSION_FTS5 -> L2_SCONES`
   - Виконує повнотекстовий FTS5-пошук у таблиці повідомлень SQLite з безпечним екрануванням спецсимволів.
5. **`COMPREHENSIVE`**:
   - Каскадний пошук за всіма рівнями з Rank Fusion та раннім виходом при досягненні високої впевненості.

---

### 3. Автоматичне Зворотне Поширення Знань (Dialogue Backpropagation)
Метод `consolidate_dialogue_to_long_term(summary)` вирішує проблему втрати знань між діалогами:
- **Нові інваріанти** (`new_invariants`) автоматично зберігаються в L1 Hermes (`MEMORY.md`).
- **Виправлені помилки** (`solved_errors`) передаються в базу `Error Distillation` L2 SCONES.
- **Прийняті архітектурні рішення** (`architectural_decisions`) фізично створюються як нові markdown-нотатки в `docs/notes/` з валідними MRH-заголовками та YAML frontmatter.

---

### 4. RAG-First Context Compaction
Метод `format_rag_context(query, max_tokens=1500)` формує чистий XML-блок:
```xml
<memory-context>
[System note: Unified Memory Broker context retrieved across tiers (Intent: ARCHITECTURE, Latency: 2.1ms)]
[Vault:Obsidian] (Title: 016 Unified Swarm Control Plane..., Score: 0.95)
...
[L2:SCONES] (Topic: FastAPI Router Patterns, Score: 0.88)
...
</memory-context>
```
Це позбавляє агента необхідності читати файли цілком з нуля і захищає від роздування контексту.

---

## 🧪 Результати Верифікації
- **Тестовий набір**: `core/tests/test_unified_memory_broker.py`
- **Кількість тестів**: 10 passed in 0.53s (100% Green)
- **Спільний прогін із модулями SCONES та трансплантації**:
  `pytest core/tests/test_scones_memory.py core/tests/test_memory_transplant.py core/tests/test_unified_memory_broker.py`
  - **15 passed in 0.25s (100% Green)**.
- **Тести Control Plane рою**:
  `pytest tests/test_swarm_control_plane.py`
  - **9 passed in 0.20s (100% Green)**.

---

## 🔗 Зв'язані Документи
- [[015 Gerych System Architecture Audit, SOTA Assimilation & Strategic Evolution Blueprint]]
- [[016 Unified Swarm Control Plane Architecture and Engine Consolidation]]
- [[000 DNK HUB Index]]
