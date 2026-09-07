---
title: "093 Результати Audit Slice 0.2-A: Контрактна Карта, Дублікати Роутерів та План Безпечної Міграції"
date: "2026-09-07"
tags:
  - audit-slice
  - api-contract
  - openapi
  - frontend
  - graphify
  - dnk-hub-0-2
status: completed
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/093_audit_slice_0_2_a_results_and_remediation.md"
# purpose: "Consolidated executive summary of Audit Slice 0.2-A for founder and mentor review"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 📌 Звіт за результатами Audit Slice 0.2-A: Контрактна карта API та Фронтенду

## 1. Що допомогло з наявних знань та інструментів
1. **Graphify AST Engine** (`graphify affected`): Розрахував точний радіус ураження (Blast Radius) для кожного роутера. Ми знаємо, що зміна `canvas.py` торкається 80 файлів та тестів, а `task_forest_router.py` — 88 файлів.
2. **FastAPI OpenAPI Introspection**: Завантажив живе ядро застосунку в пам'ять і виявив 627 діючих ендпоінтів та лавину `Duplicate Operation ID` UserWarnings.
3. **AST Static Code Analysis**: Дослідив структуру монтування в `apps/api/main.py`.
4. **Regex Scanner**: Знайшов 583 унікальних API-викликів у Next.js додатку (`apps/web`).

## 2. Головне фундаментальне відкриття аудиту
Чому виникали колізії ендпоінтів та чому ментор побачив дублювання:
1. **Подвійне ручне монтування**: Роутери `canvas`, `agent`, `artifact`, `analytics`, `taskdna`, `workflow_composer` підключалися вручну без префіксу і ще раз із префіксом `/api`.
2. **Потрійне динамічне монтування**: У рядках 195–207 `apps/api/main.py` стоїть блок `pkgutil.iter_modules`, який імпортує всі роутери з папки `apps.api.routers` і монтує їх **ще раз**!
3. **Фронтенд-розсинхрон**: Половина коду фронтенду звертається за старими адресами (`/canvas`, `/agent/run`), а інша половина — за новими (`/api/canvas`, `/api/agent/run`).

## 3. Створені артефакти
- Повна машинна карта контрактів: `docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.json`
- Детальний аналітичний звіт: `docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.md`
- Детермінований скрипт повторюваного аудиту: `scripts/audit_api_frontend_contracts.py`

## 4. Безпечний план виправлення (Zero-Downtime / Zero-Regression)
1. **Не чіпати роутери просто зараз наживо** (дотримано суворий Read-only протокол).
2. Надіслати цей звіт ментору.
3. У наступному підконтрольному кроці: уніфікувати фронтенд-клієнт на `/api/v1`, замінити потрійний автолоадер на явний канонічний реєстр і додати зворотний редирект для старих шляхів.
