# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/makazhanalpamys_soup.md"
# purpose: "SOTA Ingested Knowledge Card for MakazhanAlpamys/Soup."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Knowledge Card: MakazhanAlpamys/Soup

## 📊 Overview Metadata
- **Repository**: MakazhanAlpamys/Soup
- **License**: APACHE-2.0
- **Evolution Track**: **Direct Template Assimilation**

---

## 🏛️ Extracted Architecture & Stack
- **Primary Stack**: Python / Modern Toolchain
- **Architecture Principle**: High-velocity modular architecture (Python)

### Key Extracted Features:
- Fine-tune LLMs from one YAML. Layer streaming trains an 8B model on a 4 GB laptop GPU.
- Core domains: cli, consumer-gpu, dpo, fine-tuning, gguf
- Stars: 5464 | Open Issues: 79
- Default branch: main

---

## 🛡️ License & Legal Directives
Permissive License. Direct code structure adoption is permitted.
Incorporate modules directly into `core/` matching standard clean design patterns.

---

## 📋 Extracted Technical Schemas
```json
{'SessionRecord': {'id': 'str', 'created_at': 'int', 'is_active': 'bool'}, 'ActionLog': {'id': 'str', 'actor': 'str', 'event_type': 'str'}}
```

---

*Ingested and verified by DNK OS DNA Assimilation Engine.*
