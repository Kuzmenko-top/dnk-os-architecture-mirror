# --- DNK-MRH-HEADER ---
# mrh_id: "references/mcp_slim_guard_meta_tools_protocol.md"
# purpose: "Technical specification and operational guide for MCP Slim Guard 3 Meta-Tools context compression."
# canonical_source: false
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ MCP Slim Guard: Meta-Tools for Context Compression Protocol (SLICE-16.3)

## 1. Problem Statement & Baseline
In large multi-agent systems with 60+ tools, registering full JSON schemas into the system prompt incurs a massive **Context Window Tax**:
- **Baseline Cost**: ~17,500 tokens of schema overhead alone (and ~25,000–45,000 tokens when fully hydrated with examples and constraints).
- **Vulnerability**: Small context window models (8k/16k) overflow immediately, causing prompt truncation, hallucinations, or total call failure.

## 2. The 3 Meta-Tools Pattern
Instead of registering dozens of distinct tools, MCP Slim Guard exposes exactly three universal meta-tools:

```
┌────────────────────────────────────────────────────────┐
│                   LLM Context Window                   │
│   find_tool()  │  call_tool()  │  read_result()        │
└─────────┬───────────────┬────────────────┬─────────────┘
          │               │                │
          ▼               ▼                ▼
   ToolSemanticIndex   ToolRegistry   Sidecar Storage
   (Vector + Fallback) (Validation)   (/tmp/dnk_sidecar)
```

1. **`find_tool(query: str, tags: list[str] = None, limit: int = 5)`**:
   - Discovers tools dynamically via semantic or lexical search.
   - Returns tool names, summaries, tags, and expected parameter schema hints.
2. **`call_tool(tool_name: str, arguments: dict)`**:
   - Lazily resolves the requested tool by name or alias.
   - Validates parameters against the full JSON Schema via `jsonschema`.
   - Executes the underlying tool implementation.
   - Automatically diverts outputs exceeding the safety limit (e.g. >2,000–3,000 chars) to sidecar storage, returning a preview plus a `sidecar_ref`.
3. **`read_result(ref: str, chunk_size: int = 2000, offset: int = 0)`**:
   - Paginates large tool execution payloads on demand without flooding the LLM context window.

## 3. Two-Tier Search Engine (Zero-Dependency Fallback)
`ToolSemanticIndex` implements a dual-mode search to ensure 100% availability across diverse environments:
- **Tier 1 (Dense Vector)**: Uses `sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')` with precomputed cosine similarity embeddings and singleton caching.
- **Tier 2 (Tokenized Fallback)**: If `numpy` or `sentence_transformers` is missing, smoothly falls back to tokenized normalization, alias matching, and Jaccard token overlap.
- **Accuracy**: Delivers 100% recall on core domains (Liquid validation, Video generation, File ops, Canvas state).

## 4. Token Economics Benchmark
- **Full Tool Schemas (60+ tools)**: ~17,500 tokens.
- **MCP Slim Guard Meta-Tools (3 tools)**: ~290 tokens.
- **Schema Reduction**: **98.3% savings**.
- **Overall Request Turn**: Slashed from ~25,000 tokens to ~2,800 tokens (**88.8% reduction**).

## 5. Verification & Test Isolation Invariant
- **Benchmark Suite**: Run `python3 scripts/system/measure_context_tokens.py` to verify schema and prompt budgets.
- **Loop Tracker Isolation**: Test functions exercising hooks or interceptors must dynamically generate session IDs (e.g. `session_id = f"test_{uuid.uuid4().hex[:8]}"`). Never reuse static IDs across tests, as `/tmp/hermes_loop_tracker_<id>.json` will trip the circuit breaker.
