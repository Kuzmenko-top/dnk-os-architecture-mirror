# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-SERVICE-AUTOSCALER-RECOMMENDER"
# purpose: "Autonomous Horizontal Capacity Auto-Scaling and Cost Optimization Engine"
# canonical_source: true
# alters_files: ["apps/api/services/capacity_autoscaler_recommender.py"]
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


class CapacityAutoscalerRecommender:
    """Evaluates telemetry and load forecasts to emit horizontal scaling recommendations and cost optimization insights."""

    def __init__(
        self,
        target_cpu_pct: float = 70.0,
        target_queue_depth: int = 20,
        min_replicas: int = 2,
        max_replicas: int = 32,
        hourly_node_cost_ondemand: float = 0.24,
        hourly_node_cost_spot: float = 0.08,
    ):
        self.target_cpu_pct = target_cpu_pct
        self.target_queue_depth = target_queue_depth
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.hourly_node_cost_ondemand = hourly_node_cost_ondemand
        self.hourly_node_cost_spot = hourly_node_cost_spot

        # In-memory store: {rec_id: rec_dict}
        self._recommendations: Dict[str, Dict[str, Any]] = {}
        # In-memory reports: {report_id: report_dict}
        self._cost_reports: Dict[str, Dict[str, Any]] = {}

    def evaluate_scaling(
        self,
        workspace_id: str,
        cluster_id: str,
        current_replicas: int,
        telemetry: Dict[str, Any],
        forecast: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate real-time metrics and load forecasts to produce scale-out, scale-in, or rebalance recommendations."""
        cpu = telemetry.get("cpu_utilization_pct", 50.0)
        queue_depth = telemetry.get("queue_depth", 0)
        memory = telemetry.get("memory_utilization_pct", 50.0)

        # Lookahead from forecast if present
        predicted_cpu = forecast.get("predicted_value_p90", cpu) if forecast else cpu
        effective_cpu = max(cpu, predicted_cpu)

        target_replicas = current_replicas
        rec_type = "maintain"
        rationale = ""
        urgency = "low"
        target_metric = "cpu"

        # 1. Scale-Out Triggers
        if effective_cpu > self.target_cpu_pct or queue_depth > self.target_queue_depth:
            rec_type = "scale_out"
            urgency = "critical" if effective_cpu > 85.0 or queue_depth > 50 else "high"

            # Compute needed replicas based on CPU demand
            cpu_factor = effective_cpu / self.target_cpu_pct
            # Compute needed replicas based on queue pressure
            queue_factor = (queue_depth / self.target_queue_depth) if self.target_queue_depth > 0 else 1.0

            scaling_factor = max(cpu_factor, queue_factor)
            target_replicas = math.ceil(current_replicas * scaling_factor)
            target_replicas = min(self.max_replicas, max(current_replicas + 1, target_replicas))

            target_metric = "queue_depth" if queue_factor > cpu_factor else "cpu"
            rationale = (
                f"High load detected: {target_metric} reached {effective_cpu if target_metric == 'cpu' else queue_depth}. "
                f"Scaling out from {current_replicas} to {target_replicas} replicas to preserve SLA."
            )

        # 2. Scale-In Triggers (Low CPU and low queue depth)
        elif effective_cpu < 25.0 and queue_depth < 5 and current_replicas > self.min_replicas:
            rec_type = "scale_in"
            urgency = "low"
            # Calculate scaled down replica count
            scale_in_factor = max(0.5, effective_cpu / self.target_cpu_pct)
            target_replicas = max(self.min_replicas, math.floor(current_replicas * scale_in_factor))

            if target_replicas < current_replicas:
                rationale = (
                    f"Cluster under-utilized: CPU is at {effective_cpu:.1f}% and queue depth is {queue_depth}. "
                    f"Scaling in from {current_replicas} to {target_replicas} replicas to eliminate idle costs."
                )
            else:
                return None

        # 3. No scaling needed
        if target_replicas == current_replicas or rec_type == "maintain":
            return None

        # Calculate estimated cost delta
        replica_delta = target_replicas - current_replicas
        # Assume blended 50/50 spot & on-demand price for worker additions
        blended_hourly_cost = (self.hourly_node_cost_ondemand + self.hourly_node_cost_spot) / 2.0
        cost_delta = round(replica_delta * blended_hourly_cost, 4)

        now_utc = datetime.now(timezone.utc)
        rec_id = f"rec_{uuid.uuid4().hex[:12]}"
        recommendation = {
            "id": rec_id,
            "workspace_id": workspace_id,
            "cluster_id": cluster_id,
            "recommendation_type": rec_type,
            "current_replicas": current_replicas,
            "recommended_replicas": target_replicas,
            "target_metric": target_metric,
            "estimated_cost_delta_usd_per_hour": cost_delta,
            "rationale": rationale,
            "urgency": urgency,
            "status": "pending",
            "recommended_at": now_utc.isoformat(),
            "executed_at": None,
            "created_at": now_utc.isoformat(),
        }

        self._recommendations[rec_id] = recommendation
        return recommendation

    def generate_cost_report(
        self,
        workspace_id: str,
        cluster_id: str,
        total_nodes: int,
        spot_nodes: int,
        idle_nodes: int = 0,
        billing_period: str = "daily",
    ) -> Dict[str, Any]:
        """Generate a comprehensive spot-mix and idle cost optimization report."""
        on_demand_nodes = max(0, total_nodes - spot_nodes)
        hours_in_period = 24 if billing_period == "daily" else (24 * 30)

        # Current spend
        current_hourly_spend = (on_demand_nodes * self.hourly_node_cost_ondemand) + (
            spot_nodes * self.hourly_node_cost_spot
        )
        current_spend_usd = round(current_hourly_spend * hours_in_period, 2)

        # Optimal configuration: 75% Spot for workers, keeping at least 1 On-Demand master
        target_spot_ratio = 0.75
        recommended_spot_nodes = min(total_nodes - 1, math.floor(total_nodes * target_spot_ratio))
        recommended_spot_nodes = max(0, recommended_spot_nodes)
        recommended_on_demand = total_nodes - recommended_spot_nodes

        optimized_hourly_spend = (recommended_on_demand * self.hourly_node_cost_ondemand) + (
            recommended_spot_nodes * self.hourly_node_cost_spot
        )
        # Deduct potential savings from shutting down idle nodes
        idle_hourly_cost = idle_nodes * self.hourly_node_cost_ondemand
        optimized_hourly_spend = max(0.0, optimized_hourly_spend - idle_hourly_cost)
        optimized_spend_usd = round(optimized_hourly_spend * hours_in_period, 2)

        potential_savings = max(0.0, round(current_spend_usd - optimized_spend_usd, 2))
        savings_pct = (
            round((potential_savings / current_spend_usd) * 100.0, 2)
            if current_spend_usd > 0
            else 0.0
        )
        spot_ratio = round((spot_nodes / total_nodes), 2) if total_nodes > 0 else 0.0

        opportunities = []
        if spot_nodes < recommended_spot_nodes:
            opportunities.append({
                "type": "spot_migration",
                "description": f"Convert {recommended_spot_nodes - spot_nodes} On-Demand nodes to Spot instances.",
                "estimated_savings_usd": round(
                    (recommended_spot_nodes - spot_nodes)
                    * (self.hourly_node_cost_ondemand - self.hourly_node_cost_spot)
                    * hours_in_period,
                    2,
                ),
            })

        if idle_nodes > 0:
            opportunities.append({
                "type": "idle_reclamation",
                "description": f"Decommission {idle_nodes} idle agent worker nodes.",
                "estimated_savings_usd": round(idle_hourly_cost * hours_in_period, 2),
            })

        now_utc = datetime.now(timezone.utc)
        report_id = f"cost_{uuid.uuid4().hex[:12]}"
        report = {
            "id": report_id,
            "workspace_id": workspace_id,
            "cluster_id": cluster_id,
            "billing_period": billing_period,
            "current_spend_usd": current_spend_usd,
            "optimized_spend_usd": optimized_spend_usd,
            "potential_savings_usd": potential_savings,
            "savings_percentage": savings_pct,
            "spot_instance_ratio": spot_ratio,
            "idle_resource_cost_usd": round(idle_hourly_cost * hours_in_period, 2),
            "optimization_opportunities": opportunities,
            "generated_at": now_utc.isoformat(),
            "created_at": now_utc.isoformat(),
        }

        self._cost_reports[report_id] = report
        return report

    def get_pending_recommendations(
        self, workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all pending auto-scaling recommendations."""
        recs = [r for r in self._recommendations.values() if r["status"] == "pending"]
        if workspace_id:
            recs = [r for r in recs if r["workspace_id"] == workspace_id]
        return sorted(recs, key=lambda x: x["recommended_at"], reverse=True)

    def get_cost_reports(
        self, workspace_id: Optional[str] = None, cluster_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get generated cost optimization reports."""
        reports = list(self._cost_reports.values())
        if workspace_id:
            reports = [r for r in reports if r.get("workspace_id") == workspace_id]
        if cluster_id:
            reports = [r for r in reports if r.get("cluster_id") == cluster_id]
        return sorted(reports, key=lambda x: x.get("generated_at", ""), reverse=True)

    def execute_recommendation(self, recommendation_id: str) -> Optional[Dict[str, Any]]:
        """Mark a recommendation as executed."""
        if recommendation_id in self._recommendations:
            self._recommendations[recommendation_id]["status"] = "executed"
            self._recommendations[recommendation_id]["executed_at"] = (
                datetime.now(timezone.utc).isoformat()
            )
            return self._recommendations[recommendation_id]
        return None
