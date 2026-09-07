---
title: "073 Gemini Output Drift Monitoring, Autonomous Self-Healing, and Real-Time Telemetry"
date: "2026-09-07"
tags:
  - architecture
  - soup
  - sota
  - scones
  - drift-monitoring
  - self-healing
  - prometheus
  - grafana
  - visual-shell
status: "Completed"
version: "1.0.0"
author: "Gerych Prime & Maksym Kuzmenko"
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs_notes_073_gemini_drift_self_healing_telemetry"
# purpose: "Architecture documentation and reference for Gemini drift monitoring, autonomous self-healing, Welford/EMA streaming baselines, and Prometheus/Grafana telemetry."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧠 073 Gemini Output Drift Monitoring, Autonomous Self-Healing & Visual Telemetry

## 📌 Огляд та Мотивація

Під час роботи великих мультимодальних мовних моделей (зокрема сімейства **Google Gemini 2.5/Flash**) у високоінтенсивних агентних контурах виникають системні ризики:
1. **Колапс ентропії (Entropy Collapse)** — зациклення токенів, повторення шаблонів та генерація галюцинаторних петель.
2. **Стрибки довжини (Length Shift)** — раптова надмірна багатослівність або, навпаки, обрив генерації без завершення структури.
3. **Дегенерація JSON (Syntax Degeneration)** — синтаксичні дефекти (висячі коми, незакриті дужки, unquoted ключі, markdown-обгортки).
4. **Накопичення пам'яті $O(N)$** — традиційні монітори зберігають усю історію відповідей для обчислення середнього та дисперсії, що спричиняє вичерпання RAM в довготривалих сесіях.

Для вирішення цих викликів у **DNK OS** реалізовано 4-рівневий замкнений контур спостережуваності та автономного відновлення на базі асимільованих архітектурних патернів **MakazhanAlpamys/Soup** та внутрішньої пам'яті **SCONES**.

---

## 🏗️ 4-Рівнева Архітектура Замкненого Контуру

```
   ┌──────────────────────────────────────────────────────────────┐
   │                   Рівень 1: Вхідний Запит                     │
   │           Zero-Click SCONES Middleware Перехоплення          │
   └──────────────────────────────┬───────────────────────────────┘
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │             Рівень 2: Виконання & Генерація LLM              │
   │               (Gemini 2.5 Pro / Flash Worker)                │
   └──────────────────────────────┬───────────────────────────────┘
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │             Рівень 3: Потоковий Монітор Дрифту               │
   │        GeminiDriftMonitor (Welford O(1) Mean/Var + EMA)       │
   └──────────────────────────────┬───────────────────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       [Статистично Стабільно]          [Детектовано Дрифт/Збій]
                  │                               │
                  │                               ▼
                  │              ┌─────────────────────────────────┐
                  │              │   Рівень 4a: GeminiSelfHealer   │
                  │              │   - Евристичний ремонт JSON     │
                  │              │   - Демпфування Temperature     │
                  │              │   - Підсилення System Prompt    │
                  │              │   - Fallback на резервну модель │
                  │              └────────────────┬────────────────┘
                  │                               │ (Retry Loop)
                  │                               ▼
                  │                     [Успішно Зцілено]
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │          Рівень 4b: Експорт Телеметрії & Візуалізація        │
   │  - Prometheus Exposition Protocol (/metrics, text/plain)     │
   │  - DNK Visual Shell / Grafana JSON Telemetry Endpoint        │
   │  - Grafana Production Dashboard (gemini_drift_dashboard.json)│
   └──────────────────────────────────────────────────────────────┘
```

---

## 🔬 Ключові Компоненти та Реалізація

### 1. Zero-Click Middleware Перехоплення (`SCONES Hook`)
- Реалізовано у `core/orchestrator/scones_expect.py` та `core/scones_middleware.py`.
- Автоматично валідує вхідні та вихідні епізоди пам'яті без ручного виклику інструментів.
- Блокує заборонені абсолютні шляхи (`/Users/...`), перевіряє діапазони важливості (`0.0 <= importance <= 1.0`) та наявність обов'язкових MRH-заголовків.

### 2. Автономний Контур Самозцілення (`GeminiSelfHealer`)
- Розташування: `core/orchestrator/gemini_self_heal.py`.
- **Нульова вартість ремонту (Zero-cost Local Repair)**: наївні синтаксичні дефекти JSON (обгортки ````json`, висячі коми, одинарні лапки, unquoted ключі) виправляються локально через `repair_json_string()` за <1мс без додаткових звернень до API.
- **Стратегії самозцілення**:
  - `LOCAL_JSON_HEAL`: локальне відновлення структури без витрати токенів.
  - `TEMPERATURE_DAMPEN`: при колапсі ентропії температура знижується до безпечного рівня (`0.2`).
  - `PROMPT_REINFORCE`: при дрифті довжини додаються явні структурні та стилістичні обмеження.
  - `MODEL_FALLBACK`: у разі вичерпання ретраїв виконується автоматичне перемикання на стійку резервну модель.
- **Гігієна вікна спостереження**: дефектні спроби генерації вилучаються з поточного вікна монітора (`pop()`), запобігаючи спотворенню бейзлайну під час ретраїв.

### 3. Потокове Оновлення Бейзлайнів ($O(1)$ Пам'ять)
- Розташування: `services/dnk_analytics/drift_monitor.py`.
- **Алгоритм Уелфорда (Welford's Algorithm)**:
  $$M_n = M_{n-1} + \frac{x_n - M_{n-1}}{n}$$
  $$S_n = S_{n-1} + (x_n - M_{n-1})(x_n - M_n)$$
  $$s^2 = \frac{S_n}{n-1}$$
  Забезпечує чисельно стабільне однопрохідне обчислення середнього та вибіркової дисперсії для довільного числа вибірок за константний час $O(1)$ і константну пам'ять $O(1)$.
- **Експоненційне рухоме середнє (EMA & EMA Variance)**:
  $$\text{EMA}_\mu \leftarrow (1 - \alpha) \cdot \text{EMA}_\mu + \alpha \cdot x_n$$
  $$\text{EMA}_{\sigma^2} \leftarrow (1 - \alpha) \cdot \left( \text{EMA}_{\sigma^2} + \alpha \cdot (x_n - \text{EMA}_\mu)^2 \right)$$
  Дозволяє динамічно відстежувати поступовий концептуальний дрифт із підвищеною чутливістю до свіжих генерацій.

### 4. Експорт Телеметрії та Візуалізація у Grafana / DNK Visual Shell
- Розташування:
  - `services/dnk_analytics/telemetry_exporter.py`
  - `apps/api/monitoring/metrics.py`
  - `apps/api/routers/workspace_analytics.py`
  - `monitoring/grafana_dashboards/gemini_drift_dashboard.json`
- **Метрики Prometheus**:
  - `dnk_gemini_entropy_mean`, `dnk_gemini_entropy_stdev`, `dnk_gemini_entropy_ema` (Gauge)
  - `dnk_gemini_char_length_mean`, `dnk_gemini_char_length_stdev`, `dnk_gemini_char_length_ema` (Gauge)
  - `dnk_gemini_word_count_mean`, `dnk_gemini_word_count_ema` (Gauge)
  - `dnk_gemini_ttr_mean`, `dnk_gemini_ttr_ema` (Gauge)
  - `dnk_gemini_json_valid_ratio` (Gauge)
  - `dnk_gemini_is_healthy` (Gauge, 1.0 = здоровий, 0.0 = дрифт)
  - `dnk_gemini_drift_alarm_active{alarm_type="..."}` (Gauge)
  - `dnk_gemini_samples_total` (Counter)
  - `dnk_gemini_drift_alarms_total{alarm_type="...",severity="..."}` (Counter)
  - `dnk_gemini_self_healings_total{strategy="...",status="..."}` (Counter)
  - `dnk_gemini_retries_total` (Counter)
- **API Ендпоінти**:
  - `GET /metrics` та `GET /api/v1/metrics`: загальний Prometheus-скрейп ендпоінт.
  - `GET /api/v1/analytics/drift/metrics`: окремий цільовий Prometheus експорт для монітора дрифту.
  - `GET /api/v1/analytics/drift/telemetry`: детальний JSON payload для віджетів DNK Visual Shell та Grafana JSON Data Source.
- **Grafana Дашборд**:
  - `monitoring/grafana_dashboards/gemini_drift_dashboard.json` (UID: `gemini-drift-telemetry`, 9 панелей: статус здоров'я, валідність JSON, ентропія, довжина, TTR, частота тривог, дії зцілення).

---

## 🧪 Верифікація та Результати Тестування

Повний набір із **63 модульних та інтеграційних тестів** виконано з результатом **100% Green**:
- `tests/services/test_telemetry_exporter.py`: 7/7 PASSED (Prometheus format, Visual Shell JSON, Alarms, Healing auto-recording, API endpoints).
- `tests/services/test_drift_monitor.py`: 12/12 PASSED (Welford accuracy, EMA convergence, O(1) tracker, Alarms).
- `tests/core/test_gemini_self_heal.py`: 13/13 PASSED (Local JSON repair, Entropy & Length healing, Online baseline mode).
- `tests/core/test_scones_middleware_hook.py`: 6/6 PASSED (Zero-click memory interception).
- `tests/core/test_scones_expect.py`: 8/8 PASSED (Expectation rules & reporting).
- `tests/core/test_soup_phase2_modules.py`: 9/9 PASSED (Phase 2 baseline and drift alarms).
- `tests/core/test_soup_assimilated_modules.py`: 8/8 PASSED (Phase 1 prompt ship gates & reward synthesis).
- `scripts/system/validate_grafana_dashboards.py`: 3/3 dashboards validated OK.

---

## 🔗 Пов'язані Нотатки та Документи
- [[067_session_sentinel_v2_soup_assimilation_architecture]] — Архітектурна основа SOUP та контур аналітики.
- [[068_session_sentinel_phase3_autonomous_closed_loop]] — Автономне замикання контурів самозцілення.
- [[058_Visual_Canvas_Control_Panel_Architecture]] — Інтеграція панелей візуалізації в DNK Visual Shell.
- `services/dnk_analytics/drift_monitor.py` — Реалізація монітора дрифту та акумуляторів Welford/EMA.
- `services/dnk_analytics/telemetry_exporter.py` — Експортер Prometheus та Visual Shell JSON.
- `core/orchestrator/gemini_self_heal.py` — Оркестратор самозцілення та корекції генерацій.
- `monitoring/grafana_dashboards/gemini_drift_dashboard.json` — Графана дашборд специфікація.
