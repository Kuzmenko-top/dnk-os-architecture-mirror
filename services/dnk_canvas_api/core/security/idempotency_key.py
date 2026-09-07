# --- DNK-MRH-HEADER ---
# mrh_id: "idempotency_key.py"
# purpose: "Idempotency key generation and validation for security gates"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Idempotency key generation for security gates."""
import hashlib
import json
from typing import Any, Dict


def generate_idempotency_key(
    run_id: str,
    action_name: str,
    args: Dict[str, Any],
) -> str:
    """
    Generate unique idempotency key for destructive actions.
    
    Formula: SHA-256(run_id + action_name + sorted_args_json)
    
    Args:
        run_id: Current agent run identifier (UUID string)
        action_name: Name of the action (e.g., "delete_canvas", "deploy_service")
        args: Dictionary of action arguments
    
    Returns:
        64-character hex string (SHA-256 hash)
    """
    # Sort args for deterministic hashing
    sorted_args = json.dumps(args, sort_keys=True)
    
    # Combine all components
    raw_key = f"{run_id}:{action_name}:{sorted_args}"
    
    # Generate SHA-256 hash
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


def validate_idempotency_key(key: str) -> bool:
    """
    Validate idempotency key format (64-char hex).
    
    Args:
        key: Idempotency key to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(key, str):
        return False
    if len(key) != 64:
        return False
    try:
        int(key, 16)
        return True
    except ValueError:
        return False
