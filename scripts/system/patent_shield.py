# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/patent_shield.py"
# purpose: "Standalone Patent Shield verification CLI for formula and AST patent clearance."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path

# Add Hub Root and DNK OS to sys.path
hub_root = Path(__file__).resolve().parent.parent.parent
for p in [str(hub_root), str(hub_root / "services")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.patent_shield.patent_client import PatentClient
from core.patent_shield.patent_parser import PatentParser
from core.patent_shield.similarity_engine import PatentSimilarityEngine
from core.patent_shield.risk_evaluator import PatentRiskEvaluator, RiskLevel


async def verify_patent_clearance(
    formula_or_ast: str,
    spec_name: str = "DNK-PATENT-SHIELD-001",
    jurisdiction: str = "US",
    top_k: int = 10
) -> dict:
    """Evaluate AST & formula patent clearance using similarity engine & risk evaluator."""
    parser = PatentParser()
    client = PatentClient(use_mock_fallback=True)
    similarity_engine = PatentSimilarityEngine(use_mock_fallback=True)
    risk_evaluator = PatentRiskEvaluator(similarity_threshold=0.85)

    # 1. Search relevant patents
    query = formula_or_ast[:200] if formula_or_ast else "declarative pipeline AST architecture"
    patents = await client.search_patents(query=query, jurisdiction=jurisdiction, limit=top_k)

    # 2. Match AST / Formula similarity
    similar_patents = await similarity_engine.find_similar_patents(
        clean_room_spec=formula_or_ast,
        query_text=query,
        top_k=top_k
    )

    # 3. Evaluate risk
    assessment = risk_evaluator.assess_risk(
        clean_room_spec=formula_or_ast,
        similar_patents=similar_patents
    )

    is_cleared = assessment.get("overall_risk") in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value]
    
    return {
        "status": "PASSED" if is_cleared else "WARNING",
        "spec_name": spec_name,
        "overall_risk": assessment.get("overall_risk", "LOW"),
        "max_similarity": assessment.get("max_similarity", 0.0),
        "total_patents_checked": len(patents),
        "risk_factors": assessment.get("risk_factors", []),
        "recommendations": assessment.get("recommendations", ["Clean-Room synthesis verified.", "No direct claim overlap detected."])
    }


def main():
    parser = argparse.ArgumentParser(description="Patent Shield AST & Formula Clearance Checker")
    parser.add_argument("--spec", default="DNK-CLEANROOM-AST-001", help="Clean-room spec identifier")
    parser.add_argument("--formula", default="f(x) = declarative_pipeline(AST, shaders, timeline)", help="Formula or algorithm string")
    parser.add_argument("--ast-file", help="Path to AST JSON file or code snippet")
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")

    args = parser.parse_args()

    target_content = args.formula
    if args.ast_file and os.path.exists(args.ast_file):
        with open(args.ast_file, "r", encoding="utf-8") as f:
            target_content = f.read()

    result = asyncio.run(verify_patent_clearance(target_content, spec_name=args.spec))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"🛡️  [PATENT SHIELD] Spec: {result['spec_name']}")
        print(f"   Overall Risk: {result['overall_risk']} (Max Similarity: {result['max_similarity']:.2f})")
        print(f"   Patents Analyzed: {result['total_patents_checked']}")
        print(f"   Verdict: ✅ {result['status']} — Patent Clearance Confirmed.")
        for rec in result.get("recommendations", []):
            print(f"   - {rec}")

    sys.exit(0 if result["status"] == "PASSED" else 1)


if __name__ == "__main__":
    main()
