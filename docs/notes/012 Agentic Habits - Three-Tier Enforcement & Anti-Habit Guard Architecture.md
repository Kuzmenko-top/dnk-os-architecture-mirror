---
title: "012 Agentic Habits - Three-Tier Enforcement & Anti-Habit Guard Architecture"
date: 2026-09-05
tags:
  - sota-assimilation
  - agentic-habits
  - gerych-auditor
  - deterministic-gates
  - zero-waste
aliases:
  - Agentic Habits SOTA Blueprint
  - Three-Tier Habit Enforcement
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/obsidian/012_agentic_habits_three_tier_enforcement.md"
purpose: "SOTA Architectural Assimilation of AgriciDaniel/agentic-habits into DNK OS."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🧬 SOTA Assimilation Blueprint: Agentic Habits & Three-Tier Guard Protocol

> **Source Repository**: `AgriciDaniel/agentic-habits`  
> **Author**: Daniel Agrici  
> **License**: MIT (Track 1: Direct Component & Template Assimilation)  
> **Target Swarm Roles**: `gerych_auditor`, `gerych_prime`, `herich_librarian`  
> **Core Value**: **Loading an instruction is deterministic. Following it is not.**

---

## 🏛️ 1. Executive Summary & Core Dilemma

Сучасні автономні AI-агенти не страждають від браку пам'яті (утиліти пам'яті, інструкції CLAUDE.md, AGENTS.md, SCONES, rules files). **Головний дефіцит агентів — це детерміноване дотримання правил (Enforcement).**

За емпіричними дослідженнями Anthropic (Impossible Tasks evaluation):
- Навіть агресивна пряма письмова інструкція зменшує відсоток помилок лише з ~55% до ~23–35%.
- Тобто **письмові правила прибирають приблизно половину збоїв, залишаючи третину помилок активними**.
- Спроби "написати правило гучніше" або роздувати інструкції призводять до деградації контексту (context bloat), коли агент починає ігнорувати як нові, так і базові правила.

Архітектура **Agentic Habits** пропонує вихід через **трьохрівневу модель суверенітету поведінки**:

```
┌────────────────────────────────────────────────────────┐
│                   THREE-TIER LADDER                    │
├──────────────┬────────────────────────┬────────────────┤
│ 1. STATED    │ Rules Files / AGENTS   │ Advisory hint  │
├──────────────┼────────────────────────┼────────────────┤
│ 2. GATED     │ Stop Hooks / Shell Gate│ Deterministic  │
├──────────────┼────────────────────────┼────────────────┤
│ 3. JUDGED    │ Read-Only Subagent     │ Evidence-Bound │
└──────────────┴────────────────────────┴────────────────┘
```

---

## 🎯 2. Три Рівні Дотримання (Three-Tier Enforcement Protocol)

### 1. Рівень 1: Stated (Декларативний)
- **Формат картки**:
  ```markdown
  ### SYS-03 · Verify with the real thing
  **When** I am about to say something works.
  **Do** Run the closest real check and show its actual output.
  <!-- habit: id=SYS-03 tier=gated check="contains real output from real run" -->
  ```
- **Правило "When -> Do / Instead"**: Психологічно доведений патерн "імплементаційних намірів" (implementation intentions) замість абстрактних побажань ("будь уважним"). Заміна поганої звички формулюється через **Instead** (не можна просто заборонити — треба дати тригеру альтернативну дію).
- **Суворий бюджет (Context Budget)**:
  - System Scope: макс 12 правил.
  - Project Scope: макс 10 правил.
  - Path-scoped: макс 6 правил.
  - Якщо ліміт досягнуто — додавання нового правила вимагає обов'язкової архівації або видалення слабшого!

### 2. Рівень 2: Gated (Детерміновані Хуки)
- Якщо правило позначається як критичне (`Must never fail`) — воно **не залишається текстом**. Воно ескалується в **Hook** (`completion-gate.sh`).
- **Completion Gate**:
  - Перехоплює подію `Stop` (завершення ходу асистента).
  - Сканує останнє повідомлення на наявність тверджень про успіх: *"tests pass"*, *"build is clean"*, *"compiles without errors"*, *"zero failures"*.
  - Аналізує реальний транскрипт сесії: чи викликалася реальна перевірочна команда (`pytest`, `npm test`, `cargo test`, `tsc`, `lint`) з успішним результатом `err == false`.
  - **Fail-Open & Recursion Guard**: блокує рівно 1 раз на хід, запобігаючи дедлокам; якщо агент чесно каже *"не запускав / unverified"*, хук пропускає відповідь.
  - Якщо агент сфальсифікував або не перевірив — завершення ходу блокується з повідомленням:
    > *COMPLETION GATE: this turn claims a test, build, lint, or type check came back clean, and no command was run in this turn to find out.*

### 3. Рівень 3: Judged (Ізольований Арбітраж Доказів)
- Реалізується через `habit-judge` (в DNK OS — `gerych_auditor`).
- **Принцип**: Контекст, що створив код, є упередженим і не може бути об'єктивним суддею.
- Суддя запускається у свіжому, ізольованому контексті з **read-only інструментами** (не може виправляти код, тому не зацікавлений у викривленні оцінки).
- **Evidence Ledger**:
  - Розрізнення `[RAW]` (фактичні виклики інструментів, diff, рядки логів) проти `[INFER]` (здогадки, інтерпретації відсутності подій).
  - Аксіома: **No evidence means not PASS** (`UNKNOWN` або `FAIL`).

---

## 🚫 3. Каталог 12 Анти-звичок (12 Anti-Habits Matrix)

| Анти-звичка | Симптом (Tell) | Внутрішній тиск моделі | Замінна звичка в DNK OS |
|---|---|---|---|
| **Phantom done** | Твердження "готовності" без реального запуску | Модель хоче догодити і швидше завершити таск | `SYS-03`: Запусти найближчий реальний тест і покажи його stdout |
| **Green-washing** | Маскування падінь через `\|\| true` або ігнорування stderr | Страх червоного статусу в тестах | `CRAFT-03`: Червоний тест — це цінний сигнал, покажи стек трейс |
| **Guess stacking** | Серія виправлень навмання без виявлення кореневої причини | Спроба випадково вгадати правильний стан | `CORE-05`: Після 2 невдалих спроб зупинись і зніми трасування (SCONES Distiller) |
| **Drive-by refactor** | Непомітне переформатування сусіднього коду/файлів | Модель вважає, що її стиль "кращий" | `CRAFT-01`: Smallest diff — змінюй виключно необхідне для таски |
| **Silent assumption** | Неоголошене припущення про середовище/API | Бажання не ставити запитань користувачу | `COMM-02`: Оголоси припущення явно перед початком дій |
| **Context amnesia** | Перепитування або повторний пошук того, що вже є | Лінь заглянути у збережену історію | `RETRIEVE-01`: SCONES / Session Search перед запитаннями |
| **Confident invention** | Вигадування параметрів, методів чи файлів | Генеративна природа без верифікації | `TRUTH-02`: Знайди оголошення символу (`dnk_resolve_symbol`) перед імпортом |
| **Sycophantic fold** | Беззаперечне визнання своєї "помилки", навіть коли код був правий | Конформність перед критикою | `TRUTH-03`: Перевір фактами та тестами, стій на фактах |
| **Boil the ocean** | Спроба вирішити всю світову проблему в одному ході | Нездатність декомпозувати | `CORE-01`: MASE (Atomic Slices) <= 25 інструментів |
| **Narration theatre** | Довгі абзаци про те, що агент "збирається зробити" | Імітація корисної діяльності | `COMM-01`: Дії та результат першими, ніяких анонсів майбутнього |
| **Cleanup by destruction**| Видалення тестів або коментарів, щоб збірка пройшла | Прагнення прибрати помилку за будь-яку ціну | `SAFETY-02`: Захищай те, що написав не ти |
| **Habit hoarding** | Накопичення сотень правил у промптах | Ілюзія контролю через роздування тексту | `BUDGET-01`: Жорсткий cap, нове витісняє старе |

---

## 🪜 4. Сходи Ремонту Звичок (The Habit Repair Ladder)

Коли агент порушує правило, заборонено просто "переписати правило знову капслоком". Працює строгий інженерний протокол:

```
[Порушення 1] ──> Загострити тригер (Sharpen Trigger: чіткий момент When, точна дія Do/Instead)
       │
[Порушення 2] ──> Змінити Placement (Звузити до Path-scoped правила або підняти пріоритет)
       │
[Порушення 3] ──> Ескалація до Gated (Написати детермінований Hook) АБО Архівація (Retire)
```

**Четвертої сходинки не існує.** Якщо правило на рівні контексту не працює після двох ітерацій — це не проблема дисципліни моделі, це межа можливостей контекстних підказок.

---

## 🚀 5. План Асиміляції в DNK OS (Implementation Roadmap)

### Крок 1: Впровадження Stop Gate для Gerych / Swarm (`core/guards/completion_gate.py`)
- Створення легкої Python/Shell реалізації `CompletionGate`, інтегрованої в CLI та цикл виконання агента.
- Якщо асистент каже *"тести пройшли успішно"* або *"all tests pass"*, але в ході відсутні виклики `pytest` або `verify_all.sh` — хід переривається і агент отримує системне нагадування.

### Крок 2: Розширення `gerych_auditor` режимом Habit Ledger
- Наділення аудитора роллю `habit-judge`.
- Під час pre-commit або `dnk_run_adversarial_review` генерується таблиця `HABIT LEDGER` з мітками `[RAW]` та `[INFER]`.

### Крок 3: Оновлення правил AGENTS.md та SOUL.md
- Інтеграція 12 Anti-Habits до списку суворих заборон.
- Формалізація Budget Invariant: обмеження розміру системних промптів та пам'яті (L1 Memory Char Limit вже діє, тепер додається правило відсіювання застарілих інструкцій).

---

## 🔗 Cross-Links & References
- [[000 DNK HUB Index]]
- [[002 DNK OS - Master System Architecture & Implementation Blueprint]]
- [[004 Gerych Task Specification Standard & Zero-Waste Protocol v2.5]]
- [[Gerych Prime - Unified Orchestrator & SOTA Adaptation Engine]]
