# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/03_Trees/Tree_03_Pluggable_Services_Framework.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "tree"
# --- END DNK-MRH-HEADER ---

# 🌳 Дерево Задачі 03: Pluggable Services & Module Registry

**Сектор**: [[Sector_Core_Engine]]  
**Поле**: [[Field_DNK_HUB]]  
**Статус**: Готово до запуску (Ready)

---

## 🎯 Ціль Сесії 3:
Створення стандарту модульних мікросервісів через `service_manifest.yaml`, впровадження `ServiceRegistry` у ядрі, автоматичне монтування REST/WebSocket ендпоінтів та реєстрація кастомних Canvas-нод для кожного сервісу.

## 🌿 Кущі Задач (Feature Bushes):
- [[Bush_Service_Manifest_Spec]]
- [[Bush_Service_Registry_Core]]
- [[Bush_Service_IPC_EventBus]]

---

## ⚡ Статус виконання (Execution Log)
- [x] **Квітка 07** — успішно реалізовано `ServiceRegistry`, валідацію за допомогою Pydantic моделей та автоматичне зчитування та підтвердження маніфесту `dnk_shopify_builder`.
- [x] **Тест-кейси** — розроблено `test_service_registry.py` для повноцінного юніт-тестування реєстру мікросервісів. Усі тести пройдено успішно.