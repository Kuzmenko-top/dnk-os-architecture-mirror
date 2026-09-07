---
mrh_id: "DNK-SOTA-001"
title: "SOTA Blueprint v1.1 & Managed Deep Agents Hygiene"
purpose: "Enforce host path hygiene, ABC contracts, disclaimer callouts, and automated spec checks."
canonical_source: true
status: "Active"
version: "1.1.0"
updated_at: "2026-08-10"
author: "Maxim"
license: "DNK-INTERNAL"
---

# 🧬 R&D Assimilation Reference: Managed Deep Agents & Blueprint v1.1 Hygiene (2026-08-10)

This reference documents the clean-room architectural blueprint standards, host path hygiene requirements, and automated validation procedures assimilated during the `langchain-ai/managed-deepagents` R&D cycle.

---

## Scope & Applicability

This standard applies to:

- Sandboxed agent runtimes running inside Docker containers.
- Filesystem isolation and egress/network policies for tools executed by agents.
- Cross-language filesystem contracts (Python + TypeScript) for DNK OS.

This standard does NOT directly apply to:

- Pure UI/front-end repositories without agent tool execution.
- High-level orchestration frameworks (LangGraph, CrewAI) where sandboxing is handled differently.
- Business logic unrelated to filesystem or network isolation.

---

## 📌 1. Structural Blueprint & Spec Standards

When assimilating closed-source or public-beta repositories via clean-room reproduction, adhere to the following 4-tier specification layout:

1. **Research & Evidence Trail (RN-00X):** Maps core abstractions (e.g., Docker Runtimes, Sandbox constraints, CLI lifecycles) to actual or expected source files with documented line ranges.
2. **Architecture Spec (DNK-ARCH-00X):** Defines container topologies, subagent execution lifecycles (`Spawn ➔ Execute ➔ Capture Output ➔ Terminate`), and decoupled queue communication.
3. **Component Inventory & Interfaces (DNK-COMP-00X):** Implements strictly typed contract specifications across Python (Abstract Base Classes) and TypeScript.
4. **Security & Egress Policy (DNK-SEC-00X):** Establishes default-DROP container firewall policies (iptables, Kubernetes NetworkPolicies) and volume masking.

---

## 🛡️ 2. Host Path Hygiene & Absolute Path Eradication (v1.1)

Per `AGENTS.md` system guidelines, hardcoding absolute host paths (such as `/Users/<username>`) in technical documentation, volume mount configurations, or test scripts is strictly forbidden. 

### Path Sanitation Conventions
- **Volume Mounts in Docker Compose:**
  - *Incorrect:* `/Users/<username>/Kuzmenko/MY_LIFE_WORK/DNK_HUB/DNK OS:/workspace:ro`
  - *Correct:* `${PROJECT_ROOT:-.}:/workspace:ro`
- **TUI/CLI Indices & SKILL.md:**
  - *Incorrect:* `cd /Users/<username>/Kuzmenko/MY_LIFE_WORK/DNK_HUB && pytest`
  - *Correct:* Standalone relative commands such as `pytest tests/verification/test_sandbox_hygiene.py` or relative-scoped scripts.

---

## 🐍 3. Type-Safe Contract Specification Pattern

For specification and contract files, interface layouts must be declared as **contract-only Abstract Base Classes (ABC)** rather than serialized data structures (like Pydantic `BaseModel`) unless data parsing is explicitly intended.

```python
from abc import ABC, abstractmethod

# Contract-only interface. Implementations: DNKDockerSandboxFS, DNKLocalDevFS.
class DNKIsolatedFileSystem(ABC):
    root_boundary: str

    @abstractmethod
    def read_file(self, path: str) -> str:
        """Read the contents of a file within the sandbox root boundary."""
        ...
```

This enforces strict abstract inheritance boundaries for developers implementing subagent executors.

---

## ⚠️ 4. Unvalidated Evidence Disclaimer Callout

For evidence tables mapped during beta, early-stage, or closed-source analyses, insert the following disclaimer block to clarify lines and files are approximate:

```markdown
> ⚠️ **Validation Status:** Line ranges and file paths in this evidence
> trail are derived from structural analysis. Pending automated
> cross-validation via GitHub Contents API (`GET /repos/{owner}/{repo}/
> contents/{path}`) to confirm exact line numbers in the canonical
> repository. Until validated, treat line ranges as approximate.
```

---

## 🧪 5. Automated Spec Compliance Check

Every R&D assimilation must include an automated verification script that dynamically locates paths and validates file presence and header hygiene.

```python
import os
import re

# Resolve project root dynamically relative to the test script file location
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MVP_ROOT = os.path.join(PROJECT_ROOT, "DNK OS")

def test_no_absolute_host_paths_in_specs():
    """Verify specs don't contain hardcoded absolute host paths."""
    FORBIDDEN = "/Users/<username>"
    for path in ASSIMILATED_FILES:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert FORBIDDEN not in content, (
            f"Absolute host path found in {os.path.basename(path)}"
        )
```
