# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/standards/DNK-SEC-009_archify_execution_sandbox.md"
# purpose: "Security Standard & Sandboxing Policies for Archify Diagram Compilation."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-ARCHIFY-ASSIMILATION-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# DNK-SEC-009: Стандарт безпеки компілятора та пісочниці Archify

## 1. Захист від ін'єкцій та XSS
- **Вхідні дані (JSON IR)**: Усі рядкові поля (назви вузлів, підписи ребер, нотатки) проходять екранування в процесі рендерингу SVG/HTML.
- **Відсутність небезпечного `eval`**: Код компілятора не виконує динамічного JavaScript з вхідних файлів.
- **Self-Contained Content Security Policy**: Згенеровані HTML файли не вимагають зовнішніх дозволів `connect-src` або завантаження віддалених скриптів.

## 2. Ізоляція виконання Subprocess
- Виклик `node packages/archify/bin/archify.mjs` обмежується виключно читанням тимчасового файлу JSON та записом у вказаний цільовий шлях.
- Використовуються детерміновані таймаути (до 10 секунд на компіляцію) для запобігання безкінечним циклам.
- Тимчасові файли гарантовано видаляються у блоці `finally`.

## 3. Відповідність Zero-Waste & MRH інваріантам
- Усі генеровані файли звітності та діаграми використовують відносні шляхи.
- Жодні конфіденційні ключі, токени або реквізити не потрапляють у діаграми архітектури (всі значення маскуються через `[REDACTED]`).
