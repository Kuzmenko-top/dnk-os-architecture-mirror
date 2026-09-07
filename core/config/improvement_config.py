# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_improvement_config"
# purpose: "Global parameters and thresholds for the Self-Improvement Loop service"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from typing import List

# Кількість днів для аналізу виконань
IMPROVEMENT_ANALYSIS_WINDOW: int = 7

# Поріг успішності виконань. Якщо рівень успішності нижче за цей ліміт - запускається генерація покращень
IMPROVEMENT_MIN_SUCCESS_RATE: float = 0.8

# Автоматичне підтвердження та виконання низько-пріоритетних та low-impact покращень
IMPROVEMENT_AUTO_APPROVE_LOW_IMPACT: bool = True

# Категорії покращень, які обов'язково вимагають підтвердження та проходження Security Gate
IMPROVEMENT_REQUIRE_APPROVAL_CATEGORIES: List[str] = ["prompt", "retry_policy"]
