---
id: flower_20_canvas_runtime_transport_and_frontend_event_client
title: "🌸 Квітка 20: Canvas Runtime Transport & Frontend Event Client"
type: task_flower
plant_scale: flower
parent_id: tree_10_langgraph_multi_agent_orchestration
status: completed
verification_status: passed
tags:
  - dnk-task-forest
  - dnk-task-flower
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_20_Canvas_Runtime_Transport_and_Frontend_Event_Client.md"
# purpose: "Task Flower tracking Canvas Runtime Transport & Frontend Event Client implementation (Flower 20)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 20: Canvas Runtime Transport & Frontend Event Client

## 📋 Опис завдання
Мета — розробити та протестувати повноцінний транспорт реального часу (WebSockets) для доставки подій з `DNKLangGraphAdapter` до реального Infinite Canvas, а також забезпечити керування процесом виконання (execution) прямо з користувацького інтерфейсу за допомогою `RuntimeBridgeClient`.

## 🏁 Чек-лист реалізації (DoD)
- [x] **RuntimeEventBus**: Створено повністю асинхронний та безпечний потік подій на бекенді.
- [x] **WebSocket / REST Endpoints**: Додано WebSocket endpoint у FastAPI бекенд для підписок клієнтів у реальному часі та REST endpoint-и для контролю.
- [x] **Authentication & Isolation**: Забезпечено захист та повну ізоляцію tenant/workspace/canvas. Заборонено крос-воркспейс підписки (fail-closed behavior).
- [x] **Reconnect & Replay**: Реалізовано відновлення підключення клієнта за допомогою `last_event_id` з повторним відтворенням пропущених подій.
- [x] **Snapshot Fallback**: Реалізовано автоматичний fallback на snapshot у разі виявлення розривів або пропущених послідовностей подій.
- [x] **Frontend RuntimeBridgeClient**: Створено React-клієнт для підключення до транспорту, синхронізації та передачі команд керування.
- [x] **9 Lifecycle States**: Реалізовано редуктор (`reduceRuntimeEvent`) для підтримки всіх 9 станів життєвого циклу нод (`idle`, `queued`, `running`, `checkpointed`, `waiting_human`, `retrying`, `recovered`, `failed`, `completed`, `cancelled`).
- [x] **Controls Backchannel**: Реалізовано керування через `resume`, `cancel` та `interrupt` з підтримкою оптимістичного UI оновлення.
- [x] **Backpressure / Bounded Queue**: Додано обмеження на чергу подій підписників з витісненням найстаріших подій для уникнення витоку пам'яті.
- [x] **20+ Backend/Frontend Tests**: Розроблено 20 юніт-, інтеграційних та E2E-тестів, що покривають увесь життєвий цикл та авторизацію.
- [x] **100% Passed Regression**: Загальний регресійний пакет тестів виконано успішно (167+ PASSED).

## 📊 Результати тестування
- Усі 20 тестів у `test_canvas_runtime_bridge.py` виконано зі статусом **PASSED**.
- Повний набір тестів у `tests/` виконано успішно.
