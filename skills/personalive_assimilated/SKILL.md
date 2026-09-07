---
name: personalive_assimilated
description: "Assimilated SOTA patterns and architecture from GVCLab/PersonaLive."
version: "1.0.0"
category: "research"
assimilated_at: "2026-09-07"
track: "Track 1: Direct Template Assimilation (Permissive)"
license: "Apache-2.0"
target_worker: "dnk_video_ai_creator"
---

# 🌐 PERSONALIVE Assimilation Index

Meta-index for architecture, contracts, and component patterns assimilated from **[GVCLab/PersonaLive](https://github.com/GVCLab/PersonaLive)**.

## 📌 Repository Intel & Legal Boundary
- **Repository**: `GVCLab/PersonaLive`
- **License**: `Apache-2.0`
- **Assigned Evolution Track**: `Track 1: Direct Template Assimilation (Permissive)`
- **Target Swarm Worker**: `dnk_video_ai_creator`
- **Architectural Directive**: Direct template and component integration is authorized.

## 📁 Core Architecture & Specifications
- **Stack**: `Python`
- **Target Component Target**: `services/dnk_video/ or packages/video-audit-core/`
- **High-Level Purpose**: [CVPR 2026] PersonaLive! : Expressive Portrait Image Animation for Live Streaming

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Swarm Worker Task Delegation
Delegate implementation directly to **`dnk_video_ai_creator`**:
```python
from core.orchestrator.swarm_coordinator import SwarmCoordinator

coordinator = SwarmCoordinator()
res = coordinator.dispatch(
    agent="dnk_video_ai_creator",
    action="assimilate_adapter",
    payload={
        "technology": "GVCLab/PersonaLive",
        "track": "Track 1: Direct Template Assimilation (Permissive)",
        "action": "Implement high-performance streaming animation pipeline and real-time generation contracts."
    }
)
```

### Recipe B: Clean Interface Contract Adoption
Integrate type-safe schemas into your local module:
```python
# Clean-Room Schema derived from PersonaLive
from pydantic import BaseModel, Field

class PersonaliveConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enables feature adapter")
    mode: str = Field(default="auto", description="Execution mode")
```

## ⚠️ Pitfalls & Invariants
1. **[ZERO_ABSOLUTE_PATHS]**: Never hardcode absolute system paths. Always use `./` or `../`.
2. **[MRH_HEADER_INVARIANT]**: Any adapter or component generated from this pattern MUST carry `DNK-STD-0075` MRH header.
3. **[LICENSE_BOUNDARY]**: Respect upstream license notices and attribution.
4. **[CLEAN-ROOM REVERSE-ENGINEERING INVARIANT]**: Direct template adoption authorized under permissive license.
