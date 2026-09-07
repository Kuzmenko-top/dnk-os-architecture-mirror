# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_repositories_base_repository"
# purpose: "Base Repository with Master/Replica database connection routing and async context acquisition for DNK OS"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Optional, Any
from contextlib import asynccontextmanager

from apps.api.db.database import db_manager, PoolRole

logger = logging.getLogger("dnk.db.base_repository")


class BaseRepository:
    """
    Base repository supporting read-replica vs master write connection routing.
    """

    def __init__(self, pool_role: PoolRole = PoolRole.MASTER):
        self.default_role = pool_role

    @asynccontextmanager
    async def get_connection(self, pool_role: Optional[PoolRole] = None):
        """
        Acquires an asyncpg connection from the pool corresponding to pool_role.
        Defaults to instance default_role (MASTER or REPLICA).
        """
        target_role = pool_role or self.default_role
        async with db_manager.acquire(target_role) as conn:
            yield conn
