---
title: "087 Open Design v0.21.1 Clean Assimilation & Adapter Zero-Regression Protocol"
date: "2026-09-07"
tags:
  - visual-shell
  - open-design
  - sota-assimilation
  - architecture
  - zero-waste
  - dnk-os
status: "Active"
version: "1.0.0"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/087_open_design_v0211_clean_assimilation_plan.md"
purpose: "Architectural blueprint and zero-regression execution plan for upgrading embedded Open Design from v0.18.1 to v0.21.1."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-07"
author: "Gerych Prime & Maxim Kuzmenko"
--- END DNK-MRH-HEADER -->

# 🎨 087 Open Design v0.21.1 Clean Assimilation & Adapter Zero-Regression Protocol

## 📌 Executive Summary

Підсистема **Visual Shell** у складі DNK OS наразі базується на версії **Open Design 0.18.1** (випущена 07.08.2026). Офіційний upstream-репозиторій [`nexu-io/open-design`](https://github.com/nexu-io/open-design) наразі має останній стабільний реліз **0.21.1** (випущений 31.08.2026: *"Community First: No Login Required"*).

Цей документ формулює **чистий ізольований пайплайн асиміляції (Clean Assimilation Pipeline)** для безпечного переходу з 0.18.1 на 0.21.1 без ризику втрати чи регресії локальних доробок та адаптерів DNK OS.

---

## 🔍 1. Аудит поверхні інтеграцій DNK OS (Touchpoint Inventory)

Локальна кодова база `visual_shell/open_design` містить 7 критичних точок розширення DNK OS, які **в жодному разі не можна перезаписувати сліпим копіюванням (Blind Rsync Prohibition)**:

| Компонент / Файл | Призначення в DNK OS | Ризик при оновленні |
|---|---|---|
| `apps/web/src/lib/dnk-api.ts` | Міст між Visual Shell та FastAPI Core (`apps/api`), диспетчер 14 Swarm-агентів, A2A federation. | Повна ізоляція Visual Shell від бекенду DNK OS при видаленні або перезаписі. |
| `apps/web/src/constants/swarm.ts` | SSOT конфігурація агентів Gerych (`gerych_builder`, `dnk_shopify`, `dnk_dev_fullstack` тощо). | Втрата інтерфейсу вибору ролей агентів у чаті. |
| `apps/web/src/components/stitch/` | Робоча область Stitch (Command Center, Task Forest Drawer, Stitch Canvas, Shopify Preview). | Втрата інтеграції з Task Forest та канвас-движком. |
| `apps/web/src/components/home/DnkModelGcpQuickBar.tsx` | Панель швидкого перемикання локальних та хмарних моделей (Vertex AI / GCP). | Втрата селектора моделей у головному вікні. |
| `apps/web/src/components/project-view/conversationUtils.ts` | Обробник помилок виконання, повторних спроб та зв'язка з `design-delivery`. | Помилки рендерингу діалогу та блокування чату. |
| `apps/daemon/src/routes/canvas-persistence.ts` | Ендпоінти збереження графів канвасу `dnk_canvases` у локальну SQLite базу. | Втрата автозбереження проєктів та стану нод. |
| `scripts/start_open_design.sh` | Скрипт оркестрації демона (порт 7456) та веб-клієнта (порт 5173), фіксація PATH для Node v25. | Конфлікт версій Node.js та ABI бібліотеки `better-sqlite3`. |

---

## ⚡ 2. Що нового в Upstream 0.21.1 (Delta & SOTA Benefits)

Між `0.18.1` та `0.21.1` відбулося **375 комітів** та змінено понад 300 файлів:

1. **Community First / No Login Required (v0.21.1)**:
   - Повне скасування обов'язкової хмарної аутентифікації для локального запуску моделей і сесій.
   - Спрощений запуск офлайн-воркспейсів без зовнішніх запитів на телеметрію.
2. **ACP (Agent Client Protocol) & SSE Reliability (v0.21.0)**:
   - Нове покоління протоколу зв'язку між клієнтом та агентом у бекенд-демоні (`acp/session.ts`, `acp/updates.ts`).
   - Автоматичне відновлення перерваних SSE-стрімів без дублювання кроків генерації.
3. **Headless High-Speed Export Engine (v0.20.2)**:
   - Експорт артефактів (HTML, SVG, PDF, презентації) за час < 1 хвилини через оптимізований фоновий пайплайн.
4. **Оновлений UI та SiriOrb (v0.20.0 – v0.20.1)**:
   - Сучасніший індикатор активності моделей у реальному часі (`SiriOrb`, `thinking-orbs`).
   - Покращений вибір контексту проєктів (`ProjectReferenceModal`).

---

## 🛡️ 3. Покроковий 6-Фазовий Пайплайн Асиміляції (Execution Plan)

### Фаза 0: Створення Snapshot & Захист Резервної Копії (Freeze)
```bash
# 1. Фіксуємо робочу гілку та створюємо окремий branch під оновлення
git checkout -b feature/open-design-0211-assimilation

# 2. Створюємо ізольований cold snapshot поточної робочої версії 0.18.1
cp -R visual_shell/open_design visual_shell/open_design.bak-0.18.1

# 3. Зупиняємо поточні активні процеси перед оновленням
pkill -f "apps/daemon/dist/cli.js" || true
pkill -f "next dev.*5173" || true
```

### Фаза 1: Ізольований Upstream Staging Sandbox (Zero-Rsync)
Завантаження апстріму виконується в окрему тимчасову директорію, без торкання робочого дерева `DNK_HUB`:
```bash
mkdir -p /tmp/open_design_staging
cd /tmp/open_design_staging
git clone --depth 1 --branch open-design-v0.21.1 https://github.com/nexu-io/open-design.git source-0.21.1
```

### Фаза 2: Автоматизований AST & Patch Replay
Перенесення кастомних модулів DNK поверх чистої кодової бази 0.21.1:
1. **Копіювання автономних DNK модулів**:
   - `apps/web/src/lib/dnk-api.ts` -> `source-0.21.1/apps/web/src/lib/dnk-api.ts`
   - `apps/web/src/constants/swarm.ts` -> `source-0.21.1/apps/web/src/constants/swarm.ts`
   - `apps/web/src/components/stitch/` -> `source-0.21.1/apps/web/src/components/stitch/`
   - `apps/web/src/components/home/DnkModelGcpQuickBar.tsx` -> `source-0.21.1/apps/web/src/components/home/`
   - `apps/daemon/src/routes/canvas-persistence.ts` -> `source-0.21.1/apps/daemon/src/routes/`
2. **Адаптерний мердж точок входу**:
   - Аудит та адаптація імпортів у `apps/web/src/components/project-view/conversationUtils.ts`.
   - Реєстрація роуту `canvas-persistence` в `apps/daemon/src/cli.ts` (або `server.ts` 0.21.1).
   - Ін'єкція `DnkModelGcpQuickBar` у новий `HomeView` версії 0.21.1.

### Фаза 3: Встановлення Залежностей та Збірка Бінарних Модулів (ABI Alignment)
```bash
cd /tmp/open_design_staging/source-0.21.1
export PATH="/opt/homebrew/bin:$PATH" # Node v25.9.0
pnpm install
pnpm rebuild better-sqlite3
pnpm --filter @open-design/contracts build
pnpm --filter @open-design/daemon build
pnpm --filter @open-design/web build
```

### Фаза 4: Верифікаційні Гейти (Quality Gates)
Перед заміною кодової бази у `visual_shell/open_design`:
1. **Gate 1**: Vitest перевірка вбудованих контрактів та демона:
   `pnpm test`
2. **Gate 2**: TypeCheck фронтенду:
   `pnpm --filter @open-design/web typecheck`
3. **Gate 3**: Тестовий підйом сервісів у staging-оточенні на альтернативних портах:
   - Daemon на порту `7457`
   - Web UI на порту `5174`
   - Перевірка: `curl -s http://127.0.0.1:7457/api/health` -> `{"ok":true,"version":"0.21.1"}`

### Фаза 5: Атомарна Заміна (Hot-Swap) та Перевірка DNK OS Тестів
```bash
# Атомарна підміна директорії
rm -rf visual_shell/open_design
mv /tmp/open_design_staging/source-0.21.1 visual_shell/open_design

# Запуск через канонічний скрипт
bash scripts/start_open_design.sh

# Запуск регресійного тестового набору DNK OS
./.venv/bin/pytest tests/verification/test_visual_shell.py
./.venv/bin/pytest tests/test_project_view_decomposition.py
./.venv/bin/pytest tests/test_architecture_guard_and_blast_radius.py
./.venv/bin/pytest tests/test_web_layer_isolation.py
```

### Фаза 6: Аварійний Відкат (Rollback Protocol)
Якщо бодай один інтеграційний тест падає або порушується зв'язок зі Swarm-агентами:
```bash
pkill -f "apps/daemon/dist/cli.js" || true
pkill -f "next dev.*5173" || true
rm -rf visual_shell/open_design
mv visual_shell/open_design.bak-0.18.1 visual_shell/open_design
bash scripts/start_open_design.sh
```
Час відкату: **< 15 секунд**.

---

## 📋 4. Чек-лист Відсутності Регресій (Regression Matrix)

- [ ] `GET http://127.0.0.1:7456/api/health` повертає `version: "0.21.1"` та `ok: true`.
- [ ] `GET http://localhost:5173` завантажує інтерфейс Open Design без Next.js runtime помилок у консолі.
- [ ] Панель `DnkModelGcpQuickBar` присутня у верхній частині інтерфейсу та дозволяє обирати моделі.
- [ ] У меню створення проєкту доступний Stitch Swarm Command Center.
- [ ] Виклики до `dnk-api.ts` надсилають запити на `http://localhost:8000/api/v1/swarm/dispatch`.
- [ ] Канвас Excalidraw успішно серіалізує та зберігає дані через ендпоінт `canvas-persistence`.
- [ ] Тести `tests/verification/test_visual_shell.py` проходять на 100% (7/7 Green).
- [ ] Тести ізоляції шарів `tests/test_web_layer_isolation.py` підтверджують нульовий витік портів.

---

## 🔗 Зв'язки з іншими документами (Obsidian Graph)
- [[000 DNK HUB Index]] — Головний навігаційний хаб DNK OS.
- [[002 DNK OS - Master System Architecture & Implementation Blueprint]] — Загальна архітектура системи.
- [[005 ADR 0042 Canvas Runtime Bridge & WebSocket Integration]] — Специфікація канвас-моста.
- [[022 CapCut and Stitch Visual Cabinet with Conversational Gerych Intake]] — Архітектура робочої області Stitch.
- [[076_dnk_os_2_0_master_architecture_blueprint]] — Архітектурний фундамент DNK OS 2.0.
