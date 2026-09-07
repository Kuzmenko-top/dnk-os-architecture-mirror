# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/adaptive_prompt.py"
# purpose: "Adaptive System Prompt Pruning: Dynamic prompt tier selection and minimal prompt builder."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
Adaptive System Prompt Pruner.

Prunes system prompt overhead based on task complexity (SIMPLE / MEDIUM / COMPLEX),
reducing the base prompt from ~7,500 tokens down to 300 - 1,500 tokens.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ComplexityLevel(str, Enum):
    SIMPLE = "SIMPLE"       # ~300 токенів
    MEDIUM = "MEDIUM"       # ~600 токенів
    COMPLEX = "COMPLEX"     # ~1,500 токенів


# Alias for backwards compatibility
PromptTier = ComplexityLevel


@dataclass
class TaskSpec:
    target_files: int = 1
    estimated_steps: int = 1
    description: str = ""
    max_tool_calls: int = 25


class AdaptivePromptBuilder:
    """
    Generates minimal system prompt based on task complexity.
    """

    BASE_PROMPT = """
    You are Gerych Prime, autonomous AI engineer.
    Follow Zero-Waste Protocol (≤25 tool calls, MASE compliance).
    """

    COMPLEXITY_LEVELS = {
        ComplexityLevel.SIMPLE: {
            "instructions": """
            Execute task efficiently.
            Use file/terminal tools.
            Verify with tests if applicable.
            """,
            "tools_guideline": "Available: file.*, terminal.*, orchestration.*",
            "examples": "",
            "total_tokens": 300,
        },
        ComplexityLevel.MEDIUM: {
            "instructions": """
            You are Gerych Prime, autonomous AI engineer.
            Follow Zero-Waste Protocol (≤25 tool calls, MASE compliance).
            
            Plan before execution.
            Verify with tests after changes.
            Use introspection tools for code analysis.
            """,
            "tools_guideline": "Available: file.*, terminal.*, orchestration.*, introspection.*, cognitive.*",
            "examples": "Example workflow: file.read → terminal.run → file.write → pytest",
            "total_tokens": 600,
        },
        ComplexityLevel.COMPLEX: {
            "instructions": """
            You are Gerych Prime, autonomous AI engineer.
            Follow Zero-Waste Protocol (≤25 tool calls, MASE compliance).
            
            Full protocol:
            1. Triage task complexity
            2. Decompose into atomic slices (≤25 tools per slice)
            3. Execute with verification
            4. Run Master Quality Gate (verify_all.sh)
            5. Commit with MRH header
            
            Use all CORE_TOOLSETS as needed.
            Delegate to Swarm for complex multi-step tasks.
            """,
            "tools_guideline": "All CORE_TOOLSETS enabled: file, terminal, orchestration, introspection, cognitive, security",
            "examples": """
            Example complex task:
            1. dnk_triage_task → SWARM_PARALLEL
            2. dnk_swarm_parallel → delegate to workers
            3. Workers execute in parallel
            4. Aggregate results
            5. verify_all.sh → 100% Green
            6. git commit
            """,
            "total_tokens": 1500,
        },
    }

    def build_prompt(self, task_spec: TaskSpec) -> str:
        complexity = self.estimate_complexity(task_spec)
        template = self.COMPLEXITY_LEVELS[complexity]

        prompt = f"""
        {template['instructions']}
        
        {template['tools_guideline']}
        
        {template['examples']}
        
        Task: {task_spec.description}
        Target files: {task_spec.target_files}
        Budget: {task_spec.max_tool_calls} tool calls
        """

        return prompt

    def estimate_complexity(self, task_spec: TaskSpec) -> ComplexityLevel:
        """
        Estimate task complexity based on:
        - Number of target files
        - Estimated steps
        - Requires Swarm delegation
        """
        if task_spec.target_files <= 2 and task_spec.estimated_steps <= 5:
            return ComplexityLevel.SIMPLE  # ~300 токенів
        elif task_spec.target_files <= 5 and task_spec.estimated_steps <= 15:
            return ComplexityLevel.MEDIUM  # ~600 токенів
        else:
            return ComplexityLevel.COMPLEX  # ~1,500 токенів


# Backwards compatibility and helper functions
def classify_prompt_tier(
    complexity_score: int,
    mode: str = "SOLO",
    domains_count: Optional[Any] = None,
) -> PromptTier:
    if isinstance(domains_count, list):
        d_count = len(domains_count)
    elif isinstance(domains_count, int):
        d_count = domains_count
    else:
        d_count = 1

    if complexity_score <= 3 and d_count <= 1 and mode in ("SOLO", "RESUME_IN_FLIGHT"):
        return PromptTier.SIMPLE
    elif complexity_score <= 8 and d_count <= 2:
        return PromptTier.MEDIUM
    else:
        return PromptTier.COMPLEX


def build_adaptive_prompt(
    tier: PromptTier = PromptTier.SIMPLE,
    task_goal: str = "",
    domains: Optional[List[str]] = None,
    target_files: Optional[List[str]] = None,
    budget_tools: int = 25,
    custom_tool_catalog: Optional[str] = None,
) -> str:
    builder = AdaptivePromptBuilder()
    task_spec = TaskSpec(
        target_files=len(target_files) if target_files else 1,
        estimated_steps=5 if tier == PromptTier.SIMPLE else (12 if tier == PromptTier.MEDIUM else 20),
        description=task_goal or ("Task execution" + (f" for {domains}" if domains else "")),
        max_tool_calls=budget_tools,
    )
    prompt = builder.build_prompt(task_spec)
    if custom_tool_catalog:
        prompt = f"{prompt}\n\n{custom_tool_catalog}"
    return prompt


def estimate_prompt_tokens(prompt_text: str) -> int:
    return max(10, int(len(prompt_text.split()) * 1.3))


def get_prompt_token_savings(prompt_text: str) -> Dict[str, Any]:
    """Calculates token savings vs 15,000 baseline monolithic prompt."""
    baseline = 15000
    prompt_tokens = estimate_prompt_tokens(prompt_text)
    saved = max(0, baseline - prompt_tokens)
    savings_pct = round((saved / baseline) * 100, 1)
    return {
        "baseline_tokens": baseline,
        "prompt_tokens": prompt_tokens,
        "tokens_saved": saved,
        "savings_pct": savings_pct,
    }
