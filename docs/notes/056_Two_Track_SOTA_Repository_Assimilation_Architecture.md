---
title: "056 Two-Track SOTA Repository Assimilation Architecture"
date: 2026-09-06
tags:
  - sota-assimilation
  - scout-engine
  - license-compliance
  - clean-room-reverse-engineering
  - dnk-hub
  - swarm-orchestration
  - zero-waste
aliases:
  - "016_Two_Track_SOTA_Repository_Assimilation_Architecture"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/056_Two_Track_SOTA_Repository_Assimilation_Architecture.md"
purpose: "Unified Architecture and Operational Specification for the 5-Level Two-Track SOTA Repository Assimilation Engine and Scout System in DNK OS."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "Gerych (Hermes Prime)"
--- END DNK-MRH-HEADER -->

E6 Two-Track SOTA Repository Assimilation Architecture

Ця нотатка формалізує системну архітектуру, ліцензійні бар'єри та фоновий конвеєр асиміляції відкритих SOTA-репозиторіїв (Вектор 4 прискорення DNK_HUB).

Пов'язані архітектурні нотатки:
- [[000_DNK_HUB_INDEX]] — Головний навігатор хабу
- [[013_Zero_Touch_Inception_Gateway_Protocol]] — Вектор 1 (Inception & Socratic Gate)
- [[028 Anti-Loop and AST Fast-Path Architecture]] — Вектор 2 (Anti-Loop & Fast-Path)
- [[055_GitHub_MCP_and_CICD_Fast_Path_Architecture]] — Вектор 3 (GitHub MCP & Fail-Closed CI/CD)

---

## 🎯 1. Призначення та Проблематика

При активній розробці платформи DNK OS виникає потреба вбирання найсучасніших рішень (SOTA: State-of-the-Art) з відкритого коду:
1. **Відеогенерація та анімації**: Remotion, FrameCN, PersonaLive, audio-conditioning.
2. **Інтерактивні полотна (Canvas)**: React Flow, tldraw, Open Canvas, OCC 3-way merge.
3. **E-commerce & Checkout**: Shopify OS 2.0, Liquid AST, Rust/Wasm Functions.
4. **Backend & AI Agents**: LangGraph, AutoGen, CrewAI, FastAPI, SQLAlchemy 2.0.

### Ризики нерегульованого імпорту:
- **Ліцензійне зараження (License Contamination)**: випадкове копіювання коду під ліцензіями GPL/AGPL у комерційну пропрієтарну кодову базу робить увесь продукт вразливим до юридичних позовів.
- **Шпагеті-залежності та витік секретів**: сторонні репозиторії містять хардкод абсолютних шляхів (`/Users/...`, `/home/...`), тестові API-ключі або невідповідність стандарту MRH (`DNK-STD-0075`).
- **Перевантаження контексту LLM**: ручне читання великих репозиторіїв з'їдає весь ліміт викликів інструментів (90/90).

---

## ⚡ 2. 5-Рівневий Двотрековий Пайплайн (Two-Track SOTA Pipeline)

Конвеєр `SOTAScoutEngine` реалізує чітке 5-рівневе розділення:

```mermaid
graph TD
    A[SOTA Repo URL / Discovery] --> B[Level 1: Remote Metadata & README Fetch / Cache]
    B --> C[Level 2: Two-Track License Audit Gate]
    C -->|Permissive: MIT / Apache 2.0 / BSD / ISC| D1[Track 1: Direct Template Assimilation]
    C -->|Restrictive: GPL / AGPL / SSPL / Copyleft| D2[Track 2: Clean-Room Reverse Engineering]
    D1 --> E[Level 3: AST Pattern Extraction & Code Sanitizer]
    D2 --> E
    E --> F[Level 4: Multi-Channel Knowledge Ingestion]
    F --> G1[SCONES Cognitive Memory .scones/sota_memories.json]
    F --> G2[SOTA Knowledge Card docs/tech/sota_assimilation/]
    F --> G3[Hermes Skill skills/name_assimilated/SKILL.md]
    F --> G4[Obsidian Vault Note docs/notes/016_...md]
    E --> H[Level 5: Swarm Routing & TaskDNA DAG]
    H --> I[Target Worker: dnk_video_ai_creator | gerych_builder | dnk_shopify | dnk_dev_fullstack]
```

---

## 🛡️ 3. Two-Track License Compliance Classifier

| Параметр | **Track 1: Direct Template Assimilation** | **Track 2: Clean-Room Reverse Engineering** |
| :--- | :--- | :--- |
| **Ліцензії** | MIT, Apache 2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense | GPL-2.0, GPL-3.0, AGPL-3.0, LGPL, SSPL, BSL, CC-BY-NC |
| **Юридичний статус** | Commercial-Safe | Restrictive / Copyleft / Viral |
| **Пряме копіювання коду** | **Дозволено** (із санітизацією під `DNK-STD-0075`) | **СУВОРО ЗАБОРОНЕНО** (Hard Invariant) |
| **Метод асиміляції** | Прямий імпорт компонентів, адаптація архітектури в `core/` або `apps/` | Екстракція лише Pydantic схем, TypeScript типів, поведінкових специфікацій |
| **Результуюча ліцензія** | Збереження авторського attribution | 100% чиста комерційна реалізація під MIT-ліцензією DNK OS |

---

## 🧹 4. Санітизація коду (`CodeSanitizer`)

Усі асимільовані файли та шаблони проходять обов'язкову санітизацію:
1. **Redaction секретів та токенів**:
   - Патерни `ghp_*`, `github_pat_*`, `sk-*`, `xox*`, `password="*"` автоматично замінюються на `[REDACTED]`.
2. **Нормалізація абсолютних шляхів**:
   - Будь-які `/Users/...` або `/home/...` замінюються на безпечні відносні шляхи (`./` або `../`).
3. **Автогенерація заголовка MRH**:
   - Автоматично монтується валідний машинно-читабельний блок `DNK-MRH-HEADER` (`DNK-STD-0075`).

---

## 📚 5. Мультиканальна генерація знань (4 Knowledge Artifacts)

Після успішної асиміляції репозиторію двигун синхронно/фоново генерує 4 артефакти:

1. **Hermes Skill (`skills/<name>_assimilated/SKILL.md`)**:
   - Валідний YAML frontmatter (`name`, `description`, `version`, `category: research`, `track`, `target_worker`).
   - Quick Recipes (готові скрипти делегування у Swarm та зразки Pydantic схем).
   - Pitfalls & Invariants (ліцензійні бар'єри, Zero-Absolute-Paths, MRH-інваріант).
2. **Obsidian Vault Note (`docs/notes/016_<name>_sota_assimilation_audit.md`)**:
   - Оформлення згідно з `[OBSIDIAN_MRH_HYGIENE]`.
   - Rich `[[wikilinks]]` на хаб та пов'язані нотатки.
3. **SOTA Research Digest (`docs/tech/sota_assimilation/SOTA_<NAME>_ASSIMILATION.md`)**:
   - Повний технічний звіт, метрики GitHub (зірки, форки, ліцензія), розбір архітектури та дорожня карта інтеграції.
4. **SCONES Cognitive Memory (`.scones/sota_memories.json`)**:
   - Довгостроковий когнітивний запис для контекстного згадування агентами Swarm.

---

## 🤖 6. Swarm Routing & Автономна черга Scout

`SOTAScoutEngine` підтримує чергу завдань (`ScoutJobQueue` у `data/sota_scout_queue.json`) із пріоритетами та кешем метаданих:
- `PENDING` ➔ `ANALYZING` ➔ `ASSIMILATED` (або `REJECTED`/`FAILED`).

### Автоматична маршрутизація до воркерів Swarm:
- **`dnk_video_ai_creator`**: обробка медіа, рендеринг Remotion, синтез аудіо/мови.
- **`gerych_builder`**: нескінченні просторові полотна (Infinite Canvas), React Flow, UI.
- **`dnk_shopify`**: Liquid-шаблони, Wasm Functions, Checkout UI.
- **`dnk_dev_fullstack`**: FastAPI ендпоінти, ORM моделі SQLAlchemy 2.0, PostgreSQL.
- **`gerych_auditor`**: безпека, Red-Team тестування, фаззінг, SAST.

### CLI Інтерфейс:
```bash
# Синхронна асиміляція репозиторію
python3 scripts/system/sota_scout_runner.py --repo GVCLab/PersonaLive --focus video,streaming

# Додавання завдання до фонової черги
python3 scripts/system/sota_scout_runner.py --repo GPLOrg/CopyleftLib --enqueue --priority 1

# Перевірка статусу черги
python3 scripts/system/sota_scout_runner.py --status

# Обробка завдань із черги
python3 scripts/system/sota_scout_runner.py --process-queue --max-jobs 2
```

---

## 🏆 7. Результати верифікації

Усі 7 модульних та інтеграційних тестів у `tests/verification/test_sota_assimilation_two_track.py` пройдено з результатом **100% Green**:
- `test_sanitize_code_snippet` — санітизація коду, видалення абсолютних шляхів та токенів.
- `test_license_audit_two_track` — класифікація Permissive vs Copyleft.
- `test_swarm_routing_logic` — точний вибір агента Swarm та синтез TaskDNA.
- `test_full_assimilation_pipeline_track_1` — наскрізний Track 1 з генерацією всіх 4 артефактів.
- `test_full_assimilation_pipeline_track_2_clean_room` — наскрізний Track 2 з бар'єром Clean-Room.
- `test_scout_queue_lifecycle` — дедуплікація, пріоритизація та обробка черги.
- `test_dnk_assimilate_tool_integration` — безшовна робота нативного інструменту `dnk_assimilate_repo`.

Загальний регресійний набір (44 тести) завершився з результатом **44 passed**!
