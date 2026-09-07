---
task_id: DNK-TASK-PRIME-INTEGRATION-01
title: ⚡ Специфікація Для Герича: Впровадження Двигуна Prime Agent (PrimeIntellect-ai/prime-agent)
assignee: Hermes (Gerych Master Orchestrator)
supervisor: Antigravity (Lead Architect & Mentor)
target_workspace: DNK OS/
status: Ready for Execution
created_at: 2026-08-07
---

# ⚡ Специфікація Для Герича: Впровадження Двигуна Prime Agent

## 📋 Мета
Розширити внутрішні можливості **Герича** за допомогою архітектурних паттернів з відкритиго репозиторію **`PrimeIntellect-ai/prime-agent`**:
1. Модуль паралельної оркестрації рою (`swarm_dispatcher.py`).
2. Внутрішній цикл рефлексії та зворотного зв'язку (RL Reflection Loop).
3. Автономна робота рою (Rick, Yuriy, Cas, Tiffany) strictly inside `DNK_HUB/`.

---

## 🎯 Завдання Для Виконання (Hermes Executable Steps)

1. **Створити каталог `core/agent_factory/prime_engine/`**:
   - `__init__.py`
   - `prime_orchestrator.py`: головний клас `GerychPrimeOrchestrator`.
   - `swarm_dispatcher.py`: модуль розподілу підзадач між роєм.

2. **Створити юніт-тести у `core/agent_factory/prime_engine/tests/`**:
   - `test_prime_orchestrator.py`: перевірка паралельного запуску та підрахунку готовності.

3. **Запустити верифікацію**:
   - `PYTHONPATH=. uv run pytest core/agent_factory/prime_engine/tests/ -v`
