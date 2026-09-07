# --- DNK-MRH-HEADER ---
# mrh_id: "core_error_distillation_patch_generator"
# purpose: "Autonomous Distiller Patch Generator: Traceback similarity matching, fuzzy patch generation and safe application"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import re
import os
import json
import difflib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.error_distillation.fingerprint import ErrorFingerprint
from core.error_distillation.classifier import ErrorClassifier


@dataclass
class MatchResult:
    matched: bool
    score: float
    category: str
    root_cause: str
    solution: str
    target_pattern: str


@dataclass
class PatchResult:
    success: bool
    file_path: str
    diff: str
    error_message: Optional[str] = None


class DistillerPatchGenerator:
    """
    Autonomous Patch Generator that:
    1. Matches traceback signatures with vector/token distance against distilled solutions.
    2. Synthesizes fuzzy replacements or unified diffs.
    3. Safely applies patches to code files without manual shell loops.
    4. Records verified solutions to SCONES/Distillation database.
    """

    def __init__(self, db_path: str = "docs/scones/error_distillations.json"):
        self.db_path = db_path
        self.classifier = ErrorClassifier()

    def _load_distillations(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return []
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _token_similarity(self, s1: str, s2: str) -> float:
        """Compute normalized token overlap similarity between two text strings."""
        tokens1 = set(re.findall(r"\b\w{2,}\b", s1.lower()))
        tokens2 = set(re.findall(r"\b\w{2,}\b", s2.lower()))
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union)
        seq_match = difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
        return (jaccard * 0.7) + (seq_match * 0.3)

    def match_traceback(self, traceback_or_error: str) -> MatchResult:
        """
        Matches a traceback or error text against distilled solutions using regex patterns
        and token similarity distance.
        """
        distillations = self._load_distillations()
        best_match: Optional[Dict[str, Any]] = None
        best_score = 0.0

        for entry in distillations:
            pattern = entry.get("pattern", "")
            category = entry.get("category", "UNKNOWN")
            root_cause = entry.get("root_cause", "")
            solution = entry.get("solution", "")

            # 1. Direct Regex match
            try:
                if pattern and re.search(pattern, traceback_or_error, re.IGNORECASE):
                    return MatchResult(
                        matched=True,
                        score=1.0,
                        category=category,
                        root_cause=root_cause,
                        solution=solution,
                        target_pattern=pattern
                    )
            except re.error:
                pass

            # 2. Vector / Token Similarity Distance
            # Clean pattern from regex meta characters for cleaner semantic matching
            clean_pattern = re.sub(r"[()|'\\.*+?^$]", " ", pattern)
            corpus_text = f"{clean_pattern} {category} {root_cause} {solution}"
            score = self._token_similarity(traceback_or_error, corpus_text)
            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score >= 0.20:
            return MatchResult(
                matched=True,
                score=round(best_score, 4),
                category=best_match.get("category", "UNKNOWN"),
                root_cause=best_match.get("root_cause", ""),
                solution=best_match.get("solution", ""),
                target_pattern=best_match.get("pattern", "")
            )

        return MatchResult(
            matched=False,
            score=round(best_score, 4),
            category="UNKNOWN",
            root_cause="No matching distilled root cause found",
            solution="",
            target_pattern=""
        )

    def generate_unified_diff(
        self,
        file_path: str,
        old_content: str,
        new_content: str
    ) -> str:
        """Generates standard unified diff patch."""
        diff_lines = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        ))
        return "\n".join(diff_lines)

    def apply_fuzzy_replacement(
        self,
        file_path: str,
        target_pattern_or_snippet: str,
        replacement_snippet: str,
        backup: bool = False
    ) -> PatchResult:
        """
        Applies a fuzzy patch/replacement to a target file without manual shell loops.
        """
        if not os.path.exists(file_path):
            return PatchResult(
                success=False,
                file_path=file_path,
                diff="",
                error_message=f"File not found: {file_path}"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_text = f.read()

            new_text = original_text

            # 1. Exact string match
            if target_pattern_or_snippet in original_text:
                new_text = original_text.replace(target_pattern_or_snippet, replacement_snippet, 1)
            else:
                # 2. Regex match
                try:
                    if re.search(target_pattern_or_snippet, original_text):
                        new_text = re.sub(target_pattern_or_snippet, replacement_snippet, original_text, count=1)
                    else:
                        # 3. Fuzzy line match using SequenceMatcher
                        lines = original_text.splitlines()
                        target_lines = target_pattern_or_snippet.strip().splitlines()
                        target_len = len(target_lines)

                        best_ratio = 0.0
                        best_idx = -1

                        for i in range(len(lines) - target_len + 1):
                            window = "\n".join(lines[i:i + target_len])
                            ratio = difflib.SequenceMatcher(None, window, target_pattern_or_snippet.strip()).ratio()
                            if ratio > best_ratio and ratio >= 0.75:
                                best_ratio = ratio
                                best_idx = i

                        if best_idx != -1:
                            new_lines = lines[:best_idx] + [replacement_snippet] + lines[best_idx + target_len:]
                            new_text = "\n".join(new_lines)
                        else:
                            return PatchResult(
                                success=False,
                                file_path=file_path,
                                diff="",
                                error_message=f"Could not find match for snippet in {file_path}"
                            )
                except re.error as e:
                    return PatchResult(
                        success=False,
                        file_path=file_path,
                        diff="",
                        error_message=f"Regex error: {e}"
                    )

            if new_text == original_text:
                return PatchResult(
                    success=False,
                    file_path=file_path,
                    diff="",
                    error_message="Replacement resulted in identical content (no change)"
                )

            diff = self.generate_unified_diff(file_path, original_text, new_text)

            if backup:
                with open(f"{file_path}.bak", "w", encoding="utf-8") as f_bak:
                    f_bak.write(original_text)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_text)

            return PatchResult(
                success=True,
                file_path=file_path,
                diff=diff,
                error_message=None
            )

        except Exception as ex:
            return PatchResult(
                success=False,
                file_path=file_path,
                diff="",
                error_message=str(ex)
            )

    def log_verified_solution(
        self,
        error_pattern: str,
        category: str,
        root_cause: str,
        solution: str,
        workspace_id: str = "ws-alpha-001"
    ) -> bool:
        """
        Records a verified error solution into the self-healing distillation database.
        """
        distillations = self._load_distillations()

        # Check for existing duplicate pattern
        for entry in distillations:
            if entry.get("pattern") == error_pattern:
                entry["root_cause"] = root_cause
                entry["solution"] = solution
                entry["updated_at"] = int(datetime.now(timezone.utc).timestamp())
                entry["workspace_id"] = workspace_id
                break
        else:
            distillations.append({
                "pattern": error_pattern,
                "category": category,
                "root_cause": root_cause,
                "solution": solution,
                "recorded_at": int(datetime.now(timezone.utc).timestamp()),
                "workspace_id": workspace_id
            })

        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(distillations, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
