#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/sota_scout_runner.py"
# purpose: "CLI and Automation Runner for Two-Track SOTA Repository Assimilation Pipeline (Scout, License Audit, Skill Gen, Obsidian, TaskDNA)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure DNK_HUB root is on sys.path
HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from core.orchestrator.sota_scout import SOTAScoutEngine, ScoutJobStatus


def setup_logger(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    return logging.getLogger("SOTAScoutRunner")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DNK OS Two-Track SOTA Repository Assimilation Scout Runner"
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="GitHub repository slug or URL (e.g. 'GVCLab/PersonaLive' or 'https://github.com/owner/repo')"
    )
    parser.add_argument(
        "--focus",
        type=str,
        default="",
        help="Comma-separated focus domains (e.g. 'streaming,audio,rendering')"
    )
    parser.add_argument(
        "--track-override",
        type=str,
        choices=["permissive", "clean_room"],
        default=None,
        help="Override automatic license audit track ('permissive' or 'clean_room')"
    )
    parser.add_argument(
        "--enqueue",
        action="store_true",
        help="Enqueue repository to background Scout queue instead of immediate assimilation"
    )
    parser.add_argument(
        "--priority",
        type=int,
        default=5,
        help="Queue priority (1=highest, 10=lowest, default=5)"
    )
    parser.add_argument(
        "--process-queue",
        action="store_true",
        help="Process pending jobs in the Scout queue"
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=3,
        help="Max jobs to process when using --process-queue"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display current Scout queue status and exit"
    )
    parser.add_argument(
        "--sanitize",
        type=str,
        help="Path to code file to sanitize under DNK-STD-0075 and relative path invariant"
    )
    parser.add_argument(
        "--workspace-id",
        type=str,
        default="ws-alpha-001",
        help="Target workspace identifier (default: ws-alpha-001)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )

    args = parser.parse_args()
    logger = setup_logger(args.verbose)

    engine = SOTAScoutEngine(hub_root=HUB_ROOT)

    # 1. Status query
    if args.status:
        status = engine.get_queue_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0

    # 2. Code Sanitization utility
    if args.sanitize:
        target_path = Path(args.sanitize)
        if not target_path.exists():
            logger.error("File not found for sanitization: %s", target_path)
            return 1
        content = target_path.read_text(encoding="utf-8")
        sanitized = engine.sanitize_code(
            code_str=content,
            file_path=str(target_path.relative_to(HUB_ROOT) if target_path.is_relative_to(HUB_ROOT) else target_path),
            purpose=f"Sanitized under DNK-STD-0075 for {target_path.name}"
        )
        target_path.write_text(sanitized, encoding="utf-8")
        logger.info("Successfully sanitized %s under DNK-STD-0075", target_path)
        return 0

    # 3. Process Scout Queue
    if args.process_queue:
        logger.info("Processing Scout queue (max_jobs=%d)...", args.max_jobs)
        processed = engine.process_queue(max_jobs=args.max_jobs)
        logger.info("Processed %d jobs from Scout queue.", len(processed))
        print(json.dumps(processed, indent=2, ensure_ascii=False))
        return 0

    # 4. Enqueue or Direct Assimilation
    if not args.repo:
        logger.error("Must provide --repo, --status, --process-queue, or --sanitize.")
        parser.print_help()
        return 1

    focus_areas = [f.strip() for f in args.focus.split(",") if f.strip()]

    if args.enqueue:
        job = engine.enqueue_repository(
            repo_url=args.repo,
            focus_areas=focus_areas,
            priority=args.priority,
            requested_by="cli_runner",
        )
        logger.info("Enqueued job %s for repo %s (priority %s)", job.get("id"), job.get("repo_url"), job.get("priority"))
        print(json.dumps(job, indent=2, ensure_ascii=False))
        return 0

    # Direct immediate assimilation
    logger.info("Executing immediate SOTA assimilation for %s...", args.repo)
    result = engine.assimilate(
        repo_url=args.repo,
        focus_areas=focus_areas,
        track_override=args.track_override,
        workspace_id=args.workspace_id,
        generate_skill=True,
        generate_obsidian=True,
        sync_scones=True,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
