---
name: "managed_deepagents_assimilated"
description: "SOTA indices and maps for LangChain Managed Deep Agents assimilation."
version: "1.0.0"
category: "research"
assimilated_at: "2026-08-10"
---

# 🌐 Managed Deep Agents (MDA) Assimilation Index

Meta-index tracking the architecture, contracts, and security of sandboxed runtimes.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../../docs/reports/rd_assimilation/managed_deepagents/RN-002_managed-deepagents-research.md)**
   - Researched abstractions (Docker Runtime, Sandbox, CLI lifecycle) and verification matrix.

2. **[Sandbox Architecture Specification](../../docs/tech/specs/DNK-ARCH-002_agent-sandbox-runtime.md)**
   - Subagent sandbox topologies (Rick, Yuriy, Cas) and Supervisor-to-Sandbox async queue design.

3. **[Component Interfaces & Contracts](../../docs/tech/specs/DNK-COMP-002_isolated-fs-contracts.md)**
   - Type-safe Python Pydantic structures, TS-contracts, and error definitions (PathTraversalError).

4. **[Egress and Sandbox Security Standards](../../docs/tech/standards/DNK-SEC-002_sandbox-network-egress.md)**
   - `sandbox_runner` topology, Calico network policies, iptables rules, and anonymous Volume Masking.

5. **[SOTA Blueprint](../../docs/tech/standards/DNK-SOTA-001_managed-deepagents-blueprint-hygiene.md)**
   - Clean-room SOTA standards for host path hygiene, unvalidated disclaimers, and automated test gates.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Starting Sandbox Runner with Calico Egress Policies

**Goal:** Securely launch a child agent container (e.g. Rick/Yuriy/Cas) with full network drop constraints.

- Use the topology schema in `DNK-ARCH-002_agent-sandbox-runtime.md` to define sandbox boundaries.
- Set up Docker Compose block with anonymous volume masking per `DNK-SEC-002_sandbox-network-egress.md`:
  ```yaml
  volumes:
    - /app/node_modules
    - /app/.next
  ```
- Block host directory traversal using relative environment parameters in Python.

### Recipe B: Intercepting Traversal in Isolated Filesystem Operations

**Goal:** Enforce path safety checks on subagent workspace filesystem commands.

- Subclass the contract `DNKIsolatedFileSystem` from `DNK-COMP-002_isolated-fs-contracts.md`.
- Implement standard verification and throw typed errors on breaches:
  ```python
  from core.exceptions import PathTraversalError
  import pathlib
  
  def safe_read(workspace: str, target_path: str) -> str:
      resolved = pathlib.Path(workspace).joinpath(target_path).resolve()
      if not resolved.is_relative_to(pathlib.Path(workspace).resolve()):
          raise PathTraversalError("Path traversal violation blocked!")
      return resolved.read_text(encoding="utf-8")
  ```
