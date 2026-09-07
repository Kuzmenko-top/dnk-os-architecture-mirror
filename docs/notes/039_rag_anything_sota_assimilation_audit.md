---
title: "ADR 039: HKUDS/RAG-Anything Multimodal RAG Assimilation & Knowledge Graph Architecture"
tags:
  - architecture
  - sota-assimilation
  - rag-anything
  - multimodal-rag
  - knowledge-graph
  - mineru
  - lightrag
date: 2026-09-05
status: Active
version: 1.0.0
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/039_rag_anything_sota_assimilation_audit.md"
purpose: "Architecture Decision Record & SOTA Assimilation Audit for HKUDS/RAG-Anything Multimodal RAG Engine."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🧬 ADR 039: Глибокий Аудит та Етапи Асиміляції HKUDS/RAG-Anything

## 📌 Context & Problem Statement
У рамках розвитку екосистеми **DNK OS** ключовим когнітивним шаром є база знань та пам'ять ([[SCONES Long-Term Cognitive Memory]], [[Obsidian Task Forest]], [[DVL Video Librarian]]). Дотепер більшість RAG-інструментів фокусувалися виключно на чистому тексті, втрачаючи критичні смислові шари:
- Технічні діаграми, блок-схеми та графіки у PDF/Office-документах;
- Структуровані табличні звіти та фінансові дані;
- Математичні рівняння у форматі LaTeX;
- Просторові та ієрархічні зв'язки між візуальними елементами та пояснювальним текстом.

Репозиторій **[HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything)** (розробка Data Intelligence Lab Гонконгського університету — авторів LightRAG та VideoRAG) є глобальним SOTA у мультимодальному RAG. Він об'єднує графовий RAG (LightRAG) із глибоким мультимодальним парсингом документів.

---

## 📊 1. Репозитарний Аудит та Метрики (Repository Intel)

| Параметр | Значення | Оцінка для DNK OS |
|---|---|---|
| **Репозиторій** | `HKUDS/RAG-Anything` | Профільна лабораторія HKUDS |
| **Зірки GitHub** | ⭐ **23,213+** | Найвищий рівень перевірки індустрією |
| **Форки / Issues** | 2,698 / 96 | Активна спільнота, живий розвиток |
| **Ліцензія** | **MIT License** | **Track 1 (Permissive)**: повна свобода адаптації |
| **Базовий стек** | Python 3.10+, uv, LightRAG, MinerU | 100% сумісність із віртуальним середовищем DNK_HUB |
| **Архітектурний бал DNK** | **9.6 / 10** | Бездоганна модульність та відкритий інтерфейс |

---

## 🏛️ 2. Архітектурні Інваріанти RAG-Anything

### 2.1. Чотириетапний Мультимодальний Пайплайн
```
+-----------------------------------------------------------------------------------+
| 1. Document Parsing Stage (MinerU / Docling / PaddleOCR / LibreOffice)            |
|    - Адаптивна декомпозиція: Text Blocks + Visual Elements + Tables + LaTeX       |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 2. Modality-Aware Processing Units                                                |
|    - ImageModalProcessor: VLM-кепшонінг, просторовий аналіз                       |
|    - TableModalProcessor: структурований семантичний розбір таблиць              |
|    - EquationModalProcessor: нативний парсинг LaTeX та прив'язка до контексту    |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 3. Multimodal Knowledge Graph Indexing (на базі LightRAG)                         |
|    - Вилучення міжмодальних сутностей (Cross-modal entities)                      |
|    - Ієрархічні зв'язки "belongs_to" зі зваженими коефіцієнтами близькості        |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 4. Hybrid Intelligent Retrieval & VLM-Enhanced Querying                           |
|    - Векторно-графовий синтез (Vector Search + Graph Traversal)                   |
|    - Direct VLM Query Injection (передача знайдених картинок прямо у Vision LLM)  |
+-----------------------------------------------------------------------------------+
```

### 2.2. Ліцензійна відповідність
- Репозиторій ліцензований під **MIT License**.
- За протоколом **Two-Track SOTA Repository Assimilation Pipeline** (DNK OS v4.5), проєкт кваліфіковано як **Track 1: Direct Template Assimilation**.
- Дозволено пряму адаптацію модулів, створення гексагонального адаптера (`core/adapters/dnk_rag_anything_adapter.py`) та інтеграцію без ризику копілефту.

---

## ⚡ 3. Синергія з Можливостями Додатку DNK OS

1. **[[SCONES Long-Term Cognitive Memory]]**:
   - Інтеграція міжмодального графа RAG-Anything розширює SCONES від чисто текстових епізодів до графових вузлів, що містять схеми архітектури, скриншоти та діаграми.
2. **[[Canvas & Visual Working Cabinet]] (`visual_shell`)**:
   - Завдяки `dnk_visual_context_query`, виділені ділянки канвасу або імпортовані PDF можуть миттєво індексуватися через `RAGAnything` та ставати доступними для всіх 14 ройових агентів.
3. **Ройові агенти (`gerych_researcher`, `gerych_builder`, `dnk_dev_fullstack`)**:
   - `gerych_researcher` отримує здатність за лічені секунди витягувати з arXiv-статей та whitepaper не лише тези, а й складні формули та архітектурні діаграми.
4. **[[DVL Video Librarian]]**:
   - Поєднання транскриптів відео зі знятими слайдами/кадрами дозволяє будувати повний мультимодальний індекс лекцій та презентацій.

---

## 🗺️ 4. План Поетапної Асиміляції (TaskDNA & Swarm Routing)

Згідно з декомпозицією `dnk_decompose_task_dna`, процес розділено на 5 чітких атомних зрізів (MASE):

```
  [Етап 1: Контракти та Гексагональний Адаптер]
                      │
                      ▼
  [Етап 2: Модальні Процесори & Парсери Документів]
                      │
                      ▼
  [Етап 3: Інтеграція з Графом Пам'яті SCONES]
                      │
                      ▼
  [Етап 4: Fast-API Шлюз & Swarm Tooling]
                      │
                      ▼
  [Етап 5: Adversarial Review & 100% Quality Gate]
```

### Етап 1: Контракти та Гексагональний Адаптер (`core/adapters/`) ✅ ЗАВЕРШЕНО
- **Відповідальний агент**: `antigravity_mentor` + `dnk_dev_fullstack`
- **Завдання**:
  1. Визначити абстрактний інтерфейс `MultimodalRAGPort` (Protocol / ABC).
  2. Реалізувати `DNKRAGAnythingAdapter` з підтримкою асинхронного режиму (`ingest_document`, `ingest_text`, `ingest_canvas`, `query`, `query_multimodal`, `get_document_graph`).
  3. Підтримка конфігурації через Vault (`dnk_vault_get_secret`), Path Traversal Guard та SpendGuard.
- **Артефакти**: `core/adapters/dnk_rag_anything_adapter.py`, `tests/core/test_rag_adapter.py` (5 тестів 100% green).

### Етап 2: Модальні Процесори & Парсинг Документів (`core/rag/`) ✅ ЗАВЕРШЕНО
- **Відповідальний агент**: `gerych_builder` + `gerych_prime`
- **Завдання**:
  1. Реалізувати адаптери процесорів: `DNKImageProcessor`, `DNKTableProcessor`, `DNKEquationProcessor`, `DocumentDecomposer`.
  2. Інтеграція розбору документів (MinerU / Docling з pure-Python fallback для PDF та DOCX) з сайдкар-кешуванням (`.meta.json`, `.extracted_assets/`).
  3. Пряма ін'єкція вузлів та візуального контексту з Canvas (`CanvasVisualExtractor`).
- **Артефакти**: `core/rag/pipeline.py`, `core/rag/processors.py`, `tests/rag/test_multimodal_pipeline.py` (6 нових тестів, загалом 18/18 100% green).

### Етап 3: Інтеграція з Графом Пам'яті SCONES & LightRAG (`core/rag/knowledge_graph.py`) ✅ ЗАВЕРШЕНО
- **Відповідальний агент**: `dnk_scones_memory` + `gerych_builder` + `gerych_prime`
- **Завдання**:
  1. Реалізувати дворівневу топологію LightRAG (High-level теми + Low-level ентіті/артефакти): `DualLevelKnowledgeGraph`, `GraphNode`, `GraphEdge`.
  2. Забезпечити взаємну крос-модальну лінковку (`belongs_to_theme`, `illustrates`, `references`, `precedes`).
  3. Побудувати міст синхронізації з когнітивною пам'яттю SCONES (`sync_to_scones`).
  4. Реалізувати три режими пошуку: `local` (фокус на конкретних сутностях та 1-hop сусідах), `global` (фокус на високорівневих темах), `hybrid` (збалансоване поєднання).
  5. Експорт у формат вузлів та зв'язків Canvas (`to_canvas_graph`) для безпосередньої візуалізації у DNK Visual Shell.
- **Артефакти**: `core/rag/knowledge_graph.py`, оновлення `core/rag/__init__.py`, оновлення `core/adapters/dnk_rag_anything_adapter.py`, `tests/rag/test_knowledge_graph_scones.py` (5 тестів 100% green, сумарно 23/23 green).

### Етап 4: FastAPI Ендпоінти & Інструменти Рою (`apps/api/routers/rag.py` / `core/hermes_agent/tools/dnk_rag_tool.py`) ✅ ЗАВЕРШЕНО
- **Відповідальний агент**: `dnk_dev_fullstack` + `gerych_prime`
- **Завдання**:
  1. Реалізувати розширені FastAPI ендпоінти у `apps/api/routers/rag.py`:
     - `POST /api/v1/rag/ingest` (індексація файлів / документів);
     - `POST /api/v1/rag/ingest-text` (індексація сирого тексту або markdown);
     - `POST /api/v1/rag/ingest-canvas` (пряма ін'єкція графів Canvas та вузлів Visual Shell);
     - `POST /api/v1/rag/query` (текстовий та гібридний пошук);
     - `POST /api/v1/rag/query-multimodal` (пошук з ін'єкцією мультимодальних елементів);
     - `POST /api/v1/rag/query-dual-level` (маршрутизація запитів LightRAG: `hybrid`, `local`, `global`);
     - `POST /api/v1/rag/scones-sync` (миттєва синхронізація графа знань у когнітивну пам'ять SCONES);
     - `GET /api/v1/rag/canvas-graph` (експорт усього графа знань у формат Canvas для візуалізації в Visual Shell);
     - `GET /api/v1/rag/graph/{doc_id}` (топологія конкретного документа).
  2. Створити та зареєструвати нативні ройові інструменти Hermes:
     - `core/hermes_agent/tools/dnk_rag_tool.py`: `dnk_rag_query`, `dnk_rag_ingest`, `dnk_rag_sync_scones`.
     - Зареєструвати інструменти в `core/orchestrator/tool_aliases.py` (групи `cognitive`, `core`).
  3. Покриття FastAPI ендпоінтів та інструментів рою інтеграційними тестами (`tests/rag/test_rag_router_and_tools.py` — 8/8 passing).
- **Артефакти**: `apps/api/routers/rag.py`, `apps/api/schemas/rag.py`, `core/hermes_agent/tools/dnk_rag_tool.py`, `core/orchestrator/tool_aliases.py`, `tests/rag/test_rag_router_and_tools.py` (сумарно 31/31 RAG тестів 100% green).

### Етап 5: Adversarial Review & Master Quality Gate ✅ ЗАВЕРШЕНО
- **Відповідальний агент**: `gerych_auditor`
- **Завдання**:
  1. Проведення 2-агентного аудиту безпеки (Red Team проти Blue Team):
     - `apps/api/routers/rag.py`: 0 confirmed issues, 0 vulnerabilities.
     - `core/hermes_agent/tools/dnk_rag_tool.py`: 0 confirmed issues, 0 vulnerabilities.
     - Перевірка санітизації шляхів (Path Traversal guard), валідація payload, SpendGuard для VLM запитів.
  2. Повне тестове покриття всієї підсистеми RAG-Anything (31 тест, 100% Green).
  3. Сертифікація через `scripts/verify_all.sh`.

---

## 🔒 5. Контракт Гексагонального Інтерфейсу (Core Contract)

```python
# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_rag_anything_adapter.py"
# purpose: "Hexagonal adapter contract for HKUDS/RAG-Anything multimodal RAG."
# canonical_source: true
# --- END DNK-MRH-HEADER ---

from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class MultimodalElement:
    type: str  # "image", "table", "equation", "text"
    content: str  # text, latex or base64 image
    caption: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None

@dataclass
class RAGQueryResult:
    answer: str
    referenced_nodes: List[Dict[str, Any]]
    visual_evidence_urls: List[str]
    confidence_score: float

class MultimodalRAGPort(Protocol):
    async def ingest_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Parses document, decomposes modalities, and builds knowledge graph."""
        ...

    async def query(self, prompt: str, mode: str = "hybrid") -> RAGQueryResult:
        """Executes text/hybrid graph-vector query."""
        ...

    async def query_multimodal(self, prompt: str, elements: List[MultimodalElement], mode: str = "hybrid") -> RAGQueryResult:
        """Executes query with direct VLM visual element injection."""
        ...
```

---

## 🎯 Резюме та Наступний Крок
Асиміляція **HKUDS/RAG-Anything** надає DNK OS безпрецедентну перевагу — перетворення статичних мультимедійних документів у живий інтерактивний граф знань, доступний як через консоль Gerych, так і безпосередньо у Visual Shell Canvas.
