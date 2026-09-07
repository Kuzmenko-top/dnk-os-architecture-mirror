---
title: "045 Cross-Workspace Multi-Knowledge-Base Retrieval & Grounded Marketing Banner Pipeline"
date: "2026-09-06"
tags:
  - rag
  - multimodal
  - cross-workspace
  - marketing
  - reburn
  - canvas
  - remotion
status: "Active"
version: "1.0.0"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/045_cross_workspace_marketing_banner_pipeline.md"
purpose: "ADR and Architecture Spec for Cross-Workspace Knowledge Retrieval and Autonomous Grounded Marketing Banner Generation (ReBurn Showcase)"
canonical_source: true
alters_files:
  - "core/adapters/dnk_rag_anything_adapter.py"
  - "core/rag/marketing_banner.py"
  - "apps/api/schemas/rag.py"
  - "apps/api/routers/rag.py"
  - "core/orchestrator/tools/dnk_rag_tool.py"
  - "core/orchestrator/tool_aliases.py"
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK Swarm (Gerych Prime & Maxim)"
--- END DNK-MRH-HEADER -->

# 045 Cross-Workspace Multi-Knowledge-Base Retrieval & Grounded Marketing Banner Pipeline

## 🎯 1. Контекст та Мета

Користувач та архітектор системи поставили ключове запитання:
> *«Чи правильно я розумію, що завдяки цьому користувач зможе наповнювати бібліотеку знань для свого акаунта або для кожного зі своїх проєктів окрему базу знань і потім з кожною з баз знань працювати? Чи можемо ми реалізувати наступну логіку: Якщо у нас є вже в додатку DNK OS база знань з маркетингу, в проєкт ReBurn виробництва коптилень я додаю матеріали про виробництво коптилень, фото, інструкцію користування, агент зможе використати маркетингові навички, взяти зображення або інформацію з інструкції по коптильні і створити маркетинговий банер, який буде унікальний і 100% релевантний нашому бізнесу?»*

**Відповідь — ТАК.** Для реалізації цього сценарію було збудовано двовекторну систему:
1. **Cross-Workspace Knowledge Retrieval**: об'єднання кількох ізольованих баз знань (глобальні навички платформи + предметні бази знань проєктів) в єдиний запит із збереженням джерел (provenance tracking).
2. **Grounded Marketing Banner Pipeline**: ройовий конвеєр, який автоматично синтезує висококонверсійні банери (SVG, HTML5, Remotion props, Canvas node) на основі 100% підтверджених інженерних фактів та реальних фотографій з кешу вилучених активів `.extracted_assets/`.

---

## 🏛️ 2. Архітектурна Схема

```text
 ┌────────────────────────────────────────────────────────┐
 │           WORKSPACE 1: global-marketing                │
 │  • Психологія продажів & конверсійні фреймворки (AIDA, │
 │    PAS, BAB, FAB)                                      │
 │  • Патерни хуків для крафтових та outdoor-товарів      │
 └───────────────────────────┬────────────────────────────┘
                             │
                             │  Cross-Workspace Retrieval
                             │  (query_dual_level with
                             │   workspace_ids=[...])
                             │
 ┌───────────────────────────┴────────────────────────────┐
 │           WORKSPACE 2: ws-reburn-001 (ReBurn)          │
 │  • Інструкція користувача коптильні ReBurn Pro         │
 │  • Інженерні факти: нержавійка 2.0 мм, гідрозатвор,     │
 │    20-25°C діапазон, тріска вільхи та бука            │
 │  • Вилучені реальні фото (.extracted_assets/reburn/...) │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │      GroundedMarketingBannerSynthesizer (core/rag/)    │
 │  1. Тріангуляція фактів (Zero Hallucination)           │
 │  2. Генерація копірайтингу (Headline, Bullets, CTA)   │
 │  3. Прив'язка вилученого зображення з інструкції       │
 └───────────────────────────┬────────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  SVG Card    │      │  HTML5 Comp  │      │ Remotion /   │
│ (Scalable)   │      │ (Tailwind)   │      │ Canvas Node  │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## 🔧 3. Реалізовані Компоненти

### 3.1. `core/adapters/dnk_rag_anything_adapter.py`
- Додано підтримку багатопросторових графів знань: `_workspace_graphs: Dict[str, DualLevelKnowledgeGraph]`.
- Метод `get_knowledge_graph(workspace_id)` повертає ізольований граф для будь-якого проєкту.
- Метод `query_dual_level` приймає `workspace_ids: List[str]` і виконує крос-просторове об'єднання макро-тем, сутностей та артефактів із маркуванням простору походження (`workspace_id`).

### 3.2. `core/rag/marketing_banner.py`
- `GroundedMarketingBannerSynthesizer`: ядро синтезу банерів.
- Вилучає сухі інженерні характеристики з бази знань проєкту (`мм`, `сталь`, `гідрозатвор`, `температура`).
- Формує офер за обраним психологічним фреймворком (`AIDA`, `PAS`, `BAB`).
- Генерує 4 формати представлення:
  1. **SVG Banner**: векторний макет із градієнтом, бейджами, булетами та прев'ю фотографії.
  2. **HTML5 Component**: адаптивний компонент у темній естетиці DNK OS.
  3. **Remotion Props**: JSON-параметри для автоматичного монтажу відео / сторіз через `dnk_video_generate_composition`.
  4. **Canvas Node**: візуальний вузол для полотна React Flow у Visual Shell.

### 3.3. FastAPI Роутер (`apps/api/routers/rag.py`) & Схеми (`apps/api/schemas/rag.py`)
- Додано ендпоінт `POST /api/v1/rag/marketing-banner`.
- Оновлено ендпоінти `/query-dual-level`, `/ingest`, `/ingest-text`, `/ingest-canvas` для роботи з параметром `workspace_ids` / `workspace_id`.

### 3.4. Hermes Swarm Tool (`core/orchestrator/tools/dnk_rag_tool.py`)
- Додано інструмент рою `dnk_generate_marketing_banner` (аліас `rag.marketing_banner`), зареєстровано в `core/orchestrator/tool_aliases.py`.

---

## 🧪 4. Верифікація та Тести

1. **Модульний та інтеграційний сьют**: `tests/rag/test_cross_workspace_marketing.py`:
   - `test_cross_workspace_ingestion_and_retrieval`: перевірка паралельного завантаження знань у `global-marketing` та `ws-reburn-001` і їх спільного пошуку.
   - `test_grounded_marketing_banner_synthesizer`: перевірка безгалюцинаційної прив'язки фактів ReBurn до макетів.
   - `test_swarm_tool_dnk_generate_marketing_banner`: перевірка ройового інструменту.
   - `test_api_endpoint_marketing_banner`: перевірка REST API ендпоінту.
2. **Результат**: **35/35 RAG тестів 100% Green** (2.49s).

---

## 🔗 Пов'язані нотатки
- [[039_rag_anything_sota_assimilation_audit]] — Асиміляція HKUDS/RAG-Anything в DNK OS.
- [[023 NodeTask Cabinet Architecture and Improvement Roadmap]] — Візуальний кабінет задач та полотно Canvas.
- [[037_phase18_production_hardening]] — Харденінг бекенду та ройові інструменти.
