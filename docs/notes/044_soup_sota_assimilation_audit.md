---
title: "044 Soup SOTA Assimilation Audit: Frontier Agent Architecture & Logic"
tags:
  - sota-assimilation
  - soup
  - prompt-engineering
  - weight-ci-gate
  - deterministic-rewards
  - tool-optimization
  - dnk-orchestration
  - google-gemini
date: 2026-09-06
status: Completed
reference_repo: "https://github.com/MakazhanAlpamys/Soup"
license: "Apache-2.0 (Track 1 Permissive)"
author: "Gerych Prime & Antigravity (Maxim)"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/044_soup_sota_assimilation_audit.md"
purpose: "Deep Architectural Audit & Logic Assimilation of MakazhanAlpamys/Soup for Frontier Google Models (Gemini 2.5) in DNK OS"
canonical_source: false
alters_files: []
triggers_tasks: []
status: "Active"
version: "2.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🍲 SOTA-аудит логіки Soup для екосистеми DNK OS на передових моделях Google (Gemini)

> **Ключова передумова**: Ми **не розгортаємо та не навчаємо локальні моделі** на споживчому залізі. DNK OS використовує передові SOTA моделі від **Google (Gemini 2.5 Pro / Flash, Vertex AI)**.
> Репозиторій `MakazhanAlpamys/Soup` асимілюється **виключно заради чистої алгоритмічної логіки**: методології регресійних гейтів (Ship/Don't Ship), оптимізації схем інструментів (compile-tools), синтезу детермінованих верифікаторів (reward synth), моніторингу дрифту (drift-alarm) та аудиту агентних датасетів.

---

## 🏛️ Чому логіка Soup є цінною навіть без локального навчання?

Більшість команд розглядають `Soup` лише як інструмент запуску LoRA на 4GB GPU через Layer Streaming. Проте під капотом репозиторію знаходиться **одна з найбільш зрілих у відкритому коді систем інженерії надійності (AI Reliability & Evaluation Engineering)**, яка на 100% масштабується на роботу з фронтирними моделями Google.

```
                      ┌───────────────────────────────────────────────┐
                      │    DNK OS Core (Gemini 2.5 Pro / Flash)       │
                      └───────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼──────────────────────────────────┐
         │                                    │                                  │
         ▼                                    ▼                                  ▼
┌──────────────────┐               ┌──────────────────────┐           ┌────────────────────┐
│ compile-tools    │               │ soup ship (Gate)     │           │ reward synth       │
│ Оптимізація схем │               │ Dual-Leg регресійний │           │ Авто-синтез Python │
│ інструментів під │               │ гейт для скілів/     │           │ верифікаторів      │
│ Gemini Function  │               │ промптів (Win+Guard) │           │ результатів        │
│ Calling          │               │                      │           │ (калібровані)      │
└──────────────────┘               └──────────────────────┘           └────────────────────┘
```

---

## 🧩 5 Ключових архітектурних логік Soup для асиміляції в DNK OS

### 1. `soup compile-tools` — Авто-оптимізація схем інструментів під Google Gemini
* **Суть логіки**: У `src/soup_cli/utils/compile_tools.py` реалізовано алгоритмічний пайплайн, який бере схеми OpenAPI / MCP / JSON-Schema та датасет типових запитів, після чого ітеративно оптимізує описи інструментів та назви параметрів (через текстові градієнти або помилки валідації).
* **Користь для DNK OS**:
  - Моделі Google Gemini мають видатну підтримку Structured Outputs та Tool Calling, але чутливі до перевантажених або семантично неоднозначних описів функцій.
  - Асиміляція логіки `compile-tools` дозволяє нам створити автоматичний тестувальник наших інструментів (`hermes_tools`, `dnk_*` інструменти): система автоматично виявляє конфлікти в описах інструментів та реформулює їх для 100% точності вибору інструменту.

### 2. `soup ship` — Двоногий (Dual-Leg) Регресійний Гейт для Скілів та Промптів
* **Суть логіки**: У `src/soup_cli/commands/ship.py` та `src/soup_cli/eval/gate.py` реалізовано строгий бінарний вирок **SHIP / DON'T SHIP**:
  - **Leg 1 (Task Win)**: Чи вирішує нова версія цільову задачу краще за попередню?
  - **Leg 2 (Catastrophic Forgetting & Safety Guard)**: Чи не зламала зміна базові можливості (JSON schema validity, tool-calling format, path hygiene, core reasoning)?
  - Генерація незмінного артефакту свідчень (`evidence.json`) та публікація статусу безпосередньо в PR GitHub (`soup ship --push owner/repo#N`).
* **Користь для DNK OS**:
  - Коли ми оновлюємо `SOUL.md`, скіли в `skills/` або інструкції агентів Swarm (`dnk_shopify`, `dnk_dev_fullstack`), ми ризикуємо зламати поведінку, яка працювала вчора.
  - Асимілювавши логіку `ship` у наш гейт якості (`scripts/system/verify_skills.py` або `gerych_auditor`), ми отримуємо детермінований вердикт перед кожним коммітом чи мерджем скіла.

### 3. `soup reward synth` — Детермінований синтез каліброваних верифікаторів
* **Суть логіки**: У `src/soup_cli/commands/reward.py` реалізовано алгоритм синтезу виконуваного Python-коду валідатора (`reward.py`) для 4 родин:
  - `numeric`, `json_schema`, `regex`, `tool_call`.
  - **Головне правило безпеки**: алгоритм **відмовляється емітувати верифікатор**, якщо той не проходить калібрування проти згенерованих негативних збурень (perturbed negatives).
* **Користь для DNK OS**:
  - Замість того, щоб на кожній задачі витрачати виклики важких моделей як суддів (LLM-as-a-judge), `gerych_auditor` або `dnk_decompose_task_dna` можуть автоматично генерувати легкі, блискавичні Python-тести на базі очікуваних схем, гарантуючи нульову кількість хибнопозитивних оцінок.

### 4. `soup expect` — Декларативний фреймворк валідації агентних трейсів
* **Суть логіки**: У `src/soup_cli/commands/expect.py` створено механізм перевірки JSONL датасетів та трейсів за YAML-специфікацією (перевірка порожніх полів, розподілу довжини відповідей, обов'язкових ключів, регулярних виразів).
* **Користь для DNK OS**:
  - Ідеально лягає на валідацію пам'яті SCONES (`scones_memory`) та журналу виконаних задач TaskDNA. Це гарантує, що пам'ять агента не засмічується некоректними даними.

### 5. `soup drift-alarm` — Моніторинг дрифту генерацій Google Gemini
* **Суть логіки**: У `src/soup_cli/commands/drift_alarm.py` обчислюється статистична розбіжність (KL-дивергенція та ентропійні зсуви) між еталонними виходами системи та реальними продакшн-відповідями в часі.
* **Користь для DNK OS**:
  - Google регулярно оновлює чекпоїнти Gemini 2.5 в хмарі. Моніторинг за патерном `drift-alarm` дозволяє вчасно помітити, якщо оновлення хмарної моделі змінило довжину коду, формат відповідей або схильність до галюцинацій у наших автономних воркерах.

---

## 🛠️ План впровадження та статус реалізації (Implementation Status)

| Компонент Soup | Цільовий модуль у DNK OS | Тести | Статус |
|----------------|--------------------------|-------|--------|
| `soup ship` | `core/orchestrator/prompt_ship_gate.py` | `tests/core/test_soup_assimilated_modules.py` | ✅ **Implemented & Verified (Phase 1)** |
| `compile-tools` | `core/orchestrator/tool_optimizer.py` | `tests/core/test_soup_assimilated_modules.py` | ✅ **Implemented & Verified (Phase 1)** |
| `reward synth` | `core/auditor/reward_synthesizer.py` | `tests/core/test_soup_assimilated_modules.py` | ✅ **Implemented & Verified (Phase 1)** |
| `soup expect` | `core/orchestrator/scones_expect.py` & `core/auditor/scones_expect.py` | `tests/core/test_soup_phase2_modules.py` & `tests/core/test_scones_expect.py` | ✅ **100% Implemented & Verified (Phase 2)** |
| `drift-alarm` | `core/orchestrator/drift_alarm.py` & `services/dnk_analytics/drift_monitor.py` | `tests/core/test_soup_phase2_modules.py` & `tests/services/test_drift_monitor.py` | ✅ **100% Implemented & Verified (Phase 2)** |

---

## 🔗 Зв'язки з іншими архітектурними компонентами
- [[043_deepseek_harness_sota_assimilation_audit]] — Порівняння тестових обгорток та харнесів.
- [[042_agentic_habits_sota_assimilation_audit]] — Патерни надійності та авторефлексії агентів.
- `core/orchestrator/agents/gerych_prime/SOUL.md` — Канонічні правила оркестрації Gerych Prime.
- `scripts/verify_all.sh` — Master Quality Gate DNK OS.
