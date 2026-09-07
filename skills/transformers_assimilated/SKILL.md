---
name: transformers_assimilated
description: "HuggingFace Transformers SOTA patterns: Model Architectures, Tokenizers, Pipelines, Config, Model Hub."
version: 1.0.0
category: devops
author: "DNK-e.com Maksym"
triggers:
  - "transformers"
  - "huggingface"
  - "tokenizer"
  - "pipeline"
  - "model config"
---

# 🤖 HuggingFace Transformers Assimilated Skill

Index and recipes for HuggingFace Transformers architecture patterns assimilated into DNK OS.

## 📚 Canonical References
- [RN-018: Transformers Research Report](../../docs/reports/rd_assimilation/langchain/RN-018_transformers-research.md)
- [DNK-ARCH-018: Transformers Architecture Patterns](../../docs/tech/specs/DNK-ARCH-018_transformers-patterns.md)
- [DNK-COMP-018: Transformers Component Contracts](../../docs/tech/specs/DNK-COMP-018_transformers-contracts.md)

## 🛠️ Executable Recipes

### 1. Verify Path Hygiene & Specs
```bash
PYTHONPATH=. uv run pytest tests/verification/test_path_hygiene.py
```

### 2. Export Assimilation Artifacts
```bash
./scripts/export-assimilation.sh
```
