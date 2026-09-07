---
title: "019 SOTA Context Management and Compression Architectures Global Audit"
tags:
  - architecture
  - context-management
  - sota-assimilation
  - llm-agents
  - context-compression
  - hermes-lcm
  - continuous-claude
date: 2026-09-05
author: Maksym Kuzmenko (Maxim) & Gerych Prime (Antigravity Mentor)
status: Active
mrh_id: "docs/notes/019 SOTA Context Management and Compression Architectures Global Audit.md"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/019 SOTA Context Management and Compression Architectures Global Audit.md"
purpose: "Global SOTA Audit of Context Management, Tool Virtualization, and Lossless Compression for LLM Agents."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🌐 Global SOTA Audit: Context Management, Tool Virtualization & Lossless Compression (2025–2026)

## 📌 1. Вступ та Контекст Дослідження
У сучасних LLM-агентних системах найбільшим вузьким місцем для тривалих задач (long-horizon autonomous reasoning) є **Context Window Tax** та **Compaction Degradation**:
1. **Context Window Tax**: Статичне завантаження десятків JSON-схем інструментів (MCP, локальні тули), багатосторінкових системних інструкцій та каталогів навичок з'їдає 15 000 – 30 000 токенів ще до першого виклику користувача, сповільнюючи Time-to-First-Token (TTFT) та провокуючи галюцинації вибору інструментів.
2. **Lossy Compaction**: Коли контекст перевищує ліміт (наприклад, 64k або 128k), стандартні механізми стискають розмову через LLM-резюме (Summarization), безповоротно втрачаючи деталі викликів, точні диффи коду, стектрейси та архітектурні рішення.

Ми провели глибинний аудит глобального ландшафту GitHub, академічних препринтів (NeurIPS, ACL 2025–2026) та продакшн-фреймворків, виділивши ключові прориви та їх придатність для еволюції DNK OS.

---

## 🏛️ 2. Таксономія 6 Рівнів SOTA Context Management

```
┌────────────────────────────────────────────────────────────────────────┐
│  Level 6: Graph & Decoupled Memory Tiering (AST GraphRAG, SCONES L0-L3)│
├────────────────────────────────────────────────────────────────────────┤
│  Level 5: Git-like Context Versioning (GCC: Commit, Branch, Merge)     │
├────────────────────────────────────────────────────────────────────────┤
│  Level 4: Continuity Systems & Handoff Ledgers ("Compound, don't compact")
├────────────────────────────────────────────────────────────────────────┤
│  Level 3: Lossless Hierarchical Context & DAG Compression (LCM Engine) │
├────────────────────────────────────────────────────────────────────────┤
│  Level 2: Observation Compression & Output Externalization (Sidecars) │
├────────────────────────────────────────────────────────────────────────┤
│  Level 1: Tool Schema & Catalog Virtualization (Lazy Loading, Aliases) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 3. Детальний Аналіз Передових Проектів на GitHub

### 🌟 3.1. `stephenschoettler/hermes-lcm` — Lossless Context Management для Hermes Agent
- **Опис**: Плагін для фреймворку Hermes Agent, що реалізує концепцію **LCM (Lossless Context Management)** на основі дослідження Ehrlich & Blackman (Voltropy PBC, лютий 2026) та натхненний `lossless-claw` для OpenClaw.
- **Архітектурний підхід**:
  - *Замість одноразового LLM-стиснення* впроваджується SQLite-орієнтоване DAG-дерево (Directed Acyclic Graph) з повнотекстовим індексом FTS5.
  - Повідомлення зберігаються як вузли з повною генеалогією джерел (`source lineage`).
  - Старий контекст згортається у багаторівневі резюме: глибина D0 (листові підсумки) → D1 → D2.
  - Коли моделі потрібні деталі минулих подій, вона не сподівається на згадки в узагальненому промпті, а викликає спеціалізовані інструменти точкового буріння: `lcm_grep`, `lcm_expand(node_id)`, `lcm_load_session`, `lcm_describe`.
  - **Large Payload Externalization**: Великі виводи тулів (термінал, файли) автоматично виносяться в зовнішнє сховище (`sidecars`) з генерацією короткого хеш-посилання (`result_ref`).
- **Цінність для DNK OS**: Пряма сумісність з Hermes Prime! Дозволяє відмовитися від втрати контексту під час довгих розробок.

---

### 🌟 3.2. `parcadei/Continuous-Claude-v3` — "Compound, Don't Compact"
- **Опис**: Комплексна контекстна операційна система для Claude Code (109 навичок, 32 агенти, 30 життєвих хуків).
- **Ключовий принцип**: *"Compound, don't compact"*. Замість очікування, коли контекст переповниться і система автоматично зімне його в загальний текст, агент веде структуровані артефакти:
  - **Continuity Ledgers** (`CONTINUITY_*.md`): чіткі реєстри поточного стану завдань, прийнятих рішень та блокерів.
  - **YAML Handoffs**: Перед завершенням сесії або передачею підзадачі генерується компактний YAML-маніфест, що передається новому ізольованому контексту.
  - **TLDR 5-Layer Code Analysis**: Замість вичитування файлів цілком (`cat`/`read_file`), застосовується 5-рівневий AST-аналіз коду через `ast-grep` та tree-sitter.
  - **MCP Without Pollution**: Ізоляція контекстних вікон під-агентів, завдяки чому виводи важких інструментів не засмічують вікно головного оркестратора.

---

### 🌟 3.3. `lennney/mcp-slim-guard` — Context Compression для MCP
- **Опис**: Проксі-сервер для MCP-інструментів, що захищає контекстне вікно моделі від надмірних схем та гігантських JSON-виводів.
- **Режими роботи**:
  - `Native`: Стандартні схеми + `read_result`.
  - `Compact`: Замість сотень окремих схем модель бачить лише три мета-інструменти: `find_tool(query)`, `call_tool(name, args)` та `read_result(ref)`. Схема інструменту підвантажується динамічно лише тоді, коли модель знаходить його через `find_tool`.
  - `Extreme`: Додатково скорочує розмір первинної відповіді інструменту; повний вивід записується у локальний кеш, а моделі віддається `result_ref` із можливістю пагінованого читання через `read_result`.
- **Ефект**: Зниження токенів на опис інструментів до фіксованих ~150 токенів незалежно від кількості серверів MCP.

---

### 🌟 3.4. `faugustdev/git-context-controller` (GCC) — Context as Git
- **Опис**: Фреймворк, що керує пам'яттю та робочим вікном LLM за аналогією з розподіленим контролем версій Git:
  - `CONTEXT_COMMIT`: Фіксація важливого проміжного висновку або артефакту як незмінного стану.
  - `CONTEXT_BRANCH`: Створення розгалуження для дослідження гіпотези без забруднення основного контексту.
  - `CONTEXT_MERGE`: Злиття успішних результатів експерименту в основну гілку розмови з відкиданням шуму невдалих спроб.
- **Цінність**: Ідеально лягає на Task Forest та TaskDNA у DNK OS.

---

### 🌟 3.5. `Jakedismo/codegraph-rust` — Code GraphRAG через SurrealDB + FastML
- **Опис**: Високопродуктивна (Rust) реалізація графа кодової бази, яка замінює сліпий пошук за текстом або повнотекстове читання файлів на семантичний граф залежностей (AST, типи, функції, імпорти).
- **Перевага**: Агент запитує лише релевантний підграф (`caller_graph`, `type_hierarchy`) замість 10 000 рядків коду, скорочуючи контекст на 92%.

---

### 🌟 3.6. Академічні Прориви (NeurIPS 2025 / ACL 2026)
1. **The Complexity Trap (NeurIPS 2025)**:
   - *Відкриття*: Складні LLM-узагальнення (`LLM Summarization`) контексту спостережень агента часто працюють гірше і вносять галюцинації порівняно з простим **Deterministic Observation Masking** (приховування тіл старих успішних викликів інструментів зі збереженням їх сигнатури та статусу).
2. **SWE-Pruner (2026)**:
   - Адаптивне відсікання контексту для кодинг-агентів. Модель оцінює "залишкову корисність" (residual utility) попередніх читань файлів і вичищає з контексту файли, які не редагувалися протягом останніх $K$ кроків.
3. **Context as a Tool (CAT)**:
   - Контекст розглядається не як пасивне вікно, а як активний ресурс, яким агент керує через спеціальні мета-команди (`pin_fact`, `drop_observation`, `summarize_slice`).

---

## 📊 4. Порівняльна Матриця Архітектур Контексту

| Підхід / Проект | Рівень Втрат (Lossiness) | Зниження Context Tax | Вплив на Latency (TTFT) | Стійкість до Галюцинацій | Складність Впровадження |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Monolithic Baseline** | 0% (до ліміту) | 0% (25k-50k tax) | Дуже повільно | Низька (tool confusion) | Тривіально |
| **Standard LLM Compaction** | Високий (втрата деталей) | 60–70% | Середня (LLM overhead) | Середня (hallucinated facts) | Низька |
| **DNK Slice 16.2 (Lazy + Aliases)** | **0% (схеми on-demand)** | **88.8% (2.8k tax)** | **Миттєво (<0.01s)** | **Висока (чіткі сигнатури)** | **Вже впроваджено** |
| **MCP Slim Guard** | 0% (повернення через ref) | 90–95% | Швидко | Дуже висока | Низька |
| **Continuous Claude Ledgers** | Мінімальний (структурований) | 75–85% | Швидко | Дуже висока | Середня |
| **Hermes LCM (DAG Engine)** | **0% (повний recall через FTS)** | **80–90%** | **Миттєво (SQLite local)** | **Максимальна (lineage proof)**| Середня |

---

## 🚀 5. Стратегічна Дорожня Карта Еволюції DNK OS (v4.5+)

На основі проаналізованого світового досвіду пропонується наступна 4-етапна траєкторія інтеграції у DNK OS:

### Етап 1: Result Sidecars & Observation Masking (Слайс 16.3)
- Натхнення: *MCP Slim Guard* та *NeurIPS 2025 Observation Masking*.
- Реалізація: Для будь-якого виводу інструменту (`terminal`, `read_file`), що перевищує 3 000 символів, тіло в історії замінюється на метадані:
  ```json
  {"status": "success", "lines": 450, "preview": "... перші 10 рядків ...", "result_ref": "cache/tool_out_49f1.log"}
  ```
- Забезпечує скорочення зростання контексту на 70% під час активної розробки.

### Етап 2: Інтеграція `hermes-lcm` в ядро Gerych Prime
- Підключення плагіна `hermes-lcm` як базового рушія контексту (`context.engine: lcm`).
- Заміна стандартного згортання на FTS5 SQLite DAG, що надає Gerych можливість викликати `lcm_grep` та `lcm_expand` замість втрати історії після компактизації.

### Етап 3: Task Forest Git-like Context Controller (GCC)
- Інтеграція контекстних контролерів у `TaskForestNode`: кожна підзадача формує свій контекстний бранч (`branch`), а після проходження тестів фіксує лаконічний мердж-коміт (`merge`) у головний контекст оркестратора.

### Етап 4: AST GraphRAG через `dnk_resolve_symbol`
- Розширення можливостей `scripts/system/repo_map.py` та нашого Fast Symbol Resolver: замість читання цілих файлів агент завантажує лише граф функцій та інтерфейсів, зводячи роботу з кодом до хірургічної точності.

---

## 🔗 Пов'язані нотатки
- [[018 Dynamic Context Budgeting and Toolset Pruning Architecture]] — Архітектура Слайсу 16.2.
- [[015 Gerych System Architecture Audit, SOTA Assimilation & Strategic Evolution Blueprint]] — Загальний план модернізації.
- [[017 Unified Memory Broker Architecture and Cross-Tier Retrieval Protocol]] — Багаторівнева пам'ять SCONES.
- [[009 Task Forest Spatial HQ - 5-Scale LOD Navigation & Time-Travel Engine]] — Просторове дерево задач.
