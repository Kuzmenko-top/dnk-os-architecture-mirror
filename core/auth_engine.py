# --- DNK-MRH-HEADER ---
# mrh_id: "core/auth_engine.py"
# purpose: "Safe authorization of Maksym & session preservation (open-design donor)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import json
import stat
import hmac
import hashlib
import tempfile
from typing import Dict, Any, Optional
import time

class MaksymAuthEngine:
    """
    MaksymAuthEngine implements secure authorization and session preservation
    incorporating the secure credentials pattern (DNK-STD-0086).
    """
    def __init__(self, session_store_path: str = "sessions/session_registry.json",
                 expected_phrase: str = "погоджую"):
        self.session_store_path = session_store_path
        # Hash the expected phrase using hashlib for secure hmac comparison
        self.expected_hash = hashlib.sha256(expected_phrase.encode("utf-8")).hexdigest()
        
        # Ensure session storage directory exists
        dir_path = os.path.dirname(self.session_store_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
            
        self._initialize_store()

    def _initialize_store(self) -> None:
        """Initializes empty session store file with 0600 permissions if not present."""
        if not os.path.exists(self.session_store_path):
            self._save_store({})
            # Enforce chmod 0600 (owner read-write only)
            try:
                os.chmod(self.session_store_path, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass  # Fallback for environments with limited permission support

    def _read_store(self) -> Dict[str, Any]:
        """Reads session store securely."""
        if not os.path.exists(self.session_store_path):
            return {}
        try:
            with open(self.session_store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_store(self, data: Dict[str, Any]) -> None:
        """Atomic write protocol using tempfile to eliminate parallel write collisions."""
        dir_path = os.path.dirname(self.session_store_path) or "."
        with tempfile.NamedTemporaryFile("w", dir=dir_path, suffix=".tmp", delete=False, encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_file_name = temp_file.name

        try:
            # Set strict owner permissions on the temporary file before replacement
            os.chmod(temp_file_name, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        # Atomic replacement
        os.replace(temp_file_name, self.session_store_path)

    def verify_maksym(self, auth_phrase: str) -> bool:
        """Verifies if the authorization phrase matches the hashed expected phrase."""
        input_hash = hashlib.sha256(auth_phrase.encode("utf-8")).hexdigest()
        # Secure comparison preventing timing attacks
        return hmac.compare_digest(self.expected_hash, input_hash)

    def create_session(self, username: str, duration_sec: int = 3600, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Creates a session, stores it securely, and returns the session ID."""
        session_id = hashlib.sha256(f"{username}{time.time()}{os.urandom(8)}".encode("utf-8")).hexdigest()
        store = self._read_store()
        
        store[session_id] = {
            "username": username,
            "created_at": time.time(),
            "expires_at": time.time() + duration_sec,
            "metadata": metadata or {}
        }
        self._save_store(store)
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Validates if the session exists and has not expired."""
        store = self._read_store()
        if session_id not in store:
            return False
            
        session = store[session_id]
        if time.time() > session["expires_at"]:
            # Clean up expired session
            del store[session_id]
            self._save_store(store)
            return False
            
        return True

    def terminate_session(self, session_id: str) -> bool:
        """Terminates session and saves the store."""
        store = self._read_store()
        if session_id in store:
            del store[session_id]
            self._save_store(store)
            return True
        return False

    @staticmethod
    def redact_secret(val: str, prefix_len: int = 7) -> str:
        """Redacts sensitive values (e.g. credentials) for safe logging."""
        if not val:
            return "«empty»"
        if len(val) <= prefix_len + 3:
            return "***"
        return f"{val[:prefix_len]}***{val[-3:]}"
