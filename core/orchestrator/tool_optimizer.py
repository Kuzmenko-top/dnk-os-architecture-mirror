#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tool_optimizer.py"
# purpose: "Tool Schema & Description Compiler/Optimizer for Google Gemini Function Calling, assimilated from Soup."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("dnk_tool_optimizer")


@dataclass
class ToolDefect:
    tool_name: str
    parameter: Optional[str]
    defect_type: str  # "vague_description", "missing_type", "overlap", "missing_required"
    severity: str     # "CRITICAL", "WARNING"
    message: str


@dataclass
class OptimizationResult:
    original_tools_count: int
    defects_found: List[ToolDefect]
    optimized_tools: List[Dict[str, Any]]
    optimizations_applied: List[str]
    is_ready_for_frontier_gemini: bool


class ToolSchemaOptimizer:
    """Audits and refines tool definitions (JSON-Schema / OpenAPI specs) to maximize
    Google Gemini function-calling precision and eliminate tool confusion.
    Assimilated from MakazhanAlpamys/Soup compile-tools pattern.
    """

    MIN_DESCRIPTION_LENGTH = 15
    VAGUE_TERMS = {"data", "input", "param", "value", "stuff", "thing", "args"}

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def audit_and_optimize(
        self,
        tools: List[Dict[str, Any]],
        auto_heal: bool = True,
    ) -> OptimizationResult:
        """Audits tool list for semantic ambiguity and structural defects, returning
        optimized definitions tailored for Google Gemini / Frontier function calling.
        """
        defects: List[ToolDefect] = []
        optimizations: List[str] = []
        optimized_tools = copy.deepcopy(tools)

        seen_names: Set[str] = set()
        descriptions: Dict[str, str] = {}

        for tool_idx, tool in enumerate(optimized_tools):
            name = tool.get("name", f"tool_{tool_idx}")

            # 1. Duplicate tool names
            if name in seen_names:
                defects.append(
                    ToolDefect(
                        tool_name=name,
                        parameter=None,
                        defect_type="duplicate_name",
                        severity="CRITICAL",
                        message=f"Duplicate tool declaration for '{name}'",
                    )
                )
            seen_names.add(name)

            # 2. Tool-level description check
            desc = tool.get("description", "").strip()
            descriptions[name] = desc.lower()

            if len(desc) < self.MIN_DESCRIPTION_LENGTH:
                defects.append(
                    ToolDefect(
                        tool_name=name,
                        parameter=None,
                        defect_type="vague_description",
                        severity="WARNING",
                        message=f"Tool description for '{name}' is too brief ({len(desc)} chars). Needs >= {self.MIN_DESCRIPTION_LENGTH}.",
                    )
                )
                if auto_heal:
                    new_desc = f"Executes autonomous operation: {name.replace('_', ' ').capitalize()} within the system."
                    tool["description"] = new_desc
                    optimizations.append(f"Auto-expanded description for tool '{name}'")

            # 3. Parameters inspection
            params = tool.get("parameters", {})
            properties = params.get("properties", {})
            required_set = set(params.get("required", []))

            for prop_name, prop_meta in properties.items():
                p_type = prop_meta.get("type")
                if not p_type:
                    defects.append(
                        ToolDefect(
                            tool_name=name,
                            parameter=prop_name,
                            defect_type="missing_type",
                            severity="CRITICAL",
                            message=f"Parameter '{prop_name}' in tool '{name}' lacks explicit 'type'.",
                        )
                    )
                    if auto_heal:
                        prop_meta["type"] = "string"
                        optimizations.append(f"Inferred fallback type 'string' for '{name}.{prop_name}'")

                p_desc = prop_meta.get("description", "").strip()
                if not p_desc or p_desc.lower() in self.VAGUE_TERMS:
                    defects.append(
                        ToolDefect(
                            tool_name=name,
                            parameter=prop_name,
                            defect_type="vague_description",
                            severity="WARNING",
                            message=f"Parameter '{prop_name}' in tool '{name}' has vague or empty description '{p_desc}'.",
                        )
                    )
                    if auto_heal:
                        prop_meta["description"] = f"The {prop_name.replace('_', ' ')} parameter for {name}."
                        optimizations.append(f"Enriched description for '{name}.{prop_name}'")

        # 4. Semantic Overlap Check between tool descriptions
        tool_names = list(descriptions.keys())
        for i in range(len(tool_names)):
            for j in range(i + 1, len(tool_names)):
                n1, n2 = tool_names[i], tool_names[j]
                d1, d2 = descriptions[n1], descriptions[n2]
                words1 = set(re_tokenize(d1))
                words2 = set(re_tokenize(d2))
                if words1 and words2:
                    intersection = words1.intersection(words2)
                    jaccard = len(intersection) / len(words1.union(words2))
                    if jaccard > 0.75:
                        defects.append(
                            ToolDefect(
                                tool_name=f"{n1} <-> {n2}",
                                parameter=None,
                                defect_type="overlap",
                                severity="WARNING",
                                message=f"High description overlap ({jaccard:.2f}) between '{n1}' and '{n2}'. May cause Gemini tool confusion.",
                            )
                        )

        critical_defects = [d for d in defects if d.severity == "CRITICAL"]
        is_ready = len(critical_defects) == 0 if not auto_heal else True

        return OptimizationResult(
            original_tools_count=len(tools),
            defects_found=defects,
            optimized_tools=optimized_tools,
            optimizations_applied=optimizations,
            is_ready_for_frontier_gemini=is_ready,
        )


def re_tokenize(text: str) -> List[str]:
    import re
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    stopwords = {"the", "and", "for", "with", "from", "that", "this", "tool", "executes", "runs"}
    return [t for t in tokens if t not in stopwords]
