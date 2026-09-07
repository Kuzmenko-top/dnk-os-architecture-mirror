---
name: "openwiki_assimilated"
description: "Assimilated wiki-graph memory and markdown-sync from langchain-ai/openwiki"
version: "2.0.0"
category: "research"
assimilated_at: "2026-08-10"
---

# 🌐 OpenWiki Assimilation Index

Meta-index tracking the architecture, contracts, and security of wiki-graph memory and markdown-sync patterns.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../../docs/reports/rd_assimilation/openwiki/RN-003_openwiki-research.md)**
   - Researched abstractions (CLI, Agents, Connectors, Visualizer) and ecosystem map.

2. **[Component Interfaces & Contracts](../../docs/tech/specs/DNK-COMP-004_openwiki-parser.md)**
   - Port-and-adapter specifications for `FrontmatterParser` and `IndexSynchronizer` Python components.

3. **[Security & Governance Standards](../../docs/tech/standards/DNK-SEC-004_openwiki-governance.md)**
   - Zero-host process compliance, dockerized volume restrictions, and context firewall policies.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: YAML Frontmatter Parsing

**Goal:** Parse YAML frontmatter headers in Markdown files within DNK OS memory services.

- Instantiate and call `FrontmatterParser` defined in `DNK-COMP-004_openwiki-parser.md`:
  ```python
  from services.dnk_openwiki.parser import FrontmatterParser
  
  parser = FrontmatterParser(markdown_content)
  result = parser.parse()
  if result["valid"]:
      print("Parsed fields:", parser.fields)
  else:
      print("Validation failed:", result["issues"])
  ```

### Recipe B: Dockerized Directory Sync Setup

**Goal:** Run index synchronization safely inside a sandboxed Docker container.

- Deploy using volume mounts defined in `DNK-SEC-004_openwiki-governance.md`:
  ```bash
  docker run -v $(pwd)/docs:/openwiki/docs:ro openwiki-sync-image python -m dnk_openwiki.sync
  ```
