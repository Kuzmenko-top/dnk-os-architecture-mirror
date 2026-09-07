# --- DNK-MRH-HEADER ---
# mrh_id: "core/error_distillation/fingerprint.py"
# purpose: "Error signature and fingerprint generator with cleanup and deduplication."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import hashlib
import re

class ErrorFingerprint:
    """
    Generates a stable, reproducible fingerprint signature for exceptions.
    Cleanses dynamic details like memory addresses, IDs, and file system paths.
    """
    def __init__(self) -> None:
        # Regexes for cleansing
        self._address_re = re.compile(r"0x[0-9a-fA-F]+")
        self._number_re = re.compile(r"\b\d+\b")
        self._uuid_re = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
        self._path_re = re.compile(r"(/[^\s:]+)+")

    def cleanse_message(self, message: str) -> str:
        """Cleanses dynamic elements from an error message."""
        msg = self._uuid_re.sub("<uuid>", message)
        msg = self._address_re.sub("<hex_address>", msg)
        msg = self._path_re.sub("<file_path>", msg)
        msg = self._number_re.sub("<number>", msg)
        # Normalize whitespace and lowercase
        return " ".join(msg.strip().lower().split())

    def generate_fingerprint(self, exception: Exception) -> str:
        """Generates a stable SHA-1 hash for the cleansed error signature."""
        class_name = exception.__class__.__name__
        cleansed_msg = self.cleanse_message(str(exception))
        raw_sig = f"{class_name}:{cleansed_msg}"
        
        hasher = hashlib.sha1(raw_sig.encode("utf-8"))
        return f"ERR-FPR-{hasher.hexdigest()[:16]}"
