---
title: "057 Strategy Visual Shell Consolidation & Targeted Architecture"
date: "2026-09-06"
tags:
  - architecture
  - visual-shell
  - consolidation
  - blast-radius
  - adr
  - strategy
aliases:
  - "016 Strategy Visual Shell Consolidation & Targeted Architecture"
status: "completed"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/057 Strategy Visual Shell Consolidation & Targeted Architecture.md"
purpose: "ADR & Strategic Blueprint for Option B: Consolidating visual_shell capabilities into apps/web, targeted CI via blast radius, and automated API-Frontend contracts"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Completed"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

E7 Стратегія Консолідації Visual Shell та Таргетної Архітектури

## 1. Контекст та Стратегічне Рішення (Варіант Б)
За результатами всебічного ретроспективного аналізу кодової бази та узгодження з Максимом прийнято рішення про реалізацію **Варіанта Б**:
- **Уніфікація Фронтенду**: Повна консолідація корисних та унікальних візуальних компонентів (редактор нод, візуальний таймлайн, робочі полотна канвасу) з `visual_shell/open_design` безпосередньо в нативну структуру `apps/web/`.
- **Єдине Джерело Правди (SSOT)**: `apps/web/` стає єдиним фронтенд-додатком екосистеми DNK OS. Це усуває подвійну підтримку залежностей (`node_modules`), розбіжності в типах та прискорює збірку.
- **Архівування застарілого коду**: Після міграції віджетів та конфігурацій застаріла монолітна оболонка `visual_shell` переводиться в статус архіву або видаляється з активного білд-контуру.

---

## 2. Реалізовані Компоненти & Перші Результати

### 2.1. Таргетний CI через Blast Radius (`verify_all.sh --affected`)
- **Реалізація**: Впроваджено прапорець `--affected` (або `-a`) у головний верифікатор `scripts/verify_all.sh`.
- **Механізм**:
  1. Інтегровано клас `BlastRadiusAnalyzer`, що сканує `git status` / `git diff`.
  2. Визначаються конкретні регресійні тести (`required_pytests` та `required_vitests`), які покривають змінені файли.
  3. Якщо змінено бекенд або утиліти — запускаються лише зачеплені тести (замість повного прогону понад 2000 тестів).
- **Результат**: Час проходження скоротився з **4–5 хвилин до ~8.5 секунд** при 100% збереженні перевірок безпеки, Docker, git-гігієни, циклів імпорту та TypeScript-типізації.

---

## 3. Статус Реалізації (Всі Етапи Завершено)

### 3.1. Фаза 2 Декомпозиції `ProjectView` & Модуляризації
- ✅ Виділено модульний пакет `project-view/` з ізоляцією хуків та типів.
- ✅ Декомпозиція God-компонента пройшла аудит `architecture_and_cycle_guard.py` (0 циклів, повна модульність).

### 3.2. Автоматична Генерація Контрактів API ↔ Frontend
- ✅ Створено скрипт `scripts/system/generate_frontend_types.py`.
- ✅ Автоматично експортовано OpenAPI 3.1 схему з FastAPI (`apps/web/openapi.json` — 558 шляхів, 384 схеми).
- ✅ Згенеровано строгі TypeScript-типи у `apps/web/types/apiGenerated.ts` через `openapi-typescript` та інтегровано в `apiProtocol.ts`.

### 3.3. Жива Синхронізація Obsidian Canvas
- ✅ Розроблено `scripts/system/sync_codebase_to_canvas.py` на базі AST-аналізу роутерів, агентів, сторів та сервісів.
- ✅ Згенеровано інтерактивний граф системи у `docs/notes/DNK_HUB_Core_Architecture.canvas` (5 груп, 33 ноди, 15 зв'язків).

### 3.4. Міграція Stitch-Компонентів та Депрекація `visual_shell`
- ✅ Перенесено всі 6 ключових віджетів до `apps/web/components/stitch/`:
  1. `StitchSwarmCommandCenter.tsx`
  2. `StitchKineticTimeline.tsx`
  3. `StitchSmartInspector.tsx`
  4. `StitchShopifyPreviewDrawer.tsx`
  5. `StitchBiAnalystDrawer.tsx`
  6. `StitchTaskForestDrawer.tsx`
  7. `index.ts` (barrel export).
- ✅ Оновлено `visual_shell/README.md` та створено `visual_shell/DEPRECATED.md`: каталог офіційно заморожено, єдиним SSOT є `apps/web/`.
- ✅ Покриття тестами у `tests/test_consolidation_variant_b.py` (5/5 passed).


---

## 4. Зв'язки з іншими документами
- [[053 Architecture Defense & Blast Radius Gate]] — Впровадження базових гвардів та blast radius аналізатора.
- [[DNK_HUB My Notes/013 Canvas Engine Architecture]] — Специфікація архітектури Canvas Engine.
- `AGENTS.md` — Інваріанти Zero-Waste Swarm Protocol.
