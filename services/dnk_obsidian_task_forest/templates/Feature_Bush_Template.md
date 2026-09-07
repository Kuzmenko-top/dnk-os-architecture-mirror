---
id: "{{bush_id}}"
title: "{{bush_name}}"
type: feature_bush
plant_scale: bush
icon: 🌿
parent_id: "{{tree_id}}"
sector_id: "{{sector_id}}"
project_id: "{{project_id}}"
status: in_progress
assigned_agent: "Yuriy"
weight: 1.0
progress: 0
created_at: "{{date}}"
tags:
  - dnk-task-forest
  - dnk-feature-bush
---

# 🌿 Кущ Фічі: {{bush_name}}

**Батьківське Дерево**: `[[{{tree_name}}]]` | **Відповідальний**: `{{assigned_agent}}`  
**Статус**: `{{status}}` | **Прогрес Фічі**: `0%`

---

## 🌱 Квіточки-Підзадачі (Task Flowers)

```dataview
TABLE status, progress, assigned_agent
FROM #dnk-task-flower
WHERE parent_id = "{{bush_id}}"
SORT file.name ASC
```

---

## 📌 Кроки Виконання Фічі
- [ ] 🌱 Крок 1
- [ ] 🌱 Крок 2
