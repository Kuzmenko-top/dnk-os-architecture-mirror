# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/post_task_knowledge_harvesting_protocol.md"
# purpose: "Standard operating procedure for proactive knowledge harvesting and Obsidian archival across DNK OS swarms."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Post-Task Knowledge Harvesting & Obsidian Archival Protocol

## Overview
To prevent context drift, architectural decay, and repeated trial-and-error across agent generations, Gerych Prime and all swarm participants follow this protocol: every completed architectural milestone, non-trivial algorithm, or complex bugfix must prompt an archival recommendation to the user's Obsidian Vault.

## The Trigger Mechanism
At the conclusion of a significant task, append an explicit prompt to the user:
```markdown
💡 **"Task complete. Would you like to save this decision / algorithm to Obsidian as an [ADR / Architecture Spec / Playbook] detailing why it was built this way (context, alternatives, tradeoffs, pitfalls)?"**
```

If user confirms ("Yes" / "Save" / "Запиши"):
1. Generate the note under `~/Documents/DNK_HUB My Notes/DNK_HUB My Notes/`.
2. Follow the **Dual-Reader Principle** (structured metadata for AI parsing + callouts/diagrams for human review).
3. Update `000 DNK HUB Index.md` to maintain graph connectedness.

## The 5 Note Archetypes

### 1. ARCH (Architecture / Module Specification)
- **Use Case**: New microservice, core subsystem, or data model.
- **Key Sections**:
  - Purpose & Context
  - High-Level Architecture (Mermaid C4/Container diagram)
  - Key Invariants & Contracts
  - Code Locations (relative paths `./`, `../`)
  - Extension Guidelines

### 2. ADR (Architecture Decision Record)
- **Use Case**: Tradeoffs between libraries, algorithms, or protocol designs (e.g., choosing IndexedDB over LocalStorage, or Zod schemas over raw validation).
- **Key Sections**:
  - Context & Problem Statement
  - Decision Drivers
  - Considered Options & Comparison Matrix
  - Chosen Outcome & Rationale
  - Accepted Tradeoffs & Consequences

### 3. SOTA (State-of-the-Art Repository Assimilation)
- **Use Case**: Ingesting external open-source codebases, papers, or algorithms.
- **Key Sections**:
  - Donor Repository & License Classification (Track 1 MIT/Apache vs Track 2 GPL Clean-Room)
  - Key Architectural Discoveries
  - Adapted Patterns & Swarm Bindings
  - Security & Dependency Considerations

### 4. PLAYBOOK (Testing, Verification & Operational Runbooks)
- **Use Case**: Reproducible verification procedures, deployment flows, or recovery actions.
- **Key Sections**:
  - Pre-requisites & Environment Invariants
  - Step-by-Step Commands
  - Expected Verification Outputs
  - Common Pitfalls & Instant Fixes

### 5. AGENT (Swarm Agent Specification)
- **Use Case**: Role definition, tool permissions, and operational constraints for a swarm agent.
- **Key Sections**:
  - Mission & Persona
  - Toolset & Boundaries
  - Invariants & Fail-Closed Gates
  - Collaboration Topology with other swarm members

## Dual-Reader Formatting Invariants
- **YAML Frontmatter**:
  ```yaml
  ---
  title: "<Human-readable title>"
  aliases: ["<alternative names>"]
  tags: [dnk-os, <category>, <archetype>]
  type: arch | adr | sota | playbook | agent
  status: draft | active | deprecated
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  author: "DNK-e.com Maksym"
  repo_spec: "<relative/path/to/spec.md>"
  ---
  ```
- **DNK-MRH-HEADER**: Required immediately below frontmatter per `DNK-STD-0075` and `docs/notes/001 Obsidian & DNK OS Documentation Standard.md`. Must be formatted as a muted HTML comment block (`<!-- --- DNK-MRH-HEADER --- ... --- END DNK-MRH-HEADER -->`), NEVER as `# --- DNK-MRH-HEADER ---` which renders as an oversized H1 header in Obsidian.
- **Wikilinks**: Minimum 2 `[[Note Name]]` links, including `[[000 DNK HUB Index]]`.
- **Path Hygiene**: Absolute `/Users/...` paths are forbidden inside code blocks, tables, and frontmatter. Use relative paths (`./`, `../`).
