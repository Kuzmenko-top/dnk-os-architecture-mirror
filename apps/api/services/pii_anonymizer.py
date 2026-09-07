# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/pii_anonymizer.py"
# purpose: "GDPR/CCPA compliant PII Anonymization and Data Masking Engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import hashlib
import re
from typing import Optional, Dict, Any


def anonymize_customer_id(customer_id: Optional[str]) -> Optional[str]:
    """SHA-256 hash customer_id for GDPR/CCPA compliance."""
    if not customer_id:
        return None
    return hashlib.sha256(customer_id.strip().encode("utf-8")).hexdigest()


def anonymize_email(email: Optional[str]) -> Optional[str]:
    """
    Mask email address (e.g., john.doe@example.com -> j***e@example.com).
    Short usernames are gracefully handled.
    """
    if not email or "@" not in email:
        return email

    parts = email.strip().split("@")
    if len(parts) != 2:
        return email

    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = f"{name[0]}*" if len(name) > 0 else "*"
    else:
        masked_name = f"{name[0]}{'*' * (len(name) - 2)}{name[-1]}"

    return f"{masked_name}@{domain}"


def anonymize_ip_address(ip_address: Optional[str]) -> Optional[str]:
    """Zero out the last octet for IPv4 or last group for IPv6."""
    if not ip_address:
        return None
    ip = ip_address.strip()
    if "." in ip:  # IPv4
        octets = ip.split(".")
        if len(octets) == 4:
            return f"{octets[0]}.{octets[1]}.{octets[2]}.0"
    elif ":" in ip:  # IPv6
        parts = ip.split(":")
        if len(parts) > 1:
            return ":".join(parts[:-1]) + ":0000"
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Deeply sanitize customer identifying fields in any telemetry dictionary."""
    sanitized = dict(payload)
    if "customer_id" in sanitized and sanitized["customer_id"]:
        sanitized["customer_id"] = anonymize_customer_id(str(sanitized["customer_id"]))
    if "email" in sanitized and sanitized["email"]:
        sanitized["email"] = anonymize_email(str(sanitized["email"]))
    if "ip" in sanitized and sanitized["ip"]:
        sanitized["ip"] = anonymize_ip_address(str(sanitized["ip"]))
    return sanitized
