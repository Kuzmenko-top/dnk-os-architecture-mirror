# --- DNK-MRH-HEADER ---
# mrh_id: "core/patent_shield/__init__.py"
# purpose: "Package initialization for Patent Shield & Clean-Room IP Guard"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from .patent_client import PatentClient
from .patent_parser import PatentParser
from .similarity_engine import PatentSimilarityEngine
from .risk_evaluator import PatentRiskEvaluator, RiskLevel

__all__ = [
    "PatentClient",
    "PatentParser",
    "PatentSimilarityEngine",
    "PatentRiskEvaluator",
    "RiskLevel",
]
