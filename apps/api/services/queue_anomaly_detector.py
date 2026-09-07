# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-SERVICE-QUEUE-ANOMALY-DETECTOR"
# purpose: "Queue Analytics and Anomaly Detection Engine for Latency, Spikes and Starvation"
# canonical_source: true
# alters_files: ["apps/api/services/queue_anomaly_detector.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE3"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class QueueAnomalyDetector:
    """Detects queue spikes, processing stalls, latency outliers, and dead-letter anomalies."""

    def __init__(self, z_score_threshold: float = 3.0, window_size: int = 50):
        self.z_score_threshold = z_score_threshold
        self.window_size = window_size
        # In-memory history: {f"{workspace_id}:{queue_name}": [metric_dict, ...]}
        self._queue_history: Dict[str, List[Dict[str, Any]]] = {}
        # In-memory active alerts: {alert_id: alert_dict}
        self._alerts: Dict[str, Dict[str, Any]] = {}

    def _get_key(self, workspace_id: str, queue_name: str) -> str:
        return f"{workspace_id}:{queue_name}"

    def ingest_queue_metric(self, metric: Dict[str, Any]) -> None:
        """Ingest a QueueMetric payload."""
        workspace_id = metric.get("workspace_id", "default-ws")
        queue_name = metric.get("queue_name", "default-queue")
        key = self._get_key(workspace_id, queue_name)

        if key not in self._queue_history:
            self._queue_history[key] = []

        # Store metric with normalized timestamp
        ts = metric.get("timestamp")
        if isinstance(ts, datetime):
            metric_copy = dict(metric)
            metric_copy["timestamp"] = ts.isoformat()
        else:
            metric_copy = dict(metric)
            if not metric_copy.get("timestamp"):
                metric_copy["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._queue_history[key].append(metric_copy)
        # Bounded sliding window
        if len(self._queue_history[key]) > self.window_size:
            self._queue_history[key] = self._queue_history[key][-self.window_size :]

    def detect_anomalies(
        self,
        workspace_id: str,
        cluster_id: str,
        queue_name: str,
        current_metric: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run statistical anomaly checks across queue depth, wait time, dead-letter count, and stall conditions."""
        key = self._get_key(workspace_id, queue_name)
        history = self._queue_history.get(key, [])

        if current_metric:
            self.ingest_queue_metric(current_metric)
            metric_to_check = current_metric
        elif history:
            metric_to_check = history[-1]
        else:
            return []

        generated_alerts: List[Dict[str, Any]] = []
        now_utc = datetime.now(timezone.utc)

        # 1. Check Dead Letter Queue Anomaly
        dlq_count = metric_to_check.get("dead_letter_count", 0)
        if dlq_count > 0:
            alert = self._create_alert(
                workspace_id=workspace_id,
                cluster_id=cluster_id,
                anomaly_type="queue_overflow",
                severity="critical" if dlq_count > 10 else "warning",
                metric_name="dead_letter_count",
                detected_value=float(dlq_count),
                expected_value=0.0,
                z_score=5.0,
                description=f"Dead letter count reached {dlq_count} messages in queue {queue_name}.",
                suggested_action="Investigate poisoned messages and worker error logs immediately.",
                now_utc=now_utc,
            )
            generated_alerts.append(alert)

        # 2. Check Starvation / Processing Stall Condition
        incoming_rate = metric_to_check.get("incoming_rate_tps", 0.0)
        processing_rate = metric_to_check.get("processing_rate_tps", 0.0)
        queue_depth = metric_to_check.get("queue_depth", 0)

        if incoming_rate > 5.0 and processing_rate == 0.0 and queue_depth > 10:
            alert = self._create_alert(
                workspace_id=workspace_id,
                cluster_id=cluster_id,
                anomaly_type="starvation",
                severity="critical",
                metric_name="processing_rate_tps",
                detected_value=0.0,
                expected_value=incoming_rate,
                z_score=4.0,
                description=f"Worker starvation detected: processing rate is 0 TPS despite {queue_depth} queued items.",
                suggested_action="Check worker health, restart stalled agent instances, or scale worker pool.",
                now_utc=now_utc,
            )
            generated_alerts.append(alert)

        # 3. Statistical Z-Score Anomaly on Queue Depth
        if len(history) >= 5:
            depths = [float(m.get("queue_depth", 0)) for m in history[:-1]]
            mean_depth = sum(depths) / len(depths)
            variance = sum((d - mean_depth) ** 2 for d in depths) / len(depths)
            std_depth = math.sqrt(variance)

            cur_depth = float(metric_to_check.get("queue_depth", 0))
            if std_depth > 1e-4:
                z = (cur_depth - mean_depth) / std_depth
                if z >= self.z_score_threshold:
                    alert = self._create_alert(
                        workspace_id=workspace_id,
                        cluster_id=cluster_id,
                        anomaly_type="spike",
                        severity="critical" if z >= 4.0 else "warning",
                        metric_name="queue_depth",
                        detected_value=cur_depth,
                        expected_value=round(mean_depth, 2),
                        z_score=round(z, 2),
                        description=f"Sudden queue depth spike detected (z-score: {z:.2f}, depth: {cur_depth}).",
                        suggested_action="Scale out agent consumers or inspect upstream traffic burst.",
                        now_utc=now_utc,
                    )
                    generated_alerts.append(alert)

        # 4. Latency Outlier on P95 Latency
        p95 = metric_to_check.get("p95_latency_ms", 0.0)
        avg_wait = metric_to_check.get("avg_wait_time_ms", 0.0)
        if p95 > 1000.0 or (avg_wait > 0 and p95 > 3.0 * avg_wait and p95 > 300.0):
            alert = self._create_alert(
                workspace_id=workspace_id,
                cluster_id=cluster_id,
                anomaly_type="threshold_breach",
                severity="warning" if p95 < 2500.0 else "critical",
                metric_name="p95_latency_ms",
                detected_value=float(p95),
                expected_value=round(avg_wait, 2),
                z_score=3.2,
                description=f"P95 latency outlier detected ({p95:.1f}ms exceeds normal bounds).",
                suggested_action="Optimize query latency, increase inference concurrency, or add cache layer.",
                now_utc=now_utc,
            )
            generated_alerts.append(alert)

        return generated_alerts

    def _create_alert(
        self,
        workspace_id: str,
        cluster_id: str,
        anomaly_type: str,
        severity: str,
        metric_name: str,
        detected_value: float,
        expected_value: float,
        z_score: float,
        description: str,
        suggested_action: str,
        now_utc: datetime,
    ) -> Dict[str, Any]:
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"
        alert = {
            "id": alert_id,
            "workspace_id": workspace_id,
            "cluster_id": cluster_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "metric_name": metric_name,
            "detected_value": detected_value,
            "expected_value": expected_value,
            "z_score": z_score,
            "description": description,
            "suggested_action": suggested_action,
            "status": "open",
            "detected_at": now_utc.isoformat(),
            "resolved_at": None,
            "created_at": now_utc.isoformat(),
        }
        self._alerts[alert_id] = alert
        return alert

    def get_active_alerts(
        self, workspace_id: Optional[str] = None, cluster_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve open anomaly alerts filtered by workspace and/or cluster."""
        alerts = [a for a in self._alerts.values() if a["status"] == "open"]
        if workspace_id:
            alerts = [a for a in alerts if a["workspace_id"] == workspace_id]
        if cluster_id:
            alerts = [a for a in alerts if a["cluster_id"] == cluster_id]
        return sorted(alerts, key=lambda x: x["detected_at"], reverse=True)

    def resolve_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Mark an active alert as resolved."""
        if alert_id in self._alerts:
            self._alerts[alert_id]["status"] = "resolved"
            self._alerts[alert_id]["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return self._alerts[alert_id]
        return None

    def get_queue_health_summary(
        self, workspace_id: str, queue_name: str
    ) -> Dict[str, Any]:
        """Compute aggregated health status and statistics for a queue."""
        key = self._get_key(workspace_id, queue_name)
        history = self._queue_history.get(key, [])
        if not history:
            return {
                "workspace_id": workspace_id,
                "queue_name": queue_name,
                "status": "idle",
                "sample_count": 0,
                "latest_depth": 0,
                "avg_depth": 0.0,
                "open_alerts_count": 0,
            }

        latest = history[-1]
        depths = [float(m.get("queue_depth", 0)) for m in history]
        avg_depth = sum(depths) / len(depths)

        open_alerts = [
            a
            for a in self._alerts.values()
            if a["workspace_id"] == workspace_id and a["status"] == "open"
        ]

        status = "healthy"
        if any(a["severity"] == "critical" for a in open_alerts):
            status = "critical"
        elif any(a["severity"] == "warning" for a in open_alerts):
            status = "warning"

        return {
            "workspace_id": workspace_id,
            "queue_name": queue_name,
            "status": status,
            "sample_count": len(history),
            "latest_depth": latest.get("queue_depth", 0),
            "avg_depth": round(avg_depth, 2),
            "open_alerts_count": len(open_alerts),
            "latest_p95_latency_ms": latest.get("p95_latency_ms", 0.0),
        }
