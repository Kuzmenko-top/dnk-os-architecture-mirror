---
name: "discourse-architecture"
description: "SOTA Community Platform & Discussion Engine architecture patterns: Trust Levels 0-4, MessageBus WebSockets, Topic/Post DAG, and Guardian Authorization."
repo_url: "https://github.com/discourse/discourse"
version: "1.0.0"
category: "research"
assimilated_at: "2026-08-18"
license: "MIT (Clean-Room Cleaned from GPL-2.0 upstream)"
author: "DNK-e.com Maksym"
---

# 🌐 Навичка: Discourse Architecture (SOTA Community & Discussion Engine)

Цю навичку автоматично синтезовано з архітектури **[discourse/discourse](https://github.com/discourse/discourse)** через протокол Clean-Room Design.

## 📌 Ключові Архітектурні Паттерни

### 1. Guardian Authorization Layer
- Ізольований шар перевірки прав доступу на рівні бізнес-логіки.
- Методи: `can_see_topic?`, `can_create_post?`, `can_moderate?`, `can_edit_category?`.
- Гарантує нульовий витік приватних контекстів між агентами та користувачами.

### 2. Trust Levels (0–4) Matrix
- **TL0 (Newuser)**: Жорсткі ліміти (не більше 2 посилань, блокування спаму).
- **TL1 (Basic)**: Доступ до базових гілок та реакцій.
- **TL2 (Member)**: Підвищені ліміти, створення кастомних тегів.
- **TL3 (Regular)**: Авто-модерація, переміщення топіків.
- **TL4 (Leader)**: Закриття/відкриття топіків, захист системних категорій.

### 3. MessageBus WebSocket Architecture
- Легковаговий pub/sub через Redis для миттєвої доставки подій клієнтам.
- Гарантована послідовність повідомлень за `message_id` без перевантаження бази даних.

### 4. Topic & Post DAG Data Structure
- Лінійне та ієрархічне представлення повідомлень із повнотекстовим пошуком та дедуплікацією (`reply_to_post_number`).

## 🛠️ Використання У Свармі Герича
Використовувати цю навичку при проектуванні комунікаційних хабів, агентських форумів, систем модерації та WebSockets шин для DNK OS.
