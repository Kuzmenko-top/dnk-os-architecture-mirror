---
title: "DNK OS 0.2 API Schema & Frontend Contract Alignment Map v0.1"
date: "2026-09-07"
status: "Completed (Read-Only Audit)"
mrh_id: "docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.md"
purpose: "Comprehensive mapping of FastAPI routers, mounts, duplicate aliases, frontend consumers, tests, and Graphify blast radius"
canonical_source: true
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.md"
# purpose: "Comprehensive mapping of FastAPI routers, mounts, duplicate aliases, frontend consumers, tests, and Graphify blast radius"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🎯 Audit Slice 0.2-A: API Schema & Frontend Contract Alignment Report

## 📊 1. Executive Summary
- **Total OpenAPI Endpoints**: 627
- **Root vs `/api` Paired Aliases (Exact Duplicates)**: 13
- **Duplicate Operation IDs in Schema**: 0
- **Frontend Consumers Scanned (`apps/web`)**: 583 unique endpoint paths
- **Tested Endpoints**: 413
- **Untested / Internal-Only Endpoints**: 214

---

## 🔍 2. Root Cause Analysis: Дубльоване Монтування в `apps/api/main.py`
У файлі `apps/api/main.py` виявлено **34 ручних викликів `include_router`**.

### 2.1. Подвійне ручне монтування:
Шість ключових роутерів монтуються двічі вручну:
1. `canvas.router` -> без префіксу + `prefix='/api'`
2. `agent.router` -> без префіксу + `prefix='/api'`
3. `artifact.router` -> без префіксу + `prefix='/api'`
4. `analytics.router` -> без префіксу + `prefix='/api'`
5. `taskdna.router` -> без префіксу + `prefix='/api'`
6. `workflow_composer.router` -> без префіксу + `prefix='/api'`

### 2.2. Потрійне монтування через динамічний pkgutil-автолоадер:
У рядках 195–207 `apps/api/main.py` виконується динамічний імпорт усіх модулів із `apps.api.routers`:
```python
for _, mod_name, is_pkg in pkgutil.iter_modules(routers_pkg.__path__):
    if hasattr(mod, 'router'):
        app.include_router(mod.router)
```
**Наслідок**: роутери, які вже були підключені вручну, підключаються **втретє**. Це створює множинні `operation_id` колізії в OpenAPI.

---

## 👥 3. Зіставлення з Frontend Споживачами (`apps/web`)
Аналіз показав, що фронтенд використовує суміш обох варіантів:
| Frontend Endpoint Call | Де використовується (компоненти) | Стан на бекенді |
|---|---|---|
| `/web-pixel/metrics` | `usePixelEvents.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/agents` | `useAgents.ts, useCreateAgent.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/memory/l3/memories` | `apiGenerated.ts, useSCONESL3Memory.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/memory/l3/stats` | `apiGenerated.ts, useSCONESL3Memory.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/memory/l3/consolidate` | `apiGenerated.ts, useSCONESL3Memory.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/patent-shield/search` | `apiGenerated.ts, usePatentShield.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/patent-shield/risk-assessment` | `apiGenerated.ts, usePatentShield.ts` | ℹ️ Специфічний маршрут |
| `/api/v1/agents/metrics` | `useAgentMetrics.ts` | ℹ️ Специфічний маршрут |
| `/canvas` | `LaunchpadView.tsx, CommandBar.tsx (+1)` | ✅ Є і в `/` і в `/api` |
| `/canvas/{canvas_id}` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/api/canvas` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/api/canvas/{canvas_id}` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/agent/run` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/agent/swarm/dispatch` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/agent/swarm/adversarial-review` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/agent/swarm/status` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/agent/deploy/pr` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/api/agent/run` | `page.tsx, apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/api/agent/swarm/dispatch` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/api/agent/swarm/adversarial-review` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/api/agent/swarm/status` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/api/agent/deploy/pr` | `ArtifactPanel.tsx, apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/artifact/{canvas_id}` | `apiGenerated.ts` | ✅ Є і в `/` і в `/api` |
| `/api/artifact/{canvas_id}` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |
| `/api/analytics/overview` | `apiGenerated.ts` | ℹ️ Специфічний маршрут |

---

## 🧪 4. Тестове Покриття та Захист Контрактів
- **Захищені тестами endpoints**: 413
- **Без прямих тестів (Internal / Orphaned)**: 214

---

## 🕸️ 5. Graphify Blast Radius (Радіус Ураження)
Детермінований розрахунок зв'язків через AST Tree-sitter:
| Роутер | Залежних файлів та тестів | Приклади ключових тестів |
|---|---|---|
| `apps/api/routers/canvas.py` | **80** | `api/main.py, routers/__init__.py, verify_fast_endpoints.py` |
| `apps/api/routers/agent.py` | **80** | `api/main.py, routers/__init__.py, verify_fast_endpoints.py` |
| `apps/api/routers/artifacts.py` | **0** | `` |
| `apps/api/routers/analytics.py` | **80** | `api/main.py, routers/__init__.py, verify_fast_endpoints.py` |
| `apps/api/routers/taskdna.py` | **80** | `api/main.py, routers/__init__.py, verify_fast_endpoints.py` |
| `apps/api/routers/node_tasks_router.py` | **86** | `api/main.py, routers/__init__.py, test_occ_merge.py` |
| `apps/api/routers/task_forest_router.py` | **88** | `api/main.py, routers/__init__.py, ._init_default_forest()` |
| `apps/api/routers/shopify.py` | **82** | `api/main.py, routers/__init__.py, test_shopify_router.py` |
| `apps/api/routers/video_router.py` | **80** | `api/main.py, routers/__init__.py, verify_fast_endpoints.py` |
| `apps/api/routers/workspace.py` | **81** | `api/main.py, routers/__init__.py, ws_workspace_endpoint()` |

---

## 🛡️ 6. Rollback-Safe Migration Order (Рекомендація для DNK HUB 0.2)
Щоб перейти до чистих канонічних роутерів без ламання тестів та фронтенду:
1. **Крок 1**: Впровадити в `apps/web` єдиний API-клієнт (`apiClient.ts`), який завжди додає базовий префікс `/api/v1`.
2. **Крок 2**: У `apps/api/main.py` вимкнути неконтрольований динамічний `pkgutil.iter_modules` лоадер.
3. **Крок 3**: Змонтувати всі канонічні роутери виключно під єдиним канонічним префіксом `/api/v1`.
4. **Крок 4**: Залишити тимчасовий FastAPI `Middleware` або 307/308 redirect для застарілих шляхів `/canvas/*` -> `/api/v1/canvas/*` на період перехідного тестування.
5. **Крок 5**: Запустити `verify_all.sh` для підтвердження 100% Green статусу.
