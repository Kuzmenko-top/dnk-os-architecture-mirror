---
title: "ADR 0043: DeepSeek Harness (dsh) SOTA Audit & Assimilation Blueprint"
aliases:
  - "ADR 0043"
  - "DeepSeek Harness ADR"
  - "dsh Architecture & Assimilation"
  - "Аудит та план асиміляції DeepSeek Harness в DNK_HUB"
tags:
  - dnk-hub
  - adr
  - architecture
  - deepseek
  - harness
  - cordis
  - ptc
  - sandbox
  - sota-assimilation
type: adr
status: active
created: 2026-09-05
updated: 2026-09-05
author: "Maksym Kuzmenko & Gerych Prime"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "obsidian/DNK_HUB/02_Architecture/ADR_0043_DeepSeek_Harness_Audit_and_Assimilation.md"
purpose: "ADR 0043: Architectural Audit and Assimilation Plan for deepseek-ai/deepseek-harness into DNK_HUB"
canonical_source: false
alters_files: []
triggers_tasks: ["TASK-DSH-ASSIMILATION-001"]
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "Maksym Kuzmenko & Gerych Prime"
--- END DNK-MRH-HEADER -->

# ADR 0043: DeepSeek Harness (`dsh`) SOTA Audit & Assimilation Blueprint

## 📌 Context & Motivation

У межах протоколу безперервної еволюції DNK OS та Two-Track SOTA Assimilation Engine проведено глибокий аудит флагманського агентного фреймворку від DeepSeek AI: [[https://github.com/deepseek-ai/deepseek-harness|deepseek-ai/deepseek-harness]] (`dsh`).

Репозиторій налічує понад 212,700+ зірок, 24,970+ форків, містить 50+ функціональних доменів пакетів під pnpm workspaces та реалізує радикальну архітектурну філософію: **"Everything is a Plugin"** на базі IoC-мікроядра **Cordis** (описаного у праці *A Programming Paradigm for Spatiotemporal Composability*, arXiv:2608.25512).

## ⚖️ License & Legal Track

- **Ліцензія**: MIT License (Approved).
- **Assimilation Track**: **Track 1 (Permissive Component Adaptation & Clean Architecture Porting)**.
- **Повна юридична безпека**: Код є відкритим, без copyleft обмежень. Повна сумісність із комерційним використанням у [[DNK_HUB]].

## 🧬 Ключові Архітектурні Парадигми `dsh`

1. **Cordis Microkernel & Reversible Context (`ctx`)**:
   Жодної монолітної жорстко зашитої логіки. Усі можливості монтуються як плагіни, що реєструють сервіси та зворотні ефекти (`ctx.effect()`). При вивантаженні плагіна ресурси та інструменти очищаються автоматично.
2. **5-Stage Guarded Tool Execution Pipeline**:
   - `pre-execute` (waterfall allow/deny/ask)
   - `guard` (монотонна синхронна перевірка інваріантів)
   - `execute` (таймаути, retry, circuit-breakers)
   - `post-execute` (трансформація виводу)
   - `result` (незмінний аудит-лог)
3. **PTC (Programmatic Tool Calling) Mode**:
   Замість 10 послідовних викликів інструментів через LLM round-trips, генерується динамічний типізований SDK. Агент пише 5-рядковий скрипт, який виконується в ізольованому воркері за 1 крок.
4. **Append-Only `SessionEvent` Log**:
   Журнал подій у SQLite/JSONL. Детермінований fork/resume та автоматичне відновлення стану після падіння процесу.
5. **Zero-Trust OS Sandboxing**:
   Трирівневий захист процесів: `read-only`, `workspace-write`, `danger-full-access` з апаратною ізоляцією через Linux **Landlock / bwrap** та macOS **Seatbelt (`sandbox-exec`)**.

## 🎯 План Асиміляції в DNK_HUB / DNK_HUD

- **Етап 1**: Впровадження 5-етапного конвеєра захисту інструментів у `core/security/tool_guard_pipeline.py`.
- **Етап 2**: Реалізація Python PTC Engine (`core/executors/ptc/`) для масових пакетних операцій агентів без вичерпання ліміту інструментів.
- **Етап 3**: OS-level Sandboxing для терміналу та інструментів виконання (`core/security/sandbox/`).
- **Етап 4**: Гексагональний міст `adapters/dsh_bridge.py` для опційного виконання агентів під керуванням рідного рантайму `dsh`.

## 🔗 Повʼязані посилання

- [[docs/tech/sota_assimilation/SOTA_DEEPSEEK-HARNESS_ASSIMILATION.md|Повна специфікація асиміляції в репозиторії]]
- [[ADR_0042_Canvas_Runtime_Bridge_WebSocket_Integration|ADR 0042: Canvas Runtime Bridge]]
- [[core/orchestrator/agents/gerych_prime/SOUL.md|Gerych Prime Architecture]]
