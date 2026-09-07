---
title: "016 Unified Swarm Control Plane Architecture and Engine Consolidation"
tags: [architecture, orchestrator, swarm, control-plane, dnk-os, gerych]
created: 2026-09-05
updated: 2026-09-05
author: "DNK-e.com Maksym"
status: "Completed"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/016 Unified Swarm Control Plane Architecture and Engine Consolidation.md"
purpose: "Architecture Decision Record and Technical Specification for the Unified Swarm Control Plane and Coordination Engine Consolidation."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 👑 016. Єдиний Графовий Control Plane та Консолідація Двигунів Оркестрації

## 📌 1. Контекст та Проблематика
У процесі швидкої еволюції системи DNK OS у кодовій базі утворилося 6 паралельних механізмів координації агентів:
1. `core/orchestrator/swarm_coordinator.py` — продакшн-координатор 14 агентів, паралельних диспетчерів та фізичного скафолдингу.
2. `core/swarm_engine.py` — Supervisor/Worker пайплайни з ретраями та Error Distillation.
3. `core/swarm_orchestrator.py` — завантажувач маніфестів ролей та RAG-ін'єкція навичок.
4. `core/workflow_orchestrator.py` — графовий виконавець DAG із Human-in-the-Loop шлюзами.
5. `core/coordinators/agent_coordinator.py` — абстрактний інтерфейс розподілу завдань (`AgentCoordinator`).
6. Вбудовані субпроцеси Hermes (`delegate_task`).

### Невідповідність (Flaw)
Відсутність єдиного авторитетного State Machine / Control Plane призводила до того, що кожен модуль мав власні структури стану, власну логіку черг та відсутність єдиного механізму Checkpointing, що унеможливлювало відновлення після збоїв та Time-Travel аналіз.

---

## 🏛️ 2. Архітектурне Рішення: `SwarmControlPlane` (`core/orchestrator/control_plane.py`)
Створено єдиний авторитетний Control Plane, побудований на SOTA патернах (LangGraph StateGraph + Temporal Checkpointing):

### Ключові Компоненти:
1. **DAG State Machine**:
   - Строгі типізовані стани: `PENDING`, `SCHEDULED`, `RUNNING`, `COMPLETED`, `FAILED`, `PAUSED_APPROVAL`, `RETRYING`.
   - Топологічне сортування з обов'язковою перевіркою на циклічні залежності (`has_cycle()`) на основі DFS.
   - Повноцінна підтримка Human-in-the-Loop шлюзів (`requires_approval=True`, `grant_approval()`).
2. **StateCheckpointer (Time-Travel & Crash Recovery)**:
   - Атомарне персистентне збереження графів завдань у JSON/SQLite (`control_plane_checkpoints.json`).
   - Відновлення стану перерваного графу (`restore_checkpoint(run_id)`) з реконструюванням вузлів та результатів.
3. **Sub-50ms RAG Skill Engine**:
   - Кешований індекс навичок на основі множинної перехресної фільтрації токенів і тегів (`duration < 0.05s`).
4. **Сумісні Фасади та Адаптери (Zero Breaking Changes)**:
   - `core/workflow_orchestrator.py`: делегує виконання та перевірку циклів безпосередньо `SwarmControlPlane`.
   - `core/swarm_orchestrator.py`: інтегровано збереження маніфестів та надшвидкий RAG через `SwarmControlPlane`.
   - `core/swarm_engine.py`: `Supervisor` володіє `self.control_plane`, реєструє кожен крок та робить автоматичний чекпоінт після виконання.
   - `core/coordinators/agent_coordinator.py`: реалізовано конкретний адаптер `ControlPlaneAgentCoordinator`.
   - `core/orchestrator/swarm_coordinator.py`: `GerychSwarmCoordinator` містить `self.control_plane` як ядро стану.

---

## 🧪 3. Валідація та Тестове Покриття
Створено вичерпний тестовий набір `tests/test_swarm_control_plane.py`, що тестує:
- Топологічне виконання кроків A -> B -> C.
- Запобігання зацикленню графу (Cycle Detection).
- Зупинку на кроках із `requires_approval` та безпечне продовження після схвалення.
- Серіалізацію, збереження на диск та відновлення у новому екземплярі Control Plane.
- RAG-ін'єкцію навичок із часом виконання < 50 мс.
- Усі фасади (`WorkflowOrchestrator`, `SwarmOrchestrator`, `ControlPlaneAgentCoordinator`, `Supervisor`).

Усі 40 пов'язаних тестів пройшли зі 100% успіхом (40 passed in 6.09s).

---
*Пов'язані нотатки:*
- [[015 Gerych System Architecture Audit, SOTA Assimilation & Strategic Evolution Blueprint]]
- [[000 DNK HUB Index]]
