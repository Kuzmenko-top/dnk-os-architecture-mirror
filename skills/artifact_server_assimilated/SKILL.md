---
name: artifact_server_assimilated
description: "Assimilated SOTA patterns and architecture from plannotator/artifact-server."
version: "1.0.0"
category: "research"
assimilated_at: "2026-09-07"
track: "Track 2: Clean-Room Reverse Engineering (Restrictive/Copyleft)"
license: "AGPL-3.0"
target_worker: "gerych_researcher"
---

# 🌐 ARTIFACT-SERVER Assimilation Index

Meta-index for architecture, contracts, and component patterns assimilated from **[plannotator/artifact-server](https://github.com/plannotator/artifact-server)**.

## 📌 Repository Intel & Legal Boundary
- **Repository**: `plannotator/artifact-server`
- **License**: `AGPL-3.0`
- **Assigned Evolution Track**: `Track 2: Clean-Room Reverse Engineering (Restrictive/Copyleft)`
- **Target Swarm Worker**: `gerych_researcher`
- **Architectural Directive**: CLEAN-ROOM REVERSE ENGINEERING ONLY: Verbatim copying is forbidden. Synthesize independent MIT contracts.

## 📁 Core Architecture & Specifications
- **Stack**: `TypeScript`
- **Target Component Target**: `core/research/ or docs/tech/specs/`
- **High-Level Purpose**: The self-hosted, open-source alternative to Claude Code artifacts.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Swarm Worker Task Delegation
Delegate implementation directly to **`gerych_researcher`**:
```python
from core.orchestrator.swarm_coordinator import SwarmCoordinator

coordinator = SwarmCoordinator()
res = coordinator.dispatch(
    agent="gerych_researcher",
    action="assimilate_adapter",
    payload={
        "technology": "plannotator/artifact-server",
        "track": "Track 2: Clean-Room Reverse Engineering (Restrictive/Copyleft)",
        "action": "Deep AST extraction, competitive architectural synthesis, and algorithmic benchmarking."
    }
)
```

### Recipe B: Clean Interface Contract Adoption
Integrate type-safe schemas into your local module:
```python
# Clean-Room Schema derived from artifact-server
from pydantic import BaseModel, Field

class Artifact-ServerConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enables feature adapter")
    mode: str = Field(default="auto", description="Execution mode")
```

## ⚠️ Pitfalls & Invariants
1. **[ZERO_ABSOLUTE_PATHS]**: Never hardcode absolute system paths. Always use `./` or `../`.
2. **[MRH_HEADER_INVARIANT]**: Any adapter or component generated from this pattern MUST carry `DNK-STD-0075` MRH header.
3. **[LICENSE_BOUNDARY]**: Strict Clean-Room Isolation: Under no circumstances copy proprietary or copyleft code directly.
4. **[CLEAN-ROOM REVERSE-ENGINEERING INVARIANT]**: Direct code copying is strictly prohibited. Clean-room synthesis only.
