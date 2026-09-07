#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/auto_task_spec.py"
# purpose: "CLI tool for Auto-Task-Spec Generation: Converts unstructured user requests into standardized MASE Task Specs v2.5."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import sys
import json
import argparse
from pathlib import Path

# Ensure repo root is on PYTHONPATH
HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from core.orchestrator.task_spec_generator import (
    should_auto_spec,
    auto_generate_task_spec,
    extract_task_title,
    get_next_slice_number,
    save_task_spec
)
from core.orchestrator.task_triage import dnk_triage_task


def main():
    parser = argparse.ArgumentParser(description="Auto-Task-Spec Generator for DNK OS & Gerych Prime")
    parser.add_argument("query", nargs="*", help="User natural language prompt")
    parser.add_argument("--query", "-q", dest="query_opt", help="Prompt string alternative")
    parser.add_argument("--check", action="store_true", help="Only check if prompt should trigger auto-spec")
    parser.add_argument("--slice", dest="slice_num", help="Override slice number (e.g. 13.3)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument("--output", "-o", help="Write generated spec to file path")

    args = parser.parse_args()

    # Collect query
    raw_query = args.query_opt or (" ".join(args.query) if args.query else "")
    if not raw_query and not sys.stdin.isatty():
        raw_query = sys.stdin.read().strip()

    if not raw_query:
        if args.check:
            sys.exit(1)
        print("Error: No query provided.", file=sys.stderr)
        sys.exit(2)

    needs_spec = should_auto_spec(raw_query)

    if args.check:
        if needs_spec:
            print("AUTO_SPEC_NEEDED")
            sys.exit(0)
        else:
            print("NO_AUTO_SPEC_NEEDED")
            sys.exit(1)

    triage_res = dnk_triage_task(raw_query)
    slice_no = args.slice_num or get_next_slice_number()
    spec = auto_generate_task_spec(raw_query, triage_result=triage_res, slice_number=slice_no)
    saved_paths = save_task_spec(spec, extract_task_title(raw_query), slice_no)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(spec, encoding="utf-8")

    if args.json:
        payload = {
            "should_auto_spec": needs_spec,
            "slice_number": slice_no,
            "title": extract_task_title(raw_query),
            "mode": triage_res.mode,
            "complexity_score": triage_res.complexity_score,
            "saved_paths": saved_paths,
            "spec": spec
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"✨ Task Spec v2.5 generated & saved:")
        for k, v in saved_paths.items():
            print(f"  • {k}: {v}")
        print("\n" + "="*80 + "\n")
        print(spec)


if __name__ == "__main__":
    main()
