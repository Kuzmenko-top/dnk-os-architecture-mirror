---
title: "091 Аналіз Зміни Запиту Ментора Perplexity та План Аудиту Слайсу 0.2-A"
date: "2026-09-07"
tags:
  - architecture
  - audit-slice
  - api-contracts
  - perplexity-review
  - dnk-hub-0-2
status: active
mrh_id: "docs/notes/091_perplexity_baseline_analysis_and_audit_slice_0_2_a_opinion.md"
purpose: "Аналіз оновленого запиту ментора Perplexity на основі baseline-звіту та обґрунтування проведення контрактного аудиту API без модифікації коду"
canonical_source: true
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/091_perplexity_baseline_analysis_and_audit_slice_0_2_a_opinion.md"
# purpose: "Аналіз оновленого запиту ментора Perplexity на основі baseline-звіту та обґрунтування проведення контрактного аудиту API без модифікації коду"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🧠 Аналіз Оновленого Запиту Ментора Perplexity та Вердикт Герича

## 1. Що відбулося і чому ментор змінив свою думку?

Коли ментор Perplexity побачив реальні цифри нашого звіту `DNK_OS_CAPABILITY_BASELINE_v0.1.md`, його сприйняття проекту кардинально змінилося:
- **Було (уявлення ментора)**: "У них є набір чернеток та ідей, треба допомогти їм почати писати ядро з нуля".
- **Стало (реальність)**: "Перед нами потужна, працююча production-grade система з **2 197 тестами**, 30+ роутерами, 14 агентами та складним Canvas. Будувати з нуля — це самогубство. Потрібна **архітектурна консолідація**".

Ментор виявив високий інженерний рівень, сформулювавши 6 абсолютно реальних технічних ризиків нашої поточної системи:
1. **Подвійне монтування роутерів** у `apps/api/main.py`.
2. Залежність `gerych.sh` від сесії Google Cloud CLI.
3. Ризик розсинхронізації Obsidian Vault.
4. Поведінка WebSocket broadcast під паралельним навантаженням.
5. Статус PostgreSQL / pgvector у продакшені.
6. Рендеринг Remotion на безголовому Linux без дискретної GPU.

---

## 2. Верифікація факту: Подвійне монтування роутерів у `apps/api/main.py`

Герич провів миттєву перевірку рядків 157–185 у `apps/api/main.py`:
```python
app.include_router(canvas.router)
app.include_router(canvas.router, prefix="/api")
app.include_router(agent.router)
app.include_router(agent.router, prefix="/api")
app.include_router(artifact.router)
app.include_router(artifact.router, prefix="/api")
app.include_router(analytics.router)
app.include_router(analytics.router, prefix="/api")
app.include_router(taskdna.router)
app.include_router(taskdna.router, prefix="/api")
app.include_router(workflow_composer.router)
app.include_router(workflow_composer.router, prefix="/api")
```

**Чому це виникло історично?**
Під час швидкого прототипування фронтенд у різних компонентах використовував як відносні шляхи `/canvas/...`, так і `/api/canvas/...`. Щоб нічого не ламалося під час релізів, роутери підключалися двічі.
Це працює, але створює роздуту OpenAPI специфікацію, плутанину в документації та ризик розсинхрону.

---

## 3. Вердикт Герича щодо завдання "Audit Slice 0.2-A"

Вимога Ментора: **"Read-only audit. Не видаляти, не переміщувати та не перейменовувати код"** — це **100% професійне та безпечне рішення**.

Якщо ми зараз почнемо навмання "чистити" дублікати в `main.py`, ми ризикуємо зламати виклики у фронтенді (Next.js / Canvas) або завалити частину з 2 197 тестів.

Створення артефактів:
- `docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.md`
- `docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.json`

дасть нам вичерпну карту:
1. Які роутери дублюються.
2. Які ендпоінти реально смикає фронтенд (`apps/web`).
3. Які ендпоінти покриті автотестами.
4. Який канонічний шлях (`/api/v1/...`) зробити єдиним стандартом.

---

## 4. Рекомендація для Максима

1. **Повністю погодитися з пропозицією Ментора.** Це зберігає систему стабільною.
2. **Дати команду Геричу на виконання Audit Slice 0.2-A в режимі Read-Only.**
3. Герич збере повні дані за 1 прохід скрипта без жодної мутації кодової бази і згенерує карту контрактів.
4. Передати отриманий звіт Ментору для формування фінального рішення щодо переходу на єдиний канонічний API-шар.
