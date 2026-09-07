---
title: "DNK OS Monitoring, Metrics & Alerting Architecture"
date: "2026-09-05"
tags:
  - architecture
  - monitoring
  - prometheus
  - alerting
  - dnk-os
  - sota
status: active
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs_notes_014_monitoring_and_alerting_architecture"
purpose: "Architectural Decisions & Implementation Record for DNK OS Monitoring & Alerting (Slice 12.3)"
author: "DNK-e.com Maksym & Gerych Prime"
license: "DNK-INTERNAL"
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
--- END DNK-MRH-HEADER -->

# 📊 DNK OS Monitoring, Prometheus Metrics & Alerting Architecture

## 1. Overview & Motivation
В межах **Слайсу 12.3** розроблено та інтегровано високопродуктивну підсистему моніторингу та оповіщення для екосистеми [[DNK OS]]. Підсистема забезпечує прозорість функціонування ядра, API, баз даних та розподілених робітників Swarm.

Пов'язані компоненти:
- [[apps/api/monitoring/health_check.py]] — Engine перевірки життєдіяльності та стану залежностей.
- [[apps/api/monitoring/metrics.py]] — Prometheus-сумісний колектор та експортер системних і бізнес-метрик.
- [[apps/api/monitoring/alerts.py]] — Мультиканальний диспетчер сповіщень (Slack, Email) з тротлінгом і дедуплікацією.
- [[apps/api/routers/health.py]] — REST ендпоінти K8s Liveness/Readiness та Prometheus scraping.
- [[docs/monitoring/ALERTING.md]] — Інженерна специфікація та Runbook.

---

## 2. Ключові Архітектурні Рішення (ADR)

### ADR-01: Розділення Liveness та Readiness Probes
- **Liveness (`/health/live`)**: Миттєва перевірка доступності циклу подій (event loop) без зовнішніх викликів. Захищає процес від зависання.
- **Readiness (`/health/ready`)**: Перевірка готовності компонентів (БД, кеш, дисковий простір, пам'ять). Якщо компонент деградував або відмовив — повертає `503 Service Unavailable`, що сигналізує балансувальнику тимчасово зняти трафік.
- **Detailed Diagnostics (`/health/detailed`)**: Глибокий звіт для інженерів та адмін-панелі DNK OS.

### ADR-02: OpenMetrics & Prometheus Client з Graceful Fallback
- `MetricsRegistry` автоматично інтегрується з `prometheus_client` при його наявності у віртуальному оточенні.
- При відсутності зовнішньої бібліотеки використовується внутрішній zero-dependency генератор формату OpenMetrics 0.0.4.
- Підтримуються типи `Counter`, `Gauge`, `Histogram` для затримок HTTP, завантаження CPU/RAM, статусу задач Swarm та викликів алертів.

### ADR-03: Throttling & Cooldown для Алертингу
- Запобігання "alert fatigue" та спаму в критичних ситуаціях.
- Розрахунок хешу відбитка алерту: `fingerprint = f"{service}:{component}:{title}"`.
- Інтервал охолодження: 300 секунд (налаштовується).
- Алерти рівня `CRITICAL` мають пріоритет та обходять блокування.

---

## 3. Метрики та Валідація
Створено повний набір інтеграційних та юніт-тестів у `apps/api/tests/test_monitoring.py`.
Всі 14 тестів пройдено успішно:
- Liveness / Readiness валідація
- Динамічна реєстрація власних діагностичних перевірок
- Збір та експорт метрик у форматі Prometheus
- Емуляція Slack та SMTP відправки
- Тротлінг та обхід тротлінгу для `CRITICAL` інцидентів
- REST роутер та Swagger метадані
