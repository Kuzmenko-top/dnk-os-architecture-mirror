# --- DNK-MRH-HEADER ---
# mrh_id: "skills/README.md"
# purpose: "Canonical Architecture and Governance Guide for DNK OS Agent Skills Registry"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# ⚡ DNK OS AGENT SKILLS REGISTRY
## РЕГЛАМЕНТ СТВОРЕННЯ ТА ВИКОРИСТАННЯ НАВИЧОК АГЕНТІВ

Ця директорія містить модульні, багаторазові навички для агентів рою (Rick, Yuriy, Cas, Tiffany, Morgan).

### 🏛️ Обов'язковий 3-Елементний Каркас Навички:
Кожен підкаталог `skills/<skill_name>/` зобов'язаний містити:
1. `SKILL.md` — Інструкція для агентів із YAML frontmatter (`name`, `description`).
2. `scripts/` — Виконувані Python/Bash скрипти, які агент викликає як інструменти.
3. `references/` — Додаткова технічна документація та схеми (якщо опис > 500 рядків).

### 🛡️ Непорушні Правила:
- У шапці `SKILL.md` дозволені ТІЛЬКИ поля `name` та `description`.
- Навички мають бути ідемпотентними та підтримувати автоматичний виклик через tool dispatching.
