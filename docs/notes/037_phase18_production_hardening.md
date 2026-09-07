---
title: "037 Phase 18 Production Hardening: RateLimiter Middleware, Prometheus Metrics, Off-site Backups and Grafana Validation"
tags:
  - architecture
  - security
  - observability
  - devops
  - quality-gates
created: 2026-09-06
author: Gerych Prime (Chief Builder) & Maxim
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/037_phase18_production_hardening.md"
purpose: "Architecture documentation for Phase 18 Production Hardening: RateLimiter Middleware, Prometheus Metrics, Cloud Backups, and Grafana Dashboard Validation."
canonical_source: true
alters_files: [
  "apps/api/middleware/rate_limit.py",
  "apps/api/main.py",
  "scripts/backup/backup_database.sh",
  "scripts/system/validate_grafana_dashboards.py",
  "tests/security/test_rate_limiter_middleware.py",
  "tests/monitoring/test_prometheus_metrics.py",
  "tests/system/test_validate_grafana_dashboards.py"
]
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🛡️ 037 Phase 18 Production Hardening: Architectural Blueprint

## 1. Контекст та Передумови
Після успішного завершення системного Плану 17 ([[task_050926-3_systemic_quality_gates|Системні Quality Gates]]), було ініційовано пакет удосконалень **Phase 18 Production Hardening** для підвищення стійкості DNK OS у бойових умовах:
1. Захист API від DDoS, брутфорсу та вичерпання ресурсів через ковзний лімітер запитів.
2. Експорт метрик Prometheus (`GET /metrics`) для моніторингу затримок, 5xx та активних з'єднань.
3. Хмарна реплікація бекапів бази даних (S3, Cloudflare R2, MinIO).
4. Автоматизована валідація схем дашбордів Grafana для запобігання пошкодженню візуальних панелей.

---

## 2. Компоненти Архітектури

### 2.1. RateLimiter Middleware (`apps/api/middleware/rate_limit.py`)
- **Алгоритм**: Sliding Window Rate Limiter.
- **Failover / Resiliency**: Первинне підключення до Redis (`scripts.security.rate_limiter.RateLimiter`), з автоматичним плавним переходом (fallback) на `InMemorySlidingWindowLimiter` при недоступності Redis або у локальних середовищах.
- **Рівні лімітів (Tiered Limits)**:
  - Чутливі шляхи (`/auth`, `/checkout`, `/webhooks`): 20 запитів / 60 сек.
  - Загальні API ендпоінти: 100 запитів / 60 сек.
  - Системні байнпаси: `/health`, `/api/health`, `/metrics`, `/docs`, `/openapi.json`.
  - Тестовий байпас: активується при `TESTING=1` або `PYTEST_CURRENT_TEST`.
- **Заголовки**: Повертає `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` та `Retry-After` при HTTP 429.

### 2.2. Prometheus Metrics Instrumentation (`apps/api/main.py`)
- **Ендпоінт**: `GET /metrics` повертає телеметрію у форматі OpenMetrics/Prometheus.
- **Метрики**:
  - `http_requests_total`: лічильник запитів за методом, нормалізованим маршрутом та HTTP статусом.
  - `http_request_duration_seconds`: гістограма розподілу тривалості обробки запитів.
- **Нормалізація**: Маршрути прив'язуються до схеми `request.scope['route'].path` для запобігання розриву кардинальності метрик.

### 2.3. Хмарна Реплікація Резервних Копій (`scripts/backup/backup_database.sh`)
- Підтримка змінних середовища `AWS_S3_BUCKET`, `S3_ENDPOINT_URL` (Cloudflare R2, MinIO, Wasabi), `S3_STORAGE_CLASS`.
- Захист від падінь при відсутності `aws` CLI або у тестових середовищах через `BACKUP_DRY_RUN=1`.
- Автоматичне шифрування AES-256-CBC з PBKDF2 перед вивантаженням.

### 2.4. Grafana Dashboard Validator (`scripts/system/validate_grafana_dashboards.py`)
- Перевіряє синтаксичну валідність JSON та структурну цілісність панелей у `monitoring/grafana_dashboards/` та `monitoring/grafana/dashboards/`.
- Гарантує наявність метричних виразів (`expr`) у кожному таргеті панелей.

---

## 3. Верифікація та Результати
- `tests/security/test_rate_limiter_middleware.py`: 5/5 PASSED.
- `tests/monitoring/test_prometheus_metrics.py`: 1/1 PASSED.
- `tests/system/test_validate_grafana_dashboards.py`: 3/3 PASSED.
- `scripts/system/validate_grafana_dashboards.py`: All 2 Grafana dashboards passed schema validation.
- `scripts/backup/backup_database.sh`: DRY-RUN off-site replication tested with Cloudflare R2 endpoint.
