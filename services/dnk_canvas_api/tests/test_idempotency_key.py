# --- DNK-MRH-HEADER ---
# mrh_id: "test_idempotency_key.py"
# purpose: "Tests for idempotency key generator and validator"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Tests for idempotency key generator."""
import pytest
from uuid import uuid4

from core.security.idempotency_key import generate_idempotency_key, validate_idempotency_key


class TestIdempotencyKeyGenerator:
    """Test idempotency key generation and validation."""
    
    def test_generate_idempotency_key_deterministic(self):
        """Same inputs → same key (deterministic)."""
        run_id = str(uuid4())
        action_name = "delete_canvas"
        args = {"canvas_id": "123"}
        
        key1 = generate_idempotency_key(run_id, action_name, args)
        key2 = generate_idempotency_key(run_id, action_name, args)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA-256 hex
    
    def test_generate_idempotency_key_different_args(self):
        """Different args → different key."""
        run_id = str(uuid4())
        action_name = "delete_canvas"
        
        args1 = {"canvas_id": "123"}
        args2 = {"canvas_id": "456"}
        
        key1 = generate_idempotency_key(run_id, action_name, args1)
        key2 = generate_idempotency_key(run_id, action_name, args2)
        
        assert key1 != key2
    
    def test_validate_idempotency_key_valid(self):
        """Valid 64-char hex key → True."""
        run_id = str(uuid4())
        key = generate_idempotency_key(run_id, "delete_canvas", {"canvas_id": "123"})
        
        assert validate_idempotency_key(key) is True
    
    def test_validate_idempotency_key_invalid_length(self):
        """Wrong length → False."""
        assert validate_idempotency_key("abc123") is False
        assert validate_idempotency_key("a" * 63) is False
        assert validate_idempotency_key("a" * 65) is False
    
    def test_validate_idempotency_key_invalid_chars(self):
        """Non-hex characters → False."""
        assert validate_idempotency_key("g" * 64) is False  # 'g' is not hex
        assert validate_idempotency_key("xyz123" + "0" * 58) is False
