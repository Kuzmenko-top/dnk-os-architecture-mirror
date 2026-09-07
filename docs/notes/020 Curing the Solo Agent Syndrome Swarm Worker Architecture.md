---
title: "020 Curing the Solo Agent Syndrome Swarm Worker Architecture"
date: "2026-09-06"
tags:
  - dnk-hub
  - architecture
  - swarm-orchestration
  - solo-agent-cure
  - multi-agent
status: approved
workspace_id: ws-alpha-001
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/020_Curing_the_Solo_Agent_Syndrome_Swarm_Worker_Architecture.md"
purpose: "Systemic cure and architectural blueprint to eliminate Solo Agent Syndrome and enforce true autonomous multi-agent execution."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime (Architect)"
--- END DNK-MRH-HEADER -->

# 🐝 Лікування синдрому «Агента-Одинака»: Архітектура автономного рою воркерів

## 🔍 Діагноз: Чому Gerych Prime скочується в «Одинака»?

1. **Когнітивна інерція (Path of Least Resistance)**: Для головного агента простіше викликати `read_file`, `patch` та `terminal` безпосередньо у своєму вікні, ніж формулювати контракт завдання та чекати завершення зовнішнього підпроцесу.
2. **Контрактна імітація (In-Process Mock Execution)**: `swarm_coordinator.py` історично виконував роль диспетчера контрактів у тому ж процесі Python, створюючи ілюзію рою без фізичної ізоляції контексту.
3. **Відсутність інструментального бар'єра**: Якщо оркестратор має ті самі права на редагування будь-якого файлу, він перетворюється на вузьке місце (bottleneck).

---

## 💊 4 Архітектурні Стовпи Лікування

### Стовп 1: Фізична ізоляція процесів (True Subagent Isolation)
- Замість виклику синхронних функцій — фізичний запуск субагентів:
  1. Через нативний **`delegate_task`** (Hermes Background Subagent Daemon).
  2. Або через автономний CLI-підпроцес:
     ```bash
     hermes -p gerych_builder --goal "Implement Slice 1.1 UI" --workdir .
     ```
- **Результат**: Субагент отримує чисте контекстне вікно (0 токенів попередніх балачок), свій бюджет 25 інструментів і не засмічує пам'ять Прайма.

### Стовп 2: Контракт «Вхідний бриф ➔ Вихідний артефакт» (Artifact Boundary)
Оркестратор не повинен бачити проміжний шум думок субагента. Тільки фінальний верифікований артефакт:
```json
{
  "worker": "dnk_dev_fullstack",
  "slice_id": "slice-auth-001",
  "status": "COMPLETED",
  "target_files": ["apps/api/routers/auth.py", "tests/verification/test_auth.py"],
  "test_exit_code": 0,
  "diff_summary": "+58 lines, -4 lines",
  "artifact_path": "sessions/artifacts/slice-auth-001.json"
}
```

### Стовп 3: Рольова сегрегація інструментів (Role-Based Tool Gating)
- **Gerych Prime (Chief Architect & Orchestrator)**:
  - Інструменти: `dnk_triage_task`, `dnk_decompose_task_dna`, `delegate_task`, `dnk_swarm_parallel`, `read_file` (лише специфікації), `scones_get_memories`, `obsidian`.
  - ЗАБОРОНЕНО: писати монолітний продакшн-код або виконувати рутинну верстку безпосередньо.
- **Спеціалізовані воркери (`gerych_builder`, `dnk_shopify`, `dnk_video_ai_creator`)**:
  - Інструменти: `patch`, `write_file`, `terminal`, `tsc`, `pytest`.

### Стовп 4: Апаратний Triage Gate (Step 0 Enforcement)
Перед виконанням будь-якої дії над кодом:
```python
triage = dnk_triage_task(user_prompt)
if triage.mode in ["SWARM_PARALLEL", "SWARM_SEQUENTIAL"]:
    # ЖОРСТКА ВИМОГА: Прайм НЕ має права редагувати файли сам.
    # Прайм ЗОБОВ'ЯЗАНИЙ викликати delegate_task або dnk_swarm_parallel!
```

---

## 🚀 Покроковий план впровадження у DNK OS

1. **Крок 1**: Підключити рушій `delegate_task` безпосередньо всередину `dnk_swarm_dispatch` (кожен виклик порождує реальний фоновий субагент Hermes).
2. **Крок 2**: Забезпечити ізоляцію робочих файлів через `target_files` у пейлоаді, щоб воркери не конфліктували за одні й ті самі рядки коду.
3. **Крок 3**: Автоматичний Master Quality Gate: Прайм приймає роботу субагента тільки тоді, коли `tests_passed == True` та `git diff` відповідає архітектурній специфікації.
