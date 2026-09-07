# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_sota_agentic-habits"
# purpose: "SOTA Knowledge Assimilation Report for AgriciDaniel/agentic-habits"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "3.0.0"
# updated_at: "2026-09-05"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Assimilation Report: AgriciDaniel/agentic-habits

## 📊 1. Repository Metrics & Intel
- **Repository**: `AgriciDaniel/agentic-habits`
- **Author**: Daniel Agrici
- **License**: `MIT` (Track 1: Direct Component & Template Assimilation)
- **Primary Languages**: Bash, Markdown, Shell
- **DNK Architecture Alignment Score**: `9.8/10`
- **Core Thesis**: *"An agent is not short of memory. What it is short of is enforcement. Loading an instruction is deterministic. Following it is not."*

---

## 🛡️ 2. License Compliance & Intellectual Property Boundary
- **Track Paradigm**: **Track 1 (Permissive - Direct Template & Architecture Assimilation)**
- **Audit Findings**:
  - Ліцензія MIT дозволяє комерційне використання, модифікацію, розповсюдження та приватне використання.
  - Повна сумісність із DNK OS та Zero-Waste протоколом.

---

## 🧩 3. Key Architectural Innovations & Patterns

### 1. Трьохрівнева система суверенітету поведінки (Three Tiers of Enforcement)
1. **Tier 1: Stated (Rules & Prompts)**
   - Правила у форматі `When -> Do / Instead` із жорстким бюджетом контексту:
     - System Scope: ≤ 12 правил.
     - Project Scope: ≤ 10 правил.
     - Path Scope: ≤ 6 правил.
   - Мета: запобігання деградації уваги та перевантаженню моделі (context bloat).
2. **Tier 2: Gated (Deterministic Lifecycle Hooks)**
   - Реалізація через `completion-gate.sh` (Stop hook).
   - Інтерцептор фіксує евристики заяв про успіх (*"tests pass"*, *"all green"*, *"compiles cleanly"*) та перевіряє реальний транскрипт сесії на наявність виконаних команд-перевірок (`pytest`, `tsc`, `cargo`, `lint`) з успішним кодом завершення.
   - Fail-Open за замовчуванням, блокує рівно 1 раз на хід для уникнення зациклень.
3. **Tier 3: Judged (Independent Read-Only Auditor)**
   - Роль `habit-judge` (в DNK OS — `gerych_auditor`).
   - Свіжий контекст без права запису у файли.
   - Evidence Ledger із розділенням на `[RAW]` (виклики інструментів, diff, рядки виводу) та `[INFER]` (здогадки).
   - Залізне правило: **No evidence means not PASS**.

### 2. Сходи ремонту звичок (The Habit Repair Ladder)
Замість повторення промптів у разі помилки:
1. **Miss 1**: Загострення тригера (`When -> Do/Instead`).
2. **Miss 2**: Зміна скоупу (звуження на конкретний шлях/файли або підняття на рівень вище).
3. **Miss 3**: Ескалація до Gate (створення детермінованого шелл-хука) або архівація (Retire).

### 3. Каталог 12 Анти-звичок (12 Anti-Habits)
Систематизовано найпоширеніші хвороби агентів:
`Phantom done`, `Green-washing`, `Guess stacking`, `Drive-by refactor`, `Silent assumption`, `Context amnesia`, `Confident invention`, `Sycophantic fold`, `Boil the ocean`, `Narration theatre`, `Cleanup by destruction`, `Habit hoarding`.

---

## 🚀 4. Swarm Integration & DNK OS Mapping

| Компонент agentic-habits | Відповідник в DNK OS | Роль Swarm / Модуль |
|---|---|---|
| `skills/habits/SKILL.md` | `skills/agentic-habits/` | `gerych_prime`, `herich_librarian` |
| `completion-gate.sh` | Stop-Hook / Output Interceptor | `core/guards/completion_gate.py` |
| `agents/habit-judge.md` | `gerych_auditor` | `core/orchestrator/agents/gerych_auditor/` |
| 12 Anti-Habits | Invariants у `AGENTS.md` & `SOUL.md` | Всі 14 агентів DNK Swarm |
| Obsidian Knowledge Card | `012 Agentic Habits` | Obsidian Vault (`DNK_HUB My Notes`) |

---

## 📋 5. Actionable Assimilation Plan for DNK OS

1. **[Виконано] Архітектурний аудит та створення картки знань**:
   - Створено canonical note `012 Agentic Habits - Three-Tier Enforcement & Anti-Habit Guard Architecture.md` в Obsidian Vault.
2. **[Рекомендовано] Впровадження `CompletionGate` в `core/guards/`**:
   - Інтегрувати детерміновану перевірку реальних викликів тестів перед тим, як агент звітує про готовність задачі.
3. **[Рекомендовано] Озброєння `gerych_auditor` функцією Habit Ledger**:
   - Під час pre-commit перевірок генерувати звіт про дотримання обов'язкових інваріантів на основі чистих доказів `[RAW]`.
4. **[Рекомендовано] Створення внутрішнього скіла `agentic-habits`**:
   - Забезпечити інтерфейс команд `/habits add`, `/habits check`, `/habits judge` для безперервного покращення продуктивності та надійності розробки.
