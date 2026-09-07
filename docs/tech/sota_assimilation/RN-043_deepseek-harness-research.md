# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/RN-043_deepseek-harness-research.md"
# purpose: "Research Note: Deep Analysis of deepseek-ai/deepseek-harness Radical Modularity & PTC"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🔬 Research Note RN-043: DeepSeek Harness (`dsh`) Architecture & Innovation

## 1. Upstream Metadata
- **Repository**: `deepseek-ai/deepseek-harness`
- **Identity**: DeepSeek Harness (`dsh`) — *"Everything is a Plugin"*
- **License**: MIT (Track 1 Permissive Adaptation)
- **Key Foundations**: Cordis microkernel, spatiotemporal reversible contexts, PTC runtime, OS Sandboxing (Landlock/Seatbelt).

## 2. Core Breakthroughs
1. **5-Stage Guarded Execution Waterfall**:
   - Every tool call runs across `pre_execute -> guard -> around_execute -> post_execute -> observe`.
   - Invariant guards cannot be overridden by outer plugins or prompt injections.
2. **Programmatic Tool Calling (PTC)**:
   - Exposes a dynamic, safe code execution environment with typed in-memory SDK.
   - Eliminates 10-turn sequential LLM round-trips by running iterative loops and parallel tool calls in 1 single step.
3. **Context Diet & Pressure Reduction**:
   - Symmetric head-tail truncation prevents runaway context token bloat from large tool outputs before hitting the model context window.
