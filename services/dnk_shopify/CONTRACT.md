---
document_id: DNK-DEV-1907
file_name: CONTRACT.md
title: DNK Shopify Service Specification Contract
category: DEV
type: Specification
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - normalized
  - shopify
  - architecture
  - contracts
storage_type: git
path: services/dnk_shopify/CONTRACT.md
access_level: write
checksum: null
changelog_ref: null
---

# CONTRACT: DNK Shopify Agentic Service

## 1. Місія та Бачення (Mission & Vision)

**DNK Shopify** — це інтегрований агентний мікросервіс у складі екосистеми **DNK OS**, що призначений для автоматизації повного життєвого циклу створення, розвитку та оптимізації Shopify-магазинів. 

Сервіс використовує **dnk_git_research** як основний інтелектуальний двигун пошуку патернів та рішень, а також власну базу знань з **PostgreSQL (pgvector)** для повторного використання успішних розробок.

### Головна ціль:
Створення самопідтримуваної екосистеми розробки:
$$\text{Тема} \longrightarrow \text{Секції} \longrightarrow \text{Сторінки} \longrightarrow \text{CRO} \longrightarrow \text{Маркетинг} \longrightarrow \text{Аналітика} \longrightarrow \text{Повторне використання (Assets)}$$

---

## 2. Архітектурні Модулі (Architectural Modules)

Сервіс побудовано за модульним принципом відповідно до стандарту `DNK-STD-0080`:

1. **Orchestrator Core (`src/orchestrator.py`):**
   Аналізує вхідне завдання, здійснює роутинг, підвантажує контекст та координує спеціалізованих агентів.
2. **Git Research Adapter (`src/adapters/git_research.py`):**
   Міст до сервісу `dnk_git_research` для миттєвого пошуку патернів коду у 125+ відфільтрованих Shopify репозиторіях.
3. **Theme Intelligence (`src/theme_intel.py`):**
   Аналізує та веде мапу (Map) теми **DNK Ecom**, валідує сумісність шаблонів та налаштувань.
4. **Section Builder (`src/section_builder.py`):**
   Генерує готові Liquid-секції та блоки з інтеграцією JSON-схем для зручного редагування в Shopify Theme Editor.
5. **Content Engine (`src/content_engine.py`):**
   Формує високоефективні PDP, Landing Pages, Advertorials, Listicles, Product Cards та SEO-блоги.
6. **CRO Lab (`src/cro_lab.py`):**
   Пропонує гіпотези покращення конверсії, планує А/Б тести та генерує аналітичні звіти.
7. **App & Extension Builder (`src/app_builder.py`):**
   Розробляє Theme App Extensions, App Embeds та кастомні додаткові сервіси.
8. **Validation & Drift Control (`src/validator.py`):**
   Перешкоджає деградації коду теми, валідує схеми секцій та контролює відповідність стандартам.

---

## 3. Спеціалізовані Агенти та Ролі (Agent Registry)

| Агент (Agent) | Основна Роль | Основні Інструменти & Виходи |
| :--- | :--- | :--- |
| **Theme Agent** | Робота з глобальною структурою теми | `templates/*.json`, `layout/theme.liquid` |
| **Section Agent** | Генерація модульних налаштовуваних секцій | `sections/*.liquid`, Schema JSON |
| **Content Agent** | Копірайтинг, Landing Pages, Advertorials | `templates/page.liquid`, Markdown Copy |
| **CRO Agent** | Розробка А/Б тестів та інтеграція аналітики | `snippets/ab-tests.liquid`, GTM |
| **App Agent** | Створення кастомних Shopify Apps & Extensions | `extensions/`, Node/Remix code |
| **QA Agent** | Валідація схем та продуктивності | JSON Schema Linter, Lighthouse API |
| **Versioning Agent** | Контроль версій, логування та міграції | Changelog, Git Tags |

---

## 4. Шлях Знань (Knowledge Flow)

Кожна задача проходить лінійний детермінований шлях для запобігання деградації архітектури:

```
[Завдання (Task)] ──> [Пошук паттерну (Research)] ──> [Формування Context Pack]
                                                               │
                                                               ▼
[Acceptance / QA] <── [Валідація (Schema/CRO)] <── [Виконання (Agent Execution)]
        │
        ▼
[База Знань / PostgreSQL (Reusable Asset)]
```

---

## 5. Правила Валідації та Захисту від Дрейфу (Anti-Drift Guardrails)

* **Theme Integrity:** Заборонено створювати занадто дрібні Liquid-файли. Всі нові секції повинні мати чітко типізовану схему налаштувань (`presets`, `settings`, `blocks`).
* **Zero Duplication:** Перед генерацією будь-якого компонента Section Agent перевіряє поточну карту теми DNK Ecom. Якщо схожа секція вже є — пропонується її модернізація (екстеншн) замість створення нової.
* **Schema Strictness:** Кожна згенерована схема Liquid повинна проходити JSON-лінтинг. Порушення структури блокує збереження артефакту.

---

## 6. MVP План Роадмапу (MVP Roadmap)

### Sprint 1: Foundation (Theme Map & Registry)
* Описати базову структуру DNK Ecom theme map.
* Побудувати індекс ключів та наявних секцій.
* Описати схеми метаданих знань у PostgreSQL.

### Sprint 2: Core (Orchestrator & Basic Agents)
* Реалізувати маршрутизатор Orchestrator.
* Підключити адаптер до `dnk_git_research`.
* Запустити робочі MVP-версії Section Agent та Theme Agent.

### Sprint 3: Conversions (Content & CRO)
* Додати Content Agent (генерація Listicles / Landing Pages).
* Запустити CRO Agent (впровадження А/Б тестів на базі Liquid).
* Інтегрувати автоматичний валідаційний чек-лист.

### Sprint 4: Extensibility (Apps & Versioning)
* Запустити App Agent для побудови Theme App Extensions.
* Налагодити Version Registry для автоматичного присвоєння версій кожній зміні.

---
<i>Signed by DNK_HUB Orchestrator on 2026-07-12.</i>
