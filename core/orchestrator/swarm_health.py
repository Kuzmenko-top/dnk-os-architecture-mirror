# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/swarm_health.py"
# purpose: "Unified Swarm Health & Diagnostic Engine (Priority 4) for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.atomic_store import atomic_json_read, atomic_json_write, atomic_json_update

logger = logging.getLogger("dnk.swarm.health")


class SwarmHealthEngine:
    """
    Unified Swarm Health & Diagnostic Aggregation Engine.
    Aggregates:
      1. Swarm Worker catalog (14 agents) & lifecycle states
      2. Sentinel Watchdog anomaly alerts & self-healing queue
      3. AccountingEngine token usage & spend limit thresholds
      4. Canvas Bridge WebSocket connectivity & active observers
      5. System runtime metrics & overall cluster health status
    """

    DEFAULT_SPEND_LIMIT_USD: float = 100.0

    def __init__(self, hub_root: Optional[Path] = None):
        self.hub_root = Path(hub_root) if hub_root else Path(__file__).resolve().parents[2]
        self.alerts_file = self.hub_root / "data" / "sentinel_alerts.json"
        self.self_heal_dir = self.hub_root / "docs" / "plans" / "self_heal"
        self._start_time = time.time()

    @property
    def start_time(self) -> float:
        return self._start_time

    def get_workers_health(self, include_details: bool = True) -> Dict[str, Any]:
        """Queries the status and metadata cards for all 14 swarm agents."""
        try:
            from core.orchestrator.swarm_coordinator import GerychSwarmCoordinator
            from core.orchestrator.visual_canvas_control import SWARM_WORKER_COLORS

            agents_dir = str(self.hub_root / "core" / "orchestrator" / "agents")
            coordinator = GerychSwarmCoordinator(agents_dir=agents_dir)
            raw_agents = coordinator.list_agents()

            workers = []
            ready_count = 0
            busy_count = 0

            for a in raw_agents:
                agent_id = a.get("agent_id", "unknown")
                color_info = SWARM_WORKER_COLORS.get(agent_id, {
                    "canvas_color": "0",
                    "hex": "#94A3B8",
                    "badge": f"🤖 {agent_id}"
                })

                status = a.get("status") or "ready"
                if status == "busy":
                    busy_count += 1
                elif status in ("ready", "active"):
                    ready_count += 1

                worker_entry = {
                    "agent_id": agent_id,
                    "name": a.get("name") or agent_id.replace("_", " ").title(),
                    "status": status,
                    "capabilities": a.get("capabilities", []),
                    "badge": color_info.get("badge", f"🤖 {agent_id}"),
                    "hex": color_info.get("hex", "#94A3B8"),
                    "hex_color": color_info.get("hex", "#94A3B8"),
                    "canvas_color": color_info.get("canvas_color", "0"),
                }
                workers.append(worker_entry)

            result: Dict[str, Any] = {
                "total_agents": len(workers),
                "total_workers": len(workers),
                "ready_count": ready_count,
                "ready_workers": ready_count,
                "busy_count": busy_count,
                "busy_workers": busy_count,
            }
            if include_details:
                result["agents"] = workers
                result["workers"] = workers
            return result
        except Exception as e:
            logger.warning("Failed to collect worker health: %s", e)
            result = {
                "total_agents": 14,
                "total_workers": 14,
                "ready_count": 0,
                "ready_workers": 0,
                "busy_count": 0,
                "busy_workers": 0,
                "error": str(e),
            }
            if include_details:
                result["agents"] = []
                result["workers"] = []
            return result

    def get_sentinel_health(self, max_age_seconds: int = 900) -> Dict[str, Any]:
        """Reads recent Sentinel Watchdog alerts and pending self-healing tasks."""
        active_alerts: List[Dict[str, Any]] = []
        critical_count = 0
        warning_count = 0

        if self.alerts_file.exists():
            try:
                mtime = self.alerts_file.stat().st_mtime
                is_fresh = (time.time() - mtime) <= max_age_seconds
                if is_fresh:
                    with open(self.alerts_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    raw_alerts = data.get("alerts", [])
                    if isinstance(raw_alerts, list):
                        for item in raw_alerts:
                            sev = str(item.get("severity", "WARNING")).upper()
                            if sev == "CRITICAL":
                                critical_count += 1
                            else:
                                warning_count += 1
                            active_alerts.append(item)
            except Exception as e:
                logger.warning("Failed to parse sentinel alerts: %s", e)

        # Count pending self-healing plans
        pending_self_heal_count = 0
        if self.self_heal_dir.exists():
            try:
                pending_self_heal_count = len(list(self.self_heal_dir.glob("TASK-DNK-SELFHEAL-*.md")))
            except Exception:
                pass

        sentinel_status = "clean"
        if critical_count > 0:
            sentinel_status = "critical"
        elif warning_count > 0 or pending_self_heal_count > 0:
            sentinel_status = "warning"

        if len(active_alerts) > 0 and sentinel_status == "clean":
            sentinel_status = "alerts_active"

        return {
            "status": sentinel_status,
            "total_active_alerts": len(active_alerts),
            "active_alerts_count": len(active_alerts),
            "critical_count": critical_count,
            "critical_alerts_count": critical_count,
            "warning_count": warning_count,
            "warning_alerts_count": warning_count,
            "pending_self_heal_tasks": pending_self_heal_count,
            "self_heal_plans_count": pending_self_heal_count,
            "alerts": active_alerts,
        }

    def get_accounting_health(
        self,
        workspace_id: str = "ws-alpha-001",
        spend_limit_usd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculates token burn rate, total expenditure, and budget saturation."""
        limit = spend_limit_usd if spend_limit_usd is not None else self.DEFAULT_SPEND_LIMIT_USD
        try:
            from core.accounting_engine import AccountingEngine
            log_path = str(self.hub_root / "telemetry" / "accounting_log.json")
            engine = AccountingEngine(log_path=log_path)
            metrics = engine.get_aggregated_metrics(project_id=workspace_id)

            total_cost = float(metrics.get("total_cost_usd", 0.0))
            saturation_pct = (total_cost / limit * 100.0) if limit > 0 else 0.0

            budget_status = "normal"
            if saturation_pct >= 100.0:
                budget_status = "exceeded"
            elif saturation_pct >= 80.0:
                budget_status = "near_limit"

            return {
                "workspace_id": workspace_id,
                "budget_status": budget_status,
                "total_runs": metrics.get("total_runs", 0),
                "success_rate_pct": metrics.get("success_rate", 100.0),
                "total_tokens_in": metrics.get("total_tokens_in", 0),
                "total_tokens_out": metrics.get("total_tokens_out", 0),
                "total_cost_usd": round(total_cost, 4),
                "spend_limit_usd": limit,
                "spend_saturation_pct": round(saturation_pct, 2),
                "total_usd_saved": metrics.get("total_usd_saved", 0.0),
            }
        except Exception as e:
            logger.warning("Failed to collect accounting health: %s", e)
            return {
                "workspace_id": workspace_id,
                "budget_status": "unknown",
                "error": str(e),
                "total_cost_usd": 0.0,
                "spend_limit_usd": limit,
                "spend_saturation_pct": 0.0,
            }

    def get_canvas_bridge_health(self) -> Dict[str, Any]:
        """Inspects real-time Canvas WebSocket connectivity metrics."""
        try:
            from apps.api.routers.canvas_bridge import canvas_ws_manager
            stats = canvas_ws_manager.get_stats()
            return {
                "status": "active" if stats.get("total_connections", 0) > 0 else "idle",
                "active_connections": stats.get("total_connections", 0),
                **stats,
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "active_connections": 0,
                "total_connections": 0,
                "subscribed_canvases_count": 0,
                "subscribed_canvases": [],
                "error": str(e),
            }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Returns host process uptime and runtime information."""
        uptime = round(time.time() - self._start_time, 2)
        rss_mb = 0.0
        try:
            import resource
            # ru_maxrss is in KB on Linux, bytes on macOS
            raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform == "darwin":
                rss_mb = round(raw_rss / (1024 * 1024), 2)
            else:
                rss_mb = round(raw_rss / 1024, 2)
        except Exception:
            pass

        return {
            "uptime_seconds": uptime,
            "memory_rss_mb": rss_mb,
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
        }

    def get_health_status(
        self,
        workspace_id: str = "ws-alpha-001",
        include_agent_details: bool = True,
        spend_limit_usd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Unified aggregator calculating holistic Swarm Health Status.
        Status calculation:
          - 'unhealthy' if critical sentinel anomalies exist or budget exceeded.
          - 'degraded' if warnings exist, budget near limit, or agents missing.
          - 'healthy' when all subsystems operate normally.
        """
        workers = self.get_workers_health(include_details=include_agent_details)
        sentinel = self.get_sentinel_health()
        accounting = self.get_accounting_health(workspace_id=workspace_id, spend_limit_usd=spend_limit_usd)
        bridge = self.get_canvas_bridge_health()
        system = self.get_system_metrics()

        # Deduce overall status
        status = "healthy"
        status_reasons: List[str] = []

        if sentinel["critical_count"] > 0:
            status = "unhealthy"
            status_reasons.append(f"{sentinel['critical_count']} critical sentinel alert(s) detected")
        elif accounting["budget_status"] == "exceeded":
            status = "unhealthy"
            status_reasons.append("Accounting token spend limit exceeded")

        if status != "unhealthy":
            if sentinel["warning_count"] > 0 or sentinel["pending_self_heal_tasks"] > 0:
                status = "degraded"
                status_reasons.append(f"{sentinel['warning_count']} warning alert(s), {sentinel['pending_self_heal_tasks']} pending self-heal plan(s)")
            if accounting["budget_status"] == "near_limit":
                status = "degraded"
                status_reasons.append("Accounting token spend saturation >= 80%")
            if workers["total_agents"] < 14:
                status = "degraded"
                status_reasons.append(f"Incomplete swarm: {workers['total_agents']}/14 agents registered")

        if not status_reasons:
            status_reasons.append("All swarm subsystems operational")

        return {
            "overall_status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status_reasons": status_reasons,
            "workspace_id": workspace_id,
            "active_workers": workers,
            "sentinel": sentinel,
            "accounting": accounting,
            "canvas_bridge": bridge,
            "system": system,
            "system_metrics": system,
            "system_resources": system,
        }

    def resolve_or_heal_alert(
        self,
        alert_id: Optional[str] = None,
        action: str = "resolve",
        workspace_id: str = "ws-alpha-001",
    ) -> Dict[str, Any]:
        """
        Actively resolves / auto-heals Sentinel anomalies and archives resolved self-healing plans.
        Uses concurrency-safe atomic operations.
        """
        healed_alerts: List[Dict[str, Any]] = []
        archive_path = self.hub_root / "data" / "sentinel_alerts_archive.json"

        if self.alerts_file.exists():
            def updater(data: Any) -> Any:
                nonlocal healed_alerts
                if not isinstance(data, dict):
                    return data
                alerts = data.get("alerts", [])
                if not isinstance(alerts, list):
                    return data

                remaining: List[Dict[str, Any]] = []
                for a in alerts:
                    curr_id = str(a.get("alert_id") or a.get("id") or a.get("anomaly_id") or "")
                    if alert_id is None or alert_id in ("all", "*") or curr_id == alert_id:
                        healed_entry = dict(a)
                        healed_entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
                        healed_entry["resolution_action"] = action
                        healed_alerts.append(healed_entry)
                    else:
                        remaining.append(a)

                data["alerts"] = remaining
                return data

            atomic_json_update(self.alerts_file, updater, default={"alerts": []})

            # Append healed alerts to archive
            if healed_alerts:
                def archive_updater(archive_data: Any) -> Any:
                    if not isinstance(archive_data, list):
                        archive_data = []
                    archive_data.extend(healed_alerts)
                    return archive_data[-200:]  # keep last 200 resolved

                archive_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_json_update(archive_path, archive_updater, default=[])

        # Archive self-heal plans
        archived_plans_count = 0
        if self.self_heal_dir.exists():
            archive_dir = self.self_heal_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            for plan_file in self.self_heal_dir.glob("TASK-DNK-SELFHEAL-*.md"):
                try:
                    target = archive_dir / plan_file.name
                    plan_file.rename(target)
                    archived_plans_count += 1
                except Exception as e:
                    logger.warning("Failed to archive self heal plan %s: %s", plan_file.name, e)

        return {
            "success": True,
            "action": action,
            "workspace_id": workspace_id,
            "healed_alerts_count": len(healed_alerts),
            "archived_plans_count": archived_plans_count,
            "resolved_alerts": healed_alerts,
            "message": f"Successfully healed {len(healed_alerts)} alert(s) and {archived_plans_count} self-heal plan(s)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
