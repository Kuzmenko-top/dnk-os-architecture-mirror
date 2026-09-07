# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_02_Canvas_WS_Sync.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка: Deploy React Flow Canvas UI with WebSocket Live Sync

## 📋 Опис завдання
Розгортання та запуск інтерактивного React Flow Canvas UI з двосторонньою WebSocket синхронізацією стану (`/ws/canvas_sync` на базі FastAPI) для динамічного відображення графу зв'язків з 23,724 AST нодами нашого ядра.

## 🏁 Чек-лист реалізації (Checklist)
- [x] **Встановлення `@xyflow/react`:** Залежність успішно інстальована та прописана в `visual_shell/web_ui/package.json`.
- [x] **Реалізація WebSocket клієнта:** Підключено `/ws/canvas_sync` у `CanvasEditor.jsx` для отримання структури коду.
- [x] **Семантичний LOD-Рендерер:** Реалізовано 3 рівні деталізації (LOD):
  - Рівень 1: Відображення макро-секторів (`field_dnk_hub`, `sector_core_engine`, `sector_shopify_ecosystem`).
  - Рівень 2: Відображення епічних дерев (`tree_obsidian_task_forest`, `tree_agentic_swarm`, `tree_shopify_customizer`).
  - Рівень 3: При подвійному кліку на кущ — завантаження та розгортання відповідних класів та функцій безпосередньо з PostgreSQL через WebSocket.
- [x] **iFrame-контейнер для прев'ю:** Інтегровано кастомний вузол `IFrameCanvasNode` для перегляду та двостороннього зв'язку (через `postMessage`).
- [x] **Верифікація збірки:** Проект успішно скомпільовано без помилок за допомогою команди `npm run build` (Compiled successfully).
- [x] **Державне оновлення:** Створено та оновлено завдання в базі даних (ID завдання #70045 оновлено до `completed`).