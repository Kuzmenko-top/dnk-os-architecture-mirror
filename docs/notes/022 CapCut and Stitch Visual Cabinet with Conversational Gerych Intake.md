---
title: CapCut and Stitch Visual Cabinet with Conversational Gerych Intake
tags:
  - architecture
  - visual_cabinet
  - capcut
  - stitch
  - task_intake
status: Active
date: 2026-09-06
aliases:
  - CapCut and Stitch Visual Cabinet
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/022 CapCut and Stitch Visual Cabinet with Conversational Gerych Intake.md"
purpose: "Architecture & integration of CapCut & Google Stitch Visual Suite with Gerych Conversational Task Intake for DAG"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🎬 022 CapCut & Google Stitch Visual Cabinet with Gerych Task Intake Engine

## 1. Концепція та Мета
Робочий кабінет DNK OS об'єднує дві SOTA візуальні парадигми:
1. **Google Stitch Spatial Canvas (`stitch.withgoogle.com`)**:
   - Безмежне інтерактивне полотно.
   - Плаваючий командний док (**Stitch Prompt Dock**) по центру знизу.
   - Миттєвий ввід промптів, швидкі фільтри (`💡 Ідея`, `🎯 Задача`, `⚡ Декомпозиція`).
2. **CapCut Pro Visual Suite (`capcut.com/ai-design`)**:
   - Темно-графітова палітра (`#0a0c10` / `#12141c`) з неоново-смарагдовими акцентами (`#33EE75`).
   - Панель моніторингу агентів у реальному часі (Status Pill у лівому нижньому куті).
   - Бічна шторка діалогу з Геричем (Gerych Slide-out Drawer).

## 2. Автономний Агент Герич як Двигун Генерації Задач (Conversational Intake)
Коли користувач (Максим) веде діалог із Геричем у чаті кабінету або через командний док:
- Герич автоматично витягує сутності: **Тип** (`idea`, `task`, `epic`, `gate`), **Пріоритет** (`critical`, `high`, `medium`), **Призначений Swarm-агент** (`gerych_builder`, `dnk_dev_fullstack`, `dnk_shopify`, `dnk_video_ai_creator`, `gerych_auditor`).
- Складні запити автоматично **декомпозуються** на послідовні підзадачі з ребрами залежностей `depends_on`.
- Створені вузли миттєво зберігаються у `node_task_graph.json` та синхронізуються з Obsidian Vault (`./docs/notes/tasks_and_ideas/`).

## 3. Компоненти Системи

| Компонент | Шлях | Роль |
| :--- | :--- | :--- |
| `ConversationalTaskExtractor` | `services/dnk_node_tasks/conversational_intake.py` | Інтелектуальний парсер та генератор DAG-структур |
| API Endpoint | `POST /api/v3/node_tasks/chat_intake` | Шлюз бекенду для створення завдань із діалогу |
| `GerychTaskPromptDock` | `apps/web/components/node-tasks/GerychTaskPromptDock.tsx` | Плаваючий Stitch Command Bar знизу екрана |
| `GerychTaskChatDrawer` | `apps/web/components/node-tasks/GerychTaskChatDrawer.tsx` | Шторка повноцінного чату з Геричем зліва |
| `NodeTaskGraphCanvas` | `apps/web/components/node-tasks/NodeTaskGraphCanvas.tsx` | Основний просторовий кабінет CapCut & Stitch |

---

## 4. Консолідація Чат-Інтерфейсу та Docker Proxy Resolution
- **Єдиний Консолідований Чат**: Усунуто конфлікт одночасного відображення нижнього доку та бічної шторки чату. Коли відкрито `GerychTaskChatDrawer`, плаваючий док `GerychTaskPromptDock` автоматично приховується, запобігаючи подвійному чату. Стан повідомлень (`chatMessages`) централізовано в `nodeTasksStore`.
- **Внутрішній Docker Proxy**: У `next.config.mjs` та `Dockerfile.frontend` додано `BACKEND_INTERNAL_URL="http://backend:8000"`, що виключає спроби Next.js проксувати запити на `127.0.0.1:8000` всередині контейнера.
- **Fail-Safe Error Handling & Client Crash Resolution**: Усунуто падіння `TypeError: Cannot read properties of undefined (reading 'idea')` у `NodeTaskGraphCanvas.tsx` через невідповідність структури `stats.by_type.idea` відповіді бекенду (`ideas_count`). Реалізовано безпечний мапінг у `nodeTasksStore.ts`, розширено модель `GraphStatistics` на бекенді та додано безпечне читання `res.text()` перед `res.json()`.

## 5. Пов'язані Нотатки
- [[021 Node Based Task and Ideas DAG System Architecture]]
- [[020 DNK OS Unified Development Environment and Architecture]]
