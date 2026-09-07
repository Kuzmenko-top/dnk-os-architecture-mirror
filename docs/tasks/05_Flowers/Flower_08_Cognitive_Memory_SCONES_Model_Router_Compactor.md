# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_08_Cognitive_Memory_SCONES_Model_Router_Compactor.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 08: Create Long-term Cognitive Memory SCONES, Model Router and Context Compactor

## 📋 Опис завдання
Розробка та запуск трьох фундаментальних когнітивних компонентів інтелектуального шару DNK OS MVP:
1. **Довготривала когнітивна пам'ять SCONES** (Shared Cognitive Outcomes & Networked Extraction Storage): Модуль для збереження, вилучення та структурування тривалих когнітивних траєкторій агентів.
2. **Когнітивний роутер моделей** (`SelfHealingModelRouter`): Відмовостійкий проксі для гарячої перекомутації запитів до LLM моделей (наприклад, перемикання на NVIDIA NIM SOTA у разі помилок 404/429/500).
3. **Компактор контексту** (`sanitize_context_bloat.py`): Механізм очищення та стиснення логів/вихідних рядків для уникнення роздування LLM контексту.

## 🏁 Чек-лист реалізації (Checklist)
- [x] **SCONES Memory Engine**: Створення `core/scones_memory.py` з методами збереження когнітивних епізодів та інтеграцією з базою даних.
- [x] **Self-Healing Model Router**: Верифікація та інтеграція роутера `SelfHealingModelRouter` у `core/model_proxy/self_healing_router.py`.
- [x] **Context Compactor**: Інтеграція механізму стиснення контексту з `core/playbooks/scripts/sanitize_context_bloat.py`.
- [x] **Верифікація тестів**: Написання комплексного тест-модуля `test_scones_memory.py` та проходження pytest (100% успіх).