# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_slo_calculator"
# purpose: "SLA/SLO Monitoring Calculator for Uptime, Error Budget, Burn Rate, and Latency SLO"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


class SLOCalculator:
    """Calculates SLA/SLO metrics: Uptime %, Error Budget Remaining, Burn Rate, and Latency SLO."""

    def __init__(
        self,
        default_uptime_target_percent: float = 99.90,
        default_latency_target_ms: int = 200,
    ):
        self.default_uptime_target_percent = default_uptime_target_percent
        self.default_latency_target_ms = default_latency_target_ms
        self._snapshots: Dict[str, List[Dict[str, Any]]] = {}  # workspace_id -> snapshots list

    def calculate_uptime(
        self,
        total_requests: int,
        failed_requests: int,
    ) -> float:
        """Calculate uptime percentage based on request counts."""
        if total_requests <= 0:
            return 100.0
        successful = max(0, total_requests - failed_requests)
        uptime = (successful / total_requests) * 100.0
        return round(uptime, 2)

    def calculate_error_budget(
        self,
        uptime_percentage: float,
        uptime_target_percent: Optional[float] = None,
    ) -> float:
        """
        Calculate remaining error budget (as fraction of allowed error, e.g. 1.0 = 100% budget remaining).
        Target: 99.9% -> Allowed error: 0.1%.
        If uptime is 99.95%, error is 0.05% -> remaining is (0.1 - 0.05) / 0.1 = 0.50 (50%).
        """
        target = uptime_target_percent or self.default_uptime_target_percent
        allowed_error_pct = 100.0 - target
        if allowed_error_pct <= 0:
            return 1.0

        actual_error_pct = max(0.0, 100.0 - uptime_percentage)
        budget_remaining = (allowed_error_pct - actual_error_pct) / allowed_error_pct
        return round(budget_remaining, 4)

    def calculate_burn_rate(
        self,
        actual_error_pct: float,
        uptime_target_percent: Optional[float] = None,
    ) -> float:
        """
        Calculate error budget burn rate.
        Burn rate = actual_error_rate / allowed_error_rate.
        1.0 means consuming exactly 100% of error budget over the period.
        > 1.0 means burning faster than sustainable.
        """
        target = uptime_target_percent or self.default_uptime_target_percent
        allowed_error_pct = 100.0 - target
        if allowed_error_pct <= 0:
            return 0.0

        burn_rate = actual_error_pct / allowed_error_pct
        return round(burn_rate, 2)

    def determine_slo_status(
        self,
        uptime_percentage: float,
        uptime_target_percent: float,
        latency_p95_ms: int,
        latency_slo_target_ms: int,
        burn_rate: float,
        error_budget_remaining: float,
    ) -> str:
        """
        Determine SLO status: 'meeting', 'at_risk', or 'breached'.
        """
        if (
            uptime_percentage < uptime_target_percent
            or latency_p95_ms > latency_slo_target_ms
            or error_budget_remaining <= 0.0
        ):
            return "breached"
        elif (
            burn_rate > 1.0
            or (uptime_percentage - uptime_target_percent) < 0.05
            or (latency_slo_target_ms - latency_p95_ms) < 20
        ):
            return "at_risk"
        return "meeting"

    def compute_slo_metrics(
        self,
        workspace_id: str,
        total_requests: int = 10000,
        failed_requests: int = 5,
        latencies_ms: Optional[List[int]] = None,
        uptime_target_percent: Optional[float] = None,
        latency_slo_target_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute full SLO metrics set for a given window."""
        uptime_target = uptime_target_percent or self.default_uptime_target_percent
        latency_target = latency_slo_target_ms or self.default_latency_target_ms

        uptime_pct = self.calculate_uptime(total_requests, failed_requests)
        actual_error_pct = max(0.0, 100.0 - uptime_pct)
        error_budget_rem = self.calculate_error_budget(uptime_pct, uptime_target)
        burn_rate = self.calculate_burn_rate(actual_error_pct, uptime_target)

        # Calculate p95 latency
        if latencies_ms and len(latencies_ms) > 0:
            sorted_latencies = sorted(latencies_ms)
            idx = int(math.ceil(0.95 * len(sorted_latencies))) - 1
            idx = max(0, min(idx, len(sorted_latencies) - 1))
            latency_p95 = int(sorted_latencies[idx])
        else:
            latency_p95 = 145  # Default nominal p95 latency

        status = self.determine_slo_status(
            uptime_percentage=uptime_pct,
            uptime_target_percent=uptime_target,
            latency_p95_ms=latency_p95,
            latency_slo_target_ms=latency_target,
            burn_rate=burn_rate,
            error_budget_remaining=error_budget_rem,
        )

        return {
            "workspace_id": workspace_id,
            "uptime_percentage": uptime_pct,
            "uptime_target_percent": uptime_target,
            "error_budget_remaining": error_budget_rem,
            "latency_p95_ms": latency_p95,
            "latency_slo_target_ms": latency_target,
            "slo_status": status,
            "burn_rate": burn_rate,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
        }

    async def generate_snapshot(
        self,
        workspace_id: str,
        total_requests: int = 10000,
        failed_requests: int = 5,
        latencies_ms: Optional[List[int]] = None,
        latency_p95_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute metrics and record an immutable SLO snapshot."""
        if latency_p95_ms is not None and not latencies_ms:
            latencies_ms = [latency_p95_ms]
        metrics = self.compute_slo_metrics(
            workspace_id=workspace_id,
            total_requests=total_requests,
            failed_requests=failed_requests,
            latencies_ms=latencies_ms,
        )
        if latency_p95_ms is not None:
            metrics["latency_p95_ms"] = latency_p95_ms
            metrics["slo_status"] = self.determine_slo_status(
                uptime_percentage=metrics["uptime_percentage"],
                uptime_target_percent=metrics["uptime_target_percent"],
                latency_p95_ms=latency_p95_ms,
                latency_slo_target_ms=metrics["latency_slo_target_ms"],
                burn_rate=metrics["burn_rate"],
                error_budget_remaining=metrics["error_budget_remaining"],
            )
        return await self.create_snapshot(workspace_id, metrics)

    async def get_burn_rate_chart_data(
        self,
        workspace_id: str,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Alias for get_burn_rate_series."""
        return await self.get_burn_rate_series(workspace_id, hours=hours)

    async def create_snapshot(
        self,
        workspace_id: str,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an immutable 24h rolling SLO snapshot."""
        if not metrics:
            metrics = self.compute_slo_metrics(workspace_id=workspace_id)

        now = datetime.now(timezone.utc)
        snapshot = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "snapshot_time": now.isoformat(),
            "uptime_percentage": float(metrics["uptime_percentage"]),
            "error_budget_remaining": float(metrics["error_budget_remaining"]),
            "latency_p95_ms": int(metrics["latency_p95_ms"]),
            "latency_slo_target_ms": int(metrics["latency_slo_target_ms"]),
            "slo_status": metrics["slo_status"],
            "burn_rate": float(metrics["burn_rate"]),
        }

        self._snapshots.setdefault(workspace_id, []).append(snapshot)
        # Keep recent 100 snapshots
        if len(self._snapshots[workspace_id]) > 100:
            self._snapshots[workspace_id] = self._snapshots[workspace_id][-100:]

        return snapshot

    async def get_current_status(self, workspace_id: str) -> Dict[str, Any]:
        """Get the latest or compute live SLO status."""
        snapshots = self._snapshots.get(workspace_id, [])
        if snapshots:
            latest = snapshots[-1]
            return latest

        # If no snapshots, generate a nominal baseline snapshot
        return await self.create_snapshot(workspace_id)

    async def get_history(
        self,
        workspace_id: str,
        limit: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get historical SLO snapshots sorted chronologically."""
        snapshots = self._snapshots.get(workspace_id, [])
        if not snapshots:
            # Seed 5 sample rolling hourly snapshots
            now = datetime.now(timezone.utc)
            for i in range(5, 0, -1):
                t = now - timedelta(hours=i)
                snap = {
                    "id": str(uuid.uuid4()),
                    "workspace_id": workspace_id,
                    "snapshot_time": t.isoformat(),
                    "uptime_percentage": 99.96,
                    "error_budget_remaining": 0.60,
                    "latency_p95_ms": 160 + i * 2,
                    "latency_slo_target_ms": self.default_latency_target_ms,
                    "slo_status": "meeting",
                    "burn_rate": 0.40,
                }
                self._snapshots.setdefault(workspace_id, []).append(snap)
            snapshots = self._snapshots.get(workspace_id, [])

        return sorted(snapshots, key=lambda s: s["snapshot_time"])[:limit]

    async def get_burn_rate_series(
        self,
        workspace_id: str,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Generate time-series burn rate chart data over the given timeframe."""
        history = await self.get_history(workspace_id, limit=hours)
        chart_data = []
        for item in history:
            chart_data.append({
                "timestamp": item["snapshot_time"],
                "burn_rate": item["burn_rate"],
                "error_budget_remaining": item["error_budget_remaining"],
                "threshold": 1.0,
            })
        return chart_data

    def clear(self):
        """Helper to reset in-memory snapshots for testing."""
        self._snapshots.clear()


slo_calculator = SLOCalculator()
