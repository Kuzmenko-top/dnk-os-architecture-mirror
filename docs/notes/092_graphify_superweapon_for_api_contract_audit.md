---
title: "092 Graphify як Суперзброя для Аудиту Контрактів та Blast Radius в DNK HUB 0.2"
date: "2026-09-07"
tags:
  - graphify
  - ast
  - blast-radius
  - audit-slice
  - architecture
status: active
mrh_id: "docs/notes/092_graphify_superweapon_for_api_contract_audit.md"
purpose: "Фіксація ролі Graphify AST Engine для детермінованого аудиту роутерів, тестів та фронтенд-контрактів без витрати токенів"
canonical_source: true
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/092_graphify_superweapon_for_api_contract_audit.md"
# purpose: "Фіксація ролі Graphify AST Engine для детермінованого аудиту роутерів, тестів та фронтенд-контрактів без витрати токенів"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🕸️ Graphify як Головний Валідатор для Слайсу 0.2-A

## 1. Чи допоможе Graphify у цій задачі?

**Так, Graphify — це наша найбільша інженерна перевага у вирішенні цієї задачі.**

Коли ментор Perplexity ставить завдання визначити:
- які роутери дублюються,
- які тести захищають ці роутери,
- що зламається при зміні роутера (blast radius),
- які файли залежать від кожного ендпоінта,

класичний підхід вимагав би витратити сотні тисяч токенів або години ручного перегляду. За допомогою вже встановленого і зіндексованого у нас `graphify` ми отримуємо ці відповіді **за мілісекунди і з 0 витрачених токенів**.

---

## 2. Живий доказ (Live Proof)

Команда:
```bash
graphify affected "apps/api/routers/canvas.py"
```
Миттєво виявила **80 залежних тестів і файлів**, які імпортують цей роутер:
- `apps/api/main.py:L16`
- `tests/canvas/test_canvas_api_and_ws.py:L14`
- `tests/canvas/test_canvas_execution_engine_and_api.py:L13`
- `tests/verification/test_node_tasks_router.py:L15`
- і ще 76 тестових файлів!

Це означає, що ми точно знаємо, які саме тести потрібно запустити, якщо ми змінюємо чи уніфікуємо `canvas.py`.

---

## 3. Синергетична Формула Аудиту

| Інструмент | Що робить | Перевага |
|---|---|---|
| **Graphify AST Engine** | Будує граф зв'язків: файли $\to$ роутери $\to$ тести | Детермінований Blast Radius, 0 токенів |
| **FastAPI OpenAPI Schema** | Витягує точні шляхи, методи (GET/POST) та дублікати `operation_id` | Стандартизований JSON/OpenAPI 3.1 |
| **Frontend Endpoint Regex** | Шукає рядки `/api/...` та `/canvas/...` у Next.js компонентах | Виявляє реальних споживачів у UI |

Об'єднання цих трьох елементів дасть нам **ідеальний, математично точний звіт `API_FRONTEND_CONTRACT_MAP_v0.1`**, який не залишить ментору жодного сумніву в надійності нашого плану міграції.
