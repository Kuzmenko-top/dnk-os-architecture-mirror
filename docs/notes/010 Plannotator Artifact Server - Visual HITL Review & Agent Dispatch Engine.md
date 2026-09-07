---
title: "010 Plannotator Artifact Server - Visual HITL Review & Agent Dispatch Engine"
tags:
  - sota-assimilation
  - visual-shell
  - canvas
  - hitl-review
  - mcp-tools
  - effect-ts
  - clean-room
date: 2026-09-05
status: Active
author: Gerych Prime & DNK-e.com Maksym
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/010 Plannotator Artifact Server - Visual HITL Review & Agent Dispatch Engine.md"
purpose: "Obsidian Knowledge Note for Plannotator Artifact Server Architecture and Integration."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "2.0.0"
updated_at: "2026-09-05"
author: "Gerych Prime & DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🎨 Plannotator Artifact Server: Visual HITL Review & Agent Dispatch Engine

## 📌 Контекст та системна роль
`plannotator/artifact-server` — це відкритий self-hosted сервер для збереження, версіонування та інтерактивного візуального рецензування артефактів (HTML, SVG, React/Vite прототипів, Markdown звітів), створених штучним інтелектом.

У екосистемі [[DNK OS MVP]] він вирішує головну проблему взаємодії між розробником-людиною ([[Maxim]]) та мультиагентним роєм ([[Gerych Swarm]]): **перехід від текстового опису правок до точного візуального пін-поінту на живому інтерфейсі**.

---

## ⚖️ Ліцензійний комплаєнс: Track 2 (AGPL-3.0-only)

Upstream-репозиторій ліцензовано під строгою копілефтною ліцензією **AGPL-3.0-only** (`GNU Affero General Public License v3.0`).

### Непорушні інваріанти архітектурної ізоляції:
1. **Заборона копіювання вихідного коду**: Жоден файл з upstream не імпортується безпосередньо в директорії `apps/web`, `apps/api`, `services/`, `core/`.
2. **Sovereign Sidecar (Мережева межа)**: Офіційний docker-контейнер запускається окремим ізольованим мікросервісом у `deploy/compose.artifact-server.yaml`. Взаємодія здійснюється суто через стандартизовані мережеві протоколи:
   - **HTTP REST**: Порт `:3100` (завантаження та перегляд артефактів).
   - **MCP Endpoint**: Порт `:3100/mcp` (Streamable HTTP / SSE протокол для агентів).
3. **Clean-Room розробка**: Наші внутрішні модулі ([[apps/web/src/components/canvas/ArtifactReviewOverlay.tsx]] та [[apps/api/routers/dnk_artifact_router.py]]) пишуться з нуля на основі відкритих специфікацій протоколу.

---

## 💎 Архітектурні компоненти та протоколи

### 1. Точна специфікація MCP-інтерфейсу (31 інструмент + 1 ресурс)
Сервер експортує 31 інструмент через механізм `registerNudgedTool` та 1 ресурс `server.registerResource`:

- **Системні можливості (1)**: `artifact_capabilities`.
- **Управління проєктами та Git-історією (7)**: `project_list`, `project_create`, `project_rename`, `project_git_history_status`, `project_git_history_estimate`, `project_set_git_history`, `artifact_history_clone_token`.
- **Керування артефактами та версіями (14)**: `artifact_list`, `artifact_get`, `artifact_open`, `artifact_version_list`, `artifact_diff`, `artifact_create_upload`, `artifact_commit_upload`, `artifact_set_visibility`, `artifact_set_tags`, `artifact_restore_version`, `artifact_delete`, `artifact_link`, `artifact_capture`, `artifact_relink`.
- **Коментарі та рецензування (8)**: `comment_list`, `comment_get`, `comment_create`, `comment_reply`, `comment_resolve`, `comment_update`, `comment_delete`, `comment_clear`.
- **Поштова скринька агента (1)**: `dispatch_inbox` (підтримує операції `list`, `claim`, `delivered`, `failed`).
- **MCP Ресурс (1)**: `artifact-version-manifest` за шаблоном `artifact://{projectId}/{artifactId}/versions/{versionId}/manifest`.

### 2. Специфікація DOM-якоря (HtmlElementAnchor)
Точна Zod-схема прив'язки пінів рецензента до верстки:

```typescript
export const htmlElementAnchorSchema = z.object({
  point: z.object({
    x: z.number().min(0).max(1), // Відносна позиція всередині елемента
    y: z.number().min(0).max(1),
  }).optional(),
  selector: z.string().min(1).max(1024), // CSS шлях: main > button:nth-child(2)
  tagName: z.string().min(1).max(64),    // BUTTON, DIV, H1
  text: z.string().max(400).optional(),  // Сніпет тексту для стійкості до правок
});
```

### 3. Двосторонній postMessage міст (`reviewProtocolVersion = 1`)
Зв'язок між Host Shell та пісочницею `<iframe>`:
- **Host ➔ Frame**:
  - `as-review-init` (передача HTML, CSS токенів, початкових анотацій)
  - `as-review-annotations` (динамічне оновлення списку пінів)
  - `as-review-theme` (синхронізація теми оформлення)
  - `as-review-annotate-mode` (активація режиму додавання коментарів)
  - `as-review-focus` (фокусування на конкретному треді)
- **Frame ➔ Host**:
  - `as-review-ready` (готовність пісочниці)
  - `as-review-submit` (відправка нового коментаря з якорем `ReviewAnchor`)
  - `as-review-select` (клік на існуючий пін)
  - `as-review-annotate-mode-request` (запит на зміну режиму курсору)
  - `as-review-unanchored` (список пінів, елементи яких не знайдено в DOM)

### 4. Механізм Tool-Result Nudges
MCP не має Push-каналів, тому сервер використовує канал реактивного кермування:
- До кожного результату звичайних інструментів автоматично додається рядок контексту (максимум 400 символів) із заголовком `— artifact server —`, якщо в черзі є `queued` задачі.
- Агент бачить це нагадування і викликає `dispatch_inbox(operation: "claim")`.

---

## 🗺️ План асиміляції у 2 етапи

### Етап 1: Sovereign Sidecar (Готово до старту)
- Підготовка `deploy/compose.artifact-server.yaml` (порт 3100, volume для SQLite/artifacts).
- Налаштування підключення MCP у конфігурації Hermes.
- Створення навички `skills/artifact-server/SKILL.md` для агентів рою.

### Етап 2: Clean-Room Canvas Synthesis
- Реалізація нативного оверлею в `apps/web/src/components/canvas/ArtifactReviewOverlay.tsx`.
- Реалізація ендпоінтів черги в `apps/api/routers/dnk_artifact_router.py`.

---

## 🔗 Пов'язані нотатки та документи
- Канонічна карта асиміляції: [[docs/tech/sota_assimilation/plannotator_artifact_server.md]]
- Загальні правила взаємодії: [[AGENTS.md]]
- Мультиагентна архітектура: [[docs/architecture/SWARM_ARCHITECTURE.md]]
