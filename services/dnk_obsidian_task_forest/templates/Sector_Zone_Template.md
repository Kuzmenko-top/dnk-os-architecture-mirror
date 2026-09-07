---
id: "{{sector_id}}"
title: "{{sector_name}}"
type: sector_zone
plant_scale: sector
icon: 🏞️
project_id: "{{project_id}}"
status: in_progress
created_at: "{{date}}"
tags:
  - dnk-task-forest
  - dnk-sector-zone
---

# 🏞️ Сектор / Напрямок: {{sector_name}}

**Проєкт**: `[[{{project_name}}]]` | **Статус**: `{{status}}`  
**Прогрес Дерев у Секторі**: `0%`

---

## 🌳 Епічні Дерева Задач у Секторі (Epic Trees)

```dataview
TABLE status, progress, assigned_agent
FROM #dnk-epic-tree
WHERE sector_id = "{{sector_id}}"
SORT file.name ASC
```

---

## 📝 Опис Напрямку
- Визначте межі відповідальності та цілі цього сектора.
