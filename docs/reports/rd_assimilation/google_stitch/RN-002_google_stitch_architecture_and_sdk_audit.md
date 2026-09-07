# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/google_stitch/RN-002_google_stitch_architecture_and_sdk_audit.md"
# purpose: "Comprehensive Research Digest & Technical Reverse-Engineering Audit of Google Stitch (stitch.withgoogle.com)."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-STITCH-ASSIMILATION"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🔬 RN-002: Google Stitch Architecture, SDK & MCP Protocol Deep-Dive Audit

## 📋 1. Executive Summary & Product DNA
**Google Stitch** (`stitch.withgoogle.com`) — експериментальна AI-native платформа розробки та просторового проектирування призначена для перетворення природної мови, ескізів та URL у високовірні (high-fidelity) інтерактивні UI/UX інтерфейси, дизайн-системи та чистий фронтенд-код.

Платформа поєднує можливості мультимодальної моделі **Gemini 2.5 Pro**, відкритий протокол **Model Context Protocol (MCP)**, стандарт дизайн-токенів **DESIGN.md** та нескінченне просторове полотно (Infinite Design Canvas).

---

## 🏛️ 2. Архітектурні Шари Google Stitch

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GOOGLE STITCH PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. SPATIAL UI CANVAS: Infinite 2D Viewport / Multi-Screen DAG               │
│    - Diverge / Converge branching of UI variants                            │
│    - Device frames (Mobile / Tablet / Desktop) in sandboxed DOM iframes     │
│    - Interactive "Stitch" connections (Screen A -> Click -> Screen B)       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DESIGN INTELLIGENCE LAYER:                                               │
│    - Multi-modal Vision (Sketch / Wireframe / Screenshot ingestion)         │
│    - URL Design System Extractor (HTML/CSS computed styles to tokens)       │
│    - DESIGN.md normative YAML tokens + rationale parser                     │
│    - Real-Time Voice Agent (Conversational design critiquing)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. AGENT & EXECUTION LAYER:                                                 │
│    - Agent Manager (Parallel branch exploration & state tracking)           │
│    - Gemini 2.5 Pro Multimodal Generation & Mutation Engine                 │
│    - HTML/CSS/Tailwind Code Generator + Figma Clipboard Bridge              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. OPEN PROTOCOL & SDK BRIDGE:                                              │
│    - @google/stitch-sdk (Apache 2.0 Open Source SDK)                        │
│    - MCP Server Endpoint (https://stitch.googleapis.com/mcp)                │
│    - StitchProxy & StitchToolClient for IDEs (Hermes, Claude Code, Codex)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 3. SDK та MCP Інтерфейси (`@google/stitch-sdk`)

Google випустив відкритий SDK під ліцензією **Apache 2.0** (`github.com/google-labs-code/stitch-sdk`). Він надає програмний інтерфейс для керування Stitch через стандарт MCP (Model Context Protocol).

### 3.1 Ключові сутності SDK
- `Stitch`: Кореневий клієнт (керує списком проектів, конфігурацією автентифікації).
- `Project`: Проект, що містить екрани (`Screen[]`) та дизайн-системи (`DesignSystem[]`).
- `Screen`: Модель екрану з доступом до згенерованого HTML, CSS, скріншотів та метаданих інтерактивності.
- `DesignSystem`: Специфікація стилів на базі `DESIGN.md` або вилучених з URL.
- `StitchToolClient`: MCP-клієнт для виклику інструментів Stitch через JSON-RPC.
- `StitchProxy`: Проксі-сервер для перенаправлення запитів зовнішніх агентів до бекенду Stitch.

### 3.2 Реєстр MCP Інструментів Stitch

| Tool Name | Параметри | Опис / Повернене значення |
| :--- | :--- | :--- |
| `list_projects` | `{}` | Повертає масив проектів користувача (`projects: ProjectSummary[]`). |
| `create_project` | `{ title: string, designSystemId?: string }` | Створює новий проект на полотні. |
| `get_project` | `{ projectId: string }` | Повертає дерево екранів та зв'язків проекту. |
| `generate_screen` | `{ projectId: string, prompt: string, parentScreenId?: string, deviceType?: "mobile"\|"desktop" }` | Генерує новий екран на основі промпту та дизайн-системи. |
| `get_screen` | `{ projectId: string, screenId: string }` | Отримує вихідний HTML, CSS, скріншот та інтерактивні елементи. |
| `update_screen` | `{ projectId: string, screenId: string, prompt: string, patchMode?: boolean }` | Мутує існуючий екран зі збереженням контексту. |
| `create_design_system`| `{ name: string, designMdContent: string }` | Створює дизайн-систему на основі `DESIGN.md`. |
| `extract_design_system_from_url` | `{ url: string }` | Парсить публічний сайт і генерує `DESIGN.md` токени. |

---

## 🎨 4. Стандарт `DESIGN.md` та Figma Interop

### 4.1 Специфікація `DESIGN.md` (Apache 2.0)
Stitch використовує `DESIGN.md` як універсальний контракт між дизайнерами, AI-агентами та кодом:
1. **YAML Front Matter**: Нормативні дизайн-токени (кольори, типографіка, відступи, радіуси, тіні, стани компонентів).
2. **Markdown Body**: Раціонал для агентів (чому обрано саме такі кольори, як будується ієрархія, правила Do's & Don'ts).
3. **WCAG & Linting**: Автоматична валідація коефіцієнта контрасту (4.5:1 для AA) та виявлення осиротілих токенів.
4. **Tailwind / DTCG Export**: Пряма компіляція в `tailwind.theme.json` або Tailwind v4 `@theme` CSS змінні.

### 4.2 Figma Bridge
Stitch підтримує формат буфера обміну Figma:
- Серіалізація HTML/CSS DOM-дерева у Figma REST / Clipboard Vector Node Graph.
- Можливість копіювання згенерованого екрана прямо в полотно Figma без втрати шарів та векторів.

---

## 🚀 5. Висновки для DNK OS Open Canvas MVP
1. **Повна відкритість протоколів**: Завдяки Apache 2.0 ліцензії `stitch-sdk` та `design.md`, ми можемо без обмежень асимілювати всі структури DTO, MCP-інструменти та моделі токенів (Track 1 Permissive).
2. **Інтеграція в ройову архітектуру**: DNK OS отримує можливість керувати генерацією інтерфейсів як локально (через власні моделі та AST-транспайлери), так і через Stitch MCP міст.
