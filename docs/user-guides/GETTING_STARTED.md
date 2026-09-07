# --- DNK-MRH-HEADER ---

# mrh_id: "docs/user-guides/GETTING_STARTED.md"

# purpose: "Comprehensive Getting Started Guide & Onboarding Runbook for DNK OS"

# canonical_source: true

# alters_files: []

# triggers_tasks: []

# status: "Active"

# version: "1.0.0"

# updated_at: "2026-09-05"

# author: "DNK-e.com Maksym & Gerych"

# standard: "DNK-STD-0090"

# --- END DNK-MRH-HEADER ---

# 🚀 Посібник користувача: Швидкий старт з DNK OS

Ласкаво просимо до **DNK OS** — інтелектуальної операційної системи на базі мультиагентного рою (14 спеціалізованих агентів), інтерактивного Canvas та автономних конвеєрів розробки й електронної комерції.

---

## ⏱️ 1. Швидкий старт (5 хвилин)

Щоб почати роботу з DNK OS:

1. **Відкрийте вебінтерфейс**:
   - Перейдіть за адресою `http://localhost:3000` (або `https://app.dnk-e.com`).
   - Натисніть кнопку **"Пройти Onboarding"** або **"Розпочати роботу"** на головному екрані.

2. **Ініціалізація першого робочого простору**:
   - За замовчуванням створюється ізольований простір `ws-alpha-001`.
   - Система автоматично перевіряє статус з'єднання з бекендом FastAPI (`/health`) та WebSocket шлюзом рою.

3. **Запуск через CLI (для розробників)**:

   ```bash
   # Запуск стеку в режимі розробки
   bash scripts/dev.sh
   # Перевірка статусу системи
   bash scripts/verify_all.sh
   ```

---

## 🎨 2. Перші кроки: Створення першого Canvas

Canvas в DNK OS — це безмежне реактивне полотно для спільної роботи людей та AI-агентів.

### Крок 1: Створення полотна

1. У лівій панелі Launchpad натисніть **"+ Нове полотно"** або комбінацію `Cmd/Ctrl + N`.
2. Оберіть початковий шаблон:
   - **Blank Canvas**: Чисте полотно.
   - **Product Launch Blueprint**: Шаблон запуску бренду (Shopify + Video AI).
   - **Agent Swarm Architecture**: Шаблон архітектурного проектування.

### Крок 2: Додавання вузлів та зв'язків

- **Текстові ноди**: Подвійний клік на полі для створення замітки або промпту.
- **AI Task ноди**: Натисніть `Space`, щоб викликати командний рядок агентів.
- **З'єднання**: Потягніть конектор від однієї ноди до іншої для створення залежностей (TaskDNA DAG).

### Крок 3: Генерація результатів (AI Generation)

- Виділіть потрібну ноду та натисніть кнопку **"Generate"** (або `Cmd + Enter`).
- Спеціалізований агент (`gerych_builder`, `dnk_shopify` чи `dnk_video_ai_creator`) виконає генерацію в реальному часі.

---

## ⚡ 3. Просунуті можливості (Advanced Features)

### 3.1. Мультиагентний рій (14 Swarm Agents)

- **Gerych Prime**: Головний диспетчер і планувальник завдань.
- **Gerych Builder**: Генерація інтерфейсів, компонентів та React/Next.js коду.
- **DNK Shopify**: Інтеграція Liquid-шаблонів, каталогу продуктів та Checkout.
- **DNK Video AI Creator**: Синтез промо-відео на базі Remotion.
- **SCONES Memory Vault**: Довготривала семантична пам'ять із tenant-ізоляцією.

### 3.2. Приклади коду для інтеграції

#### Python SDK Example

```python
import asyncio
from core.orchestrator.swarm_manager import SwarmManager

async def main():
    manager = SwarmManager(workspace_id="ws-alpha-001")
    result = await manager.dispatch_task(
        agent="gerych_builder",
        task_description="Створити форму оформлення замовлення",
        payload={"framework": "react", "styling": "tailwind"}
    )
    print(f"Статус завдання: {result['status']}")
    print(f"Результат: {result['output']}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### TypeScript / JavaScript SDK Example

```typescript
import { DNKClient } from '@dnk-os/sdk';

const client = new DNKClient({
  endpoint: 'http://localhost:8000',
  workspaceId: 'ws-alpha-001'
});

async function runOnboardingDemo() {
  const session = await client.canvas.create({
    title: 'Мій перший проект',
    template: 'blank'
  });
  console.log(`Створено полотно: ${session.id}`);

  await client.swarm.dispatch({
    agent: 'gerych_builder',
    prompt: 'Створити Hero секцію для e-commerce сайту'
  });
}

runOnboardingDemo();
```

---

## 🛠️ 4. Вирішення проблем (Troubleshooting)

| Проблема | Причина | Рішення |
| ---------- | --------- | --------- |
| Помилка `Connection Refused` до бекенду | Сервер FastAPI не запущений на порту 8000 | Запустіть `./.venv/bin/uvicorn apps.api.main:app --port 8000` |
| Помилка авторизації GitHub API | Не встановлено токен `GH_TOKEN` | Експортуйте токен: `export GH_TOKEN=ghp_...` |
| Canvas не зберігає зміни | Відсутній зв'язок з WebSocket шлюзом | Перевірте статус з'єднання у правому верхньому кутку |
| LocalStorage скидає onboarding | Режим інкогніто або очищення кешу браузера | Натисніть "Пройти тур" знову або увійдіть у свій акаунт |

---

## ❓ 5. Поширені запитання (FAQ)

**П: Чи можу я використовувати DNK OS без підключення до хмари?**
В: Так! DNK OS підтримує локальні LLM (Ollama, vLLM, llama.cpp) та локальну пам'ять SCONES SQLite.

**П: Як налаштувати доступ моїх власних агентів?**
В: Використовуйте конфігурацію в `config.yaml` або скористайтеся інструментом `dnk_swarm_dispatch`.

**П: Де зберігаються створені відео та медіа?**
В: У директорії `./storage/artifacts/` вашого робочого простору.
