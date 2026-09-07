# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Automated engine to load, search, validate, and dynamically append agentic patterns inside DNK OS."
# canonical_source: true
# alters_files: ["core/pattern_synthesizer.py"]
# triggers_tasks: ["TF_CORE_PATTERN_SYNTHESIZER"]
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import json
import re
import time
from jsonschema import validate, ValidationError

DEFAULT_REGISTRY_PATH = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md"
DEFAULT_SCHEMA_PATH = "docs/schemas/agentic_pattern_schema.json"

class PatternSynthesizer:
    def __init__(self, registry_path: str = DEFAULT_REGISTRY_PATH, schema_path: str = DEFAULT_SCHEMA_PATH):
        self.registry_path = registry_path
        self.schema_path = schema_path
        self.patterns = []
        self.schema = {}
        self.load_schema()
        self.load_patterns()

    def load_schema(self):
        """Load JSON validation schema."""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found at {self.schema_path}")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def load_patterns(self):
        """Extract and parse existing patterns from the registry markdown file."""
        if not os.path.exists(self.registry_path):
            self.patterns = []
            return
            
        with open(self.registry_path, "r", encoding="utf-8") as f:
            content = f.read()

        json_blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if not json_blocks:
            self.patterns = []
            return

        for block in json_blocks:
            try:
                parsed = json.loads(block)
                if isinstance(parsed, list) and len(parsed) > 0 and "id" in parsed[0]:
                    self.patterns = parsed
                    return
            except json.JSONDecodeError:
                continue
        self.patterns = []

    def validate_pattern(self, pattern: dict) -> bool:
        """Validate a pattern against the JSON schema."""
        schema_clean = self.schema.copy()
        if "_mrh_header" in schema_clean:
            del schema_clean["_mrh_header"]
            
        try:
            validate(instance=pattern, schema=schema_clean)
            return True
        except ValidationError as exc:
            raise ValidationError(f"Pattern validation failed: {exc.message}")

    def synthesize_pattern(self, name: str, description: str, pattern_type: str, roles: list, triggers: list, validation_methods: list, prefix: str = "DNK-PAT", metadata: dict = None) -> dict:
        """Synthesize, validate, and write a new pattern card with strict validations."""
        # 1. Validate empty strings
        if not name or not name.strip():
            raise ValueError("Pattern name cannot be empty.")
        if not description or not description.strip():
            raise ValueError("Pattern description cannot be empty.")
        if not pattern_type or not pattern_type.strip():
            raise ValueError("Pattern type cannot be empty.")
        
        if not roles or any(not r or not r.strip() for r in roles):
            raise ValueError("Roles list or elements cannot be empty.")
        if not triggers or any(not t or not t.strip() for t in triggers):
            raise ValueError("Triggers list or elements cannot be empty.")
        if not validation_methods or any(not v or not v.strip() for v in validation_methods):
            raise ValueError("Validation methods list or elements cannot be empty.")

        # 2. Case-insensitive name duplicate check
        normalized_name = name.strip().lower()
        for p in self.patterns:
            if p.get("name", "").strip().lower() == normalized_name:
                raise ValueError(f"Pattern with name '{name}' already exists (case-insensitive duplicate).")

        # 3. Auto-increment PAT-001, PAT-002, etc. (using prefix)
        if prefix not in ["DNK-PAT", "DNK-AGNT"]:
            raise ValueError("Prefix must be either 'DNK-PAT' or 'DNK-AGNT'")

        ids = []
        for p in self.patterns:
            p_id = p.get("id", "")
            match = re.match(rf"^{prefix}-(\d{{3}})$", p_id)
            if match:
                ids.append(int(match.group(1)))

        next_num = max(ids) + 1 if ids else (2 if prefix == "DNK-AGNT" else 8)
        next_id = f"{prefix}-{next_num:03d}"

        new_pattern = {
            "id": next_id,
            "name": name.strip(),
            "description": description.strip(),
            "type": pattern_type.strip(),
            "roles": [r.strip() for r in roles],
            "triggers": [t.strip() for t in triggers],
            "validation_methods": [v.strip() for v in validation_methods],
            "metadata": metadata or {"status": "Active", "version": "1.0.0"}
        }

        # Validate against JSON schema
        self.validate_pattern(new_pattern)

        # Save to list and Markdown
        self.patterns.append(new_pattern)
        self.export_markdown(save=True)

        return new_pattern

    def add_pattern(self, name: str, description: str, pattern_type: str, roles: list, triggers: list, validation_methods: list, prefix: str = "DNK-PAT", metadata: dict = None) -> dict:
        """Alias or fallback for add_pattern to support any existing code/tests."""
        return self.synthesize_pattern(name, description, pattern_type, roles, triggers, validation_methods, prefix, metadata)

    def register_in_orchestrator(self, orchestrator, pattern: dict):
        """Register the pattern as a skill in SwarmOrchestrator."""
        if not hasattr(orchestrator, "register_skill"):
            raise AttributeError("Orchestrator object does not have 'register_skill' method.")
        orchestrator.register_skill(pattern)

    def search_patterns(self, query: str) -> list:
        """Search preloaded patterns by keyword or token intersection inside ID, name, description, roles, triggers. Performance target: <0.05s"""
        if not query:
            return []
            
        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))
        results = []
        for p in self.patterns:
            in_id = query_lower in p.get("id", "").lower()
            in_name = query_lower in p.get("name", "").lower()
            in_desc = query_lower in p.get("description", "").lower()
            in_type = query_lower in p.get("type", "").lower()
            in_roles = any(query_lower in r.lower() for r in p.get("roles", []))
            in_triggers = any(query_lower in t.lower() for t in p.get("triggers", []))
            
            if in_id or in_name or in_desc or in_type or in_roles or in_triggers:
                results.append(p)
                continue

            # Key term intersection (fields inside query)
            pat_text = f"{p.get('id', '')} {p.get('name', '')} {p.get('description', '')} " + \
                       " ".join(p.get("roles", [])) + " " + " ".join(p.get("triggers", []))
            pat_words = set(re.findall(r"\w+", pat_text.lower()))
            
            stop_words = {"an", "and", "the", "a", "or", "in", "on", "at", "to", "for", "with", "by", "of", "setup", "design"}
            significant_query_words = query_words - stop_words
            significant_pat_words = pat_words - stop_words
            
            if significant_query_words.intersection(significant_pat_words):
                results.append(p)

        return results

    def export_markdown(self, save: bool = True, custom_path: str = None) -> str:
        """Generate the updated markdown text for the registry."""
        target_path = custom_path or self.registry_path

        # Split patterns
        agnt_patterns = [p for p in self.patterns if p.get("id", "").startswith("DNK-AGNT")]
        pat_patterns = [p for p in self.patterns if p.get("id", "").startswith("DNK-PAT")]

        # Generate AGNT markup
        agnt_markup = ""
        for p in agnt_patterns:
            agnt_markup += f"""### 📘 Картка {p['id']}: {p['name']}

- **ID**: {p['id']}
- **Назва**: {p['name']}
- **Тип**: {p['type']}
- **Ролі**: {", ".join(p['roles'])}
- **Тригери**: {", ".join(p['triggers'])}
- **Опис**: {p['description']}
- **Методи верифікації**: {", ".join(p['validation_methods'])}

"""
            if p['id'] == "DNK-AGNT-001":
                agnt_markup += f"""
#### 🌊 1. Архітектура 3-хвильового збагачення (3-Wave Enrichment Architecture)

Двигун збагачення працює за трьома послідовними хвилями для забезпечення максимальної якості когнітивного результату:

```
[Вхідна задача]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 🌊 Wave 1: Context Harvesting & Intent Alignment        │
│    - Збір метаданих проекту та оточення                │
│    - Визначення меж робочого простору (DNK OS/)      │
│    - Синхронізація з SOUL та поточною пам'яттю          │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 🌊 Wave 2: Capability & Tool Synthesis                 │
│    - Динамічне підключення релевантних навичок (skills) │
│    - Ін'єкція архітектурних інваріантів та безпеки     │
│    - Вибір оптимальної LLM за допомогою matrix роутингу │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ 🌊 Wave 3: Meta-cognitive Optimization & Verification │
│    - Додавання контурів самокорекції (Evaluator-Opt)   │
│    - Визначення Definition of Done (DoD)               │
│    - Специфікація точних команд верифікації (pytest/cli)│
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
[Збагачена SOTA-інструкція для Агента]
```

* **Wave 1: Context Harvesting & Intent Alignment (Перша хвиля: Збір контексту та вирівнювання намірів)**: Збирає всі необхідні метадані середовища виконання, сканує межі робочого простору (наприклад, конфігурацію папки `DNK_HUB/`), підтягує активні сесії та файли пам'яті. Зіставляє намір користувача з місією та філософією (SOUL) конкретного воркера для вирівнювання розуміння кінцевої мети.
* **Wave 2: Capability & Tool Synthesis (Друга хвиля: Синтез спроможностей та інструментів)**: На основі доступного набору інструментів та навичок (skills) динамічно збагачує промпт точними покроковими інструкціями з відповідних навичок. Додає системні обмеження безпеки (zero host pollution, використання виключно Docker-контейнерів для важких середовищ, відносні шляхи) та обирає модель за матрицею роутингу (GLM для UI чи Mistral для коду).
* **Wave 3: Meta-cognitive Optimization & Verification (Третя хвиля: Мета-когнітивна оптимізація та верифікація)**: Вбудовує в інструкцію когнітивні шаблони поведінки типу "Оцінювач-Оптимізатор", які змушують модель валідувати проміжні результати. Чітко визначає критерії успіху (DoD) та автоматично генерує точні CLI-команди для запуску верифікаційних скриптів або pytest-суїтів.

#### 📊 2. Таблиця універсального застосування (Universal Application Table)

| Агент / Роль | Сценарій використання | Очікуваний ефект збагачення | Метод верифікації |
| :--- | :--- | :--- | :--- |
| **Gerych (herich_librarian)** | Оркестрація мультиагентних робіт, аналіз R&D репозиторіїв | 100% точність визначення меж та розподілу підзадач | Автоматичний запуск pytest суїтів |
| **dnk_koder** | Написання, оптимізація та рефакторинг складного коду | Скорочення синтаксичних помилок та галюцинацій на 95% | Pytest, лінтування, AST парсинг |
| **dnk-dev-01** | Створення FastAPI ендпоінтів та React UI компонентів | Чиста гексагональна архітектура, надійне підключення до БД | Docker-compose інтеграційні тести |
| **dnk_governance_companion**| Перевірка standards коду, MRH-хедерів та лімітів токенів | Гарантія 100% дотримання архітектурних інваріантів | Автоматичний audit перед мержем |

"""

        # Generate PAT markup
        pat_markup = ""
        for idx, p in enumerate(pat_patterns, 1):
            pat_markup += f"""### {idx}. {p['name']}
- **ID**: {p['id']}
- **Тип**: {p['type']}
- **Ролі**: {", ".join(p['roles'])}
- **Тригери**: {", ".join(p['triggers'])}
- **Опис**: {p['description']}
- **Методи верифікації**: {", ".join(p['validation_methods'])}

"""

        markdown_template = f"""# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Canonical registry of technological improvements and dictionary of agentic enrichments inside DNK OS."
# canonical_source: true
# alters_files: ["docs/tech/SPEC_02_Agentic_Patterns_Registry.md"]
# triggers_tasks: ["TF_REGISTRY_PATTERN_001_ENRICHMENT"]
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

# 🌸 Офіційний реєстр агентних патернів (Agentic Patterns Registry)

Цей реєстр містить канонічні паттерни взаємодії та покращення агентних систем, які впроваджені в екосистемі **DNK OS**. Всі нові паттерни повинні відповідно відповідати схемі `docs/schemas/agentic_pattern_schema.json`.

---

## 📖 Словник технологічних покращень агентів (Agentic Technological Improvements Dictionary)

Місія словника полягає у фіксації, структуризації та стандартизації технологічних покращень, які дозволяють оптимізувати роботу великих та малих мовних моделей, що виступають у ролі агентів (воркерів чи оркестраторів) в екосистемі **DNK OS**. Словник забезпевує уніфікований підхід до підвищення когнітивних здатностей агентів через збагачення промптів, контекстів та інструкцій.

---

{agnt_markup.strip()}

---

## 🧬 Опис патернів

{pat_markup.strip()}
---

## 📇 Офіційний JSON-список патернів для валідації (Pattern Cards JSON)

У наведеному нижче блоці містяться машинозчитувані картки патернів, які використовуються автоматизованими тестами для валідації відповідності JSON-схемі.

```json
{json.dumps(self.patterns, indent=2, ensure_ascii=False)}
```
"""
        if save:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(markdown_template)

        return markdown_template
