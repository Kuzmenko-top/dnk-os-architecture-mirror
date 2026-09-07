---
id: flower_14_visual_selection_context_bridge
title: "🌸 Квітка 14: Visual Selection Context Bridge & Screenshot Ingestion"
type: task_flower
plant_scale: flower
parent_id: bush_websockets_canvas_sync
status: completed
verification_status: passed
tags:
  - dnk-task-forest
  - dnk-task-flower
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_14_Visual_Selection_Screenshot_Ingestion.md"
# purpose: "Task Flower tracking Visual Selection Context Bridge (VSCB) implementation and complete verification."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-10"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 14: Visual Selection Context Bridge & Screenshot Ingestion

## 📋 Опис завдання
Реалізація системи безкінечного полотна (Infinite Canvas) з підтримкою зчитування виділень на полотні (Canvas Selection), збереженням знімків екрану (Screenshot Ingestion), парсингом OCR та автоматичним прокиданням контексту (VSCB DTO) до Supervisor/Worker контуру з повним дотриманням ізоляції клієнтів (Tenant/Workspace Isolation).

## 🏁 Чек-лист реалізації (Checklist)
- [x] **VisualContext DTO**: Описано стабільну Pydantic-схему з урахуванням `tenant_id`, `workspace_id` та `canvas_id`.
- [x] **Canvas Selection Event**: Реалізовано генерацію стабільного idempotent `context_id` на базі геш-функції SHA-256 від виділених нод та координат.
- [x] **Screenshot / Region Capture**: Підключено збереження знімків екрану на диску у `DNK OS/public/uploads/` через `VisualContextBridge`.
- [x] **Asset Persistence Route**: Створено persistence-шлях з підтримкою уникнення неконтрольованого дублювання файлів.
- [x] **Context Bridge Adapter**: Реалізовано `VisualContextBridge` з методами ізольованої перевірки прав та зв'язування контекстів.
- [x] **Task Context Integration**: Інтегровано прокидання visual контексту у Supervisor `execute_task_pipeline` та передача Worker-у.
- [x] **Strict Security & Isolation**: Створено механізм перевірки прав власності нод (`_verify_node_ownership`) перед будь-яким імпортом знімків або нод, унеможливлюючи витоки між воркспейсами.
- [x] **Unit & E2E Testing**: Створено 8 юніт-тестів та 1 повний End-to-End тест у `core/tests/test_visual_context.py` (усі пройшли на 100%).
- [x] **Таблиці та Метадані**: Структуровано схеми та підключено зберігання метаданих у нашому канонічному реєстрі.
