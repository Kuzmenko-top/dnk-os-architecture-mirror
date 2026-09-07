---
id: "{{flower_id}}"
title: "{{flower_name}}"
type: task_flower
plant_scale: flower
icon: 🌱
parent_id: "{{bush_id}}"
sector_id: "{{sector_id}}"
project_id: "{{project_id}}"
status: pending
assigned_agent: "Rick"
weight: 1.0
progress: 0
created_at: "{{date}}"
tags:
  - dnk-task-forest
  - dnk-task-flower
---

# 🌱 Квіточка / Мікро-Підзадача: {{flower_name}}

**Батьківський Кущ**: `[[{{bush_name}}]]` | **Відповідальний**: `{{assigned_agent}}`  
**Статус**: `{{status}}` | **Оцінка тривалості**: `1-4 години`

---

## 📋 Чекліст Виконання
- [ ] Оглянути вхідні вимоги
- [ ] Виконати фізичне редагування коду
- [ ] Запустити перевірку pytest / path_guard
