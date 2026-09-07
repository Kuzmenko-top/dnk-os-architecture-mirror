# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/ai_native_sdlc/RN-003_claude_code_intent_md_and_ai_native_sdlc_audit.md"
# purpose: "Comprehensive Technical Audit of Anthropic's AI-Native SDLC Playbook, intent.md Artifact Chain, and SOTA GitHub Assimilation Plan."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-SDLC-INTENT-ASSIMILATION", "TASK-SWARM-WORKTREE-ISOLATION"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🔬 RN-003: Claude Code AI-Native SDLC, INTENT.MD Architecture & SOTA GitHub Discovery Strategy

## 📋 1. Executive Summary & Paradigm Shift

**Source Video Analyzed**: [Claude Codes New INTENT.MD, What is It?](https://www.youtube.com/watch?v=LoMOPj-lO8U) (Rob Shocks, Switch Dimension).  
**Primary Canonical Source**: Anthropic Official Playbook: *The AI-Native SDLC Playbook* (by Boris Cherny & Anthropic Engineering, 2026).

### 💡 Core Thesis: "Code Is No Longer The Bottleneck — Your Process Is"
У класичному життєвому циклі розробки ПЗ (SDLC: Plan ➔ Design ➔ Build ➔ Test ➔ Deploy ➔ Maintain) етап **Build** (написання коду) займав до 70% часу та бюджету. З приходом автономних кодинг-агентів (Claude Code, Hermes Prime, Cursor) вартість і час генерації коду стиснулися в 5–10 разів. 

У результаті виник гострий дисбаланс: **вузьке горло (bottleneck) змістилося ліворуч (Planning & Spec) та праворуч (Testing, Code Review, Security Gates, Maintenance)**. Спроба використовувати традиційні 2-тижневі спринти, ручні PRD, наради та ручний line-by-line code review для коду, згенерованого за лічені хвилини — це «встановлення реактивного двигуна на кінний візок».

---

## 🏛️ 2. The Artifact Chain: The Golden Thread of AI-Native SDLC

Anthropic та передові автори формалізують парадигму **Golden Thread** (Золота Нить) — нерозривний ланцюг машиночитних та людинозрозумілих артефактів, де кожен наступний крок детерміністично випливає з попереднього:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE ARTIFACT CHAIN (GOLDEN THREAD)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. INCEPTION / DISCOVERY:                                                   │
│    Originator (Human/Agent) ──[Interview Q&A Loop]──> intent/*.intent.md    │
│    - Pain points, business value, constraints, non-goals, user journeys     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DESIGN & SPECIFICATION:                                                  │
│    intent.md + [skills/ + agents.md + standards] ──> specs/spec.md          │
│    - Architecture, data models, API contracts, bounded context units        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. BUILD / CONSTRUCTION PLANNING:                                           │
│    spec.md ──[Interrogation: "What could break?"]──> plans/plan.md          │
│    - Self-contained task DAG, file lists, blast radius, proof criteria      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. EXECUTION IN BOLTS (SWARM PARALLEL):                                     │
│    plan.md ──[Git Worktrees + Subagents]──> Code & Tests                    │
│    - Test-first invariants, hooks blocking test tampering                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. VERIFICATION & GATE AUDITING:                                            │
│    Automated Tests + Playwright/Headless Browser ──> evidence/evidence.json │
│    - Zero prose without proof; deterministic verification                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. ASYNC DEPLOY & AGENT REVIEW:                                             │
│    Agent Pull Request ──[Independent AI Auditor Review]──> REVIEW.md        │
│    - Security scan, architectural conformance, release gates                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 7. AUTONOMOUS MAINTENANCE:                                                  │
│    Sentry / Telemetry Spike / Log Alert ──> Auto-Generated intent.md        │
│    - Async diagnosis, reproduction test, self-healing fix PR                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 3. Detailed Phase Breakdown from Video & Industry Evidence

### 3.1. Phase 1: Inception & `intent.md` Discovery Phase
- **Originator Role**: Будь-який суб'єкт (продакт-менеджер, розробник, клієнт із багрепортом або автоматизований монітор).
- **Interactive Interview Loop**: Агент не просто приймає промпт — він активно проводить інтерв'ю з користувачем, ставлячи мінімум 3–5 уточнюючих запитань, виявляючи приховані припущення, крайові випадки та протиріччя (Overconfidence Prevention).
- **Сховище**: Каталог `intent/` (або `.aidlc/inception/`), наприклад `intent/dark-mode.intent.md`.
- **Властивості**: Human-readable (для валідації людиною) та Machine-actionable (для подальших пайплайнів).

### 3.2. Phase 2: Design & Spec Governance (`spec.md`)
- Автоматична генерація специфікації на основі `intent.md` за допомогою заздалегідь закодованих правил (`AGENTS.md`, `skills/`, Brand Guides).
- Розбиття на автономні доменні одиниці (DDD Bounded Context Units) для усунення переповнення контекстного вікна LLM.

### 3.3. Phase 3: Plan Mode & Self-Contained Invariant (`plan.md`)
- **Self-Contained Rule**: План повинен містити достатньо інформації, щоб будь-який ізольований субагент міг реалізувати задачу з нульовим контекстом попереднього діалогу.
- **Interrogation Step**: Обов'язкове питання перед стартом: *"What changes could break existing contracts or schemas?"*
- Структура плану:
  1. File modification list.
  2. Sequential task DAG.
  3. Risks & constraints.
  4. Deterministic proof criteria (lints, unit tests, integration tests).

### 3.4. Phase 4: Fast-Path Build Loop & Guardrails
- **Git Worktrees**: Створення окремих ізольованих робочих дерев Git під кожного паралельного агента, що виключає конфлікти у робочій копії.
- **Anti-Tampering Hooks**: Критичний механізм безпеки — заборона агенту модифікувати файли існуючих тестів під час виправлення багів (запобігає фальсифікації "green tests" через видалення асертів).
- **Subagent Division**: Розподіл завдань між спеціалізованими субагентами (UI, Backend, Security, Auditor).

### 3.5. Phase 5: Autonomous Testing & Evidence
- Заміна довгих очікувань QA автоматичними тестами: агент сам пише тести, піднімає локальний сервер, запускає Playwright/Headless Browser, робить скріншоти та валідує відповіді.
- **Continuous Evals**: Постійний набір із 20+ "золотих" реальних задач для регресійного тестування змін у промптах, скілах або оновленнях LLM-моделей.

### 3.6. Phase 6: Asynchronous PR Review & Governance Gates
- Агент створює PR у Git.
- Інший незалежний агент-аудитор перевіряє PR на відповідність політиці безпеки та архітектурним стандартам.
- Детерміністичні гейти блокують деплой без виконання критеріїв або апруву оператора.

### 3.7. Phase 7: Autonomous Maintenance (Самозцілення)
- Моніторинг виявляє аномалію (сплеск 500 помилок, падіння сервісу).
- Агент автоматично запускається, зчитує логи, генерує новий `incident-xxx.intent.md`, локалізує дефект, пише репродукційний тест і створює draft PR до того, як інженер відкриє ноутбук.

---

## ⚖️ 4. DNK OS Gap Analysis & Implementation Matrix

Порівняння наявних можливостей DNK OS / Gerych Prime з практиками AI-Native SDLC:

| Практика AI-Native SDLC | Стан у DNK OS наразі | Оцінка | Що необхідно імплементувати |
| :--- | :--- | :---: | :--- |
| **1. Intent Discovery (`intent.md`)** | Є ad-hoc діалог та `dnk_decompose_task_dna`, але відсутній формальний стандарт інтерв'ю та каталог `intent/` | 🟡 60% | Створити скіл `dnk-intent-discovery` та каталог `specs/intents/` з валідатором схеми. |
| **2. The Golden Thread Pipeline** | Є `AGENTS.md`, `generate_evidence.py`, `verify_all.sh` | 🟢 85% | Пов'язати: `intent.md` ➔ `spec.md` ➔ `plan.md` ➔ `evidence.json` через єдиний ID. |
| **3. Anti-Tampering Test Guardrail** | Pre-Tool Hook контролює циклічні читання/записи, але не блокує модифікацію тестів під час фіксів | 🔴 30% | Додати Pre-Tool Guardrail: заборона зміни файлів у `tests/` під час виконання фіксів без прапорця `--allow-test-edit`. |
| **4. Git Worktrees для Swarm** | Робота ведеться в єдиному дереві репозиторію | 🔴 20% | Реалізувати підтримку `git worktree` для субагентів (`dnk_swarm_parallel`), щоб ізолювати контексти. |
| **5. Golden Evals Suite в CI** | Тести є (`tests/test_*.py`), але відсутній benchmark на якість виконання скілів та агентських промптів | 🟡 40% | Створити `core/evals/` з 15-20 ретроспективними задачами для тестування нових моделей/скілів. |
| **6. Autonomous Maintenance Loop** | Реалізовано cronjob/watchdog механізми, але немає автоматичного генератора `intent.md` з логів | 🟡 50% | Зв'язати логгер помилок або вебхук зі скілом авто-діагностики, що створює PR. |

---

## 🚀 5. Actionable Implementation Plan for DNK OS

### Крок 1: Впровадження стандарту `DNK-STD-INTENT-001`
Створити структуру збереження бізнес-намірів:
- Директорія: `docs/intents/{INTENT_ID}_{slug}.intent.md`
- Секції:
  - `Originator` & `Date`
  - `Problem Statement & Core Value`
  - `Domain Context & User Journey`
  - `Constraints & Non-Goals`
  - `Acceptance Criteria (Measurable)`
  - `Clarification Q&A Transcript`

### Крок 2: Створення скіла `dnk-intent-discovery`
Скіл для Gerych Prime, який активується на запит створення нової фічі чи рефакторингу:
1. Задає користувачу 3-5 цільових запитань.
2. Проводить аналіз суперечностей (Contradiction Detection).
3. Зберігає фінальний узгоджений `intent.md`.
4. Автоматично викликає `dnk_decompose_task_dna` для генерації `spec.md` та `plan.md`.

### Крок 3: Захисний хук проти "зламу тестів" (Anti-Tampering Hook)
Додати у перевірки перед виконанням інструментів `patch` та `write_file`: якщо ціль — файл у `tests/` під час виконання задачі з тегом `bugfix`, вимагати явного підтвердження або блокувати зміну існуючих асертів.

---

## 🌐 6. GitHub SOTA Global Research & Assimilation Plan

План сканування відкритого коду світових рішень у GitHub за нашим **Two-Track SOTA Assimilation Protocol**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   GLOBAL SOTA GITHUB DISCOVERY MATRIX                       │
├───────────────────────────────┬────────────────────────────┬────────────────┤
│ Цільовий репозиторій / Проект │ Опис та Архітектурна цінність │ Ліцензія / Трек│
├───────────────────────────────┼────────────────────────────┼────────────────┤
│ 1. wico216/ai-sdlc            │ AI-SDLC для Claude Code:   │ MIT            │
│    (GitHub)                   │ 3 фази (Inception, Const-  │ Track 1        │
│                               │ ruction, Operations), 5 гей│ (Direct        │
│                               │ тів, Golden Thread,        │ Assimilation)  │
│                               │ Structured Questions.      │                │
├───────────────────────────────┼────────────────────────────┼────────────────┤
│ 2. ai-sdlc-framework/ai-sdlc  │ Decision Engine для        │ Apache 2.0     │
│    (GitHub / ai-sdlc.io)      │ spec-driven AI workflows,  │ Track 1        │
│                               │ Decision Catalog (RFC-35), │ (Direct        │
│                               │ DoR Gate (RFC-11).         │ Assimilation)  │
├───────────────────────────────┼────────────────────────────┼────────────────┤
│ 3. github/spec-kit            │ Офіційний Spec Kit від     │ MIT / Permiss. │
│    (GitHub)                   │ GitHub: Spec ➔ Plan ➔      │ Track 1        │
│                               │ Tasks ➔ Implement пайплайн.│ (Direct)       │
├───────────────────────────────┼────────────────────────────┼────────────────┤
│ 4. switch-dimension/          │ Репозиторій автора відео   │ MIT            │
│    molten-os-core             │ (Rob Shocks): скіли        │ Track 1        │
│    (GitHub)                   │ molten-validate, brand,    │ (Direct)       │
│                               │ design, landing.           │                │
├───────────────────────────────┼────────────────────────────┼────────────────┤
│ 5. Fission-AI/OpenSpec        │ Spec-driven development    │ MIT            │
│    (GitHub)                   │ (SDD) для агентів кодингу. │ Track 1        │
├───────────────────────────────┼────────────────────────────┼────────────────┤
│ 6. get-shit-done-cc/          │ GSD Framework для Claude   │ Open Source    │
│    get-shit-done-cc           │ Code: прародич ai-sdlc     │ Track 1        │
│    (GitHub)                   │ з фазовою моделлю.         │                │
└───────────────────────────────┴────────────────────────────┴────────────────┘
```

### Деталізований 4-етапний план асиміляції у DNK OS:

#### Фаза 1: Deep Mining & AST Scan (Дні 1–3)
- Сканувати репозиторії `wico216/ai-sdlc` та `github/spec-kit` за допомогою GitHub API.
- Витягти шаблони промптів фази Inception, структури запитань (`[Answer]:`), детекції протиріч та валідації артефактів.
- Дослідити реалізацію `RFC-0011 (Definition of Ready Gate)` в `ai-sdlc-framework/ai-sdlc`.

#### Фаза 2: Синтез артефактів DNK OS (Дні 4–7)
- Створити `docs/tech/specs/DNK-SPEC-SDLC-001_golden_thread_protocol.md`.
- Розробити скіл `skills/software-development/dnk-intent-discovery/SKILL.md`.
- Створити CLI-хелпер `scripts/system/intent_engine.py` для перевірки повноти заповнення `intent.md`.

#### Фаза 3: Git Worktree & Test Protection Hooks (Дні 8–11)
- Оновити механізм `dnk_swarm_parallel` у `core/orchestrator/` для створення ізольованих робочих дерев `git worktree add .worktrees/{task_id}` під кожного субагента з наступним auto-merge або PR.
- Додати хук блокування тестів під час фіксів у Pre-Tool Hook.

#### Фаза 4: Evals Suite & CI Verification (Дні 12–14)
- Зібрати 15 реальних минулих тасок DNK OS у `core/evals/fixtures/`.
- Написати скрипт автоматичного бенчмаркінгу `scripts/evals/run_agent_evals.py`.
- Інтегрувати перевірку у `bash scripts/verify_all.sh`.
