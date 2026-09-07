# --- DNK-MRH-HEADER ---
# mrh_id: "core/error_distillation/classifier.py"
# purpose: "Classification engine mapping traceback patterns and exception signatures to standard classes."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import re
from typing import Tuple

class ErrorClassifier:
    """
    Classifies raw exceptions and tracebacks into:
    - transient: Temporary/retryable errors (rate limits, timeouts).
    - validation: User input, formatting, and structural schema violations.
    - dependency: Environment, uninstalled packages, or service down.
    - logic: Standard python coding/attribute/type crashes.
    - security: Workspace violations, authentication, or ACL failures.
    """
    def __init__(self) -> None:
        # Define re patterns matching error messages/classes
        self._patterns = {
            "transient": [
                re.compile(r"(rate limit|429|503|timeout|gateway|hiccup|connection reset|temporary)", re.IGNORECASE),
            ],
            "validation": [
                re.compile(r"(validation|valueerror|pydantic|schema violation|bad parameter|invalid input)", re.IGNORECASE),
            ],
            "dependency": [
                re.compile(r"(modulenotfounderror|importerror|connectionrefusederror|sqlite3\\.operationalerror|no such table)", re.IGNORECASE),
            ],
            "logic": [
                re.compile(r"(zerodivisionerror|typeerror|attributeerror|indexerror|keyerror|nameerror)", re.IGNORECASE),
            ],
            "security": [
                re.compile(r"(permissionerror|permission denied|unauthorized|autherror|forbidden|isolation violation|403|401)", re.IGNORECASE),
            ]
        }

    def classify(self, exception: Exception) -> Tuple[str, int]:
        """
        Classifies an exception instance.
        Returns a tuple: (error_type, error_code).
        """
        msg = str(exception).lower()
        exc_name = exception.__class__.__name__.lower()
        combined = f"{exc_name}: {msg}"

        # Match patterns
        for err_type, pattern_list in self._patterns.items():
            for pat in pattern_list:
                if pat.search(combined):
                    # Determine custom status codes
                    code = 500 if err_type in ['logic', 'dependency'] else 400
                    if err_type == "transient":
                        code = 429 if "429" in combined else 503
                    elif err_type == "security":
                        code = 403 if "isolation" in combined or "denied" in combined else 401
                    elif err_type == "dependency":
                        code = 500
                    return err_type, code

        # Default classification
        return "logic", 500
