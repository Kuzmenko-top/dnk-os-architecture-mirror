# --- DNK-MRH-HEADER ---
# mrh_id: "canvas-backend-ownership.md"
# purpose: "Архітектурний розподіл відповідальності (Backend Ownership) між Express та FastAPI для Canvas Engine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# Canvas Backend Ownership & Integration Architecture

Цей документ зафіксовує остаточне архітектурне рішення щодо розподілу обов'язків між Express Daemon та FastAPI у складі DNK OS Canvas Engine.

---

## 1. Розподіл архітектурних зон (Ownership Matrix)

| Функція / Сфера | Первинний Власник (Canonical Owner) | Другорядний Власник (Secondary Owner) | Деталі та Границі |
| :--- | :--- | :--- | :--- |
| **Canonical Canvas API** | **FastAPI** (`dnk_orchestrator`) | Express (Proxy) | Усі персистентні операції над Canvas належать FastAPI. |
| **Database Owner** | **FastAPI** (`dnk_db`) | None | PostgreSQL БД кешується та управляється через SQLAlchemy/Alembic у FastAPI. |
| **Local Daemon Only** | **Express** (`apps/daemon`) | None | Локальний запуск Docker-контейнерів, локальні файлові операції. |
| **Authentication** | **FastAPI / JWT** | Express (Token Forward) | FastAPI верифікує токени доступу (JWT). |
| **Authorization** | **FastAPI / RBAC** | Express | Перевірка прав доступу до конкретних `canvas_id` на основі ролей. |
| **Event Publisher** | **FastAPI / Redis** | Express (SSE Bridge) | Публікація подій через Redis Pub/Sub, Express ретранслює їх у SSE. |
| **OpenAPI Source** | **FastAPI** | None | Єдиним джерелом специфікацій OpenAPI є FastAPI `/openapi.json`. |
| **Migrations** | **FastAPI / Alembic** | None | Усі міграції таблиць Canvas виконуються через Alembic (Python). |

---

## 2. Детальний опис рішень

### 1. Canonical API Owner
**FastAPI** є єдиним canonical-власником Canvas API. Будь-які запити на створення, модифікацію, видалення полотен та знімків (snapshots) обробляються первинно сервісом FastAPI.

### 2. Express Daemon Responsibility
Express виступає як **Local Sidecar / Proxy**:
- Ретранслює запити від TMA (Telegram Mini App) клієнта до FastAPI бекенду.
- Керує локальними статичними ресурсами та бінарними файлами (Images/Assets), які завантажуються на локальний диск перед збереженням у хмару S3/GCS.
- Здійснює запуск локальних Docker-середовищ для агентів розробки.

### 3. FastAPI Responsibility
FastAPI є **Core Orchestrator**:
- Виконує бізнес-логіку збереження сцени, перевірки прав доступу, валідації схем та версіонування.
- Взаємодіє з PostgreSQL для персистентного збереження метаданих та знімків Canvas.
- Запускає черги завдань агентів через Celery/Redis.

### 4. Database Owner
База даних PostgreSQL (`dnk_db`) повністю належить сервісу FastAPI. Схеми таблиць Canvas та Snapshots описуються як SQLModel/SQLAlchemy класи у Python. Експрес-демон не має прямого доступу на запис/читання в БД PostgreSQL для запобігання десинхронізації схем.

### 5. Authentication Boundary
Кордон автентифікації проходить на рівні FastAPI:
- Кожен запис Canvas містить заголовок `Authorization: Bearer <JWT_TOKEN>`.
- FastAPI перевіряє підпис токена. Express Daemon просто пересилає заголовок без власної дешифрації, виступаючи транзитним проксі.

### 6. Authorization Boundary (RBAC)
Запит на доступ до конкретного Canvas ID перевіряється FastAPI за схемою:
- Власник проекту (Owner) має повні права (Read/Write/Delete).
- Запрошені учасники (Peers) мають обмежені права (Read/Write).
- Сторонні запити повертають `403 Forbidden` або `401 Unauthorized`.

### 7. Event Publisher
Усі події змін сцени полотна та запусків агентів (`agent.run.*`) публікуються FastAPI у Redis-канал. Express Daemon підписується на Redis і транслює ці події клієнтам у формі Server-Sent Events (SSE).

### 8. OpenAPI Source
Вся документація API є автоматично генерованою з FastAPI за допомогою Swagger/ReDoc. Будь-які зміни в специфікації Canvas API здійснюються в FastAPI.

### 9. Migration Owner
Усі таблиці сцени, елементів, мета-інформації та файлів мігруються виключно через **Alembic** (Python). Express Daemon не містить міграційних SQL скриптів.

### 10. Deprecation Plan for Duplicate Routes
Для усунення дублювання логіки збереження:
1. Поточні тимчасові маршрути Express `/api/v1/canvases/*` перетворюються на проксі-маршрути до відповідних FastAPI ендпоінтів `http://dnk-orchestrator:8000/api/v1/canvases/*`.
2. Файлова локальна персистентність Express в `.od/dnk_canvases` залишається виключно як автономний резервний офлайн-режим (Standalone Fallback).
3. Після повної інтеграції `dnk_orchestrator` локальний файловий режим в Express депрекується протягом 3 місяців, залишаючи Express суто в ролі ретранслятора.

---

## 3. Database Technology & Production Migration Status

> [!IMPORTANT]
> **DATABASE STATUS & POLICY GATES**:
> 
> 1. **SQLite is development/fixture-only**:
>    The local SQLite database (`canvas_engine.db`) initialized and managed inside `canvas-persistence.ts` is strictly for development, testing, and fixture-only simulation workflows. It must never be deployed in any multi-user production environment.
> 
> 2. **PostgreSQL is the canonical production database**:
>    The production persistent data store is PostgreSQL, managed and queried exclusively through the FastAPI `dnk_orchestrator` service using SQLAlchemy/SQLModel structures.
> 
> 3. **FastAPI owns canonical persistence API**:
>    All permanent data modifications and element state persistence must eventually live on the FastAPI endpoints.
> 
> 4. **Production PostgreSQL migration: NOT DONE**:
>    The automatic DB migration scripts (Alembic) to port the local Excalidraw element snapshots, design runs, and audit logs into PostgreSQL tables are **NOT DONE**. The local SQLite file store currently acts as the single active persistence engine for this local pre-release slice.
