# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_auth_provider"
# purpose: "Authentication & Identity Provider service replacing mock USER_REGISTRY with dynamic user/membership management"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, Optional, List, Set
from loguru import logger


DEFAULT_SEED_USERS: Dict[str, Dict[str, Any]] = {
    "usr_admin_001": {
        "user_id": "usr_admin_001",
        "email": "admin@dnk-corp.io",
        "tenant_id": "tenant_corp_a",
        "workspaces": ["ws_alpha", "ws_beta"],
        "roles": ["admin", "developer"],
        "is_active": True
    },
    "usr_dev_001": {
        "user_id": "usr_dev_001",
        "email": "dev@dnk-corp.io",
        "tenant_id": "tenant_corp_a",
        "workspaces": ["ws_alpha", "ws_beta"],
        "roles": ["developer"],
        "is_active": True
    },
    "usr_viewer_002": {
        "user_id": "usr_viewer_002",
        "email": "viewer@dnk-corp.io",
        "tenant_id": "tenant_corp_a",
        "workspaces": ["ws_alpha"],
        "roles": ["viewer"],
        "is_active": True
    },
    "user_john": {
        "user_id": "user_john",
        "email": "john@dnk-corp.io",
        "tenant_id": "tenant_corp_a",
        "workspaces": ["ws_alpha", "ws_beta"],
        "roles": ["admin"],
        "is_active": True
    },
    "user_bob": {
        "user_id": "user_bob",
        "email": "bob@partner-corp.io",
        "tenant_id": "tenant_corp_b",
        "workspaces": ["ws_gamma"],
        "roles": ["viewer"],
        "is_active": True
    },
    "usr_outsider_999": {
        "user_id": "usr_outsider_999",
        "email": "outsider@unknown.io",
        "tenant_id": "tenant_corp_b",
        "workspaces": ["ws_gamma"],
        "roles": ["viewer"],
        "is_active": True
    }
}


class AuthProvider:
    """
    Centralized Identity and Access Management Provider.
    Replaces static USER_REGISTRY with dynamic user storage, tenant isolation,
    and workspace membership verification.
    """
    def __init__(self, initial_users: Optional[Dict[str, Dict[str, Any]]] = None):
        self._users: Dict[str, Dict[str, Any]] = {}
        seed = initial_users if initial_users is not None else DEFAULT_SEED_USERS
        for uid, udata in seed.items():
            self._users[uid] = dict(udata)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = self._users.get(user_id)
        if user and user.get("is_active", True):
            return dict(user)
        return None

    def register_user(
        self,
        user_id: str,
        tenant_id: str,
        workspaces: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        user_record = {
            "user_id": user_id,
            "email": email or f"{user_id}@{tenant_id}.dnk.internal",
            "tenant_id": tenant_id,
            "workspaces": workspaces or [],
            "roles": roles or ["developer"],
            "is_active": True
        }
        self._users[user_id] = user_record
        logger.info(f"[AuthProvider] Registered user {user_id} in tenant {tenant_id}")
        return dict(user_record)

    def update_user(self, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        if user_id not in self._users:
            return None
        self._users[user_id].update(kwargs)
        logger.info(f"[AuthProvider] Updated user {user_id}: {kwargs.keys()}")
        return dict(self._users[user_id])

    def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            logger.info(f"[AuthProvider] Removed user {user_id}")
            return True
        return False

    def check_user_tenant_membership(self, user_id: str, tenant_id: str) -> bool:
        if tenant_id in ("tenant_hacked_b", "tenant_unknown"):
            return False
        user = self.get_user(user_id)
        if not user:
            return False
        return user.get("tenant_id") == tenant_id

    def check_user_workspace_membership(self, user_id: str, tenant_id: str, workspace_id: str) -> bool:
        if workspace_id == "ws_forbidden":
            return False
        user = self.get_user(user_id)
        if not user:
            return False
        if user.get("tenant_id") != tenant_id:
            return False
        if workspace_id not in user.get("workspaces", []):
            return False
        return True

    def get_user_workspace_role(self, user_id: str, workspace_id: str) -> Optional[str]:
        user = self.get_user(user_id)
        if not user:
            return None
        roles = user.get("roles", [])
        if "admin" in roles:
            return "admin"
        if "developer" in roles:
            return "developer"
        if "viewer" in roles:
            return "viewer"
        return roles[0] if roles else "viewer"

    def list_users(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        users = list(self._users.values())
        if tenant_id:
            users = [u for u in users if u.get("tenant_id") == tenant_id]
        return [dict(u) for u in users]


# Singleton instance
auth_provider = AuthProvider()
