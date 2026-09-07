#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/task_triage.py"
# purpose: "Autonomous Swarm Triage Engine: Evaluates task complexity, detects technological domains, and automatically routes tasks to SOLO execution or Parallel/Sequential Swarm Delegation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym, Antigravity Mentor & Perplexity Mentor"
# --- END DNK-MRH-HEADER ---

import os
import re
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Literal, Set, Optional

from core.orchestrator.tool_aliases import (
    format_compact_tool_catalog,
    estimate_tool_tokens,
    format_all_tool_summaries,
)
from core.orchestrator.adaptive_prompt import (
    classify_prompt_tier,
    build_adaptive_prompt,
    estimate_prompt_tokens,
    AdaptivePromptBuilder,
    TaskSpec,
)
from core.orchestrator.lazy_tool_loader import LazyToolLoader

HUB_ROOT = Path(__file__).resolve().parent.parent.parent

# Technological domain classification mapping
DOMAIN_PATTERNS = {
    "backend_api": [
        r"\bapps/api/",
        r"\brouters/",
        r"\bFastAPI\b",
        r"\bWebSocket\b",
        r"\buvicorn\b",
        r"\bSQLAlchemy\b",
        r"\bcore/obsidian/",
        r"\bcore/mindmap/",
    ],
    "frontend_canvas": [
        r"\bapps/web/",
        r"\bcomponents/canvas/",
        r"\bReact\b",
        r"\bReact Flow\b",
        r"\bZustand\b",
        r"\bstore/canvasStore\b",
        r"\b\.tsx\b",
        r"\b\.jsx\b",
    ],
    "shopify_ecom": [
        r"\bservices/dnk_shopify/",
        r"\bLiquid\b",
        r"\b\.liquid\b",
        r"\bShopify\b",
        r"\bcheckout_ui\b",
    ],
    "media_video": [
        r"\bservices/dnk_video_ai_creator/",
        r"\bRemotion\b",
        r"\bFFmpeg\b",
        r"\bcomposition\b",
        r"\bvideo_audit\b",
    ],
    "qa_security": [
        r"\btests/",
        r"\btest_",
        r"\b_test\.py\b",
        r"\bverify_all\.sh\b",
        r"\badversarial\b",
        r"\bsecurity_guard\b",
    ],
    "knowledge_docs": [
        r"\bdocs/",
        r"\bObsidian\b",
        r"\bVault\b",
        r"\b\.md\b",
        r"\bADR\b",
    ]
}

# Domain to preferred specialized swarm worker mapping
DOMAIN_WORKER_MAP = {
    "backend_api": "dnk_dev_fullstack",
    "frontend_canvas": "gerych_builder",
    "shopify_ecom": "dnk_shopify",
    "media_video": "dnk_video_ai_creator",
    "qa_security": "gerych_auditor",
    "knowledge_docs": "herich_librarian",
}

# Domain to specialized toolset mapping (Context Window Tax mitigation)
CORE_TOOLSETS = ["file", "terminal", "dnk_orchestration", "dnk_introspection", "dnk_cognitive"]

DOMAIN_TOOLSET_MAP = {
    "backend_api": [],
    "frontend_canvas": ["dnk_canvas"],
    "shopify_ecom": ["dnk_shopify"],
    "media_video": ["dnk_media"],
    "qa_security": ["dnk_security"],
    "knowledge_docs": ["obsidian"],
}

ALL_SPECIALIZED_TOOLSETS = [
    "dnk_shopify",
    "dnk_media",
    "dnk_canvas",
    "dnk_security",
    "browser",
    "computer_use",
    "tts",
    "cronjob",
]


def compute_dynamic_toolsets(domains_detected: List[str], mode: str) -> tuple[List[str], List[str]]:
    """
    Computes enabled and disabled toolsets to eliminate Context Window Tax.
    Prunes irrelevant schemas from system context based on detected task domains.
    """
    enabled = list(CORE_TOOLSETS)
    # In SWARM_PARALLEL mode, Prime is purely orchestrator: domain tools belong strictly to workers
    if mode != "SWARM_PARALLEL":
        for dom in domains_detected:
            for ts in DOMAIN_TOOLSET_MAP.get(dom, []):
                if ts not in enabled:
                    enabled.append(ts)

    disabled = [ts for ts in ALL_SPECIALIZED_TOOLSETS if ts not in enabled]
    return enabled, disabled


def compute_context_optimization(
    complexity_score: int,
    mode: str,
    domains: List[str],
) -> tuple[str, str, int, float]:
    """
    Computes prompt tier, compact catalog, estimated tokens, and savings percentage.
    Baseline unoptimized context: ~24,800 tokens.
    """
    tier = classify_prompt_tier(complexity_score, mode)
    catalog = format_compact_tool_catalog(domains=domains)
    prompt = build_adaptive_prompt(tier=tier, domains=domains, custom_tool_catalog=catalog)
    estimated_tokens = estimate_prompt_tokens(prompt) + 1200  # prompt + memory + lod skills
    baseline_tokens = 24800
    savings = round(max(0.0, (baseline_tokens - estimated_tokens) / baseline_tokens) * 100, 1)
    return tier.value, catalog, estimated_tokens, savings


@dataclass
class TriageSlicePlan:
    slice_id: str
    title: str
    target_domain: str
    assigned_agent: str
    scope_files: List[str]
    parallel_group: int
    depends_on: List[str] = field(default_factory=list)


@dataclass
class TriageResult:
    mode: Literal["SOLO", "SWARM_PARALLEL", "SWARM_SEQUENTIAL", "RESUME_IN_FLIGHT"]
    complexity_score: int
    f_files: int
    d_domains: int
    s_stages: int
    rationale: str
    domains_detected: List[str]
    execution_plan: List[Dict[str, Any]]
    mandatory_directive: str = ""
    enabled_toolsets: List[str] = field(default_factory=list)
    disabled_toolsets: List[str] = field(default_factory=list)
    prompt_tier: str = "SIMPLE"
    compact_tool_catalog: str = ""
    estimated_context_tokens: int = 0
    token_savings_pct: float = 0.0
    system_prompt: str = ""
    estimated_tokens: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def extract_file_paths(text: str) -> List[str]:
    """Extracts explicit file paths mentioned in prompt text."""
    pattern = r'(?:[\w\-\./]+\.(?:py|tsx|ts|jsx|js|json|md|yaml|yml|liquid|sh|html|css))'
    matches = re.findall(pattern, text)
    valid_prefixes = (
        "core/", "apps/", "services/", "tests/", "scripts/", "packages/",
        "docs/", "config/", "./"
    )
    cleaned = []
    for m in matches:
        clean = m.lstrip("./").strip("`'\"")
        if any(clean.startswith(p) or f"/{p}" in clean for p in valid_prefixes):
            if clean not in cleaned:
                cleaned.append(clean)
    return cleaned


def detect_domains(text: str, file_paths: List[str]) -> List[str]:
    """Detects technological domains from file paths and semantic text cues."""
    detected = set()
    combined_content = f"{text} " + " ".join(file_paths)

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, combined_content, re.IGNORECASE):
                detected.add(domain)
                break

    return sorted(list(detected))


def count_stages_or_slices(text: str) -> tuple[int, List[Dict[str, Any]]]:
    """Extracts slice definitions, section bodies, and count from markdown prompt."""
    slice_pattern = re.compile(
        r"(?im)^\s*(?:#{2,4}\s*|\*{1,2}\s*)(?:слайс|slice)\s*(\d+[\.\-]\d+|\d+)[:\s\-]*([^\n\r]+)?",
        re.IGNORECASE
    )
    matches = list(slice_pattern.finditer(text))
    slices = []
    if matches:
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            clean_sid = m.group(1).replace(".", "-")
            clean_title = (m.group(2) or f"Slice {clean_sid}").strip(" *`_")
            body = text[start:end]
            slices.append({"slice_id": clean_sid, "title": clean_title, "body": body})
    else:
        # Check numbered table rows or list items
        numbered_pattern = re.compile(
            r"(?m)^\s*(?:-\s*|\d+\.\s+)\*\*?(?:Крок|Слайс|Step|Stage)\s*(\d+[\.\-]\d+|\d+)\*?[:\s\-]*([^\n\r]+)?",
            re.IGNORECASE
        )
        n_matches = list(numbered_pattern.finditer(text))
        for i, m in enumerate(n_matches):
            start = m.end()
            end = n_matches[i + 1].start() if i + 1 < len(n_matches) else len(text)
            clean_sid = m.group(1).replace(".", "-")
            clean_title = (m.group(2) or f"Step {clean_sid}").strip(" *`_")
            body = text[start:end]
            slices.append({"slice_id": clean_sid, "title": clean_title, "body": body})

    stage_count = max(len(slices), 1)
    return stage_count, slices


def dnk_triage_task(goal_or_prompt: str) -> TriageResult:
    """
    Evaluates task complexity and determines whether Gerych should execute SOLO
    or orchestrate SWARM (PARALLEL or SEQUENTIAL).

    Formula: C = F_files + (2 * D_domains) + (3 * S_stages)
    Threshold:
      C <= 3: SOLO
      C > 3:  SWARM (PARALLEL if disjoint domains, else SEQUENTIAL)
    """
    if not goal_or_prompt or not goal_or_prompt.strip():
        en, dis = compute_dynamic_toolsets([], "SOLO")
        tier, cat, est_tok, sav = compute_context_optimization(0, "SOLO", [])
        return TriageResult(
            mode="SOLO",
            complexity_score=0,
            f_files=0,
            d_domains=0,
            s_stages=0,
            rationale="Empty prompt - default to SOLO lightweight mode.",
            domains_detected=[],
            execution_plan=[],
            mandatory_directive="Execute directly as SOLO.",
            enabled_toolsets=en,
            disabled_toolsets=dis,
            prompt_tier=tier,
            compact_tool_catalog=cat,
            estimated_context_tokens=est_tok,
            token_savings_pct=sav,
        )

    file_paths = extract_file_paths(goal_or_prompt)
    f_files = len(file_paths)

    domains = detect_domains(goal_or_prompt, file_paths)
    d_domains = max(len(domains), 1)

    s_stages, slices_meta = count_stages_or_slices(goal_or_prompt)

    # Complexity formula
    complexity = f_files + (2 * d_domains) + (3 * s_stages)

    # In-Flight Compaction Resume Detection
    # If declared [NEW] target files already exist on disk (>100 bytes), or compaction markers exist,
    # route to RESUME_IN_FLIGHT to eliminate redundant swarm re-dispatch loops.
    declared_new_files = re.findall(r'\[NEW\]\s+([^\s\n\]]+)', goal_or_prompt)
    has_compaction_marker = any(
        m in goal_or_prompt for m in ("[CONTEXT COMPACTION", "Earlier turns were compacted")
    )
    hub_root = Path(__file__).resolve().parent.parent.parent
    existing_new_count = sum(
        1 for nf in declared_new_files
        if (hub_root / nf).is_file() and (hub_root / nf).stat().st_size > 100
    )
    is_in_flight_resume = (
        (len(declared_new_files) >= 2 and existing_new_count >= max(int(len(declared_new_files) * 0.6), 2))
        or (has_compaction_marker and existing_new_count > 0)
    )

    if is_in_flight_resume:
        en, dis = compute_dynamic_toolsets(domains, "RESUME_IN_FLIGHT")
        tier, cat, est_tok, sav = compute_context_optimization(1, "RESUME_IN_FLIGHT", domains)
        return TriageResult(
            mode="RESUME_IN_FLIGHT",
            complexity_score=1,
            f_files=f_files,
            d_domains=1,
            s_stages=1,
            rationale=(
                f"In-Flight Task Resumption: {existing_new_count}/{len(declared_new_files)} target [NEW] files "
                "already exist on disk with code. Bypassing parallel swarm re-dispatch to prevent churn. "
                "Proceeding directly to refinement, verification, and testing."
            ),
            domains_detected=domains,
            mandatory_directive=(
                "⚡ IN-FLIGHT RESUME: Target files already exist on disk. "
                "Do NOT re-dispatch swarm. Run verification command (`pytest` or `verify_all.sh`) and report completion."
            ),
            execution_plan=[{
                "slice_id": "resume-1",
                "title": "In-Flight Verification & Finalization",
                "target_domain": domains[0] if domains else "general",
                "assigned_agent": "gerych_prime",
                "scope_files": file_paths,
                "parallel_group": 1,
                "depends_on": []
            }],
            enabled_toolsets=en,
            disabled_toolsets=dis,
            prompt_tier=tier,
            compact_tool_catalog=cat,
            estimated_context_tokens=est_tok,
            token_savings_pct=sav,
        )

    # Solo threshold: single domain, 1-2 files, single stage
    if complexity <= 3 or (f_files <= 2 and d_domains <= 1 and s_stages == 1):
        mode = "SOLO"
        rationale = f"Lightweight task (Score {complexity} <= 3, {f_files} files, {d_domains} domain). Gerych executes directly."
        en, dis = compute_dynamic_toolsets(domains, mode)
        tier, cat, est_tok, sav = compute_context_optimization(complexity, mode, domains)
        return TriageResult(
            mode=mode,
            complexity_score=complexity,
            f_files=f_files,
            d_domains=d_domains,
            s_stages=s_stages,
            rationale=rationale,
            domains_detected=domains,
            mandatory_directive="Lightweight task (Score <= 3). Gerych executes directly within <= 15 tool calls.",
            execution_plan=[{
                "slice_id": "solo-1",
                "title": "Solo Execution Slice",
                "target_domain": domains[0] if domains else "general",
                "assigned_agent": "gerych_prime",
                "scope_files": file_paths,
                "parallel_group": 1,
                "depends_on": []
            }],
            enabled_toolsets=en,
            disabled_toolsets=dis,
            prompt_tier=tier,
            compact_tool_catalog=cat,
            estimated_context_tokens=est_tok,
            token_savings_pct=sav,
        )

    # Swarm Mode determination
    execution_plan: List[TriageSlicePlan] = []
    
    if slices_meta:
        # We have explicit slices
        for idx, sm in enumerate(slices_meta):
            sid = sm["slice_id"]
            title = sm["title"]
            body = sm.get("body", "")

            # Extract files specific to this slice section
            section_files = extract_file_paths(f"{title}\n{body}")
            slice_files = section_files if section_files else [
                f for f in file_paths
                if sid.replace("-", ".") in f or any(kw in f.lower() for kw in title.lower().split()[:2])
            ]
            if not slice_files and file_paths:
                slice_files = file_paths[idx:idx+2] if idx < len(file_paths) else []

            slice_domains = detect_domains(f"{title}\n{body} " + " ".join(slice_files), slice_files)
            primary_domain = slice_domains[0] if slice_domains else (domains[idx % len(domains)] if domains else "backend_api")
            worker = DOMAIN_WORKER_MAP.get(primary_domain, "gerych_builder")

            # Check if this is an integration / e2e / audit slice
            is_join_barrier = (
                any(w in title.lower() or w in sid.lower() for w in ("e2e", "audit", "verify", "gate", "test_sync", "test"))
                or idx == len(slices_meta) - 1
            )

            if is_join_barrier and len(slices_meta) > 1:
                group = 2
                depends = [s["slice_id"] for s in slices_meta[:idx]]
                if any(w in title.lower() for w in ("audit", "verify", "test", "e2e")):
                    worker = "gerych_auditor"
            else:
                group = 1
                depends = []

            execution_plan.append(
                TriageSlicePlan(
                    slice_id=sid,
                    title=title,
                    target_domain=primary_domain,
                    assigned_agent=worker,
                    scope_files=slice_files,
                    parallel_group=group,
                    depends_on=depends
                )
            )
    else:
        # Synthesize slices based on detected domains
        for idx, dom in enumerate(domains):
            worker = DOMAIN_WORKER_MAP.get(dom, "gerych_builder")
            dom_files = [f for f in file_paths if any(re.search(p, f) for p in DOMAIN_PATTERNS.get(dom, []))]
            execution_plan.append(
                TriageSlicePlan(
                    slice_id=f"auto-{idx+1}",
                    title=f"Subtask for {dom}",
                    target_domain=dom,
                    assigned_agent=worker,
                    scope_files=dom_files,
                    parallel_group=1,
                    depends_on=[]
                )
            )

    # Check if we have parallel groups in Group 1
    group_1_items = [p for p in execution_plan if p.parallel_group == 1]
    if len(group_1_items) > 1:
        mode = "SWARM_PARALLEL"
        rationale = (
            f"Cross-domain swarm task (Complexity Score {complexity} > 3). "
            f"Detected {d_domains} domains across {f_files} files with {len(group_1_items)} parallelizable workers in Group 1."
        )
        directive = (
            "🚨 STRICT DISPATCH LAW: Mode is SWARM_PARALLEL. You MUST invoke dnk_swarm_parallel(tasks_json=...) next. "
            "Solo file mutations and excessive solo exploration (>3 reads) are blocked by the Swarm Circuit Breaker."
        )
    else:
        mode = "SWARM_SEQUENTIAL"
        rationale = (
            f"Sequential multi-step task (Complexity Score {complexity} > 3). "
            f"Requires phased handoffs across {len(execution_plan)} stages."
        )
        directive = "Sequential phased handoffs via dnk_swarm_dispatch or atomic slices (MASE <= 25 tool calls)."

    en, dis = compute_dynamic_toolsets(domains, mode)
    tier, cat, est_tok, sav = compute_context_optimization(complexity, mode, domains)

    # Adaptive System Prompt Pruning & Lazy Tool Summaries
    prompt_builder = AdaptivePromptBuilder()
    task_spec = TaskSpec(
        target_files=max(1, f_files),
        estimated_steps=max(1, complexity * 2),
        description=goal_or_prompt,
        max_tool_calls=25,
    )
    base_sys_prompt = prompt_builder.build_prompt(task_spec)
    context_toolsets = list(en)
    for dom in domains:
        for ts in DOMAIN_TOOLSET_MAP.get(dom, []):
            if ts not in context_toolsets:
                context_toolsets.append(ts)
    tool_summary = format_all_tool_summaries(context_toolsets)
    full_system_prompt = f"{base_sys_prompt.strip()}\n\n{tool_summary}\n\n(Use tool name to get full schema on demand)"
    est_prompt_tokens = round(len(full_system_prompt.split()) * 1.3, 1)

    return TriageResult(
        mode=mode,
        complexity_score=complexity,
        f_files=f_files,
        d_domains=d_domains,
        s_stages=s_stages,
        rationale=rationale,
        domains_detected=domains,
        mandatory_directive=directive,
        execution_plan=[asdict(p) for p in execution_plan],
        enabled_toolsets=en,
        disabled_toolsets=dis,
        prompt_tier=tier,
        compact_tool_catalog=cat,
        estimated_context_tokens=est_tok,
        token_savings_pct=sav,
        system_prompt=full_system_prompt,
        estimated_tokens=est_prompt_tokens,
    )


def triage_task(prompt: str) -> Dict[str, Any]:
    """
    Evaluates task complexity, routes execution mode, and constructs
    minimal adaptive prompt with lazy tool summaries and Git Context Controller.
    """
    import uuid
    from core.orchestrator.git_context_controller import GitContextController
    from core.orchestrator.mcp_slim_guard import MCPSlimGuard

    res = dnk_triage_task(prompt)
    triage_result = res.to_dict()

    gcc = GitContextController()
    is_experiment = any(kw in prompt.lower() for kw in ["experiment", "refactor", "try", "test", "експеримент"])

    adaptive_prompt = triage_result.get("system_prompt") or f"Task execution plan for {res.mode}"

    if is_experiment:
        branch_id = gcc.create_branch(f"experiment-{uuid.uuid4()}")
        gcc.checkout(branch_id)
        system_prompt = f"""{adaptive_prompt}

Context Branch: {branch_id} (isolated experiment)
- If successful: merge to main as summary (500 tokens)
- If failed: discard (0 tokens)

Available tools (meta-tools):
1. find_tool(query: str, top_k: 5) → List[str]
2. call_tool(name: str, args: Dict) → str
3. read_result(ref: str, chunk_size: 1000) → str

Task: {prompt}"""
    else:
        system_prompt = f"""{adaptive_prompt}

Available tools (meta-tools):
1. find_tool(query: str, top_k: 5) → List[str]
2. call_tool(name: str, args: Dict) → str
3. read_result(ref: str, chunk_size: 1000) → str

Task: {prompt}"""

    mcp_guard = MCPSlimGuard()
    mcp_guard.context_controller = gcc

    return {
        **triage_result,
        "system_prompt": system_prompt,
        "estimated_tokens": int(len(system_prompt.split()) * 1.3),
        "gcc": gcc,
        "is_experiment": is_experiment,
        "mcp_guard": mcp_guard,
    }


def dnk_triage_task_json(goal_or_prompt: str) -> str:
    """Returns JSON string format suitable for LLM tool output."""
    res = dnk_triage_task(goal_or_prompt)
    return json.dumps(res.to_dict(), indent=2, ensure_ascii=False)


def get_slim_guard_context(goal_or_prompt: str) -> Dict[str, Any]:
    """
    Returns MCP Slim Guard meta-tools context (<800 tokens) for a triaged task.
    Replaces upfront schemas with find_tool, call_tool, read_result.
    """
    from core.orchestrator.mcp_slim_guard import MCPSlimGuard
    guard = MCPSlimGuard()
    schema = guard.get_meta_tools_schema()
    return {
        "mode": "MCP_SLIM_GUARD",
        "meta_tools": [t["name"] for t in schema["tools"]],
        "meta_tools_schema": schema,
        "token_estimate": 150,
        "savings_vs_baseline": "99.1%",
    }


if __name__ == "__main__":
    import sys
    test_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Етап 11.3: Obsidian Vault Sync"
    print(dnk_triage_task_json(test_text))
