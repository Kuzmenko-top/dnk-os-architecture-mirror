---
title: "014 Mentor Architecture Roadmap: Reactive Bridge, OCC, Swarm HUD & Health"
date: "2026-09-06"
tags:
  - architecture
  - obsidian-canvas
  - react-flow
  - swarm-orchestration
  - telemetry
status: "In-Progress"
author: "Gerych Prime & Maxim Kuzmenko"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/014 Mentor Architecture Roadmap.md"
purpose: "Canonical Mentor Roadmap & Architecture Decisions for DNK OS Visual Bridge & Swarm Telemetry."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🗺️ 014 Mentor Architecture Roadmap: Visual Bridge & Swarm Telemetry

Цей документ фіксує узгоджену архітектурну стратегію розвитку взаємодії між [[012 TaskForest Canvas and Bi-directional Markdown Architecture|Obsidian Canvas]], веб-інтерфейсом React Flow та розподіленим роєм агентів [[001 Unified Agent Architecture|DNK OS Swarm]].

---

## 🎯 4 Ключові Архітектурні Вектори

### 1. Пріоритет А: Реактивний FileWatcher для Canvas Bridge (Push замість Polling)
- **Статус**: ✅ **Реалізовано (2026-09-06)**
- **Модуль**: `apps/api/routers/canvas_bridge.py` (`@router.websocket("/ws")`)
- **Механізм**: Асинхронний бекграунд-таск `file_watcher` відстежує `mtime` цільового `.canvas` файлу (кожні 500ms).
- **Поведінка**: При зовнішньому збереженні в Obsidian сервер автоматично транслює пакет `{"type": "CANVAS_UPDATE", "source": "file_watcher", "react_flow": {...}}` всім підключеним клієнтам React Flow без необхідності ручного опитування або перезавантаження сторінки.

### 2. Пріоритет Б: Оптимістичний Контроль Конфліктів (OCC 3-Way Merge)
- **Статус**: ✅ **Реалізовано (2026-09-06)**
- **Модулі**: `apps/api/routers/canvas_bridge.py` (`POST /api/v1/canvas/bridge/merge`, WebSocket action `merge`), `core/occ_merge.py` (`OCCConcurrencyEngine`)
- **Ціль**: Усунення проблем паралельного редагування (*Last Write Wins*) при одночасній зміні полотна у вебі та Obsidian.
- **Підхід**: Використання `OCCConcurrencyEngine.merge_graph_state`:
  - *Base State*: стан графа на момент отримання клієнтом (`base_flow`).
  - *Server State*: актуальний `.canvas` на диску (`theirs_flow`).
  - *Client State*: вхідна мутація від React Flow (`incoming_flow`).
  - *Результат*: Тристороннє злиття зберігає паралельно додані вузли та ребра з обох джерел, запобігає затиранню правок та повертає повну структуру `react_flow` і список вирішених колізій. Тести перевірено на 100%.

### 3. Пріоритет В: Live Swarm HUD — Візуалізація Роботи Агентів на Полотні
- **Статус**: ✅ **Реалізовано (2026-09-06)**
- **Модулі**: `apps/api/routers/canvas_bridge.py` (`POST /events/swarm`, `POST /swarm-hud`, WebSocket action `swarm_event`, `CanvasBridgeConnectionManager`), `core/orchestrator/visual_canvas_control.py` (`SWARM_WORKER_COLORS`), `apps/web/types/canvasBridge.ts`
- **Ціль**: Візуальний моніторинг життєвого циклу завдань у реальному часі без перезавантаження сторінки.
- **Підхід**:
  - Трансляція легкозважених подій життєвого циклу воркерів (`TASK_STARTED`, `TASK_PROGRESS`, `TASK_COMPLETED`, `TASK_FAILED`).
  - Візуальне кодування агентів рою (бейджі, кольори Obsidian Canvas, HEX кольори для вебу, прогрес-бари `render_progress_bar`).
  - Підтримка опціонального збереження мутацій ноди на диску (`update_canvas_disk=True`) для постійної синхронізації з Obsidian.
  - Менеджер WebSocket підключень `CanvasBridgeConnectionManager` для миттєвої доставки подій усім підключеним клієнтам React Flow (`type: "SWARM_HUD_EVENT"`).

### 4. Пріоритет Г: Єдиний Swarm Health Dashboard (`/api/v1/health/swarm`)
- **Статус**: ✅ **Реалізовано (2026-09-06)**
- **Ціль**: Агрегація діагностичних метрик системи в єдиний легкий JSON ендпоінт та стрімінговий WebSocket.
- **Складові**:
  - `active_workers`: статус 14 агентів рою, бейджі, HEX та Canvas кольори, деталі можливостей (`capabilities`).
  - `sentinel`: активні аномалії з `data/sentinel_alerts.json`, підрахунок критичних та попереджувальних інцидентів, кількість незакритих планів самозцілення `docs/plans/self_heal/`.
  - `accounting`: спалювання токенів, загальні витрати, відсоток вичерпання бюджету сесії з `AccountingEngine`.
  - `canvas_bridge`: статус WebSocket мосту, кількість активних з'єднань, зареєстровані полотна та лічильник надісланих подій (`CanvasBridgeConnectionManager.get_stats()`).
  - `system`: uptime процесу, RSS використання оперативної пам'яті, версія Python та платформи.
- **Ендпоінти**:
  - `GET /api/v1/health/swarm` (і кореневий псевдонім `GET /health/swarm`) з підтримкою фільтрів `workspace_id`, `details`, `spend_limit_usd`.
  - `WebSocket /api/v1/health/swarm/ws` для миттєвого знімка стану (`SWARM_HEALTH_SNAPSHOT`), push-оновлень (`refresh`) та перевірки життєздатності (`ping`/`pong`).
- **Тести**: `tests/verification/test_swarm_health_dashboard.py` (13/13 тестів, 100% Green).

---

## 🔗 Пов'язані матеріали
- [[012 TaskForest Canvas and Bi-directional Markdown Architecture]]
- [[013 Bi-directional Canvas Obsidian Sync Bar Integration]]
- [[001 Unified Agent Architecture]]
