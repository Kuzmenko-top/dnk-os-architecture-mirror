# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/mindwalk_citymap/RND_REPORT.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 📊 R&D Report: 3D Code CityMap & Two-Phase Sealed LLM Judge

## Секція 1: Executive & Commercial Summary
Асиміляція `mindwalk` вирішує дві найскладніші проблеми довготривалих ШІ-агентів: наочну візуалізацію фокусу розробки на 3D Treemap-картах ("Code City") та детерміновану оцінку якості сесій за допомогою двоетапного ізольованого ШІ-судді (Two-Phase Sealed Judge) без модельних галюцинацій у балах.

## Секція 2: Core Architectural Patterns & Code Blueprints
### 1. Trace Normalization Phase Matrix
JSONL-траса асимілюється у 5 стандартних станів розробки: `search`, `read`, `edit`, `exec`, `verify`.

### 2. Two-Phase Sealed Judge Pipeline
- **Фаза 1 (Rubric Draft):** Генерація динамічної рубрики на основі аналізу запиту користувача.
- **Фаза 2 (Unified Scoring):** Оцінка сесії за 4 вимірами (exploration, scope, wandering, verification) у ізольованому CLI.
- **Mechanical Verdict Rollup:** Розрахунок вердиктів за детермінованою матрицею штрафів (penalty rules).

## Секція 3: DNK OS Mapping Matrix
- **Модуль у DNK OS:** `services/dnk_git_research` & `scripts/verification/path_guard.py`
- **Інтеграція:** Забезпечує автоматичний аудит якості та відсутності дрейфу інструкцій (rules drift) у дочірніх агентах.

## Секція 4: Executable Skills & Verification
- **Згенеровані навички:** `cosmtrek/mindwalk`
- **Верифікація:** Запуск `pytest services/dnk_git_research/tests/test_dag_validator.py` для перевірки цілісності графів виконання.