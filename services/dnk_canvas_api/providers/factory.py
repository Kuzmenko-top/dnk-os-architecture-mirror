# --- DNK-MRH-HEADER ---
# mrh_id: "providers/factory.py"
# purpose: "Implement LLM Provider Factory to instantiate Vertex AI or Claude adapters."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Optional
from .base import LLMProvider
from .vertex_gemini import VertexGeminiProvider
from .anthropic_claude import AnthropicClaudeProvider

class ProviderFactory:
    @staticmethod
    def get_provider(provider_name: str) -> LLMProvider:
        # Standard names: 'vertex_gemini', 'anthropic_claude'
        if provider_name == "vertex_gemini":
            return VertexGeminiProvider()
        elif provider_name == "anthropic_claude":
            return AnthropicClaudeProvider()
        else:
            # Safe default fallback
            return VertexGeminiProvider()

# Global factory
factory = ProviderFactory()
