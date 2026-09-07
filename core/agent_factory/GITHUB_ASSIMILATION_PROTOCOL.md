---
protocol_id: DNK-PROT-GITHUB-ASSIMILATION-01
title: 🌐 Протокол Асиміляції Інновацій З GitHub (GitHub Tech Assimilation Protocol)
owner: Antigravity (Lead Architect & Mentor) & Gerych
target_workspace: DNK OS/
status: Active
created_at: 2026-08-07
---

# 🌐 Протокол Асиміляції Інновацій З GitHub (GitHub Tech Assimilation Protocol)

Цей протокол описує стандарт перетворення будь-якої новітньої технології чи репозиторію з **GitHub.com** у нативну навичку або спеціалізованого агента **DNK OS**.

---

## 🔬 Покроковий Процес Асиміляції

1. **Крок 1: Вхідні Дані Репозиторію**:
   - Герич отримує URL репозиторію (наприклад, `https://github.com/AgentSwarms-fyi/agentswarms` чи `https://github.com/PrimeIntellect-ai/prime-agent`).

2. **Крок 2: Авто-Сканування Та Вилучення Коду**:
   - `github_assimilator.py` зчитує ключові файли: `README.md`, `pyproject.toml`, архітектуру коду, шаблони промптів та класи.

3. **Крок 3: Синтез Навички Та Специфікації Агента**:
   - Генерується навичка: `skills/<repo_name>/SKILL.md`.
   - За потреби створюється спеціалізований агент через `core/agent_factory/agent_generator.py`.

4. **Крок 4: Авто-Тестування Та Фіксація У Саду Задач**:
   - Запускається `pytest` для верифікації нативності нового модуля.
   - Створюється відповідний `Feature Bush` у Саду Задач.
