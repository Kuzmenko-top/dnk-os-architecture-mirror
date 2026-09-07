---
title: "008 Archify Spatial Diagram Engine - Autonomous Architecture & Workflow Assimilation Protocol"
aliases:
  - "Archify Audit"
  - "Archify Diagram Engine"
  - "Аудит та Асиміляція Archify"
  - "Spatial Diagram Engine"
tags:
  - dnk-hub
  - archify
  - diagrams
  - architecture
  - sota-assimilation
  - swarm-orchestration
  - zero-waste
type: architecture
status: active
created: 2026-09-04
updated: 2026-09-04
author: "Maksym Kuzmenko & Gerych Prime"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "obsidian/DNK_HUB/008 Archify Spatial Diagram Engine - Autonomous Architecture & Workflow Assimilation Protocol.md"
purpose: "Canonical Architectural Specification, Technical Audit & Assimilation Roadmap for Archify (tt-a1i/archify) in DNK OS."
canonical_source: true
alters_files: []
triggers_tasks: ["TASK-ARCHIFY-ASSIMILATION-001"]
status: "Active"
version: "1.0.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

-->

# 📐 008 Archify Spatial Diagram Engine: Автономний рушій інтерактивних просторових діаграм та протокол асиміляції

> [!abstract] **Суть системи в одному реченні**
> **Archify** (`tt-a1i/archify`) — це ультра-швидкий, повністю автономний (self-contained) компілятор інтерактивних діаграм нового покоління для ШІ-агентів: він компілює строгий типізований JSON IR у самодостатній єдиний HTML-файл з векторним SVG, плавною анімацією потоків сигналів (`signal-flow`), інтерактивним зумом/панорамуванням, семантичними лінзами фокусування (`views`) та нульовими зовнішніми залежностями в рантаймі.

---

## 👤 Частина 1: Для Максима (Людина / Архітектор)

### 💡 Проста аналогія: Чому це вирішує давній біль і чому це краще за Mermaid та PlantUML?
Уяви, як створюються схеми зараз:
1. **Mermaid / PlantUML:** Вони непогані для простих блок-схем у Markdown, але коли система стає складною (14 агентів Swarm, черги, бази даних, мікросервіси), схема перетворюється на "макаронну фабрику", де стрілки перетинаються, текст налазить на блоки, а сама схема абсолютно статична і пласка.
2. **Figma / Miro / Lucidchart:** У них чудовий вигляд, але ШІ-агенти не можуть напряму підтримувати їх в актуальному стані в репозиторії, і за кожен перегляд потрібні сторонні сайти чи підписки.

**Archify робить революцію у візуалізації архітектури:**
- **Повна автономність (Zero-Network Single HTML):** Згенерований файл (`.html`) містить абсолютно все всередині — стилі, векторний SVG, скрипти інтерактивності. Його можна відкрити локально у браузері, переслати партнеру або вбудувати в наш додаток без жодного сервера чи Інтернету.
- **Інтерактивність рівня Figma з коду:** Ти можеш зумити схему, перетягувати полотно (pan/zoom), перемикати темну/світлу тему, клікати на семантичні лінзи (наприклад, подивитися тільки шлях безпекового аудиту або тільки ланцюг обробки відео) та бачити, як сигнал біжить по лініях.
- **Вбудований лінтер краси та розмірів:** Компілятор автоматично вимірює ширину тексту в пікселях і блокує збірку, якщо текст вилазить за межі картки або стрілки ламають читабельність.

### 🌟 Що це дає екосистемі DNK OS?
1. **Жива архітектурна карта DNK OS ([[002 DNK OS - Master System Architecture & Implementation Blueprint|002 Master Blueprint]]):**
   При кожному релізі чи зміні мікросервісів наші агенти автоматично оновлюють інтерактивні карти архітектури.
2. **Візуалізація 14-агентного Рою ([[Gerych Prime - Unified Orchestrator & SOTA Adaptation Engine|Gerych Prime & Swarm]]):**
   Завдання Максима розкладається на фази: `Task DNA Triage` ➔ `Gerych Builder` ➔ `Fullstack Dev` ➔ `Auditor` ⚔️ ➔ `Master Quality Gate`. Завдяки домену `workflow` ми бачимо плавальні доріжки кожного агента та точний статус.
3. **Sequence-діаграми для A2A Mesh:**
   Миттєва генерація таймлайнів спілкування між агентами (хто кому передав контекст, де спрацював SCONES кеш, які артефакти повернено).

---

## 🤖 Частина 2: Архітектурна специфікація та технічні кишки (Для Герича та Агентів Рою)

### 🔬 1. Топологія та взаємодія компонентів

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 ARCHIFY / DNK OS INTEGRATION TOPOLOGY                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. PYTHON HEXAGONAL ADAPTER (`core/adapters/dnk_archify_adapter.py`):       │
│    - Pydantic v2 DTOs: ArchifyNode, ArchifyEdge, ArchifyPhase, ArchifyLane  │
│    - JSON IR Generator & Schema Validator (Architecture, Workflow, etc.)    │
│    - Preset Builders: `build_swarm_workflow_preset()`                       │
│                                                                             │
│ 2. CORE COMPILER ENGINE (`packages/archify/`):                              │
│    - Node.js CLI: `node packages/archify/bin/archify.mjs render`            │
│    - Schemas: `architecture`, `workflow`, `sequence`, `dataflow`, `lifecycle│
│    - Diagnostics: `diagnostics.mjs` (layout constraints & width verification│
│                                                                             │
│ 3. DELIVERABLE ARTIFACTS (`docs/diagrams/*.html`):                          │
│    - Self-contained SVG Canvas with Embedded Vanilla Pan/Zoom Script        │
│    - Signal-flow CSS animations & SVG Filters                               │
│    - Views & Route Focus Tracing                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🧬 2. Стандартизація артефактів за протоколом DNK-TASK-STD-001
- **Research Digest:** `docs/reports/rd_assimilation/archify/RN-009_archify_diagram_engine_audit_and_assimilation.md`
- **Architecture Spec:** `docs/tech/specs/DNK-ARCH-009_archify_spatial_diagram_engine.md`
- **Contracts:** `docs/tech/specs/DNK-COMP-009_archify_diagram_contracts.md`
- **Security Standard:** `docs/tech/standards/DNK-SEC-009_archify_execution_sandbox.md`
- **Skill:** `skills/archify_assimilated/SKILL.md`

### 💻 3. Приклад використання в коді

```python
from core.adapters.dnk_archify_adapter import DNKArchifyAdapter, ArchifyDiagramType

adapter = DNKArchifyAdapter()

# Перевірка працездатності рушія
assert adapter.is_engine_ready() is True

# Генерація інтерактивного воркфлоу Рою DNK OS
preset = adapter.build_swarm_workflow_preset(output_path="docs/diagrams/dnk_swarm_workflow.html")
html_path = adapter.render_diagram(
    diagram_type=ArchifyDiagramType.WORKFLOW,
    payload=preset,
    output_html_path="docs/diagrams/dnk_swarm_workflow.html"
)
```

### 🎯 4. Зв'язки з іншими підсистемами DNK OS
- [[000 DNK HUB Index|DNK HUB Index]] — Головний реєстр системи.
- [[002 DNK OS - Master System Architecture & Implementation Blueprint|002 Master Blueprint]] — Системна архітектура та маппінг компонентів.
- [[004 Gerych Task Specification Standard & Zero-Waste Protocol v2.5|004 Zero-Waste Protocol]] — Стандарти виконання завдань та генерації артефактів.
- [[006 Diffusion Studio Editor - Agent-Native Video Engine & Assimilation Protocol|006 Diffusion Studio Editor]] — Візуальний відео-стек.
