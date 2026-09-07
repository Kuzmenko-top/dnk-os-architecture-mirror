---
name: "dnk-prime-agent-rlm-assimilation"
description: "Recursive Language Model (RLM), Continual Harness, and Smart Compaction from Prime Agent"
version: "2.0.0"
category: "devops"
assimilated_at: "2026-08-10"
---

# 🌐 Prime Agent RLM & Harness Assimilation Index

Meta-index tracking RLM, Continual Harness, and Context Compaction specs.

## 📁 Core Specifications

1. **[Architecture Specification](../../docs/tech/specs/DNK-ARCH-003_prime-agent-rlm.md)**
   - Persistent IPython kernels, control-channel ZeroMQ, Continual Harness, and Smart Context Compaction.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Asynchronous Subagent Spawning (Non-blocking)

**Goal:** Spawn a sandboxed subagent asynchronously without blocking Gerych's main reasoning thread.

- Use the RLM spawn interface defined in `DNK-ARCH-003_prime-agent-rlm.md`:
  ```python
  # Async delegator
  handle = await rlm.spawn("Scan for credentials", name="review-agent")
  print("Spawned worker ID:", handle.session_id)
  
  # Await completion on-demand
  result = await handle.wait()
  ```

### Recipe B: Safe Context Compaction Slicing

**Goal:** Cleanly compact history tokens without severing tool call connections.

- Implement cutting points restricted strictly to user/assistant bounds per `DNK-ARCH-003_prime-agent-rlm.md`:
  ```python
  def find_safe_cut_index(messages):
      # Traverse backward, find User/Assistant boundaries, avoid separating Tool and Tool Result!
      for idx, msg in enumerate(reversed(messages)):
          if msg.role in ["user", "assistant"] and not msg.is_tool_bound:
              return len(messages) - idx
      return 0
  ```
