# --- DNK-MRH-HEADER ---
# mrh_id: "providers/base.py"
# purpose: "Define abstract LLMProvider protocol for provider-neutral interactions."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Protocol, List, Dict, Any, Optional
from .types import ProviderResult

class LLMProvider(Protocol):
    async def generate_structured(
        self,
        *,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        response_schema: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        ...
