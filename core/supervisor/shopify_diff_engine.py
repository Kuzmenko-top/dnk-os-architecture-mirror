# --- DNK-MRH-HEADER ---
# mrh_id: "core_supervisor_shopify_diff_engine"
# purpose: "Deterministic Diff Engine & Hash Calculator for Shopify Product Sync Pilot (DNK-SHOPIFY-PILOT-002)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
from typing import Dict, Any, Optional, Tuple


def calculate_json_hash(data: Any) -> str:
    """
    Computes deterministic SHA256 hash of canonical JSON string representation.
    """
    canonical_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def compute_canonical_arguments_hash(approval_payload: Dict[str, Any]) -> str:
    """
    Computes deterministic SHA256 arguments_hash for canonical approval payload.
    Ensures sorted keys, stable array ordering, normalized values, and zero timestamps/random fields.
    """
    canonical_dict: Dict[str, Any] = {
        "action_name": str(approval_payload.get("action_name", "shopify.product_sync.preview")),
        "workspace_id": str(approval_payload.get("workspace_id", "")),
        "plugin_id": str(approval_payload.get("plugin_id", "")),
        "plugin_version": str(approval_payload.get("plugin_version", "")),
        "source_product_id": str(approval_payload.get("source_product_id", "")),
        "diff_hash": str(approval_payload.get("diff_hash", "")),
        "idempotency_key": str(approval_payload.get("idempotency_key", "")),
        "mode": str(approval_payload.get("mode", "simulated_write_plan")),
    }

    req_perms = approval_payload.get("requested_permissions", [])
    if isinstance(req_perms, list):
        canonical_dict["requested_permissions"] = sorted([str(p) for p in req_perms])
    else:
        canonical_dict["requested_permissions"] = []

    prop_muts = approval_payload.get("proposed_mutations", [])
    if isinstance(prop_muts, list):
        formatted_muts = []
        for m in prop_muts:
            if isinstance(m, dict):
                formatted_muts.append({
                    "field": str(m.get("field", "")),
                    "before": m.get("before"),
                    "after": m.get("after"),
                })
        canonical_dict["proposed_mutations"] = sorted(formatted_muts, key=lambda x: x["field"])
    else:
        canonical_dict["proposed_mutations"] = []

    return calculate_json_hash(canonical_dict)


def generate_canonical_idempotency_key(
    workspace_id: str,
    plugin_id: str,
    source_product_id: str,
    input_hash: str,
    custom_key: Optional[str] = None,
) -> str:
    """
    Generates deterministic canonical idempotency key for Shopify sync event.
    If a custom key is provided, returns custom key.
    """
    if custom_key and str(custom_key).strip():
        return str(custom_key).strip()

    raw_str = f"{workspace_id}:{plugin_id}:{source_product_id}:{input_hash}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_product_diff(
    existing_state: Optional[Dict[str, Any]],
    incoming_normalized_state: Dict[str, Any],
) -> Tuple[Dict[str, Any], str, str]:
    """
    Computes deterministic field-level diff between existing product state and incoming normalized state.
    Returns tuple: (diff_dict, canonical_state_hash, diff_hash)
    """
    canonical_existing = existing_state if isinstance(existing_state, dict) else {}
    canonical_state_hash = calculate_json_hash(canonical_existing)

    if not canonical_existing:
        # Product is brand new (created)
        field_diffs = {}
        for k, v in incoming_normalized_state.items():
            field_diffs[k] = {
                "status": "added",
                "new_value": v,
            }
        summary = {
            "added_fields": sorted(list(field_diffs.keys())),
            "modified_fields": [],
            "removed_fields": [],
            "unchanged_fields": [],
        }
        diff = {
            "status": "created",
            "has_changes": True,
            "field_diffs": field_diffs,
            "summary": summary,
        }
        diff_hash = calculate_json_hash(diff)
        return diff, canonical_state_hash, diff_hash

    # Existing state present -> calculate field-by-field diff
    all_keys = sorted(list(set(canonical_existing.keys()).union(set(incoming_normalized_state.keys()))))
    field_diffs = {}
    added_fields = []
    modified_fields = []
    removed_fields = []
    unchanged_fields = []

    for key in all_keys:
        in_existing = key in canonical_existing
        in_incoming = key in incoming_normalized_state

        if in_incoming and not in_existing:
            field_diffs[key] = {
                "status": "added",
                "new_value": incoming_normalized_state[key],
            }
            added_fields.append(key)
        elif in_existing and not in_incoming:
            field_diffs[key] = {
                "status": "removed",
                "old_value": canonical_existing[key],
            }
            removed_fields.append(key)
        else:
            old_val = canonical_existing[key]
            new_val = incoming_normalized_state[key]
            if old_val == new_val:
                field_diffs[key] = {
                    "status": "unchanged",
                    "value": old_val,
                }
                unchanged_fields.append(key)
            else:
                field_diffs[key] = {
                    "status": "modified",
                    "old_value": old_val,
                    "new_value": new_val,
                }
                modified_fields.append(key)

    has_changes = len(added_fields) > 0 or len(modified_fields) > 0 or len(removed_fields) > 0
    diff_status = "updated" if has_changes else "unchanged"

    summary = {
        "added_fields": added_fields,
        "modified_fields": modified_fields,
        "removed_fields": removed_fields,
        "unchanged_fields": unchanged_fields,
    }

    diff = {
        "status": diff_status,
        "has_changes": has_changes,
        "field_diffs": field_diffs,
        "summary": summary,
    }

    diff_hash = calculate_json_hash(diff)
    return diff, canonical_state_hash, diff_hash
