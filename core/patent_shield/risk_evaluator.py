# --- DNK-MRH-HEADER ---
# mrh_id: "core/patent_shield/risk_evaluator.py"
# purpose: "Multi-factor patent infringement risk scoring and mitigation engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
from enum import Enum
from typing import Dict, List, Any

logger = logging.getLogger("dnk.patent_shield.risk")


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatentRiskEvaluator:
    """
    Evaluates multi-factor IP infringement risks between Clean-Room specifications and patent corpora.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def assess_risk(
        self,
        clean_room_spec: str,
        similar_patents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate multi-factor risk: similarity score, claims lexical overlap, and classification match.
        """
        if not similar_patents:
            return {
                "clean_room_spec": clean_room_spec,
                "overall_risk": RiskLevel.LOW.value,
                "max_similarity": 0.0,
                "risk_factors": [],
                "recommendations": ["✅ Низький ризик: Жодних співпадінь у патентній базі не знайдено."],
            }

        risk_factors = []
        max_similarity = 0.0

        for patent in similar_patents:
            similarity = float(patent.get("similarity_score", 0.0))
            max_similarity = max(max_similarity, similarity)
            patent_id = patent.get("patent_id", "UNKNOWN")

            # 1. High similarity factor
            if similarity >= self.similarity_threshold:
                risk_factors.append({
                    "factor": "high_similarity",
                    "patent_id": patent_id,
                    "score": round(similarity, 4),
                    "severity": "high" if similarity < 0.95 else "critical",
                })

            # 2. Claims overlap analysis
            claims = patent.get("claims", [])
            claims_overlap = self._analyze_claims_overlap(clean_room_spec, claims)
            if claims_overlap["overlap_ratio"] > 0.4:
                risk_factors.append({
                    "factor": "claims_overlap",
                    "patent_id": patent_id,
                    "overlap_ratio": round(claims_overlap["overlap_ratio"], 4),
                    "severity": "medium" if claims_overlap["overlap_ratio"] < 0.7 else "high",
                    "overlapping_claims": claims_overlap["overlapping_claims"],
                })

            # 3. CPC/IPC classification match
            if self._check_classification_match(clean_room_spec, patent):
                risk_factors.append({
                    "factor": "classification_match",
                    "patent_id": patent_id,
                    "severity": "low",
                })

        # 4. Calculate overall risk
        overall_risk = self._calculate_overall_risk(max_similarity, risk_factors)

        return {
            "clean_room_spec": clean_room_spec,
            "overall_risk": overall_risk.value,
            "max_similarity": round(max_similarity, 4),
            "risk_factors": risk_factors,
            "recommendations": self._generate_recommendations(overall_risk, risk_factors),
        }

    def _analyze_claims_overlap(
        self,
        clean_room_spec: str,
        patent_claims: List[str],
    ) -> Dict[str, Any]:
        """
        Compute lexical and n-gram overlap between Clean-Room specification and claims.
        """
        if not clean_room_spec or not patent_claims:
            return {"overlap_ratio": 0.0, "overlapping_claims": []}

        spec_words = set(clean_room_spec.lower().split())
        all_claim_words = set()
        overlapping_claims = []

        for claim in patent_claims:
            claim_str = claim if isinstance(claim, str) else str(claim)
            claim_words = set(claim_str.lower().split())
            all_claim_words.update(claim_words)
            if spec_words:
                overlap = len(spec_words & claim_words) / len(spec_words)
                if overlap > 0.25:
                    overlapping_claims.append({
                        "claim": claim_str[:120] + ("..." if len(claim_str) > 120 else ""),
                        "overlap": round(overlap, 4),
                    })

        total_union = spec_words | all_claim_words
        overlap_ratio = len(spec_words & all_claim_words) / len(total_union) if total_union else 0.0

        return {
            "overlap_ratio": overlap_ratio,
            "overlapping_claims": overlapping_claims,
        }

    def _check_classification_match(
        self,
        clean_room_spec: str,
        patent: Dict[str, Any],
    ) -> bool:
        """
        Check for domain classification alignment (e.g., G06T for graphics/animation, G06F for software).
        """
        target_classifications = ["G06T13/00", "G06T13/20", "G06T13/40", "G06F8/30", "G06F16/24"]
        patent_classifications = patent.get("classifications", [])
        return any(c in target_classifications for c in patent_classifications)

    def _calculate_overall_risk(
        self,
        max_similarity: float,
        risk_factors: List[Dict[str, Any]],
    ) -> RiskLevel:
        """
        Determine composite risk level from similarity scores and severity counts.
        """
        critical_count = len([f for f in risk_factors if f.get("severity") in ("critical", "high")])
        medium_count = len([f for f in risk_factors if f.get("severity") == "medium"])

        if max_similarity >= 0.95 or critical_count >= 3:
            return RiskLevel.CRITICAL
        elif max_similarity >= self.similarity_threshold or critical_count >= 1:
            return RiskLevel.HIGH
        elif max_similarity >= 0.70 or medium_count >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendations(
        self,
        overall_risk: RiskLevel,
        risk_factors: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Generate actionable architectural recommendations based on risk assessment.
        """
        recommendations = []

        if overall_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recommendations.append(
                "⚠️ Критичний/високий патентний ризик: Рекомендується переглянути архітектурні рішення "
                "та модифікувати сигнатури компонентів для виключення прямих запозичень."
            )
            recommendations.append(
                "📞 Провести аудит Clean-Room специфікації з патентним повіреним перед випуском у production."
            )

        if any(f.get("factor") == "claims_overlap" for f in risk_factors):
            recommendations.append(
                "🔍 Виявлено лексичний перетин із патентними формулами: "
                "переробіть термінологію та декомпозицію методів."
            )

        if overall_risk == RiskLevel.MEDIUM:
            recommendations.append(
                "ℹ️ Помірний ризик: Рекомендується провести додаткову перевірку непатентної літератури (Prior Art)."
            )

        if overall_risk == RiskLevel.LOW:
            recommendations.append(
                "✅ Низький ризик: Специфікація є достатньо унікальною, перетин із відомими патентами в межах норми."
            )

        return recommendations
