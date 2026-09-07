---
id: "{{project_id}}"
title: "{{project_name}}"
type: project_field
plant_scale: field
icon: 🌾
status: in_progress
owner: "{{owner}}"
created_at: "{{date}}"
tags:
  - dnk-task-forest
  - dnk-project-field
---

# 🌾 Поле Проєкту: {{project_name}}

**Статус Поля**: `{{status}}` | **Власник**: `{{owner}}`  
**Загальний Прогрес Задач-Рослин**: `0%`

---

## 🏞️ Сектори Та Напрямки (Sector Zones)

```dataview
TABLE status, progress, plant_scale
FROM #dnk-sector-zone
WHERE project_id = "{{project_id}}"
SORT file.name ASC
```

---

## 📊 Візуальний Граф Поля (Mermaid Graph BT — Ріст Знизу Вгору)

```mermaid
graph BT
    %% Авто-згенеровано DNK OS Task Forest Engine
    Field_Root["🌾 {{project_name}} (0%)"]
```

---

## 📝 Нотатки Проєкту та Стратегія
- Опишіть головну мету поля та ключові результати.
