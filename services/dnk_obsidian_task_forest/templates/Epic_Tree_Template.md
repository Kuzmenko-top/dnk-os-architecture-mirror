---
id: "{{tree_id}}"
title: "{{tree_name}}"
type: epic_tree
plant_scale: tree
icon: 🌳
sector_id: "{{sector_id}}"
project_id: "{{project_id}}"
parent_id: "{{sector_id}}"
status: in_progress
assigned_agent: "Hermes (Gerych)"
weight: 1.0
progress: 0
created_at: "{{date}}"
tags:
  - dnk-task-forest
  - dnk-epic-tree
---

# 🌳 Дерево Задачі: {{tree_name}}

**Сектор**: `[[{{sector_name}}]]` | **Відповідальний**: `{{assigned_agent}}`  
**Статус**: `{{status}}` | **Прогрес Розрахунку Знизу Вгору (Bottom-Up Rollup)**: `0%`

---

## 🌿 Кущі та Гілки Фіч (Feature Bushes)

```dataview
TABLE status, progress, assigned_agent
FROM #dnk-feature-bush
WHERE parent_id = "{{tree_id}}"
SORT file.name ASC
```

---

## 🕸️ Дерево Задачі (Graph BT)

```mermaid
graph BT
    Tree_Root["🌳 {{tree_name}} (0%)"]
```

---

## 🎯 Специфікація Та Технічне Завдання
- Опишіть глобальну епічну мету та критерії успіху.
