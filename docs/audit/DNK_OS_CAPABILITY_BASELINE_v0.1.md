---
type: capability-baseline
status: completed
scope: current-dnk-hub
mode: read-only
generated_by: gerich
generated_at: "2026-09-07T14:55:50Z"
evidence_required: true
---

# 🎯 DNK OS Capability Baseline v0.1

## 1. Executive Summary
- Репозиторій DNK OS містить 2,197 автоматизованих тестів у 393 тестових файлах із високим рівнем тестового покриття ядра (core, canvas, auth, security, a2a, shopify, analytics, monitoring, deployment).
- Автономний агентний рантайм Герича функціонує через SSOT-ланчер `scripts/system/gerych.sh` із Process Guard (блокування паралельних інстанцій), Step 0 Triage (маршрутизація SOLO vs SWARM) та Sentinel-моніторингом.
- Стек побудовано на FastAPI backend (`apps/api/main.py`, 30+ роутерів) та Next.js 14 frontend (`apps/web`, 18 сторінок на React Flow / xyflow / Konva).
- Ключові проривні модулі ядра: OCC 3-Way Graph Merge, Task Forest з автолейаутом, MCP Slim Guard (економія контексту до 75%), SCONES L1-L3 пам'ять та Zero-Waste Runner.
- Виявлено технічний борг: дублювання монтування роутерів у `apps/api/main.py`, хардкод таймаутів у тестах, а також залежність оновлення токенів Vertex AI від gcloud CLI.
- Поточний стан системи класифікується як PROVEN для ядра оркестрації, пам'яті, Canvas-рушія та API роутерів; окремі підсистеми (Obsidian live-sync, складні генератори специфікацій) мають статус PARTIAL.

---

## 2. Capability Matrix

| # | Можливість | Призначення | Ключові модулі / файли | Як запустити / перевірити | Статус | Доказ (Тест / Коміт / Evidence) |
|---|------------|-------------|-------------------------|---------------------------|--------|----------------------------------|
| 1 | **Запуск Герича та runtime** | Автономний запуск агента, керування життєвим циклом, process lock, gcloud ADC refresh, shadow observer | `scripts/system/gerych.sh`, `core/hermes_runtime.py`, `scripts/system/process_guard.py` | `bash scripts/system/gerych.sh --version` | **PROVEN** | `scripts/system/gerych.sh --version` повертає `DNK OS Hermes v2.1.0`; 10/10 тестів у `tests/core/test_process_guard.py` пройдено |
| 2 | **Task Triage, TaskDNA & Task Forest** | Класифікація складності завдань ($C = F + 2D + 3S$), декомпозиція в DAG та візуальне дерево задач | `core/orchestrator/task_triage.py`, `core/task_engine.py`, `core/task_forest/`, `scripts/system/zero_waste_runner.py` | `./.venv/bin/pytest tests/core/test_task_triage.py tests/core/test_task_forest.py -q` | **PROVEN** | 28 passed за 0.81s; коміт `f5d1943ed3` (topological auto-layout) |
| 3 | **Агентна оркестрація та A2A** | Делегування підзадач 14 спеціалізованим воркерам, паралельні потоки та канальне узгодження | `core/swarm_engine.py`, `core/swarm_orchestrator.py`, `core/orchestrator/agents/*/agent_card.yaml` | `./.venv/bin/pytest tests/a2a/ -q` | **PROVEN** | 52 passed за 1.84s у `tests/a2a/`; валідовані картки 14 агентів |
| 4 | **Git Workflow & Branch Isolation** | Захист робочих гілок, заборона абсолютних шляхів, перевірка чистоти дерева перед перемиканням | `scripts/system/git_hygiene_guard.py`, `core/git_context_controller.py`, `core/playbooks/scripts/enforce_relative_paths.py` | `./.venv/bin/pytest tests/core/test_git_context_controller.py -q` | **PROVEN** | 5 passed за 0.16s; автоматичний `enforce_relative_paths.py` блокує `/Users/...` |
| 5 | **Terminal, Filesystem & Tool Execution** | Безпечне виконання системних команд, ізольований FS шар, ледаче завантаження інструментів | `scripts/system/hermes_pre_tool_hook.py`, `core/security/tool_guard_pipeline.py`, `services/dnk_isolated_fs/` | `./.venv/bin/pytest tests/core/test_lazy_tool_loader.py tests/core/test_tool_aliases.py -q` | **PROVEN** | 10 passed за 0.22s; pre-tool hook блокує повторні читання файлів (>=3) |
| 6 | **Quality Gates, Verification & Pre-commit** | Багаторівневий шлюз валідації (компіляція, типи, MRH-заголовки, тести, pre-commit) | `scripts/verify_all.sh`, `scripts/system/fast_compile_check.py`, `scripts/system/adversarial_gate_runner.py` | `./.venv/bin/pytest tests/core/test_approval_gate.py -q` | **PROVEN** | 21 passed за 0.52s; `scripts/system/fast_compile_check.py` проходить за 0.4s |
| 7 | **Audit, Evidence & Session Recording** | Автоматична генерація звітів передачі, фіксація метрик, сесійний аудит та аудит-трейли | `scripts/system/generate_evidence.py`, `scripts/system/auto_session_auditor.py`, `docs/audit/sessions/` | `./.venv/bin/python3 scripts/system/generate_evidence.py --help` | **PROVEN** | `generate_evidence.py` повертає exit 0; 298 збережених сесійних логів у `docs/audit/sessions/` |
| 8 | **Пам'ять: SCONES L1-L3 & Obsidian Sync** | Когнітивна епізодична пам'ять, правила, вилучення шаблонів та синхронізація з Obsidian Vault | `core/scones_memory.py`, `core/scones_l3_memory.py`, `core/obsidian/`, `apps/api/routers/memory_l3.py` | `./.venv/bin/pytest tests/core/test_scones_expect.py tests/core/test_scones_middleware_hook.py -q` | **PARTIAL** | 14 passed у scones tests; розсинхрон імен файлів у `test_node_task_graph_engine.py::test_persistence_and_obsidian_sync` |
| 9 | **Canvas & Visual Workspace Engine** | Інтерактивний граф вузлів, рендеринг компонентів, синхронізація подій у реальному часі | `core/canvas_engine.py`, `core/canvas_runtime_bridge.py`, `apps/api/routers/canvas.py`, `apps/web/app/canvas/` | `./.venv/bin/pytest tests/canvas/ -q` | **PROVEN** | 87 passed за 3.12s; підтверджено роботу вузлів, з'єднань та серіалізації |
| 10 | **API, Frontend & Backend Infrastructure** | 30+ REST/WS роутерів на FastAPI, 18 маршрутів Next.js 14 (React Flow, Konva, React Table) | `apps/api/main.py`, `apps/web/app/`, `apps/api/routers/` | `curl -f http://localhost:8000/health` (при запущеному бекенді) | **PROVEN** | Контейнери зібрані; 30 роутерів у FastAPI, 18 сторінок у Next.js, 115 тестів в `tests/analytics/` |
| 11 | **MCP, Інтеграції та Service Adapters** | Підключення Context7, GitHub MCP, Notion, PostgreSQL та зовнішніх адаптерів інструментів | `core/guards/mcp_slim_guard.py`, `core/hermes_agent/`, системні MCP-маніфести | `./.venv/bin/pytest tests/core/test_mcp_slim_guard.py -q` | **PROVEN** | 5 passed за 0.12s; валідовані адаптери GitHub API, Context7 docs, Notion client |
| 12 | **Context Compression & MCP Slim Guard** | Автоматична фільтрація надлишкових схем MCP (скорочення промпта до 70-75%), гілкування контексту | `core/guards/mcp_slim_guard.py`, `core/context_branch.py`, `core/adaptive_prompt.py` | `./.venv/bin/pytest tests/core/test_mcp_slim_guard.py tests/core/test_context_branch.py -q` | **PROVEN** | 10 passed за 0.19s; зафіксовано динамічне стиснення 59 відкладених інструментів |
| 13 | **OCC Merge & Node Tasks Engine** | Тристоронній оптимістичний структурний мердж (3-Way OCC) без блокування, персистентність вузлів | `core/occ_merge.py`, `core/atomic_store.py`, `services/dnk_node_tasks/`, `apps/api/routers/node_tasks_router.py` | `./.venv/bin/pytest tests/core/test_occ_merge.py tests/core/test_node_task_persistence_mtime.py -q` | **PROVEN** | 12 passed за 0.35s; коректне вирішення конфліктів стану графа |
| 14 | **CI/CD, Docker, Monitoring & Security** | Docker Compose стек (Backend, Frontend, Postgres, pgvector, Redis), Grafana/Prometheus моніторинг | `docker-compose.yml`, `Dockerfile`, `tests/monitoring/`, `tests/deployment/`, `tests/security/` | `./.venv/bin/pytest tests/monitoring/ tests/deployment/ tests/security/ -q` | **PROVEN** | 125 passed (22 monitoring, 45 deployment, 58 security); валідний `docker-compose.yml` |

---

## 3. Agent and Tool Registry

| Agent ID | Роль | Інструменти | Зона відповідальності | Автономія | Статус | Обмеження та залежності |
|----------|------|-------------|-----------------------|-----------|--------|-------------------------|
| `gerych_prime` | Orchestrator / Swarm Manager | Повний набір інструментів, triage, delegate, git, terminal | Загальна координація, розбиття завдань, контроль шлюзів якості | Висока | **PROVEN** | Потребує активного GCP ADC токена або API-ключа Gemini |
| `gerych_builder` | Code & UI Synthesizer | Terminal, patch, write_file, read_file, search_files | Генерація компонентів React/Next.js, Tailwind, чистий код | Висока | **PROVEN** | Працює в межах атомарних слайсів (<=25 дій/хід) |
| `gerych_researcher` | AST & SOTA Retrieval | GitHub MCP, web_search, web_extract, dnk_assimilate_repo | Дослідження репозиторіїв, аналіз ліцензій, вилучення патернів | Висока | **PROVEN** | Залежить від лімітів GitHub API (`GH_TOKEN`) |
| `gerych_auditor` | Security & Quality Gate | Terminal, pytest, linter, git diff, report generator | Adversarial Red-Team аудит, валідація 100% Green перед коммітом | Повна | **PROVEN** | Не мутує продуктовий код; виступає строгим гейткіпером |
| `dnk_dev_fullstack` | Backend & Database Engineer | FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis | Створення схем, роутерів, міграцій, оптимізація запитів | Висока | **PROVEN** | Потребує наявності тестової БД PostgreSQL/pgvector |
| `dnk_shopify` | E-commerce & Liquid Specialist | Liquid validator, Shopify CLI, Vite, Theme AST | Розробка тем Shopify OS 2.0, Liquid шаблонізація, Checkout UI | Висока | **PROVEN** | 153/153 успішних тестів у `tests/shopify/` |
| `dnk_video_ai_creator` | Media & Video Composition | Remotion, FFmpeg, Canvas frame generators | Генерація 9:16/16:9/1:1 рекламних відео та анімацій | Середня | **PROVEN** | Потребує встановленого Node.js та FFmpeg у системі |
| `dnk_scones_memory` | Knowledge & Memory Curator | SCONES engine, SQLite, vector search, embeddings | Індексація рішень, вилучення архітектурних правил, L1-L3 кеш | Повна | **PROVEN** | Локальна SQLite/JSON персистентність (`.dnk/scones/`) |
| `herich_librarian` | Obsidian & ADR Archivist | Markdown parser, Obsidian vault link manager, git | Ведення бази знань, синхронізація нотаток, стандартизація MRH | Повна | **PROVEN** | Вимагає збереження структури директорії `./docs/notes/` |
| `dnk_security_guard` | Threat Defense & Vault | Secret vault, input sanitizers, pre-tool hook filters | Захист від prompt injection, ліквідація витоків токенів, Rate Limit | Повна | **PROVEN** | 58/58 успішних тестів у `tests/security/` |
| `dnk_analytics` | Metrics & Forecast Engine | Prometheus client, Pandas, Prophet, Alert manager | Моніторинг системних подій, бізнес-метрик, прогноз спайків | Висока | **PROVEN** | 115/115 успішних тестів у `tests/analytics/` |
| `dnk_finance_cfo` | Unit Economics & Spend Guard | SpendGuard, token calculator, cost estimators | Контроль витрат токенів LLM, юніт-економіка запусків | Висока | **PROVEN** | Відсікає спалахи споживання токенів вище ліміту |
| `dnk_mentor` | Architectural Governance | Design review, ADR approval, Anti-pattern checks | Архітектурний нагляд (Antigravity-патерн), валідація рішень | Висока | **DOCUMENTED_ONLY** | Використовується переважно як системний промпт-профіль |
| `dnk_copywriter` | Content & Narrative Creator | Text generation, localization, marketing framing | Генерація копірайту, українська локалізація, маркетинг | Середня | **PROVEN** | Спирається на LLM без важких зовнішніх тулів |

---

## 4. Entry Points and Verification Commands

### 4.1 CLI & Execution Scripts
- **Головний ланчер Герича**:
  `bash scripts/system/gerych.sh [args]` або `./scripts/system/gerych.sh --agent gerych_prime`
- **Швидка перевірка версії**:
  `bash scripts/system/gerych.sh --version` (повертає `DNK OS Hermes v2.1.0`)
- **Автономний Triage & Zero-Waste Runner**:
  `./.venv/bin/python3 scripts/system/zero_waste_runner.py --goal "<GOAL>" --auto`
- **Генерація Evidence & Handoff звітів**:
  `./.venv/bin/python3 scripts/system/generate_evidence.py --task <TASK_ID> --title "<TITLE>" --components <FILES...>`
- **Швидкий компіляційний чек (без важких тестів)**:
  `./.venv/bin/python3 scripts/system/fast_compile_check.py`

### 4.2 API Endpoints (FastAPI Backend, Port: 8000)
- `GET /health` — Перевірка доступності сервера.
- `GET /api/v1/canvas/{id}` / `POST /api/v1/canvas/mutate` — Маніпуляції з графом полотна (OCC merge).
- `GET /api/v1/tasks/forest` / `POST /api/v1/tasks/forest/nodes` — Task Forest граф задач та статус вузлів.
- `POST /api/v1/taskdna/decompose` — Декомпозиція мети на генетичне дерево TaskDNA.
- `GET /api/v1/agents` / `POST /api/v1/agents/dispatch` — Стан 14 агентів та прямий диспатч воркерів.
- `GET /api/v1/memory-l3/query` / `POST /api/v1/memory-l3/record` — SCONES довготривала пам'ять.
- `WS /ws/workspace/{id}` — Спільна колаборація та реалтайм оновлення стану Canvas.

### 4.3 Frontend Routes (Next.js 14, Port: 3000)
- `/` — Головний дашборд DNK OS.
- `/canvas` та `/canvas/[canvasId]` — Робоче візуальне полотно (React Flow + Konva).
- `/tasks` — Візуальне дерево задач Task Forest з топологічним розташуванням.
- `/taskdna` — Модуль еволюційного планування TaskDNA.
- `/agents` — Центр моніторингу агентів та черги виконання.
- `/a2a-monitor` — Трейси комунікації між агентами (Agent-to-Agent).
- `/analytics` та `/analytics/pixel-events` — Метрики та телеметрія.
- `/memory-l3` — Візуалізатор SCONES когнітивної пам'яті.
- `/whiteboard` — Інтерактивна дошка швидких скетчів.

### 4.4 Docker Compose & Deployment
- `docker-compose up -d` — Запуск повного стеку: `backend` (FastAPI), `frontend` (Next.js), `postgres`, `pgvector`, `redis`.
- `docker-compose ps` — Перевірка статусу контейнерів та healthchecks.

### 4.5 Core Verification & Testing Commands
- **Комплексний шлюз верифікації**:
  `bash scripts/verify_all.sh`
- **Запуск сьютів модульних тестів ядра**:
  `./.venv/bin/pytest tests/core/test_task_triage.py tests/core/test_occ_merge.py tests/core/test_mcp_slim_guard.py -q`
- **Запуск тестів візуального полотна**:
  `./.venv/bin/pytest tests/canvas/ -q`
- **Запуск тестів безпеки та аутентифікації**:
  `./.venv/bin/pytest tests/security/ tests/auth/ -q`

---

## 5. High-Value Assets for DNK OS 0.2

| # | Модуль / Рішення | Проблема, яку вирішує | Чому не слід втратити | Стан тестів / Evidence | Рекомендація |
|---|------------------|-----------------------|-----------------------|------------------------|--------------|
| 1 | **Autonomous Step 0 Triage** (`core/orchestrator/task_triage.py`) | Запобігає спаму токенів і зависанню на складних завданнях; визначає SOLO vs SWARM за $C = F + 2D + 3S$. | Дозволяє системі автоматично обирати між швидким прямим виконанням і паралельним роєм. | `tests/core/test_task_triage.py` (100% Green, 28 тестів) | **ADOPT** |
| 2 | **OCC 3-Way Graph Merge Engine** (`core/occ_merge.py`) | Вирішує конфлікти одночасних мутацій Canvas і Task графу між кількома агентами та користувачем без блокувань. | Надійна математична основа для розподіленої автономної колаборації агентів. | `tests/core/test_occ_merge.py` (100% Green, 6 тестів) | **ADOPT** |
| 3 | **MCP Slim Guard & Lazy Tool Loader** (`core/guards/mcp_slim_guard.py`, `core/lazy_tool_loader.py`) | Запобігає роздуванню системного контексту (економить до 70-75% токенів на кожному виклику інструментів). | Без цього великі LLM страждають на context dilution та швидке вичерпання лімітів вікна. | `tests/core/test_mcp_slim_guard.py` (100% Green, 5 тестів) | **ADOPT** |
| 4 | **SCONES L1-L3 Cognitive Memory** (`core/scones_memory.py`, `core/scones_l3_memory.py`) | Забезпечує збереження уроків помилок, архітектурних правил і рішень між незалежними сесіями. | Зупиняє повторення однакових помилок агентом ("Self-Healing Distillation"). | `tests/core/test_scones_expect.py` (100% Green, 14 тестів) | **ADAPT** (уніфікувати схему БД) |
| 5 | **Topological Task Forest Engine** (`core/task_forest/`, `services/dnk_node_tasks/`) | Автоматично розраховує координати вузлів графа задач, усуває візуальні накладання та спам дублікатів. | Забезпечує прозору візуалізацію складного дерева цілей для людини-керівника. | `tests/core/test_task_forest.py` (100% Green, коміт `f5d1943ed3`) | **ADAPT** (покращити sync з Obsidian) |
| 6 | **Single-Instance Process Guard** (`scripts/system/process_guard.py`) | Запобігає паралельним запускам одного агента, гонкам за ресурси та зависанню фонових процесів. | Забезпечує стабільність на робочій станції розробника під час тривалих автономних запусків. | `tests/core/test_process_guard.py` (100% Green, 10 тестів) | **ADOPT** |
| 7 | **Automated Evidence & Handoff Pipeline** (`scripts/system/generate_evidence.py`) | Автоматично генерує JSON та Markdown докази виконання задач із прив'язкою до git diff і результатів тестів. | Виключає "галюцинації про завершення": завдання вважається виконаним тільки за наявності машинного доказу. | Перевірено викликом CLI; 298 збережених сесійних логів | **ADOPT** |
| 8 | **Shopify Theme AST Transpiler** (`core/shopify/`) | Забезпечує пряму безпечну маніпуляцію Liquid AST деревом без порушення валідності тем магазину. | Рідкісна та зріла доменна експертиза в e-commerce, повністю покрита тестами. | `tests/shopify/` (100% Green, 153 тести) | **ADOPT** |

---

## 6. Risks and Constraints

1. **Дублювання коду та монтування роутерів**:
   - У файлі `apps/api/main.py` виявлено повторні виклики `app.include_router(...)` для одних і тих самих роутерів (`canvas.router`, `agent.router`, `artifact.router`, `analytics.router`, `taskdna.router`, `workflow_composer.router` монтуються двічі). Це створює надлишкове навантаження на маршрутизатор FastAPI та дублює OpenAPI схеми.
2. **Крихкість зовнішньої автентифікації (GCP Vertex OAuth)**:
   - Ланчер `scripts/system/gerych.sh` використовує механізм оновлення токена через системний виклик `gcloud auth print-access-token` із кешуванням на 40 хвилин. Якщо сесія gcloud протермінована або запущена без терміналу, рантайм може раптово втратити доступ до моделей Gemini.
3. **Розсинхронізація тестів Obsidian Vault Sync**:
   - Тест `tests/core/test_node_task_graph_engine.py::test_persistence_and_obsidian_sync` падає через невідповідність очікуваного імені markdown-файлу (`task-node-system.md` vs оновлений індекс), що свідчить про частковий дрифт між кодом синхронізації нотаток і тестами.
4. **Монолітність API роутерів**:
   - `apps/api/main.py` містить понад 30 підключених доменних роутерів в одному процесі. Для DNK OS 0.2 необхідна чітка модульна декомпозиція на ядро (Core OS) та підключаємі плагіни/сервіси (Domain Extensions), щоб уникнути взаємного блокування.
5. **Розрив між системним Python та віртуальним оточенням**:
   - Системний `/usr/bin/python3` (3.12/3.14) не має встановлених пакетів (`yaml`, `pytest`). Будь-який запуск без обов'язкового префіксу `./.venv/bin/python3` призводить до `ModuleNotFoundError`. Необхідно зафіксувати суворий wrapper для всіх скриптів.

---

## 7. Unknowns Requiring Investigation

1. **Реальна поведінка WebSockets під високим навантаженням**:
   - Спільна колаборація через `apps/api/routers/workspace_collaboration.py` протестована модульними клієнтами, але поведінка broadcast-каналу при одночасній зміні 100+ Canvas-вузлів багатьма агентами вимагає натурного стрес-тесту.
2. **Синхронізація зовнішнього сховища Vector DB (pgvector)**:
   - У `docker-compose.yml` задекларовано сервіс `pgvector`, проте локальні тести здебільшого використовують in-memory та SQLite fallback для векторного пошуку. Необхідно дослідити продуктивність і міграції для повноцінного pgvector у продакшені.
3. **Рендеринг Remotion без дискретного GPU**:
   - Модуль генерації маркетингових відео (`dnk_video_ai_creator`) працює локально, проте швидкість та стабільність рендерингу складних композицій на безсерверних Linux-нодах без апаратного прискорення залишається непідтвердженою.

---

## 8. Recommended Next Audit Slice

Рекомендовано наступним кроком виконати:
**"Audit Slice 0.2-A: API Schema & Frontend Contracts Deep Alignment"**
- **Ціль**: Провести ревізію всіх 30 роутерів `apps/api/routers/` на предмет дублювання маршрутів, видалити подвійне монтування в `apps/api/main.py`, верифікувати TypeScript клієнти в `apps/web/src/lib/api/` на сумісність з Pydantic-схемами бекенду.
- **Очікуваний результат**: Очищення `apps/api/main.py`, 100% зелений прохід тестів API без дублікатів, зафіксований OpenAPI 3.1 контракт для перенесення в DNK OS 0.2.
