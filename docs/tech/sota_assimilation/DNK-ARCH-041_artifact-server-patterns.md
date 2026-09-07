# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-ARCH-041_artifact-server-patterns.md"
# purpose: "Architectural patterns and Hexagonal design for DNK OS Artifact Server integration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🏛️ DNK Architecture Spec: Artifact Server Patterns (DNK-ARCH-041)

## 1. Hexagonal Ports & Adapters Structure
```
               +---------------------------+
               |  FastAPI Router           |
               |  (/artifacts, /comments)  |
               +-------------+-------------+
                             |
                             v
               +---------------------------+
               |    ArtifactServerPort     |
               | (Abstract Interface Core) |
               +-------------+-------------+
                             |
                             v
               +---------------------------+
               |  DNKArtifactServerAdapter |
               |   - Version History       |
               |   - Comment Threading     |
               |   - Path & Type Guard     |
               +---------------------------+
```

## 2. Invariants & Guarantees
1. **Version Immutability**: Historical versions (v1, v2...) are append-only and cannot be mutated retroactively.
2. **Deterministic Version Sequencing**: Every new revision increments `current_version` by 1 and stamps ISO timestamps.
3. **Decoupled Review Layer**: Comments and annotations target a specific `artifact_id` and `version`, preserving review context across iterations.
