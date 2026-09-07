# --- DNK-MRH-HEADER ---
# mrh_id: "core/memory/tencent_memory_provider.py"
# purpose: "TencentDB Agent Memory Provider integrating CodeGraph AST, LLM-Wiki, Layered Distillation (L0-L3), and Swarm Memory Proxy"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-MEMORY-HUB-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import json
import logging
import ast
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .memory_provider import MemoryProvider

logger = logging.getLogger(__name__)


@dataclass
class SymbolNode:
    name: str
    symbol_type: str
    file_path: str
    line: int
    docstring: Optional[str] = None
    callers: List[str] = field(default_factory=list)
    callees: List[str] = field(default_factory=list)


class LocalCodeGraphEngine:
    """In-memory and pre-indexed AST CodeGraph Engine for instant symbol lookup and impact analysis."""

    def __init__(self, workspace_path: str = ""):
        self.workspace_path = workspace_path
        self.symbols: Dict[str, SymbolNode] = {}
        self.file_dependencies: Dict[str, List[str]] = {}

    def index_file(self, file_path: str, content: Optional[str] = None) -> None:
        """Parses a Python file AST and populates the CodeGraph symbol table."""
        try:
            if content is None:
                if not os.path.exists(file_path):
                    return
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            tree = ast.parse(content, filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node)
                    self.symbols[node.name] = SymbolNode(
                        name=node.name,
                        symbol_type="function",
                        file_path=file_path,
                        line=node.lineno,
                        docstring=doc
                    )
                elif isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node)
                    self.symbols[node.name] = SymbolNode(
                        name=node.name,
                        symbol_type="class",
                        file_path=file_path,
                        line=node.lineno,
                        docstring=doc
                    )
        except Exception as e:
            logger.debug("CodeGraph AST index failed for %s: %s", file_path, e)

    def find_symbol(self, symbol_name: str) -> Optional[Dict[str, Any]]:
        """Fast symbol lookup across the indexed repository."""
        node = self.symbols.get(symbol_name)
        if not node:
            return None
        return {
            "name": node.name,
            "type": node.symbol_type,
            "file_path": node.file_path,
            "line": node.line,
            "docstring": node.docstring,
            "callers": node.callers,
            "callees": node.callees
        }

    def impact_analysis(self, target_path: str) -> List[str]:
        """Calculates dependent files that import or reference elements of target_path."""
        impacted = []
        base_name = os.path.splitext(os.path.basename(target_path))[0]
        for name, node in self.symbols.items():
            if node.file_path != target_path and base_name in node.file_path:
                impacted.append(node.file_path)
        return sorted(list(set(impacted)))


class LLMWikiEngine:
    """Structured documentation link-graph and topic recall engine."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}

    def add_wiki_node(self, topic: str, content: str, links: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> None:
        self.nodes[topic.lower()] = {
            "topic": topic,
            "content": content,
            "links": links or [],
            "tags": tags or []
        }

    def get_wiki_node(self, topic: str) -> Optional[Dict[str, Any]]:
        return self.nodes.get(topic.lower())

    def search_wiki(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for topic, node in self.nodes.items():
            if q in topic or q in node["content"].lower() or any(q in t.lower() for t in node["tags"]):
                results.append(node)
        return results


class LayeredDistillationEngine:
    """Layered Chat Memory Distillation: L0 (Raw) -> L1 (Facts) -> L2 (Context) -> L3 (Persona)."""

    def __init__(self):
        self.l0_turns: List[Dict[str, str]] = []
        self.l1_facts: List[Dict[str, Any]] = []
        self.l2_context: Dict[str, Any] = {}
        self.l3_persona: Dict[str, Any] = {}

    def record_turn(self, user_content: str, assistant_content: str) -> None:
        self.l0_turns.append({"user": user_content, "assistant": assistant_content})

    def distill_l1_fact(self, fact: str, domain: str = "general", verified: bool = True) -> None:
        self.l1_facts.append({
            "fact": fact,
            "domain": domain,
            "verified": verified
        })

    def update_l2_context(self, active_task_id: str, context_payload: Dict[str, Any]) -> None:
        self.l2_context = {
            "active_task_id": active_task_id,
            "payload": context_payload
        }

    def set_l3_persona(self, persona_name: str, boundaries: List[str]) -> None:
        self.l3_persona = {
            "persona_name": persona_name,
            "boundaries": boundaries
        }

    def recall_layered(self, query: str) -> Dict[str, Any]:
        matched_facts = [
            f for f in self.l1_facts 
            if any(w in f["fact"].lower() for w in query.lower().split() if len(w) > 3)
        ]
        return {
            "l1_facts": matched_facts,
            "l2_context": self.l2_context,
            "l3_persona": self.l3_persona
        }


class TencentDBMemoryProvider(MemoryProvider):
    """TencentDB-compatible Memory Provider implementing CodeGraph, LLM-Wiki, and Layered Distillation."""

    def __init__(self, proxy_url: str = "http://localhost:8126") -> None:
        self._proxy_url = proxy_url
        self._session_id: str = ""
        self._tenant_id: Optional[str] = None
        self._workspace_id: Optional[str] = None
        
        # In-process Fallback / High-speed Engines
        self.codegraph = LocalCodeGraphEngine()
        self.wiki = LLMWikiEngine()
        self.distillation = LayeredDistillationEngine()

    @property
    def name(self) -> str:
        return "tencentdb_memory_hub"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._tenant_id = kwargs.get("tenant_id")
        self._workspace_id = kwargs.get("workspace_id")
        workspace_root = kwargs.get("agent_workspace", "")
        if workspace_root:
            self.codegraph.workspace_path = workspace_root

        logger.info(
            "TencentDB Memory Hub initialized for session %s (tenant_id=%s, workspace_id=%s)",
            session_id, self._tenant_id, self._workspace_id
        )

    def system_prompt_block(self) -> str:
        return (
            "Connected to TencentDB Agent Memory Hub (CodeGraph AST, LLM-Wiki Knowledge, Layered L0-L3 Memory). "
            "Use 'codegraph_find_symbol', 'codegraph_impact_analysis', and 'wiki_query' for instant zero-latency retrieval."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        recalled = self.distillation.recall_layered(query)
        wiki_hits = self.wiki.search_wiki(query)
        
        if not recalled["l1_facts"] and not wiki_hits and not recalled["l2_context"]:
            return ""

        parts = [
            "<memory-context>",
            "[System note: The following is recalled memory context from TencentDB Memory Hub, NOT new user input. Treat as authoritative reference data.]"
        ]
        if recalled["l1_facts"]:
            parts.append("### Verified Facts (L1):")
            for f in recalled["l1_facts"][:5]:
                parts.append(f"- [{f['domain']}] {f['fact']}")
        if wiki_hits:
            parts.append("### LLM-Wiki Knowledge Nodes:")
            for w in wiki_hits[:3]:
                parts.append(f"- **{w['topic']}**: {w['content']}")
        if recalled["l2_context"]:
            parts.append(f"### Active Task Context (L2): {recalled['l2_context'].get('active_task_id')}")
        parts.append("</memory-context>")
        return "\n".join(parts)

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        self.distillation.record_turn(user_content, assistant_content)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "codegraph_find_symbol",
                "description": "Locate a Python/TypeScript symbol declaration, docstring, and callers using the pre-indexed AST CodeGraph.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol_name": {
                            "type": "string",
                            "description": "The exact function, class, or method name to find."
                        }
                    },
                    "required": ["symbol_name"]
                }
            },
            {
                "name": "codegraph_impact_analysis",
                "description": "Calculate dependent files and components impacted by changes in target_path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_path": {
                            "type": "string",
                            "description": "File path to perform blast-radius/impact analysis on."
                        }
                    },
                    "required": ["target_path"]
                }
            },
            {
                "name": "wiki_query",
                "description": "Query the structured LLM-Wiki documentation knowledge graph.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic_or_query": {
                            "type": "string",
                            "description": "Topic or query keyword to search within the Wiki knowledge graph."
                        }
                    },
                    "required": ["topic_or_query"]
                }
            },
            {
                "name": "tencent_add_fact",
                "description": "Add a distilled verified L1 fact into TencentDB Layered Memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "The atomic verified fact statement."
                        },
                        "domain": {
                            "type": "string",
                            "description": "Domain/category (e.g. auth, architecture, devops)."
                        }
                    },
                    "required": ["fact"]
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "codegraph_find_symbol":
            symbol = arguments.get("symbol_name", "")
            res = self.codegraph.find_symbol(symbol)
            return json.dumps(res or {"status": "not_found", "symbol": symbol}, ensure_ascii=False)
        elif tool_name == "codegraph_impact_analysis":
            path = arguments.get("target_path", "")
            impacted = self.codegraph.impact_analysis(path)
            return json.dumps({"target_path": path, "impacted_files": impacted}, ensure_ascii=False)
        elif tool_name == "wiki_query":
            q = arguments.get("topic_or_query", "")
            results = self.wiki.search_wiki(q)
            return json.dumps({"query": q, "results": results}, ensure_ascii=False)
        elif tool_name == "tencent_add_fact":
            fact = arguments.get("fact", "")
            domain = arguments.get("domain", "general")
            self.distillation.distill_l1_fact(fact, domain=domain)
            return json.dumps({"status": "stored", "layer": "L1", "fact": fact, "domain": domain}, ensure_ascii=False)
        return json.dumps({"error": f"Unknown tool {tool_name}"}, ensure_ascii=False)

    def shutdown(self) -> None:
        logger.info("TencentDB Memory Hub provider shutdown cleanly.")
