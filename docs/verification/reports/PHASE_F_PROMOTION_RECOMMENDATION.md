# --- DNK-MRH-HEADER ---
# mrh_id: "docs_verification_reports_phase_f_promotion_recommendation"
# purpose: "Formal Phase F Promotion Recommendation for Hermes Agent v0.21.0."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚀 Рекомендація щодо просування: Phase F — Promotion Recommendation

```yaml
promotion_recommendation:
  candidate: hermes-agent-v0.21.0
  current_production: hermes-agent-v0.20.5
  recommendation: GO
  evidence_complete: true
  security_review: passed
  data_boundary_review: passed
  accounting_review: passed
  rollback_review: passed
  open_risks: []
  required_human_approvals:
    - production_runtime_switch
    - launcher_update
    - state_migration
    - production_mcp_enablement
```

---

## 👑 1. Архітектурне Рішення та Вердикт
На основі всебічного та незалежного аудиту результатів тестування у фазі канарейки (Phase E / Gate E), задокументованого у [Звіті Canary Review](./PHASE_F_CANARY_REVIEW.md), виноситься архітектурний вердикт **GO** (Дозволено до просування). 

Кандидат **Hermes Agent v0.21.0** повністю готовий до промислової експлуатації (Production promotion), оскільки всі критичні ризики безпеки, ізоляції секретів та цілісності даних були успішно зняті та верифіковані програмним шляхом із збереженням 100% ізоляції діючого середовища (Production v0.20.5).

---

## 🛡️ 2. Результати Спеціалізованих Перевірок (Gate Status)

1. **Security Review (passed):**
   - Усі спроби несанкціонованого читання системних та користувацьких секретів (`.env`, приватні ключі) успішно заблоковані на рівні механізмів безпеки ядра (`file_safety.py`).
   - Будь-яке випадкове виведення токенів у лог-файли, stdout/stderr або шину подій автоматично маскується за допомогою оптимізованого алгоритму регулярних виразів.

2. **Data Boundary Review (passed):**
   - Підтверджено 100% відсутність витоку сирих токенів (raw secrets) у модельний контекст (LLM input payload), логи CLI, шину подій, бази даних сесій чи контрольні точки відновлення.
   - Межа Shopify верифікована на рівні Policy Engine: спроба виконати деструктивну мутацію для продакшн-магазину `dnk-e.myshopify.com` блокується без відправки вихідних мережевих HTTP-запитів.

3. **Accounting Review (passed):**
   - Математичний інваріант обліку токенів виконується без жодних похибок.
   - Система повторних спроб (retries) працює ізольовано, записуючи помилки як окремі спроби без подвійного нарахування успішних подій, що усуває фінансові ризики перевитрат.

4. **Rollback Review (passed):**
   - Екстрений відкат з версії v0.21.0 до v0.20.5 займає **0.208 секунди** (відповідно до SLA <= 30.0s).
   - Підтверджено збереження всіх аудиторських та фінансових файлів канарейки після процедури відкату.

---

## 📋 3. План Виконання Умов Просування (Promotion Checklist & Transition Plan)

Згідно з інструкцією Максима, перехід версії v0.21.0 у промислову експлуатацію дозволяється **виключно після окремого покрокового підтвердження** наступних умов:

| Статус | Умова просування | Метод перевірки / Опис процедури |
| :---: | :--- | :--- |
| [ ] | **Security review підписано** | Клієнтський підпис Максима на фінальному релізі. |
| [ ] | **Secret boundary доведена до raw-context рівня** | Верифіковано тестом `verify_phase_f_canary_review.py` (0 витоків у 5 sinks). |
| [ ] | **Shopify production request path перевірено** | Доведено повне блокування на рівні Gateway, 0 мережевих запитів до prod. |
| [ ] | **State migration має backup і rollback** | Створення резервної копії бази даних сесій: `cp ~/.hermes/state.db ~/.hermes/state.db.bak_v0.20.5` перед запуском міграції. |
| [ ] | **Launcher switch має atomic procedure** | Атомарне оновлення символічного посилання: `ln -sf ~/.hermes_staging/bin/hermes ~/.local/bin/hermes`. |
| [ ] | **Production MCP profile перевірений** | Валідація схеми `core/registry/runtime_registry.yaml` на відповідність діючим MCP серверам. |
| [ ] | **Cron migration має deduplication plan** | Запобігання дублюванню завдань завдяки зчитуванню останньої мітки часу виконання (continuity checkpoint) з нової бази даних. |
| [ ] | **Memory migration не змінює L3 без review** | Довгострокова пам'ять воркерів мігрує в режимі Read-Only до моменту першого успішного сеансу. |
| [ ] | **Accounting baseline збережено** | Збереження історичного реєстру токенів v0.20.5 у `docs/audit/baseline_accounting.json`. |
| [ ] | **Maintenance window визначено** | Вікно обслуговування тривалістю менше 1 секунди (завдяки атомарності символічного посилання). |
| [ ] | **Rollback drill повторено** | Повторна перевірка SLA відкату безпосередньо перед перемиканням. |
| [ ] | **Максим окремо підтвердив production promotion** | Фінальний запуск процедури перемикання після отримання згоди. |

---

## 👤 4. Обов'язкові Людські Затвердження (Required Human Approvals)

Для запуску промислового релізу Максиму необхідно підтвердити наступні операції:
1. `production_runtime_switch` — дозвіл на зміну робочої директорії та запуск v0.21.0 як головного процесу.
2. `launcher_update` — дозвіл на зміну системного бінарника/лаунчера `~/.local/bin/hermes`.
3. `state_migration` — дозвіл на оновлення схеми та даних існуючих сесій.
4. `production_mcp_enablement` — активація промислового профілю інтеграцій воркерів.

---
**РЕКОМЕНДАЦІЯ АРХІТЕКТОРА:** 
Рекомендується підписати дану рекомендацію зі статусом **GO**, затвердити План переходу (Transition Plan) та очікувати зручного вікна обслуговування для фінального перемикання лаунчера.

*Документ створено автоматично на основі PHASE_F_EVIDENCE_MANIFEST.json.*
*Локальний підпис рекомендації: 715b7a21d047906ade7e3e420200457c6fca40bb6f167daa2fdc42e39fa0972e*
