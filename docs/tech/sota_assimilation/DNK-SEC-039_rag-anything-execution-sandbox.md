# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-SEC-039_rag-anything-execution-sandbox.md"
# purpose: "Security Sandbox & Hardening: Path Traversal Defense, SpendGuard Limits, and AST Sanitization for Multimodal RAG."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🛡️ DNK-SEC-039: Multimodal RAG Security & Sandbox Hardening

## 1. Path Traversal & File Injection Defense
Document ingestion accepts file paths for markdown and asset analysis. To prevent Local File Inclusion (LFI) and traversal attacks:
- All input paths pass through `_sanitize_path(file_path)`:
  - Normalization via `os.path.normpath`.
  - Rejection with `ValueError("Security Alert: Path traversal detected...")` if path begins with `..` or contains parent directory traversal sequences (`/../`).
  - Size validation against `max_file_size_mb` (default: 25MB) prior to disk reading.

## 2. SpendGuard VLM Budget Protection
Multimodal VLM queries incur significant token consumption per high-resolution image or complex layout:
- Ingestion tracks cumulative spend.
- `query_multimodal` computes token cost per image ($0.002) and verifies that `_cumulative_spend_usd + cost <= spendguard_budget_usd`.
- Exceeding the threshold raises a fail-closed `RuntimeError` / HTTP 429 rather than triggering unbounded LLM provider bills.

## 3. LaTeX / Math AST Injection Defense
Mathematical equations processed by `DNKEquationProcessor` are sanitized to prevent shell escaping or command injection during downstream rendering:
- Strips delimiters (`$`, `$$`).
- Extracts strictly whitelisted tokens (ASCII single letters and valid LaTeX command macros matching `\\[a-zA-Z]+`).
- Prohibits dangerous raw shell or file inclusion commands (`\input`, `\write18`, `\immediate`).

## 4. Quality & Security Verification Gate
All components are audited under `tests/rag/test_rag_anything_adapter.py` and comply with:
- Zero hardcoded secrets / tokens.
- Parameterized safe inputs.
- 100% Green test suite execution.
