#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/validate_prompt.py"
# purpose: "Zero-Waste Prompt Validator: Intercepts monolithic multi-slice prompts before Hermes/Gerych execution to enforce MASE (DNK-STD-0080)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
import re
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


def extract_prompt(argv: list[str]) -> str:
    """Extracts prompt text from gerych CLI arguments."""
    if not argv:
        return ""

    # Check for -z or --prompt flags
    for i, arg in enumerate(argv):
        if arg in ("-z", "--prompt") and i + 1 < len(argv):
            return argv[i + 1]

    # Check for raw string arguments that are not flags
    non_flag_args = [a for a in argv if not a.startswith("-")]
    if non_flag_args:
        return " ".join(non_flag_args)

    return ""


def validate_prompt(prompt_text: str) -> tuple[bool, str]:
    """Validates that a prompt conforms to Mandatory Atomic Slice Execution (MASE)."""
    if not prompt_text.strip():
        return True, ""

    # If explicitly bypassed by environment variable
    if os.environ.get("DNK_ALLOW_MULTI_SLICE", "").strip().lower() in ("1", "true", "yes"):
        return True, ""

    # Detect multi-slice headers
    slice_pattern = re.compile(
        r"(?i)(?:#{2,4}\s*|\*{1,2}\s*)(?:слайс|slice)\s*(\d+[\.\-]\d+|\d+)",
        re.IGNORECASE
    )
    matches = slice_pattern.findall(prompt_text)

    # Filter unique slice identifiers
    unique_slices = list(dict.fromkeys(matches))

    if len(unique_slices) > 1:
        slices_str = ", ".join(f"Slice {s}" for s in unique_slices)
        error_msg = (
            f"\n\033[91m{'=' * 80}\n"
            f"🛑 DNK OS ZERO-WASTE PROTOCOL VIOLATION (DNK-STD-0080 / MASE)\n"
            f"{'=' * 80}\033[0m\n"
            f"⚠️  Detected monolithic multi-slice prompt containing {len(unique_slices)} slices: [{slices_str}].\n\n"
            f"⚡ Invariant: 1 Gerych Session = 1 Atomic Slice (≤ 25 tool calls).\n"
            f"Attempting multi-slice execution in a single turn causes iteration budget exhaustion (90/90 cut-off)!\n\n"
            f"\033[96m💡 RECOMMENDED RESOLUTION:\033[0m\n"
            f"  1. Use the Zero-Waste Runner to execute slices one-by-one:\n"
            f"     python3 scripts/system/zero_waste_runner.py --step\n"
            f"  2. Or feed ONLY ONE slice to Gerych at a time.\n"
            f"  3. If you intentionally wish to bypass this guard, set:\n"
            f"     export DNK_ALLOW_MULTI_SLICE=1\n"
            f"\033[91m{'=' * 80}\033[0m\n"
        )
        return False, error_msg

    return True, ""


def main():
    prompt = extract_prompt(sys.argv[1:])
    valid, err = validate_prompt(prompt)
    if not valid:
        sys.stderr.write(err)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
