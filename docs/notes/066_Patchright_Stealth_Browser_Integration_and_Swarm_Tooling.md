---
title: "066 Patchright Stealth Browser Integration & Swarm Tooling"
date: "2026-09-06"
status: "Active"
tags:
  - stealth
  - browser
  - patchright
  - swarm
  - architecture
aliases:
  - "038_Patchright_Stealth_Browser_Integration_and_Swarm_Tooling"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/066_Patchright_Stealth_Browser_Integration_and_Swarm_Tooling.md"
purpose: "Architectural documentation of Patchright SOTA stealth browser deployment, CLI Runner, and Swarm Agent Tooling."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

F6 Patchright Stealth Browser Integration & Swarm Tooling

## 🎯 Executive Summary
Інтегровано SOTA Stealth Browser двигун на базі **Patchright** (модифікований Playwright із Zero-CDP патчами ядра Chromium) у середовище **DNK OS**. Забезпечено обхід сучасних систем антибот-детекції (Cloudflare Turnstile, DataDome, Kasada) без витоку прапорця `navigator.webdriver` та без тригера `Runtime.enable`.

Реалізовано два взаємодоповнюючі інтерфейси:
1. **Варіант А (Direct Python Context Manager & CLI Runner)**: швидкий локальний запуск і скрипти для прямого видобутку контенту.
2. **Варіант Б (Swarm Agent Tooling)**: ройовий інструмент `stealth.scrape` (`dnk_stealth_scrape`) для ройових агентів (`dnk_shopify`, `gerych_builder`, `gerych_researcher`).

---

## 🏗️ Architecture & Component Topology

```
+-------------------------------------------------------------+
|                     DNK OS Ecosystem                        |
|                                                             |
|   [Swarm Agents]                [CLI & Python Scripts]     |
|   dnk_shopify, gerych_builder    scripts/stealth/           |
|         │                               │                   |
|         ▼                               ▼                   |
|   core/orchestrator/            scripts/stealth/            |
|   tools/stealth_browser_tool.py patchright_scraper.py       |
|         │                               │                   |
|         └───────────────┬───────────────┘                   |
|                         ▼                                   |
|             core/adapters/dnk_patchright_adapter.py         |
|             (DNKPatchrightAdapter - Context Manager)        |
|                         │                                   |
|                         ▼                                   |
|             Patchright Chromium Engine (Zero-CDP)           |
+-------------------------------------------------------------+
```

---

## 🚀 Execution Modes

### 1. Варіант А: CLI Runner та Python Контекстний Менеджер
- **Скрипт**: `scripts/stealth/patchright_scraper.py`
- **Клас**: `core.adapters.dnk_patchright_adapter.DNKPatchrightAdapter`
- **Переваги**:
  - Безпечне завершення процесів через `__enter__` / `__exit__`.
  - Підтримка селекторів та безпечного виконання JS через C++ AST evaluation.
  - CLI підтримка прапорців `--url`, `--selector`, `--eval`, `--json`, `--headed`.

### 2. Варіант Б: Swarm Tooling (`stealth.scrape`)
- **Інструмент**: `core/orchestrator/tools/stealth_browser_tool.py`
- **Шлюз**: `core/orchestrator/tool_executor.py` (`stealth.scrape` / `dnk_stealth_scrape`)
- **Реєстр**: `core/orchestrator/tool_registry.py` & `core/orchestrator/tool_aliases.py`
- **Ройова навичка**: `skills/software-development/patchright_assimilated/SKILL.md`
- **Переваги**:
  - Асинхронний виклик ройовими агентами через єдину точку входу.
  - Fail-safe fallback на емульовану відповідь при збоях дисплея чи відсутності браузера.

---

## 🧪 Verification Matrix
- `tests/stealth/test_patchright_adapter.py`: **7/7 Green** (100% тестів пройдено за 0.62s).
- Live Chromium Test: `navigator.webdriver == False` підтверджено наживо.
- Git Commits:
  - `733744abb6`: Upgrade dnk patchright adapter to live zero-cdp chromium engine.
  - `c1f6a1a261`: Implement CLI scraper runner and swarm tool stealth.scrape with 7/7 tests.

---

## 🔗 Cross-Links & References
- [[056_Two_Track_SOTA_Repository_Assimilation_Architecture]] — пайплайн асиміляції SOTA технологій.
- [[063_Agent_Swarm_Architecture_Benchmark_2026]] — бенчмарки та топологія ройових агентів.
- [[000 DNK HUB Index]] — центральний індекс документації DNK OS.
