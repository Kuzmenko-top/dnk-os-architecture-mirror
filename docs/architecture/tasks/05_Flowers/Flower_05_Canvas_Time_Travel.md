# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_05_Canvas_Time_Travel.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 05: Import Time-Travel Version History and State Stepping

## 📋 Опис завдання
Імпорт механізму "灵感时光机" (Inspiration Time Machine / Time-Travel Version History) з асимільованого донора `open-design` (open-canvas) у наше ядро `CanvasEngine`. Це дозволяє фіксувати знімки стану полотна (snapshots), відкочуватися назад (undo), повторювати дії вперед (redo) та запобігати будь-яким петлям залежностей (loop-free DAG) на кожному кроці історичної лінії.

## 🏁 Чек-лист реалізації (Checklist)
- [x] **Snapshot History Engine**: Розширення `CanvasEngine` атрибутами `history` та `history_cursor` для збереження глибоких копій стану (вузлів та зв'язків).
- [x] **Методи Time-Travel**:
  - `take_snapshot(description)` — запис поточного стану з часовою міткою та описом.
  - `undo()` — переміщення курсору назад у часі та відновлення стану.
  - `redo()` — переміщення курсору вперед та повторне накладання версії.
- [x] **Тест-драйв і верифікація**: Додавання автоматизованих тестів до `test_canvas_flow.py` для перевірки лінійності історії та коректності відновлення даних.
- [x] **Запобігання колізіям**: Перевірка відсутності циклів (`has_cycle()`) при будь-якому кроці time-travel.