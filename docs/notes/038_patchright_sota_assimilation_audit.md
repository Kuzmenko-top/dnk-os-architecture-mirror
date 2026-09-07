---
title: "ADR 038: Patchright Stealth Browser Assimilation & Anti-Bot Evasion Architecture"
tags:
  - architecture
  - stealth
  - browser-automation
  - anti-detect
  - sota-assimilation
  - scraping
date: 2026-09-05
status: Active
version: 1.0.0
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/038_patchright_sota_assimilation_audit.md"
purpose: "Architecture Decision Record & SOTA Assimilation Audit for Patchright Undetectable Browser."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🥷 ADR 038: Аудит та Архітектура Асиміляції Patchright (Zero-CDP Stealth Browser)

## 📌 Context & Problem Statement
Для автономної роботи ройових агентів DNK OS ([[Gerych Prime - Unified Orchestrator & SOTA Adaptation Engine]], `dnk_shopify`, `gerych_researcher`) критично важливо здійснювати моніторинг цін конкурентів, збір документації, перевірку Shopify-магазинів та взаємодію з веб-додатками. Проте сучасні захисні антифрод-системи (**Cloudflare Turnstile**, **DataDome**, **Kasada**, **Akamai**) блокують стандартні інструменти автоматизації (Puppeteer, ванільний Playwright) через витоки у протоколі CDP та прапорці автоматизації.

Репозиторій **[Kaliiiiiiiiii-Vinyzu/patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)** пропонує революційне розв'язання цієї проблеми через AST-мутації кодової бази Playwright.

---

## 🔍 Глибокий Аудит Архітектури Patchright

### 1. Механізм AST-трансформації (`ts-morph`)
Замість підтримки складного та нестабільного форку, Patchright використовує скрипти на базі `ts-morph` (`patchright_driver_patch.ts`), які застосовуються безпосередньо до сирцевого коду `playwright-core`. Це гарантує безшовне оновлення з апстрім-версіями Microsoft Playwright.

### 2. Ключові Вектори Маскування (Stealth Invariants)
- **Zero-CDP Noise Suppression**: Повне вилучення викликів `Runtime.enable` та `Console.enable`. Антибот-скрипти більше не можуть зафіксувати активність через `Error.prepareStackTrace` чи глобальні слухачі консолі.
- **Евристика `globalThis`**: Context ID витягується через `objectId.split('.')[1]` одиночного запиту `Runtime.evaluate` без активізації домену подій.
- **Очищення прапорців Chromium**: Вилучення `--enable-automation`, додавання `--disable-blink-features=AutomationControlled`.
- **Crypto-Random InitScript Interception**: Мережеве перехоплення та ін'єкція скриптів ініціалізації з випадковими 20-байтними хеш-тегами без залишення артефактів у DOM.
- **Closed Shadow DOM Piercing**: Кастомний рушій `XPathSelectorEngine`, здатний взаємодіяти з елементами всередині закритих Shadow Root (зокрема віджетами Cloudflare Turnstile).

### 3. Ліцензійний Аудит
- **Ліцензія**: **Apache 2.0** (Track 1 Permissive).
- **Правовий статус**: Повна сумісність із пропрієтарним та комерційним кодом DNK OS без ризику вірусного copyleft-зараження.

---

## 🗺️ Дорожня Карта Поетапної Асиміляції в DNK OS

```
  +-----------------------------------------------------------+
  |  Етап 1: Hexagonal Port & Driver Adapter                 |
  |  (core/adapters/dnk_patchright_adapter.py)               |
  +-----------------------------------------------------------+
                               |
                               v
  +-----------------------------------------------------------+
  |  Етап 2: Swarm Worker Integration & Tooling              |
  |  (dnk_shopify, gerych_researcher, stealth tools)          |
  +-----------------------------------------------------------+
                               |
                               v
  +-----------------------------------------------------------+
  |  Етап 3: TLS / JA4 Fingerprint Hardening (Curtain)       |
  |  (Residential Proxy Pool + HTTP/2 Fingerprint Masking)    |
  +-----------------------------------------------------------+
                               |
                               v
  +-----------------------------------------------------------+
  |  Етап 4: Self-Healing & Bot-Defense Distillation         |
  |  (SCONES Cognitive Memory + Error Distillation DB)        |
  +-----------------------------------------------------------+
                               |
                               v
  +-----------------------------------------------------------+
  |  Етап 5: Continuous Verification & Master Quality Gate    |
  |  (Automated Tests + Evidence JSON Generation)             |
  +-----------------------------------------------------------+
```

### Деталізація етапів:
1. **Етап 1: Hexagonal Port & Adapter**:
   - Реалізовано `PatchrightBrowserPort` та адаптер `DNKPatchrightAdapter` (`core/adapters/dnk_patchright_adapter.py`).
   - Покриття тестами: `tests/stealth/test_patchright_adapter.py` (5/5 PASSED, 100% Green).
2. **Етап 2: Інтеграція в ройові агенти**:
   - Підключення адаптера до воркерів `dnk_shopify` (моніторинг конкурентів) та `gerych_researcher` (глибокий R&D захищених сайтів).
   - Створення навички `patchright_assimilated` в базі знань агентів.
3. **Етап 3: TLS / JA4 Hardening**:
   - Синхронізація відбитків TLS (JA3/JA4) через проксі-пул та модуль `curl_cffi` для усунення невідповідності між сигнатурами браузера та мережевого рівня.
4. **Етап 4: Дистиляція знань у SCONES**:
   - Фіксація патернів у довготривалій пам'яті SCONES (`SCONES-MEM-1788636422738`) для миттєвого самолікування при зміні евристик Cloudflare Turnstile.
5. **Етап 5: Автоматизована верифікація**:
   - Інтеграція перевірок у загальний CI/CD пайплайн `scripts/verify_all.sh`.

---

## 🔗 Зв'язки (Cross-Links)
- [[001 Obsidian & DNK OS Documentation Standard]]
- [[037_phase18_production_hardening]]
- [[Gerych Prime - Unified Orchestrator & SOTA Adaptation Engine]]
- `docs/tech/sota_assimilation/RN-038_patchright-research.md`
- `docs/tech/sota_assimilation/DNK-ARCH-038_patchright-patterns.md`
- `docs/tech/sota_assimilation/DNK-COMP-038_patchright-contracts.md`
- `docs/tech/sota_assimilation/DNK-SEC-038_patchright-execution-sandbox.md`
