# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/04_Bushes/Bush_5_Atom_Canvas_Molecules.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "bush"
# --- END DNK-MRH-HEADER ---

# 🌿 Кущ: 5-Atom Canvas Molecules

## 📋 Опис куща фіч
Цей кущ фіч структурує та формалізує наше ядро `CanvasEngine` за 5-атомною молекулярною структурою:
1. **State Atom**: Зберігання стану полотна (`nodes`, `edges`, `history`, `history_cursor`).
2. **Cognitive Atom**: Алгоритмічні розрахунки та обмеження (`has_cycle`, `calculate_auto_layout`).
3. **View Atom**: Інтерфейси рендерингу та серіалізації (`render_canvas_text`, `to_reactflow_graph`).
4. **Control Atom**: Модифікація та контроль за часом (`update_node_state`, `undo`, `redo`).
5. **Action Atom**: Зовнішня синхронізація та завантаження патернів (`sync_patterns_to_nodes`, `sync_with_pattern_registry`).

## 🏁 Стан реалізації (Status)
- [x] **State Atom** — інтегровано глибокі копії та історію snapshots.
- [x] **Cognitive Atom** — валідація DAG унеможливлює петлі залежностей.
- [x] **View Atom** — повна сумісність з ReactFlow графом на фронтенді.
- [x] **Control Atom** — додано методи `undo` та `redo` з перевіркою меж історії.
- [x] **Action Atom** — синхронізація з реєстром патернів працює безперебійно.