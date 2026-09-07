---
title: "GitHub MCP & CI/CD Fast-Path Architecture"
date: 2026-09-06
tags:
  - architecture
  - github-mcp
  - cicd
  - quality-gate
  - session-sentinel
  - zero-waste
aliases:
  - "015_GitHub_MCP_and_CICD_Fast_Path_Architecture"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/055_GitHub_MCP_and_CICD_Fast_Path_Architecture.md"
purpose: "Architectural specification and design documentation for GitHub MCP & CI/CD Fast-Path, Fail-Closed Pre-PR Quality Gate, and Sentinel Telemetry."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🚀 GitHub MCP & CI/CD Fast-Path Architecture

## 1. Контекст та Проблема
При розробці автономних агентів у великих монорепозиторіях виникають три критичні точки затримок та збоїв:
1. **Важкі Git операції та аутентифікаційні глухі кути**: Виклики інтерактивних `gh auth login`, неаутентифіковані запити, або очікування важких `git clone` для інспекції віддалених PR.
2. **Фантомні Pull Request (Phantom Done / Unverified PRs)**: Спроби агента відкрити PR або зафіксувати виконання завдання, коли в репозиторії є невипробувані модифікації або відсутній верифікований звіт проходження Master Quality Gate.
3. **Дублювання PR та 404 помилки**: Спроби створення нових PR для гілки, де PR уже існує, або використання застарілих / неіснуючих назв репозиторіїв.

## 2. Архітектура Рішення: Zero-Waste Fast-Path

Система базується на трирівневій моделі взаємодії:

```
[Агент / Swarm Worker]
        │
        ├── 1. Запит на PR (mcp__github__create_pull_request / gh pr create)
        │       │
        │       ▼
        ├── [hermes_pre_tool_hook.py] (Fail-Closed Pre-PR Gate)
        │       ├── Перевірка свіжості Master Quality Gate (< 15 хв)
        │       ├── Перевірка docs/audit/*-evidence.json (status: Completed)
        │       └── ❌ БЛОКУВАННЯ, якщо тести не пройдені або є неперевірені мутації
        │
        ├── 2. Генерація Доказів (generate_evidence.py)
        │       ├── Запуск verify_all.sh / pytest
        │       ├── Фіксація 100% Green звіту в JSON та Markdown
        │       └── Виклик fast_create_or_update_pr(...)
        │
        └── 3. GitHub MCP & REST Fast-Path (core/orchestrator/github_fast_path.py)
                ├── Динамічне визначення валідного repo_slug
                ├── Безпечне отримання GH_TOKEN / GITHUB_TOKEN
                ├── Idempotent Sync: якщо PR існує -> оновлення бейджа доказів; якщо ні -> створення PR
                └── Телеметрія SessionSentinel (детекція CI_CD_VIOLATION)
```

## 3. Ключові Компоненти

### 3.1. `core/orchestrator/github_fast_path.py`
- **Dynamic Slug Resolution**: Динамічно аналізує remotes (`origin`, `dnk-mvp`) або змінні середовища, запобігаючи помилкам 404.
- **Fail-Closed Evidence Verification**: Метод `verify_evidence_ready(task_id)` перевіряє наявність файлу доказів у `docs/audit/`, статус `Completed` та успішність `master_quality_gate`.
- **Idempotent PR Sync**: Метод `fast_create_or_update_pr` перевіряє наявність відкритого PR для гілки (`fast_get_pull_request`). Якщо PR знайдено — оновлює його опис та бейдж без помилки дублювання; якщо відсутній — створює новий PR.
- **Автоматичний бейдж Master Quality Gate**: Включає у body PR структурований блок із даними Task ID, комміту, статусу інваріантів та версії протоколу.

### 3.2. Fail-Closed Pre-PR Hook (`scripts/system/hermes_pre_tool_hook.py`)
- Функція `is_pr_creation_request(...)` перехоплює:
  - Прямі виклики інструментів `mcp__github__create_pull_request` та `tool_call(name="mcp__github__create_pull_request")`.
  - Shell-команди `gh pr create`, `gh pr edit`, та `gh api .../pulls`.
- Функція `has_completed_evidence(...)` перевіряє, чи було згенеровано валідний evidence-файл упродовж останніх 15 хвилин (`file_age <= 900`).
- Якщо агент намагається відкрити PR з неперевіреними змінами — хук негайно блокує дію з вказівкою запустити `generate_evidence.py`.
- Підтримується аварійний байпас `DNK_BYPASS_PR_GATE=1`.

### 3.3. SessionSentinel CI/CD Telemetry (`core/orchestrator/session_sentinel.py`)
- Додано нову категорію аномалій: `AnomalyCategory.CI_CD_VIOLATION`.
- Sentinel перевіряє сесійну траєкторію агента. Якщо агент намагався створити або оновити PR без виконання тестів чи з неперевіреними змінами коду — фіксується порушення `Unverified Pull Request Attempt (CI/CD Quality Gate Breach)` високої важливості.

### 3.4. Оновлення `scripts/system/generate_evidence.py`
- Інтегровано з `github_fast_path.fast_create_or_update_pr`.
- Після проходження Quality Gate та генерації звітів `generate_evidence.py` автоматично викликає швидкий шлях для публікації чи оновлення PR.

## 4. Зв'язок із суміжними концептами
- [[013_Zero_Touch_Inception_Gateway_Architecture|Вектор 1: Zero-Touch Inception Gateway]]
- [[028 Anti-Loop and AST Fast-Path Architecture|Вектор 2: Anti-Loop & AST Fast-Path]]
- [[AGENTS|DNK OS Unified Governance Rules]]
- [[TWO_TIER_DEVELOPMENT_PROTOCOL|Two-Tier Architecture Protocol]]