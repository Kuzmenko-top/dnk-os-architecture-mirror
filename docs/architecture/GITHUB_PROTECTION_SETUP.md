# GitHub Branch Protection — Налаштування

> ⚠️ **Поточний статус:** Protection **не ввімкнено** (репо приватне на GitHub Free plan — protection доступне лише від **GitHub Pro** $4/міс або для публічних репо). Працюємо за правилом "тільки через PR" вручну. Цей документ — інструкція на той момент, коли буде апгрейд.

Довідник для ручного налаштування у GitHub.
Шлях: `Repository → Settings → Branches → Add branch ruleset` (або `Add rule` у класичному UI)

---

## Правило для гілки `main` (Production)

**Branch name pattern:** `main`

### Обовʼязкові налаштування ✅

| Налаштування | Значення |
|---|---|
| Require a pull request before merging | ✅ Увімкнути |
| Required number of approvals | `1` (мінімум) |
| Dismiss stale pull request approvals | ✅ Увімкнути |
| Require review from Code Owners | ✅ Увімкнути |
| Require status checks to pass before merging | ✅ Увімкнути |
| Require branches to be up to date before merging | ✅ Увімкнути |
| Do not allow bypassing the above settings | ✅ Увімкнути |

### Status checks для додавання
Після першого запуску Actions зʼявиться у списку:
- `validate / Validate Theme Files`

---

## Правило для гілки `staging`

**Branch name pattern:** `staging`

| Налаштування | Значення |
|---|---|
| Require a pull request before merging | ✅ Увімкнути |
| Required number of approvals | `1` |
| Require status checks to pass | ✅ Увімкнути |
| `validate / Validate Theme Files` | ✅ Required |

---

## Правило для гілки `development` (опційно)

**Branch name pattern:** `development`

Слабший захист — щоб не блокувати активну розробку:

| Налаштування | Значення |
|---|---|
| Require status checks to pass | ✅ Увімкнути |
| `validate / Validate Theme Files` | ✅ Required |

---

## Shopify ↔ GitHub Integration

У Shopify Admin → Online Store → Themes → Add theme → Connect from GitHub:

| Гілка | Підключити до теми |
|---|---|
| `main` | **Production theme** (Live — та, яку продаєш клієнтам) |
| `staging` | **Staging theme** (для тестування оновлень) |
| `development` | **НЕ підключати** — працюємо локально через `shopify theme dev` |

Після підключення — кожен push у `main`/`staging` автоматично синхронізує відповідну тему в Shopify.

> ⚠️ Не редагуй підключені теми вручну в Shopify Admin — зміни перезапишуться при наступному push з GitHub.
