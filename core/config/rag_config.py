# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_rag_config"
# purpose: "Configuration constants for Knowledge Base & RAG Service"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

RAG_EMBEDDING_MODEL: str = "text-embedding-004"
RAG_SEARCH_LIMIT: int = 10
RAG_MIN_SCORE_THRESHOLD: float = 0.7
RAG_MAX_CONTENT_LENGTH: int = 4096
