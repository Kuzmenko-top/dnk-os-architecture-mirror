# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/GERYCH_CORES_AND_KERNELS_STATUS.md"
# purpose: "Comprehensive overview of Gerych active runtime core and all existing kernels/engines in the DNK OS ecosystem."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧠 Архітектура Ядер Gerych та Системні Двигуни DNK OS

## 1. Активне Робоче Ядро Gerych (Поточний Стан)

У поточному сеансі та конфігурації Gerych функціонує на базі трьох інтегрованих рівнів:

1. **Модельне Ядро (AI Intelligence Kernel)**:
   - **Активна модель**: `gemini-3.8-flash`
   - **Провайдер**: Google Cloud Vertex AI (`vertex`)
   - **Регіон**: `global`
   - **Автентифікація**: OAuth2 ADC токен (`ya29...`) через автоматичний інжектор `scripts/system/gerych.sh` (проєкт: `project-930a8ed3-3e40-4f43-9d4`).
   - **Reasoning Effort**: `high`
   - **Контекстне вікно**: до 1,000,000 токенів.

2. **Резервні Ядра Відмовостійкості (Fallback Kernels)**:
   - `gemini-3.5-flash` (Vertex AI, 1M context)
   - `gemini-3.5-flash-lite` (Vertex AI, 1M context)
   - Зовнішні інтеграції: NVIDIA NIM (`nvidia`), OpenRouter (`openrouter`).

3. **Агентний Рантайм (Agent Runtime Core)**:
   - **Двигун**: `Hermes Agent` v2.1.0 (`core/hermes_agent`)
   - **Активний профіль**: `gerych_prime` (`core/orchestrator/agents/gerych_prime`)
   - **Процесний наглядач**: `Process Guard` (`scripts/system/process_guard.py`) з блокуванням подвійного запуску та single-instance locks.

---

## 2. Системні Ядра та Двигуни в DNK OS (`core/`)

В архітектурі DNK OS розгорнуто єдине об'єднане ядро `FastMCPKernel` та спеціалізовані функціональні ядра:

### А. FastMCPKernel (`core/kernel.py`)
Головне координаційне ядро протоколу FastMCP, що об'єднує 5 ключових підсистем (V2 Core):
1. **MaksymAuthEngine** (`core/auth_engine.py`): Контроль авторизації Творця (Maksym) та збереження сесій.
2. **CanvasEngine** (`core/canvas_engine.py`): Управління просторовим полотном, графами вузлів та станом Canvas Studio.
3. **HermesRuntime** (`core/hermes_runtime.py`): Безпечне середовище виконання (dry-run, валідація, rollback).
4. **SwarmOrchestrator** (`core/swarm_orchestrator.py` / `core/swarm_engine.py`): Диспетчеризація завдань по агентах рою.
5. **AccountingEngine** (`core/accounting_engine.py`): Облік токенів, фінансових витрат та технічної телеметрії.

### Б. Спеціалізовані Ядра Системи
- **TaskEngine & TaskGraphManager** (`core/task_engine.py`, `core/orchestrator/task_graph_manager.py`): Двигун еволюційного планування TaskDNA, побудова ациклічних графів залежностей (DAG).
- **SconesMemory & SconesL3Memory** (`core/scones_memory.py`, `core/scones_l3_memory.py`): 3-рівнева когнітивна пам'ять (L1 швидкий контекст, L2 доменні правила, L3 глибокі векторизовані знання).
- **DNAAssimilationEngine** (`core/dna_assimilation.py`): 5-рівневий конвеєр засвоєння репозиторіїв (Track 1 Permissive / Track 2 Clean-room).
- **ErrorDistillationEngine** (`core/error_distillation/`): Двигун дистиляції та самовідновлення після збоїв без вгадувань.
- **PatternSynthesizer** (`core/pattern_synthesizer.py`): Синтез архітектурних шаблонів та компонентів.
- **VisualContextEngine** (`core/visual_context.py`): Обробка просторових UI/UX контекстів.

---

## 3. Ядра Агентів Рою (Swarm Agent Profiles в `core/orchestrator/agents/`)

У системі налаштовано 14 ізольованих агентних профілів:

1. **Координаційні та Знаннєві Ядра**:
   - `gerych_prime`: Головний будівничий та менеджер рою (Chief Builder & Swarm Manager).
   - `herich_librarian`: Бібліотекар бази знань, хранитель SCONES та протоколів.

2. **Інженерні та Виробничі Воркери**:
   - `gerych_builder`: Розробка фронтенду, компонентів UI та монолітного коду.
   - `gerych_researcher`: Глибинний R&D, аналіз чужих кодових баз, AST-сканування.
   - `gerych_auditor`: Аудит безпеки, змагальний огляд (Adversarial Review) та контроль воріт якості (`verify_all.sh`).
   - `dnk_dev_fullstack`: Генерація FastAPI ендпоінтів, Pydantic схем, SQLAlchemy моделей.
   - `dnk_shopify`: Спеціалізоване ядро Shopify (Liquid AST, Checkout UI extensions, Shopify Functions).
   - `dnk_video_ai_creator`: Медіа-ядро (Remotion, генерація відеокомпозицій, анімації).
   - `dnk_scones_memory`: Оператор векторних сховищ знань та рішень.
   - `dnk_security_guard`: Контроль токенів, файрвол секретів, захист ключів доступу.

3. **Бізнес- та Операційні Воркери**:
   - `dnk_analytics`: Аналітика поведінки, метрики конверсій.
   - `dnk_marketing_cmo`: Контентні стратегії та воронки.
   - `dnk_finance_cfo`: Фінансовий моніторинг та юніт-економіка.
   - `dnk_erp_supply`: Логістика, складські залишки та ERP інтеграції.
