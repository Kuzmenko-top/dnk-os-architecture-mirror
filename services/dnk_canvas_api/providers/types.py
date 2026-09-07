# --- DNK-MRH-HEADER ---
# mrh_id: "providers/types.py"
# purpose: "Define types and schemas for LLM Provider results and usage metrics."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class UsageMetrics:
    input_tokens: int
    output_tokens: int
    cost_usd: float

@dataclass
class ToolCallResult:
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class ProviderResult:
    provider: str
    model: str
    request_id: str
    output: Optional[Dict[str, Any]]
    tool_calls: List[ToolCallResult]
    usage: UsageMetrics
    finish_reason: str
    latency_ms: int
    raw_response_hash: str
