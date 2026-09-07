# --- DNK-MRH-HEADER ---
# mrh_id: "core/patent_shield/patent_parser.py"
# purpose: "Parser and AST feature extraction engine for patent specifications and claims"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("dnk.patent_shield.parser")


class PatentParser:
    """
    Parser for converting raw patent structures into normalized records.
    Extracts claims, abstract, CPC/IPC classifications, assignees, and dates.
    """

    def extract_claims(self, patent_data: Dict[str, Any]) -> List[str]:
        """
        Extract normalized list of claim strings from patent payload.
        Handles both structured dictionaries, strings, and list of objects.
        """
        claims: List[str] = []
        raw_claims = patent_data.get("claims", [])
        if isinstance(raw_claims, list):
            for claim in raw_claims:
                if isinstance(claim, dict):
                    text = claim.get("text") or claim.get("claim_text") or ""
                    if text:
                        claims.append(str(text).strip())
                elif isinstance(claim, str):
                    if claim.strip():
                        claims.append(claim.strip())
        elif isinstance(raw_claims, str):
            # Split claims by numbers e.g. "1. A system...", "2. The method..."
            split_claims = re.split(r'(?=\b\d+\.\s+)', raw_claims)
            for c in split_claims:
                if c.strip():
                    claims.append(c.strip())
        return claims

    def extract_abstract(self, patent_data: Dict[str, Any]) -> str:
        """
        Extract and clean patent abstract string.
        """
        abstract = patent_data.get("abstract", "")
        if isinstance(abstract, dict):
            abstract = abstract.get("text", "") or abstract.get("paragraph", "")
        elif isinstance(abstract, list):
            abstract = " ".join(str(item) for item in abstract if item)
        return str(abstract).strip()

    def extract_classifications(self, patent_data: Dict[str, Any]) -> List[str]:
        """
        Extract CPC, IPC, and US patent classification codes.
        """
        codes: List[str] = []
        raw_classes = patent_data.get("classifications", []) or patent_data.get("cpc_codes", [])
        if isinstance(raw_classes, list):
            for item in raw_classes:
                if isinstance(item, dict):
                    code = item.get("code") or item.get("symbol") or ""
                    if code:
                        codes.append(str(code).strip())
                elif isinstance(item, str) and item.strip():
                    codes.append(item.strip())
        return list(dict.fromkeys(codes))  # Deduplicate while preserving order

    def extract_prior_art(self, patent_data: Dict[str, Any]) -> List[str]:
        """
        Extract cited patent documents and prior art references.
        """
        citations: List[str] = []
        raw_citations = patent_data.get("citations", []) or patent_data.get("references", [])
        if isinstance(raw_citations, list):
            for cit in raw_citations:
                if isinstance(cit, dict):
                    doc_num = cit.get("document_number") or cit.get("patent_id") or ""
                    if doc_num:
                        citations.append(str(doc_num).strip())
                elif isinstance(cit, str) and cit.strip():
                    citations.append(cit.strip())
        return list(dict.fromkeys(citations))

    def parse_patent(self, patent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and parse a patent payload into a standardized dictionary representation.
        """
        patent_id = (
            patent_data.get("publication_number")
            or patent_data.get("patent_id")
            or patent_data.get("id")
            or ""
        )
        title = patent_data.get("title", "").strip() if isinstance(patent_data.get("title"), str) else ""

        return {
            "patent_id": str(patent_id).strip(),
            "title": title,
            "abstract": self.extract_abstract(patent_data),
            "claims": self.extract_claims(patent_data),
            "classifications": self.extract_classifications(patent_data),
            "prior_art": self.extract_prior_art(patent_data),
            "filing_date": patent_data.get("filing_date"),
            "grant_date": patent_data.get("grant_date"),
            "assignee": patent_data.get("assignee"),
            "jurisdiction": patent_data.get("jurisdiction", "US"),
            "metadata": patent_data.get("metadata", {}),
        }
