# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/scripts/sanitize_context_bloat.py"
# purpose: "Script-First Execution utility sanitizing heavy log outputs and preventing LLM context bloat."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import sys


def sanitize_text(text: str, max_lines: int = 50) -> str:
    """
    Truncates large outputs to prevent context bloat for AI agents.
    """
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text

    half = max_lines // 2
    head = lines[:half]
    tail = lines[-half:]
    return "\n".join(head) + f"\n\n... [TRUNCATED {len(lines) - max_lines} LINES TO PREVENT CONTEXT BLOAT] ...\n\n" + "\n".join(tail)


def main() -> None:
    print("🧹 [Playbook PB-001] Sanitize Context Bloat Utility Running...")
    sample_text = "Log line\n" * 200
    cleaned = sanitize_text(sample_text, max_lines=20)
    print(f"✅ Успішно оптимізовано лог: {len(sample_text.splitlines())} рядків -> {len(cleaned.splitlines())} рядків!")


if __name__ == "__main__":
    main()
