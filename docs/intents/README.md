<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/intents/README.md"
# purpose: "Canonical Registry for Business Intent Specifications in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Antigravity (Mentor & Chief Architect)"
# --- END DNK-MRH-HEADER ---
-->

# 🎯 DNK OS Intent Registry (`docs/intents/`)

Ця директорія є канонічним сховищем бізнес-намірів (**Business Intents**) для розробки та модифікації модулів у DNK OS MVP.

## 🏛️ Принцип The Golden Thread
Кожна нова функціональність, рефакторинг або виправлення інциденту у DNK OS розпочинається зі створення файлу наміру:
```
docs/intents/{INTENT_ID}_{slug}.intent.md ➔ specs/*.spec.md ➔ plans/*.plan.md ➔ Code & Evidence
```

Шаблон для створення нового наміру: [INTENT_TEMPLATE.md](../templates/INTENT_TEMPLATE.md).
