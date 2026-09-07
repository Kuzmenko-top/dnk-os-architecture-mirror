# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_07_Service_Registry_Shopify_Builder.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 07: Create ServiceRegistry and Register First Plugin dnk_shopify_builder

## 📋 Опис завдання
Створення, налаштування та верифікація єдиного реєстру сервісів `ServiceRegistry` у ядрі DNK OS MVP. Реєстр автоматично сканує теки мікросервісів, парсить і валідує їхні маніфести `service_manifest.yaml`, а також реєструє перший плагін `dnk_shopify_builder` з його портами та кінцевими точками (endpoints).

## 🏁 Чек-лист реалізації (Checklist)
- [x] **ServiceRegistry Engine**: Валідація за допомогою Pydantic-моделей `ServiceManifestModel` та `EndpointModel` у `core/service_registry.py`.
- [x] **Парсинг маніфестів**: Очищення YAML від MRH коментарів перед парсингом.
- [x] **Реєстрація dnk_shopify_builder**: Автоматичне зчитування та підтвердження маніфесту `services/dnk_shopify_builder/service_manifest.yaml`.
- [x] **Верифікація коду**: Створення комплексного тесту `test_service_registry.py` та успішне проходження pytest на хості.