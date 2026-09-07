# --- DNK-MRH-HEADER ---

# mrh_id: "docs/tech/guides/DNK-GUIDE-001_gcp-account-rotation.md"

# purpose: "User and Agent operational guide for instant GCP account/project rotation"

# canonical_source: true

# alters_files: []

# triggers_tasks: []

# status: "Active"

# version: "1.0.0"

# updated_at: "2026-08-11"

# author: "DNK-e.com Maksym"

# --- END DNK-MRH-HEADER ---

# 🔄 ІНСТРУКЦІЯ: ШВИДКА ЗМІНА GCP АКАУНТА ТА КВОТ (GCP ACCOUNT ROTATION)

> Цей документ призначений для **Людини (Максима)** та для **Агентів DNK OS** для швидкої ротації Google Cloud акаунтів і проектів Vertex AI у разі вичерпання лимитів, квот або білінгових кредитів.

---

## ⚡ Швидка ротація у 2 дії (Для Людини)

Коли закінчилися кредити чи квота на поточному акаунті:

### Крок 1. Залогінься у новий акаунт Google

У терміналі Mac виконай:

```bash
gcloud auth login
```

*У вікні браузера обери новий поштовий акаунт Google з наявними кредитами.*

### Крок 2. Запусти автоматичний світчер

Передай нову пошту та Project ID:

```bash
./scripts/switch_gcp_account.sh new_email@gmail.com new-project-id
```

> 💡 **Порада**: Якщо ти вже вибрав активний проект через `gcloud config set project new-project-id`, достатньо просто запустити скрипт без параметрів:
>
> ```bash
> ./scripts/switch_gcp_account.sh
> ```

---

## 🤖 Що скрипт робить автоматично (Для Агентів)

При виконанні `./scripts/switch_gcp_account.sh` система робить наступні кроки без людського втручання:

1. **GCloud CLI Context**: Встановлює `core/account` та `core/project`.
2. **API Activation**: Вмикає `aiplatform.googleapis.com`, `generativelanguage.googleapis.com` та `serviceusage.googleapis.com` у новому проекті.
3. **ADC Credentials Sync**: Оновлює `quota_project_id` в `~/.config/gcloud/application_default_credentials.json`.
4. **Environment Sync**: Оновлює `GOOGLE_CLOUD_PROJECT` в `DNK_HUB/.env` та `~/.hermes/.env`.
5. **Config YAML Sync**: Оновлює провайдер на `google-vertex` в `~/.hermes/config.yaml` та `herich_librarian/config.yaml`.
6. **Token Generation**: Генерує свіжий OAuth2 токен `ya29...` в `~/.hermes/vertex_token.txt` та `~/.config/gcloud/gerych_active_token.txt`.
7. **Cron Sync**: Фоновий crontab-процес (щогодини) підхоплює новий проект для безперервного поновлення токенів при тривалих паузах.

---

## 🧪 Верифікація успішності переходу

Для перевірки активного акаунта та проекту після ротації:

```bash
./scripts/refresh_gerych_token.sh
```

Або запустіть Герича:

```bash
./scripts/gerych.sh
```

Якщо у консолі відобразиться:
`[GCP] OAuth2 token injected for Vertex AI (account: ..., project: ...)`
— ротацію завершено успішно, Герич працює з новими кредитами! 💎🚀
