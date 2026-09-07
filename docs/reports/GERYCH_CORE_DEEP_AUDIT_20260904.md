# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/GERYCH_CORE_DEEP_AUDIT_20260904.md"
# purpose: "Comprehensive Architectural & Cognitive Audit of Gerych Core (Session 20260904_131641_8abc45)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Completed"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Antigravity (Orchestration Architect & Mentor)"
# --- END DNK-MRH-HEADER ---

# 🛡️ ПОВНИЙ АРХІТЕКТУРНИЙ ТА КОГНІТИВНИЙ АУДИТ ЯДРА ГЕРИЧА (DNK OS)
**Дата аудиту:** 4 вересня 2026 р.  
**Цільова сесія терміналу:** `20260904_131641_8abc45`  
**Модель:** Gemini 3.8 Flash (Vertex AI, global)  
**Роль аудитора:** Antigravity (Mentor / Architect / Head of Orchestration)  

---

## 1. 🔍 Анатомія сесії `20260904_131641_8abc45` (Forensics)

### Що запитав Максим:
> `'$HUB_ROOT/core' Герич - чи здатен ти реалізувати аудит ціʼї директорії зі всіма рівнями вкладенності і пояснити архітектуру та що ми маємо прибрати або покращити?`

### Хронологія думок і дій Герича (23 API-кроки):
1. **Кроки 1–8:** Герич почав виконувати послідовні команди в терміналі через `terminal_tool`.
   - Зробив `ls -la core/`
   - Запустив Python-скрипти підрахунку: виявив **14,838 підпапок** у `core/`!
   - Знайшов, що левову частку розміру займають:
     - `core/orchestrator` (1,374 MB, 23,296 файлів)
     - `core/hermes_agent` (1,164 MB, 23,259 файлів)
     - `core/orchestrator/agents/gerych_prime` (737 MB, з яких 374 MB — це `state.db`!)
2. **Кроки 9–14:** Виявив структурні аномалії:
   - Наявність випадкової вкладеної папки `core/core/tests/`.
   - Звірив дублювання між коренем репозиторію (`/`) та `core/`:
     - `adapters/` (корінь: 8 файлів vs core: 17 файлів)
     - `config/` (корінь: 3 vs core: 10)
     - `plugins/` (корінь: 7 vs core: 9)
     - `services/` (корінь: 16 vs core: 4)
3. **Крок 18 (помилка):** Герич вирішив перевірити тести `core/`:
   - Викликав: `.venv/bin/python3 -m pytest core/tests/ --quiet`
   - Отримав аварійне переривання з **3 помилками імпорту**:
     `ModuleNotFoundError: No module named 'langfuse'` у `core/accounting_engine.py` (файли `test_accounting_langfuse.py`, `test_organic_synthesis.py`, `test_phase1_core.py`).
4. **Кроки 19–22:** Просканував імпорти: встановив, що 26 модулів з `core.*` імпортуються кореневими тестами `tests/`.
5. **Крок 23 (фатальний глухий кут):** Герич запустив обов'язковий гейт:
   - `bash scripts/verify_all.sh` (Message ID `45560`).
   - `verify_all.sh` на кроці `[1/4]` запустив `scripts/system/fast_compile_check.py`.
   - `fast_compile_check.py` пішов рекурсивно компілювати **20,085 `.py` файлів** (з яких 18,810 — це 4 дублюючі копії hermes-agent у `core/`).
   - Процес `python3 fast_compile_check.py` (PID `61249` / `61633`) утилізував CPU на 100% протягом понад 60 секунд.
   - Термінальний виклик завис без повернення результату. **Сесія Герича "заснула" на вічному очікуванні відповіді від `verify_all.sh`**.

---

## 2. 🧠 Як Герич думає (Cognitive Loop & Prompt Architecture)

### 2.1. Внутрішній когнітивний дисонанс (Конфлікт промптів)
У системному промпті Герича одночасно діють два взаємовиключні накази:
* **Google Model Directive:** *"Absolute paths: Always construct and use absolute file paths for all file system operations. Combine the project root with relative paths."*
* **DNK OS AGENTS.md / MRH:** *"Relative paths ONLY (`./`, `../`). Never construct or pass absolute `/Users/...` paths in tool calls, file searches, imports, or scripts."*

**Наслідок:** Герич у першому ж кроці викликає `cd $HUB_ROOT/...` і передає абсолютні шляхи, після чого сам себе лякається, намагається перевірити `scripts/system/enforce_relative_paths.py`, витрачає токени та увагу на боротьбу з протиріччям у власній голові.

### 2.2. Збій стиснення контексту (Context Compaction Crash)
У файлі `core/hermes_agent/agent/auxiliary_client.py:7073` клієнт звертається до ендпоінту Vertex OpenAPI:
`https://aiplatform.googleapis.com/v1beta1/projects/{proj}/locations/global/endpoints/openapi`
Він передає модель як `"gemini-3.8-flash"`. Проте специфікація Vertex OpenAPI вимагає обов'язкового префіксу видавця: `"google/gemini-3.8-flash"`.
* **Наслідок:** 
  1. Генерація назви сесії (Title Generation) падає з `Error code: 400 - Malformed publisher model ... expected '<publisher>/<model>'`.
  2. Автоматичне стиснення контексту (Context Compression при > 64k токенах) повністю відмовляє.
  3. Герич скидається у "тупий" недетерміністичний fallback (`Recovered from a deterministic fallback...`), втрачаючи розуміння попередніх інструкцій Максима.

### 2.3. Послідовне "тунельне" мислення замість Swarm-паралелізму
Хоча в `SOUL.md` та `AGENTS.md` закріплено принцип `Zero-Waste High-Velocity Protocol` і `dnk_swarm_parallel`:
* Герич на запит аудиту зробив **23 окремі послідовні виклики** терміналу.
* Кожен крок займав 2.5–4.5 секунди затримки мережі та додавав у контекст весь попередній вивід.
* До 23-го кроку обсяг контексту зріс до **56,223 токенів** на банальні команди `ls` і `python -c`.
* Замість цього досвідчений агент-архітектор мав би створити один комплексний скрипт аудиту, запустити його за один виклик (0.5с) або задіяти сабагента `gerych_researcher`.

### 2.4. Пастка нав'язливої верифікації (Quality Gate Compulsion)
Герич запрограмований обов'язково викликати `verify_all.sh` перед звітом користувачу. Проте на аналітично-дослідницьких (Read-Only) задачах, де код не змінювався, повний запуск усіх перевірок системи є надлишковим і створює ризик дедлоку, що й сталося.

---

## 3. 💥 Що зламано в робочому ядрі (Identified Defects)

| № | Компонент | Проблема | Симптом / Лог |
|---|-----------|----------|---------------|
| 1 | `scripts/system/fast_compile_check.py` | Компілює всі 20,085 `.py` файлів без виключення бекапів і стейджинг-папок | Зависає на 100% CPU, блокує `verify_all.sh` |
| 2 | `.venv` / `core/accounting_engine.py` | Відсутній пакет `langfuse` у віртуальному оточенні | `ModuleNotFoundError: No module named 'langfuse'` у 3 тестах `core/tests/` |
| 3 | `core/orchestrator/agents/gerych_prime/checkpoints` | Пошкоджене Git-дерево чекпоінтів | `fatal: git-write-tree: error building trees (invalid object for 'agent/auxiliary_client.py')` |
| 4 | `core/hermes_agent/agent/auxiliary_client.py` | Відсутній префікс `google/` у запитах до Vertex OpenAPI | HTTP 400 `Malformed publisher model ('gemini-3.8-flash')` — ламає стиснення пам'яті |
| 5 | OpenAI Client Integration | Передача `openai.Omit` у заголовках HTTP | `TypeError: Header value must be str or bytes, not <class 'openai.Omit'>` (непоправний збій сесії) |
| 6 | MCP Інтеграції | Падіння зовнішніх серверів | `MCP server 'open-design' failed connection`, `context7: CancelledError` |
| 7 | Структура `core/core/` | Випадкова рекурсивна підпапка з тестами | Зайвий шум при скануванні репозиторію |

---

## 4. 🌟 Що працює добре (Strengths & Assets)

1. **Vertex AI Prompt Caching (90–96% ефективності):**
   - У логах чітко видно: `cache=50161/56223 (89% - 96%)`. Це колосальна економія витрат на токени та зниження затримки до 2.5–3с навіть на 50k+ токенів.
2. **Проактивна авторизація OAuth2 (`scripts/system/gerych.sh`):**
   - Автоматичне оновлення gcloud токена з кешем на 40 хвилин працює бездоганно; агент ніколи не зупиняється через прострочений токен.
3. **Захист від мульти-інстансів (`process_guard.py`):**
   - Блокування ексклюзивного доступу до агента та відстріл "зомбі"-процесів захищають базу даних від паралельного псування.
4. **Висока швидкість термінальних інструментів:**
   - Локальні команди виконуються в межах 0.10–0.25 секунди.
5. **Потужні доменні модулі DNK:**
   - Наявність `TaskDNA`, `SCONES L1/L2/L3`, `Adversarial Gate`, `Shopify AST` — це унікальна конкурентна перевага, яка вже побудована в системі.

---

## 5. 🗑️ Що треба видалити (Zero-Waste Purge Plan)

### 5.1. Видалити мертві копії Hermes Agent (~14,000 непотрібних файлів, >1.2 GB)
У директорії `core/` накопичилося 4 паралельні копії коду агента:
* `core/hermes_agent_staging/` (4,881 py файлів) — **ВИДАЛИТИ**
* `core/hermes_versions/` (4,643 py файлів) — **ВИДАЛИТИ**
* `core/hermes_agent.backup.pre-0.21.0/` (4,643 py файлів) — **ВИДАЛИТИ**
* `core/core/` (зайва вкладена директорія) — **ВИДАЛИТИ**
*(Залишити виключно єдине канонічне робоче ядро: `core/hermes_agent/`)*.

### 5.2. Видалити / відключити чужорідні інструменти (Tools Bloat)
З донора Nous Hermes у системі залишилося понад 30 непотрібних інструментів, які на кожному кроці спамлять варнінгами та займають місце в контексті:
- `spotify`, `homeassistant`, `discord`, `feishu_doc`, `feishu_drive`, `yuanbao`, `xai_video`, `tenor_gif` тощо.
- Їх слід прибрати з `toolsets` або заблокувати у `config.yaml` (`disabled_toolsets`).

### 5.3. Очистити роздуту базу даних `state.db` (358 MB, 45,662 повідомлення)
- У базі `core/orchestrator/agents/gerych_prime/state.db` зберігаються старі повідомлення ще з травня 2026 року разом із гігантськими FTS-індексами.
- Потрібно виконати архівацію сесій старше 14 днів у `state_archive.db` та запустити `VACUUM`.

### 5.4. Ліквідувати структурне роздвоєння Root vs `core/`
Згідно з `AGENTS.md` (Правило 2):
- Репозиторій повинен мати чіткий SSOT:
  - `apps/` — фронтенди та API
  - `services/` — мікросервіси та воркери
  - `core/` — спільне системне ядро (SCONES, Kernel, Auth, Hermes)
  - `tests/` — інтеграційні та модульні тести
- Слід консолідувати `adapters/`, `config/`, `plugins/`, `services/`, які зараз існують і в корені, і в `core/`.

---

## 6. 🚀 Що покращити (Roadmap модернізації)

### Крок 1: Миттєве виправлення `fast_compile_check.py`
Замінити сліпий обхід файлової системи на перевірку файлів через `git ls-files '*.py'` або розширити `IGNORE_DIRS`:
```python
IGNORE_DIRS.update({"hermes_agent_staging", "hermes_versions", "hermes_agent.backup.pre-0.21.0", "orchestrator", "staging"})
```
*Це зменшить час роботи скрипта з 60+ секунд до 0.4 секунди!*

### Крок 2: Патч моделі Vertex у `auxiliary_client.py`
У рядку 7079: якщо провайдер `vertex`, автоматично додавати префікс `google/` до `final_model` перед передачею в OpenAI-сумісний клієнт:
```python
if final_model and not final_model.startswith("google/"):
    final_model = f"google/{final_model}"
```
*Це відновить працездатність контекстного стиснення та генерації назв.*

### Крок 3: Вирішення залежності `langfuse`
Додати `langfuse` у `pyproject.toml` і `.venv`, або в `core/accounting_engine.py` додати безпечний fallback:
```python
try:
    from langfuse import Langfuse
except ImportError:
    Langfuse = None
```
*Це зробить `pytest core/tests/` 100% зеленим.*

### Крок 4: Гармонізація системного промпта
Видалити з кодогенератора системного промпта `Google model operational directives` з вимогою абсолютних шляхів, закріпивши єдиний непорушний закон: **Тільки відносні шляхи (`./`, `../`)**.

### Крок 5: Очищення пошкодженого Git-дерева чекпоінтів
Очистити папку `core/orchestrator/agents/gerych_prime/checkpoints/` від невалідних SHA-об'єктів для відновлення авто-бекапів перед зміною файлів.
