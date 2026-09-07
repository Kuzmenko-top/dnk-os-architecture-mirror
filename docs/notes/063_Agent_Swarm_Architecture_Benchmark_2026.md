---
title: "063 Agent Swarm Architecture Benchmark 2026"
aliases:
  - "035_Agent_Swarm_Architecture_Benchmark_2026"
  - "Agent Swarm Comparative Analysis"
  - "Бенчмарк та порівняльний аналіз архітектур роїв агентів 2026"
  - "Ruflo vs Swarms vs CCSwarm vs DevSwarm vs AgentSwarms"
tags:
  - dnk-hub
  - architecture
  - swarm
  - benchmark
  - sota
  - gerych
  - obsidian
type: architecture-benchmark
status: active
created: 2026-09-06
updated: 2026-09-06
author: "Gerych Prime & Maksym Kuzmenko"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "obsidian/DNK_HUB/063_Agent_Swarm_Architecture_Benchmark_2026.md"
purpose: "Deep comparative architectural benchmark of 5 Agent Swarm repositories to define the SSOT swarm foundation for DNK OS."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🐝 Порівняльний архітектурний бенчмарк 5 репозиторіїв Swarm-систем (2026)

## 📌 1. Виконавче резюме (Executive Summary)

Для реалізації **дійсно працюючого, технологічно зрілого та надійного Agents Swarm у реальному виробництві** (особливо для інженерії, кодингу, оркестрації CLI-агентів та безпечного паралельного виконання) безумовним лідером є:

1. **👑 Абсолютний переможець за промисловою зрілістю та практикою:**
   **`ruvnet/ruflo`** (раніше `claude-flow`, 70.9k+ ⭐, v3.38.21, TypeScript + Rust/RuVector, ліцензія MIT).
   Це де-факто індустріальний стандарт meta-harness оркестратора, створений спеціально для реальних CLI-агентів (Claude Code, OpenAI Codex, Hermes Agent, OpenCode, Amp).

2. **💎 Найкращий архітектурний донор для ізоляції та детермінізму:**
   **`nwiizo/ccswarm`** (151 ⭐, Rust edition 2024, Tokio, ліцензія MIT).
   Містить дві фундаментальні інженерні перлини: **Git Worktree Isolation** (паралельні агенти ніколи не ламають спільні файли) та **Sangha Consensus & MovementJudge** (математично суворий консенсус перед мутацією коду).

3. **📊 Когнітивний донор топологій (суто для алгоритмів промптів):**
   **`kyegomez/swarms`** (7.1k ⭐, Python v15, Apache-2.0).
   Хороша енциклопедія теоретичних топологій (Mixture-of-Agents, Majority Voting, Hierarchical Swarm), але не підходить як інфраструктурний рантайм через надмірний хайп і відсутність системного сандбоксу.

---

## 🔬 2. Порівняльна матриця

| Критерій | `ruvnet/ruflo` | `nwiizo/ccswarm` | `kyegomez/swarms` | `justrach/devswarm` | `AgentSwarms-fyi/agentswarms` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Основна мова** | TypeScript + Rust | Rust (Tokio) | Python | Zig (0.15) | TypeScript (React 19) |
| **Зірки / Форки** | **70,922** / 8,431 | 151 / 15 | 7,138 / 1,012 | 67 / 7 | 232 / 56 |
| **Ліцензія** | **MIT** (вільна) | **MIT** (вільна) | **Apache-2.0** | ⚠️ AGPL-3.0 (Copyleft) | ⚠️ Elastic License 2.0 |
| **Фокус системи** | **Meta-Harness & Swarm Ledger** | **Git DevOps & Quality Gates** | Алгоритми промпт-роїв | High-perf MCP Graph | Fullstack Data/BI UI |
| **Ізоляція виконання** | Process / MCP / Plugins | **Git Worktrees per Agent** | Немає (in-process LLM) | MCP Subprocess | Docker / Cloud |
| **Пам'ять & Контекст** | **AgentDB / RuVector / HNSW** | Faceted Context / NDJSON | In-memory conversation | In-memory AST DB | Supabase / Lakehouse |
| **Сумісність з DNK OS** | **100% (Native MCP / Hermes)** | **95% (Rust engine patterns)** | 40% (лише алгоритми) | 30% (ліцензійний ризик) | 20% (це UI/BI застосунок) |

---

## 🏛️ 3. Детальний аналіз кожного кандидата

### 🥇 1. `ruvnet/ruflo` — Король Meta-Harness та індустріальний стандарт
- **Архітектурна філософія**: Чіткий поділ на **Ledger (Координатор)** та **Executors (Виконавці)**.
  - *Ledger (ruflo)*: веде глобальний реєстр завдань, зберігає спільну пам'ять у векторизованій БД (`RuVector` / `agentdb.rvf`), перевіряє політики безпеки та транслює події через MCP.
  - *Executors (Claude Code / Hermes / Codex)*: реальні агентні інструменти, які пишуть код і виконують тести.
- **Технологічна зрілість**:
  - Більше 8.1 мільйона завантажень компонентів екосистеми.
  - Постійні щоденні релізи (v3.38.21).
  - Підтримка 60+ спеціалізованих агентських ролей.
  - Нативна інтеграція з протоколом Model Context Protocol (MCP).
- **Вердикт для DNK OS**: Головна платформа для прямої інтеграції або запозичення структури координаційного леджера.

### 🥈 2. `nwiizo/ccswarm` — Інженерний еталон надійності та Git-ізоляції
- **Архітектурна філософія**: Суворе детерміноване керування життєвим циклом агентів мовою Rust.
  - **Git Worktree Isolation**: Коли спавниться 3-4 паралельних агенти, вони працюють у фізично ізольованих гілках Git Worktree. Це повністю унеможливлює стан гонитви (race conditions) при паралельній правці файлів.
  - **Sangha Consensus Protocol**: Математично формалізована рада агентів перед затвердженням архітектурного плану чи мерджем коду.
  - **Faceted Prompting**: Розділення промптів на чіткі фасети (Policy, Persona, Knowledge).
  - **NDJSON Audit Stream**: Повний аудит усіх дій із можливістю точного реплею та відкату (replay / rollback).
- **Вердикт для DNK OS**: Критично важливий донор для ядра паралельного виконання рою DNK OS.

### 🥉 3. `kyegomez/swarms` — Теоретичний інкубатор когнітивних топологій
- **Архітектурна філософія**: Python-бібліотека високорівневих топологій (Sequential, Concurrent, GroupChat, Mixture-of-Agents, Majority Voting).
- **Слабкі сторони**:
  - Дуже високий рівень маркетингу при нестабільному API (постійні злами між версіями).
  - Працює як звичайна обгортка над API OpenAI/Anthropic: немає розуміння Git, терміналу, компіляції чи системного середовища.
- **Вердикт для DNK OS**: Використовувати виключно як довідник математичних патернів маршрутизації думок (MoA / Voting).

### ⚠️ 4. `justrach/devswarm` — Високошвидкісний, але ліцензійно ризикований
- **Архітектурна філософія**: Сервер MCP на мові Zig для аналізу радіусу ураження змін (blast radius) та AST-графа коду.
- **Обмеження**:
  - Ліцензія **AGPL-3.0**: вірусна копілефт-ліцензія, яка створює правові ризики для закритих або клієнтських компонентів DNK OS.
  - Версія `v0.0.28`, рання експериментальна стадія.

### 🛑 5. `AgentSwarms-fyi/agentswarms` — Не той клас систем
- **Архітектурна філософія**: Це повноцінний Web-додаток (React 19, Supabase, TanStack Start) для створення бізнес-дашбордів, data lakehouse та простих чат-ботів.
- **Вердикт для DNK OS**: Не є інструментом для розробницьких роїв чи системного кодингу.

---

## 🚀 4. Стратегічна рекомендація для DNK OS Swarm

Для побудови найбільш продуктивного рою в DNK OS (`gerych_prime` + 14 спеціалізованих воркерів):

1. **Фундамент оркестрації (L1)**: Архітектура **`ruvnet/ruflo`** (відокремлення координаційного Ledger від фізичних агентів-виконавців через MCP).
2. **Механіка паралельного виконання (L2)**: Патерн **`nwiizo/ccswarm`** (Git Worktree ізоляція для паралельних воркерів `gerych_builder`, `dnk_dev_fullstack` та гейт `Sangha Consensus`).
3. **Когнітивна маршрутизація (L3)**: Топології **Mixture-of-Agents** та **Council as Judge** із `kyegomez/swarms`.
