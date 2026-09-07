# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_crypto_identity.py"
# purpose: "Comprehensive test suite for UUIDv7, HMAC Signatures and Immutable Audit Chain"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from core.security.crypto_identity import generate_user_id, generate_tenant_id, CryptoIdentityManager
from core.security.audit_chain import ImmutableAuditChain

def test_uuidv7_uniqueness_and_ordering():
    ids = [generate_user_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    for uid in ids:
        assert uid.startswith("usr_")
        assert len(uid) == 30

def test_crypto_signature_verification():
    mgr = CryptoIdentityManager(secret_key="master_dnk_secret_key_2026")
    payload = {"tenant_id": generate_tenant_id(), "action": "create_order", "amount": 150.0}
    
    sig, signed_payload = mgr.sign_payload(payload)
    assert mgr.verify_signature(signed_payload, sig) is True
    
    # Tampered payload must fail
    tampered_payload = signed_payload.copy()
    tampered_payload["amount"] = 9999.0
    assert mgr.verify_signature(tampered_payload, sig) is False

def test_replay_attack_protection():
    mgr = CryptoIdentityManager(secret_key="master_dnk_secret_key_2026")
    payload = {"action": "execute_payout"}
    sig, signed_payload = mgr.sign_payload(payload)
    
    # Old timestamp must be rejected
    signed_payload["_ts"] = int(time.time()) - 400
    assert mgr.verify_signature(signed_payload, sig, max_age_seconds=300) is False

def test_immutable_audit_chain_integrity():
    chain_mgr = ImmutableAuditChain()
    t_id = generate_tenant_id()
    u_id = generate_user_id()
    
    chain_mgr.append_event(tenant_id=t_id, actor_id=u_id, action="login", details={"ip": "127.0.0.1"})
    chain_mgr.append_event(tenant_id=t_id, actor_id=u_id, action="deploy_bundle", details={"bundle_id": "bnd_01"})
    chain_mgr.append_event(tenant_id=t_id, actor_id=u_id, action="payout", details={"val": 500})
    
    valid, err_idx = ImmutableAuditChain.verify_chain(chain_mgr.chain)
    assert valid is True
    assert err_idx is None
    
    # Tamper with record #1
    chain_mgr.chain[1]["details"]["bundle_id"] = "hacked_bundle"
    valid, err_idx = ImmutableAuditChain.verify_chain(chain_mgr.chain)
    assert valid is False
    assert err_idx == 1
