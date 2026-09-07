# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_cross_region_replication"
# purpose: "Cross-Region Database & Cache Replication Manager & Lag Evaluator (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class CrossRegionReplicationManager:
    """Monitors cross-region read replicas and logical replication status across clouds."""

    def __init__(self):
        self._streams: Dict[str, Dict[str, Any]] = {}
        self._seed_default_streams()

    def _seed_default_streams(self):
        default_streams = [
            {
                "id": str(uuid.uuid4()),
                "source_region": "us-east-1",
                "target_region": "eu-west-1",
                "replication_type": "async",  # 'sync', 'async', 'logical'
                "lag_seconds": 1,
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "status": "healthy",  # 'healthy', 'lagging', 'broken'
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "source_region": "us-east-1",
                "target_region": "ap-southeast-1",
                "replication_type": "async",
                "lag_seconds": 3,
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "status": "healthy",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "source_region": "us-east-1",
                "target_region": "us-central1",
                "replication_type": "logical",
                "lag_seconds": 0,
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "status": "healthy",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "source_region": "us-east-1",
                "target_region": "europe-west3",
                "replication_type": "async",
                "lag_seconds": 2,
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
                "status": "healthy",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        for s in default_streams:
            self._streams[s["id"]] = s

    def list_streams(self) -> List[Dict[str, Any]]:
        return list(self._streams.values())

    def get_stream(self, stream_id: str) -> Optional[Dict[str, Any]]:
        return self._streams.get(stream_id)

    def register_stream(
        self,
        source_region: str,
        target_region: str,
        replication_type: str = "async",
        lag_seconds: int = 0,
    ) -> Dict[str, Any]:
        status = self._evaluate_status(lag_seconds)
        stream = {
            "id": str(uuid.uuid4()),
            "source_region": source_region,
            "target_region": target_region,
            "replication_type": replication_type,
            "lag_seconds": lag_seconds,
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._streams[stream["id"]] = stream
        return stream

    def record_lag(self, source_region: str, target_region: str, lag_seconds: int) -> Dict[str, Any]:
        """Records/updates replication lag for a source -> target region pair."""
        for s in self._streams.values():
            if s["source_region"] == source_region and s["target_region"] == target_region:
                updated = self.update_replication_lag(s["id"], lag_seconds)
                if updated:
                    return updated
        # Create new stream if not exists
        return self.register_stream(source_region, target_region, replication_type="async", lag_seconds=lag_seconds)

    def update_replication_lag(self, stream_id: str, lag_seconds: int) -> Optional[Dict[str, Any]]:
        stream = self._streams.get(stream_id)
        if not stream:
            return None

        stream["lag_seconds"] = lag_seconds
        stream["last_sync_at"] = datetime.now(timezone.utc).isoformat()
        stream["status"] = self._evaluate_status(lag_seconds)
        return stream

    def _evaluate_status(self, lag_seconds: int) -> str:
        if lag_seconds < 10:
            return "healthy"
        elif lag_seconds < 60:
            return "lagging"
        else:
            return "broken"

    def get_aggregate_replication_lag(self) -> Dict[str, Any]:
        streams = list(self._streams.values())
        if not streams:
            return {"max_lag_seconds": 0, "avg_lag_seconds": 0, "unhealthy_count": 0, "total_streams": 0}

        lags = [s["lag_seconds"] for s in streams]
        unhealthy = [s for s in streams if s["status"] != "healthy"]
        overall = "healthy" if not unhealthy else ("broken" if any(s["status"] == "broken" for s in unhealthy) else "lagging")

        return {
            "max_lag_seconds": max(lags),
            "avg_lag_seconds": round(sum(lags) / len(lags), 2),
            "unhealthy_count": len(unhealthy),
            "total_streams": len(streams),
            "overall_status": overall,
        }
