---
document_id: DNK-DEV-1922
file_name: GITHUB_SHOPIFY_WORKFLOW.md
title: GitHub & Shopify Multi-Branch Deployment Strategy
category: DEV
type: Guide
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - shopify
  - github
  - multi-branch
  - workflow
  - deployment
storage_type: git
path: services/dnk_shopify/docs/tech/GITHUB_SHOPIFY_WORKFLOW.md
access_level: write
checksum: null
changelog_ref: null
---

# 🔱 СТРАТЕГІЯ: БАГАТОГІЛКОВА РОЗРОБКА ТА ПОСТУПОВИЙ ДЕПЛОЙ (GITHUB & SHOPIFY)

Для безпечного тестування фіч на різних гілках та поступової публікації оновлень у Shopify (без ризику зламати «живий» сайт клієнта Мудрий Крафтяр), ми впроваджуємо **канонічний Git-Shopify Workflow**.

Цей підхід базується на офіційній інтеграції **Shopify GitHub Integration** та використанні окремих тем-оточень для кожної гілки.

---

## 🗺️ 1. Архітектурна карта гілок та тем (Branch-to-Theme Mapping)

Кожна гілка у нашому GitHub-репозиторії зв'язується з окремою копією теми в адмінці Shopify. Це дозволяє тестувати кожну зміну в ізольованому середовищі.

```
       [ FEATURE BRANCH ] ────> ( Авто-деплой у "Feature-Theme" для тестування Максом )
               │
               ▼ ( Pull Request & Код-рев'ю ШІ-агентами )
       [ STAGING BRANCH ] ────> ( Авто-деплой у "Staging-Theme" для клієнта Мудрий Крафтяр )
               │
               ▼ ( Merge після затвердження )
       [ MAIN BRANCH ]    ────> ( Авто-деплой у головну "Live Production" тему )
```

| Гілка GitHub | Тема в Shopify | Цільове призначення | Хто тестує |
| :--- | :--- | :--- | :--- |
| `main` | **Мудрий Крафтяр - Production (Live)** | «Живий» сайт, який бачать покупці. | Покупці |
| `staging` | **Мудрий Крафтяр - Staging** | Перед-релізна тема для фінальної перевірки клієнтом. | Максим & Клієнт |
| `feature/*` | **DNK-Ecom - Feature [Назва фічі]** | Ізольована тема для тестування конкретної секції/дизайну. | Тільки Максим / ШІ |

---

## ⚙️ 2. Покрокове налаштування інтеграції (Set Up)

### Крок A: Налаштування зв'язку в Shopify Admin
1. Перейди в адмінці магазину Мудрий Крафтяр у розділ **Online Store -> Themes**.
2. У розділі **Theme library** натисни кнопку **Add theme -> Connect from GitHub**.
3. Увійди у свій GitHub-акаунт та вибери потрібний репозиторій теми.
4. Створи перше з'єднання: вибери гілку `main` та підключи її (Shopify автоматично створить тему, під назвою твого репо).
5. Повтори дію для гілки `staging` та фіче-гілок. Тепер **кожен твій комміт у ці гілки буде миттєво та автоматично деплоїтись у відповідну тему в Shopify!**

---

## 🔁 3. Робочий процес розробки та деплою (Step-by-Step Workflow)

Коли ти або ШІ-агент створюєте нову фічу (наприклад, таймер або новий Advertorial):

### Етап 1: Створення ізольованого простору (Feature Branch)
Ми створюємо нову гілку від `staging` або `main`:
```bash
git checkout -b feature/reburn-countdown-timer
```
Працюємо над кодом Liquid-секцій.

### Етап 2: Автоматична перевірка лінтером (Quality Gate)
Перед відправкою на GitHub обов'язково запускаємо перевірку синтаксису:
```bash
shopify theme check
```

### Етап 3: Пуш на GitHub та ізольоване тестування
Відправляємо зміни на GitHub:
```bash
git add .
git commit -m "feat: додав кастомний таймер зворотного відліку як App Block"
git push origin feature/reburn-countdown-timer
```
*Результат:* Shopify миттєво оновлює підключену фіче-тему. Ти можеш відкрити її попередній перегляд (Preview) та подивитися на роботу таймера, не впливаючи на інші частини сайту.

### Етап 4: Перенесення на Staging для перевірки клієнтом
Коли ти переконався, що все працює чудово, створюєш **Pull Request** з гілки `feature/...` у гілку `staging`.
Після мержу, клієнт (Мудрий Крафтяр) заходить на тему `Staging` і затверджує оновлення.

### Етап 5: Публікація (Release to Production)
Робимо фінальний мерж `staging` $\rightarrow$ `main`. Головна тема магазину автоматично оновлюється без жодної хвилини простою сайту (zero-downtime deploy)!
