# 📚 Зведений Індекс Плейбуків Та Досвіду (6 Місяців R&D)

| ID | Проблема / Задача | Розв'язок Та Скрипт Виконання | Статус |
|---|---|---|---|
| **PB-001** | Засмічення контекстного вікна агента логами | `scripts/sanitize_context_bloat.py` | ✅ Active |
| **PB-002** | Випадкові абсолютні шляхи у коді/MD | `scripts/enforce_relative_paths.py` | ✅ Active |
| **PB-003** | Перевірка цілісності системи та модулів | `scripts/run_system_health_audit.py` | ✅ Active |
| **PB-004** | Перевірка 100% покриття авто-тестами | `PYTHONPATH=. uv run pytest` | ✅ Active |

---

## 💡 Уроки Пам'яті (Lessons Learned)
- **`LL_001_CONTEXT_OPTIMIZATION.md`**: Правила запобігання росту логів та оптимізація токенів.
- **`LL_002_PATH_GUARD_STANDARDS.md`**: Стандарт відносних шляхів та захисту середовища.
