# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/DNK_HUB_COMPREHENSIVE_AUDIT_2026_09_02.md"
# purpose: "Comprehensive Technical and Security Audit of DNK_HUB Monorepo, Invariant Deviations, and Remediation Blueprint."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych Prime (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 🛡️ Комплексний технічний аудит монорепозиторію DNK_HUB
**Дата аудиту:** 2 вересня 2026 року  
**Аудитор:** Gerych (Hermes Prime), Chief Builder & Swarm Manager  
**Об'єкт аудиту:** Монорепозиторій `DNK_HUB` (гілка `feature/dnk-studio-arch-001`)  
**Цільовий стандарт:** DNK OS Unified Architecture & Zero-Waste Protocol v4.3.0  

---

## 📊 1. Executive Summary & Аудиторська матриця

У ході глибокого аудиту монорепозиторію було задіяно набір внутрішніх інструментів перевірки (`scripts/system/full_directory_audit.py`, `scripts/check_path_hygiene.py`, `scripts/check_license_policy.py`, `scripts/system/secret_scanner.py`, `scripts/verify_all.sh`), проведено інспекцію робочого дерева git, а також протестовано підсистему досліджень `services/dnk_git_research`.

### Підсумковий скоринг стану системи:

| Категорія | Статус | Оцінка | Критичні зауваження |
|:---|:---:|:---:|:---|
| **Безпека та секрети (Secrets)** | 🔴 КРИТИЧНО | **45 / 100** | Виявлено незамаскований активний GitHub PAT (`gho_...`) у відкритому конфігураційному файлі. |
| **Чистота Git (Working Tree Hygiene)** | 🟠 ПОТРЕБУЄ УВАГИ | **60 / 100** | 688 модифікованих файлів, 90 невідслідковуваних файлів/каталогів. |
31|| **Гігієна шляхів (Path Hygiene & Two-Tier)** | 🟡 ЗАДОВІЛЬНО | **75 / 100** | Зафіксовано застарілі абсолютні шляхи (`<ROOT>/DNK OS`) та legacy-згадки. |
| **Стандартизація коду (MRH Headers)** | 🟡 ЗАДОВІЛЬНО | **58.9%** | 1672 файли з 2836 відповідають стандарту `DNK-STD-0075`. |
| **Тестові ворота (Quality Gate & CI)** | 🟢 ДОБРЕ | **85 / 100** | Базові тести проходять (100% Green), проте 5 складних інтеграційних сьютів виключено через відсутність pgvector. |
| **SOTA Дослідження (`dnk_git_research`)** | 🟢 ВІДМІННО | **95 / 100** | Двигун працює штатно, підтримує 2-Track ліцензування та генерацію специфікацій. |

---

## 🚨 2. P0: Критичні проблеми безпеки (Security & Secret Leaks)

### 2.1. Відкритий персональний токен GitHub (GitHub Personal Access Token)
- **Локація:** `core/orchestrator/agents/gerych_prime/config.yaml`, рядок 450
- **Зміст:**
  ```yaml
  GITHUB_PERSONAL_ACCESS_TOKEN: gho_[REDACTED]
  ```
- **Ризик:** Повний компромат доступу до приватних репозиторіїв GitHub, ризик витоку коду при коміті конфігурації у віддалений репозиторій.
- **Невідповідність:** Порушує інваріант безпеки `DNK OS Secret Hygiene` та `security-incident-and-secret-hygiene`.
- **Рекомендація:**
  1. **Негайно відкликати (Revoke / Rotate)** даний токен у налаштуваннях облікового запису GitHub.
  2. Замінити пряме значення в `config.yaml` на підстановку змінної середовища:
     ```yaml
     GITHUB_PERSONAL_ACCESS_TOKEN: ${GITHUB_TOKEN}
     ```
  3. Додати `core/orchestrator/agents/*/config.yaml` до правил перевірки `secret_scanner.py` або винести чутливі параметри в `.env` (який уже є в `.gitignore`).

---

## ⚠️ 3. P1: Стан робочого дерева Git та дрифт кодової бази

### 3.1. Масштабний дрифт незафіксованих змін (Working Tree Drift)
- **Поточний стан:** 688 модифікованих файлів (`M`) та 90 невідслідковуваних сутностей (`??`).
- **Складові незафіксованих змін:**
  1. **Невідслідковуваний новий функціонал:**
     - `services/dnk_git_research/cli.py`
     - `services/dnk_git_research/src/git_researcher.py`
  2. **Службові артефакти та кеші:**
     - `apps/api/visual_shell_db.json`, тимчасові файли SQLite та сесійні логи Hermes.
     - `.tmp/`, файли розширення редактора, дампи налагодження.
  3. **Масові правки конфігурацій агентів:**
     - Зміна моделі на `gemini-3.8-flash` та оновлення параметрів `reasoning_effort: high` у `core/orchestrator/agents/*/config.yaml`.
- **Ризик:** Втрата контексту змін, конфлікти при злитті гілок (merge conflicts), ризик випадкового коміту тимчасових БД.
- **Рекомендація:**
  1. Оновити `.gitignore`, внісши `apps/api/visual_shell_db.json`, `*.db`, `*.sqlite`, `.tmp/`.
  2. Зробити атомарні тематичні коміти:
     - `feat(git-research): add SOTA repository research CLI and analyzer`
     - `chore(agents): synchronize gemini-3.8-flash model configurations`
     - `fix(security): sanitize hardcoded tokens and update config schemas`

---

## 🏛️ 4. P1: Архітектурні інваріанти та Two-Tier гігієна шляхів

### 4.1. Хардкод абсолютних шляхів до неіснуючих директорій
- **Локація:** `core/hermes_agent/check_mrh.py`, рядок 7:
  ```python
  root_dir = "$DNK_HUB_ROOT/DNK OS"
  ```
- **Проблема:**
  - Директорія `DNK OS` була успішно ліквідована під час консолідації репозиторію в корінь `DNK_HUB` SSOT.
  - Жорсткий абсолютний шлях порушує інваріант **Relative Paths ONLY** (`AGENTS.md`, розділ 3).
- **Рекомендація:**
  - Переписати `check_mrh.py` для динамічного визначення кореня через відносний шлях:
    ```python
    import pathlib
    root_dir = pathlib.Path(__file__).resolve().parents[2]
    ```

### 4.2. Залишкові згадки legacy-структури `DNKOS_MVP`
- **Локація:** `core/hermes_agent/tools/dnk_*_tool.py`, документаційні файли.
- **Проблема:** Змінні на зразок `DNKOS_MVP_PATH = HUB_ROOT` або посилання у коментарях на вкладені підмодулі створюють плутанину для агентів рою.
- **Рекомендація:** Виконати фінальну санацію коментарів та змінних через `scripts/system/sanitize_dnkos_mvp_references.py`.

---

## 📋 5. P2: Стандартизація коду та Machine-Readable Headers (MRH)

### 5.1. Покриття заголовками `DNK-STD-0075`
- **Поточний показник:** **58.96%** (1672 валідних файлів із 2836).
- **Найбільш проблемні зони:**
  - Нові утиліти та скрипти в `services/dnk_git_research/`
  - Допоміжні компоненти `apps/web/components/`
  - Нові тестові модулі `tests/verification/`
- **Рекомендація:**
  - Запустити системний автоматичний інжектор заголовків:
    ```bash
    python3 scripts/system/ensure_dnk_tui_integrity.py
    ```
  - Включити обов'язкову перевірку MRH у pre-commit hook (`scripts/system/auto_precommit_guard.py`).

---

## 🧪 6. P2: Тестові ворота та інтеграційні тести (Verification Gate)

### 6.1. Придушення (Suppress) тестів у `scripts/verify_all.sh`
- **Локація:** `scripts/verify_all.sh`, рядок 89:
  ```bash
  -k "not test_timeline and not test_security_gate and not test_knowledge_base_rag and not test_improvement_loop and not test_multi_agent_collaboration"
  ```
- **Причина придушення:**
  - `tests/verification/test_security_gate.py` вимагає активного підключення до PostgreSQL із встановленим розширенням `pgvector` (`extension "vector" is not available`).
  - При запуску в локальному оточенні без запущеного `docker compose up postgres` тести падають із помилкою `FeatureNotSupportedError`.
- **Рекомендація:**
  1. Додати у фікстуру `db_pool` перевірку наявності розширення `vector` перед накатуванням міграцій:
     ```python
     has_vector = await conn.fetchval("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
     if not has_vector:
         pytest.skip("PostgreSQL extension 'vector' (pgvector) is not available locally")
     ```
  2. Це дозволить тестам елегантно пропускатися (`skip`), а не призводити до падіння сьютів, що дасть змогу прибрати прапорець виключення в `verify_all.sh`.

---

## 🔬 7. Оцінка підсистеми `services/dnk_git_research`

### 7.1. Функціональна готовність
Модуль повністю реалізує конвеєр SOTA Repository Assimilation Pipeline (`core/dna_assimilation.py`):
- **Пошук репозиторіїв (CLI & API):** Працює через GitHub REST API із підтримкою фільтрації за зірками, темами та мовами.
- **Аудит ліцензій (License Audit):**
  - **Track 1 (Permissive: MIT, Apache-2.0, BSD):** Дозволяє пряме запозичення коду та компонентів.
  - **Track 2 (Copyleft: GPL, AGPL):** Блокує пряме копіювання, формує clean-room архітектурну специфікацію для реверс-інжинірингу.
- **Генератор специфікацій асиміляції:** Автоматично створює JSON-структуру з оцінкою ризиків та рекомендованим рівнем адаптації (R1 Research -> R3 Swarm Skill).

### 7.2. Виявлені недоліки модуля:
1. Файли `cli.py` та `src/git_researcher.py` є невідслідковуваними в git.
2. Відсутні юніт-тести для `services/dnk_git_research` у каталозі `tests/`.
3. Необхідно додати валідацію лімітів запитів GitHub API (`RateLimitError` при вичерпанні 60 req/hr без токена).

---

## 🛠️ 8. Покроковий план виправлення (Remediation Action Plan)

### Крок 1. Невідкладні заходи безпеки (Immediate - 15 хв)
```bash
# 1. Замінити відкритий токен у конфігураціях агентів на змінну оточення
sed -i '' 's/GITHUB_PERSONAL_ACCESS_TOKEN: gho_.*/GITHUB_PERSONAL_ACCESS_TOKEN: ${GITHUB_TOKEN}/g' core/orchestrator/agents/*/config.yaml

# 2. Перевірити відсутність витоків токенів
python3 scripts/system/secret_scanner.py
```

### Крок 2. Очищення робочого дерева Git та фіксація коду (30 хв)
```bash
# 1. Затрекати та зафіксувати двигун git research
git add services/dnk_git_research/
git commit -m "feat(git-research): integrate SOTA repository research engine and CLI"

# 2. Оновити .gitignore для тимчасових баз та кешів
echo "apps/api/visual_shell_db.json" >> .gitignore
echo "*.tmp" >> .gitignore
git add .gitignore
git commit -m "chore(git): ignore transient local DBs and temp files"
```

### Крок 3. Виправлення гігієни шляхів (Path Hygiene - 15 хв)
```bash
# Виправити check_mrh.py
sed -i '' 's|root_dir = "$DNK_HUB_ROOT/DNK OS"|root_dir = str(pathlib.Path(__file__).resolve().parents[2])|g' core/hermes_agent/check_mrh.py
```

### Крок 4. Нормалізація фікстур тестів безпеки (20 хв)
- Оновити `tests/verification/test_security_gate.py`, додавши витончений пропуск (`pytest.skip`) у разі відсутності `pgvector` у локальній PostgreSQL.
- Повернути сьюти у `scripts/verify_all.sh`.

### Крок 5. Масова інжекція MRH-заголовків (20 хв)
```bash
python3 scripts/system/ensure_dnk_tui_integrity.py
```

### Крок 6. Фінальна верифікація Quality Gate
```bash
bash scripts/verify_all.sh
```

---
*Звіт сформовано та завірено Gerych Prime в рамках протоколу DNK OS Quality Gate.*
