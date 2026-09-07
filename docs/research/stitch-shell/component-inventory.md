# --- DNK-MRH-HEADER ---
# mrh_id: "component-inventory.md"
# purpose: " паспорт кожного Stitch-компонента з описом реквізитів, стану та обмежень."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# Component Inventory: Stitch Shell Baseline

Цей документ містить детальний паспорт для кожного з 5 базових Stitch-компонентів, які утворюють каркас дизайну.

---

## 1. StitchCanvasContainer.tsx
- **Purpose**: Головне нескінченне полотно (Infinite Canvas), що управляє рендерингом сітки, перетягуванням (pan), масштабуванням (zoom), гарячими клавішами, показом сповіщень (toasts) та містить інші плаваючі інтерфейси.
- **Props**: None (є основним контейнером сторінки).
- **State**:
  - `scale` (number): поточний масштаб (0.1 - 3.0).
  - `pan` ({x, y}): поточний зсув координат полотна.
  - `isDragging` (boolean): прапорець перетягування.
  - `toasts` (Array): список активних сповіщень.
  - `activeTool` (string): активний інструмент з панелі інструментів.
  - `canvasState` (QualityState): стан полотна.
  - `artifactState` (QualityState): стан прев'ю артефакту (empty, loading, success).
- **Events**:
  - `onWheel`: масштабування коліщатком миші.
  - `onMouseDown` / `onMouseMove` / `onMouseUp`: перетягування сітки полотна.
  - `onKeyDown`: гарячі клавіші (Escape - скидання, S/H/D/M/F - швидка зміна інструменту).
- **Side Effects**:
  - `useEffect`: підписка на `keydown` глобальні події вікна.
  - `useEffect`: автоматичне видалення старого toast-повідомлення через 3.5 секунди.
- **API Calls**: None безпосередньо (опосередковано через дочірні виклики команд).
- **External Dependencies**: `React`, `lucide-react` (у планах), `./StitchTopHeader`, `./StitchLeftAgentPanel`, `./StitchRightToolbar`, `./StitchPromptDock`.
- **Missing Tests**: Емуляція складних жестів тачпаду (pinch-to-zoom).
- **Known Limitations**: Grid зсувається тільки візуально через CSS `transform`, немає реального віртуалізованого рендерингу для великої кількості нод.

---

## 2. StitchTopHeader.tsx
- **Purpose**: Верхня панель управління з відображенням назви системи, відсотком масштабу полотна, швидким скиданням та кнопками експорту/поділитися.
- **Props**:
  - `scale` (number): поточний масштаб.
  - `setScale` (function): функція оновлення масштабу.
  - `setPan` (function): функція скидання зсуву.
  - `onNotification` (function): callback для надсилання toasts.
- **State**:
  - `exportState` (QualityState): стан процесу експорту.
  - `exportMessage` (string): повідомлення про результат експорту.
- **Events**:
  - `onClick` (Reset): скидання зсуву та масштабу до 100%.
  - `onClick` (Export Code): виклик команди експорту коду `canvas.export`.
  - `onClick` (Share): заблокована кнопка ділення проектом.
- **Side Effects**: None.
- **API Calls**: Виклик `commandDispatcher.dispatch('canvas.export', { format: 'code' })`.
- **External Dependencies**: `React`, `../../features/design/design.commands`.
- **Missing Tests**: Тест на натискання кнопки Share в стані offline.
- **Known Limitations**: Кнопка Share є неактивною.

---

## 3. StitchLeftAgentPanel.tsx
- **Purpose**: Панель логів (консолі) Гєрича та інших агентів. Дозволяє бачити хід генерації та перемикати якісні стани для симуляції.
- **Props**:
  - `onNotification` (function): callback для надсилання toasts.
- **State**:
  - `panelState` (QualityState): поточний стан відображення панелі (success, loading, empty, error, offline, disabled).
  - `logs` (Array<string>): масив рядків журналювання.
- **Events**:
  - `onClick` (State Toggle): перемикання станів відображення для демонстрації та тестування.
- **Side Effects**: None.
- **API Calls**: None (базується на локальних моках подій).
- **External Dependencies**: `React`, `../../features/design/design.types`.
- **Missing Tests**: Оновлення логів у реальному часі через EventSource.
- **Known Limitations**: Логи є статичними і не підключені до живого SSE потоку безпосередньо.

---

## 4. StitchRightToolbar.tsx
- **Purpose**: Права панель швидкого вибору поточного інструменту на полотні (Select, Hand, Draw, Media, Search).
- **Props**:
  - `activeTool` (string): поточний активний інструмент.
  - `onToolSelect` (function): callback зміни активного інструменту.
  - `onNotification` (function): callback надсилання toasts.
- **State**: None (повністю контрольований компонент).
- **Events**:
  - `onClick` (Tool): зміна активного інструменту та відправка toast.
- **Side Effects**: None.
- **API Calls**: None.
- **External Dependencies**: `React`, `../../features/design/design.types`.
- **Missing Tests**: Перевірка стилів ховеру та тултіпів.
- **Known Limitations**: Кнопки інструментів відображають лише першу літеру назви замість SVG-іконок.

---

## 5. StitchPromptDock.tsx
- **Purpose**: Нижня консоль введення промптів користувачем з підтримкою швидких кнопок (pills). Відправляє команди в шину `design.commands`.
- **Props**:
  - `onNotification` (function): callback надсилання toasts.
  - `onCommandStatus` (function): callback для синхронізації результатів команди з іншими частинами інтерфейсу.
- **State**:
  - `prompt` (string): поточний текст у полі введення.
  - `dockState` (QualityState): стан дока.
  - `activeCommandResult` (CommandStatus | null): результат виконання останньої відправленої команди.
- **Events**:
  - `onChange` (Input): введення тексту промпту.
  - `onKeyDown` (Enter): запуск команди на виконання.
  - `onClick` (Run): запуск команди на виконання.
  - `onClick` (Pills): миттєва відправка відповідної команди.
- **Side Effects**:
  - `setTimeout`: імітує мережеву затримку в 400мс для реалістичного фідбеку.
- **API Calls**: Викликає `commandDispatcher.dispatch(...)`.
- **External Dependencies**: `React`, `../../features/design/design.commands`.
- **Missing Tests**: Автоматичний фокус поля при завантаженні сторінки.
- **Known Limitations**: Введення промптів не зберігається в персистентній історії сесії.
