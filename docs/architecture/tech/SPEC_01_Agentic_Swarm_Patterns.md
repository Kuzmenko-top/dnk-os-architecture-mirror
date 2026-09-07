# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/SPEC_01_Agentic_Swarm_Patterns.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🐝 Маніфест Агентних Паттернів Та Самопокращення (AgentSwarms & DNK OS)

Цей документ описує концептуальну та технічну модель побудови **Самонавчальної Агентної Платформи** в **DNK OS**, синтезовану на основі принципів з репозиторію [AgentSwarms](https://github.com/AgentSwarms-fyi/agentswarms).

---

## 🧬 1. Чотири Ключові Агентні Паттерни (Agentic Patterns)

### 1.1 Паттерн "Оркестратор - Ворекери" (Orchestrator-Workers Pattern)
- **Головний Оркестратор**: **Герич (Hermes)**.
- **Воркери-Спеціалісти**:
  - **🔧 Rick**: Спеціаліст з рефакторингу, оптимізації та написання юніт-тестів pytest.
  - **📚 Yuriy**: Спеціаліст з RAG, парсингу нотаток та консолідації баз знань.
  - **⚡ Cas**: Спеціаліст з інфраструктури, Docker, FastAPI та CLI-і струментів.
  - **🎨 Tiffany**: Спеціаліст з UI/UX, ReactFlow Canvas, TailwindCSS та в'ю-компонентів.
  - **💼 Morgan**: Спеціаліст з аналітики, бізнес-метрики та Shopify UCP екосистеми.

### 1.2 Паттерн "Оцінювач - Оптимізатор" (Evaluator-Optimizer Loop)
- Ніколи не вважати задачу виконаною за 1 запуск.
- Після того, як робітник пише код, Оцінювач (Path Guard & Pytest suite) запускає перевірку.
- При виявленні відхилень коду чи помилок, задача автоматично повертається на доопрацювання.

### 1.3 Паттерн "Самопокращення Та Навчання" (Autonomous Reflection Loop)
- Після проходження 100% циклу розробки (закриття Куща чи Дерева):
  1. Збирається **Execution Blueprint** (що змінили, які промпти спрацювали).
  2. Урок виписується у `docs/reports/execution_cycles/CYC_{id}_REPORT.md`.
  3. Автоматично оновлюється файл пам'яті агентів та навичка.

### 1.4 Паттерн "Модульна Навичка Контексту" (Standardized Skill Architecture)
Кожна навичка у системі повинна мати стандартний склад папок для 100% точності контексту:
```text
skills/<skill_name>/
├── SKILL.md                 # YAML-фронтматер + markdown-інструкція (до 500 рядків)
├── scripts/                 # Автономні Python/Shell скрипти розширення
├── references/              # Глибока технічна документація та стандарти
├── examples/                # Зразки коду та прикладів ужитку
└── resources/               # JSON-схеми, конфіги та шаблони
```

---

## 🏛️ 2. Стандарт Фабрики Агентів (Agent Factory Standard)

Будь-який новий агент у **DNK OS** створюється за єдиним канонічним шаблоном:

```text
core/agent_factory/templates/agent_template/
├── SOUL.md                  # Філософія, місія та комунікаційний протокол
├── MANIFEST.yaml            # Метадані, дозволи, версія, підключені інструменти
├── skills/                  # Локальні навички агента
└── memory/                  # Файли короткострокової та довгострокової пам'яті
```

### Структура `MANIFEST.yaml`:
```yaml
agent_id: "agent_rick_01"
name: "Rick"
role: "Senior Refactoring & Testing Engineer"
capabilities:
  - pytest_runner
  - path_guard_auditor
  - code_cleaner
allowed_skills:
  - dnk-task-graph-manager
  - obsidian-task-forest
memory_path: "core/agent_factory/agents/rick/memory/"
```