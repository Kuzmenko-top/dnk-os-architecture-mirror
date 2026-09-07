# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-IMPL-004"
# purpose: "Technical specification for the Self-Improvement Loop of DNK OS (Run Analyzer, Improvement Generator, Improvement Executor, Security Gate, and Configuration)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK-IMPL-004: Self-Improvement Loop Technical Specification

## 1. Run Analyzer (Аналізатор виконань)

**Файл:** `core/analyzers/run_analyzer.py`

Run Analyzer зчитує історію виконання (runs, tasks, events) з Timeline DB для конкретного агента, обчислює загальну успішність (success rate), середню тривалість та виявляє помилки й системні вузькі місця (bottlenecks).

### Порт
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from uuid import UUID

from core.models.improvement import RunAnalysis

class RunAnalyzer(ABC):
    @abstractmethod
    async def analyze_runs(
        self,
        agent_id: UUID,
        limit: int = 100,
    ) -> RunAnalysis:
        pass

    @abstractmethod
    def detect_patterns(
        self,
        runs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        pass
```

### Моделі (`core/models/improvement.py`)

- **RunAnalysis**:
  - `agent_id`: str / UUID
  - `total_runs`: int
  - `success_rate`: float (0.0-1.0)
  - `avg_duration_seconds`: float
  - `common_errors`: List[str]
  - `bottlenecks`: List[str]
  - `suggestions`: List[ImprovementSuggestion]

- **ImprovementSuggestion**:
  - `category`: str ("prompt", "retry_policy", "timeout", "tool_selection")
  - `description`: str
  - `priority`: str ("high", "medium", "low")
  - `estimated_impact`: str ("high", "medium", "low")
  - `suggested_action`: str

---

## 2. Improvement Generator (Генератор покращень)

**Файл:** `core/generators/improvement_generator.py`

Improvement Generator об'єднує та структурує знайдені пропозиції щодо покращення у єдиний виконуваний план `ImprovementPlan`. Він також сортує зміни за пріоритетом та розраховує очікуваний сумарний ефект.

### Порт
```python
from abc import ABC, abstractmethod
from typing import List
from core.models.improvement import ImprovementSuggestion, ImprovementPlan

class ImprovementGenerator(ABC):
    @abstractmethod
    def generate_plan(
        self,
        agent_id: str,
        suggestions: List[ImprovementSuggestion],
    ) -> ImprovementPlan:
        pass
```

### Модель (`ImprovementPlan`)
- `agent_id`: str
- `improvements`: List[ImprovementSuggestion]
- `priority_order`: List[str] (описи у порядку виконання)
- `estimated_total_impact`: str ("high", "medium", "low")
- `rollback_plan`: str (план відкоту змін у разі деградації роботи)

---

## 3. Improvement Executor (Виконавець покращень)

**Файл:** `core/executors/improvement_executor.py`

Improvement Executor застосовує покращення з `ImprovementPlan` до конфігурації або коду агента та записує аудит-лоґ у Timeline DB.

### Порт
```python
from abc import ABC, abstractmethod
from uuid import UUID
from core.models.improvement import ImprovementPlan

class ImprovementExecutor(ABC):
    @abstractmethod
    async def execute_plan(
        self,
        plan: ImprovementPlan,
        run_id: UUID,
    ) -> bool:
        pass
```

### Аудит-лоґ у Timeline DB
Кожне успішно застосоване покращення реєструє `Event` з параметрами:
- `event_type`: `"improvement_applied"`
- `payload`: `{"agent_id": "...", "improvement": "...", "category": "...", "run_id": "..."}`

---

## 4. Security Gate для покращень

**Файл:** `core/services/improvement_security_service.py`

Запобігає несанкціонованій деградації роботи чи неконтрольованій зміні поведінки агентів (наприклад, ядра промптів).

- Оцінює безпеку змін через `SecurityGateService.evaluate_policy`.
- High-impact зміни (`estimated_impact == "high"`) або категорії, що вимагають погодження, автоматично тригерить запит на **manual approval** (викликаючи `PermissionError`).
- Якщо політикою заборонено (`allowed=False`) -> скасовує покращення.

---

## 5. Конфігурація

**Файл:** `core/config/improvement_config.py`

```python
IMPROVEMENT_ANALYSIS_WINDOW = 7  # Аналізувати ostanni N днів
IMPROVEMENT_MIN_SUCCESS_RATE = 0.8  # Генерувати покращення, якщо success_rate нижче ліміту
IMPROVEMENT_AUTO_APPROVE_LOW_IMPACT = True  # Автоматично затверджувати low-impact
IMPROVEMENT_REQUIRE_APPROVAL_CATEGORIES = ["prompt", "retry_policy"]  # Категорії з обов'язковим погодженням
```

---

## 6. Верифікаційне тестування

Всі тести реалізовано у файлі `tests/verification/test_improvement_loop.py` з повною ізоляцією схем Postgres:

1. `test_analyze_runs_success_rate` — Верифікація коректності розрахунку success rate та avg_duration.
2. `test_detect_patterns_common_errors` — Виявлення частих помилок, таймаутів, рейт-лімітів.
3. `test_generate_plan_priority` — Сортування за пріоритетом (high -> medium -> low).
4. `test_execute_plan_prompt_update` — Оновлення промпту агента.
5. `test_execute_plan_retry_policy_update` — Оновлення retry_policy.
6. `test_security_gate_approval_required` — Спрацювання блокування на high-impact та категорії, що потребують ручного затвердження.
7. `test_audit_trail` — Перевірка запису подій `improvement_applied` в Timeline DB.
