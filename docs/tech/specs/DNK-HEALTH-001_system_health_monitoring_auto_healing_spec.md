<!-- --- DNK-MRH-HEADER ---
mrh_id: "DOC-SPEC-DNK-HEALTH-001"
purpose: "TaskDNA Specification for System Health Monitoring & Auto-Healing Engine (DNK-HEALTH-001)"
canonical_source: true
alters_files: [
  "apps/api/db/models/health_metric_rule.py",
  "apps/api/db/models/system_incident.py",
  "apps/api/db/models/remediation_action.py",
  "apps/api/db/models/auto_healing_policy.py",
  "apps/api/db/models/service_health_snapshot.py",
  "apps/api/db/models/alert_notification_log.py",
  "apps/api/services/health_metric_aggregator.py",
  "apps/api/services/incident_detection_engine.py",
  "apps/api/services/auto_healing_executor.py",
  "apps/api/services/alert_dispatcher_service.py",
  "apps/api/routers/health_monitoring_router.py"
]
triggers_tasks: ["DNK-HEALTH-001-PHASE1", "DNK-HEALTH-001-PHASE2", "DNK-HEALTH-001-PHASE3", "DNK-HEALTH-001-PHASE4"]
status: "Active"
version: "1.0.0"
updated_at: "2026-08-29"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER --->

# 🩺 DNK-HEALTH-001: System Health Monitoring & Auto-Healing Engine

## 1. Overview & Business Objectives
DNK-HEALTH-001 establishes an enterprise-grade, proactive self-healing infrastructure layer across the DNK OS ecosystem. It provides continuous real-time anomaly detection, sliding-window telemetry aggregation, automatic incident classification, and deterministic safe remediation playbooks (process recovery, traffic isolation, cache eviction, replica auto-scaling, circuit breaking) with flap-prevention and audit trails.

## 2. Core Architecture & Components
1. **Health Metric Rules & Aggregation**:
   - Multi-dimensional metric collection (CPU, RAM, RTT latency, Error Rate, Disk IOPS, P99 SLA).
   - Sliding-window statistical evaluation (mean, p95, spike detection, threshold breaching).
2. **Incident Detection Engine**:
   - Automated severity grading (`INFO`, `WARNING`, `CRITICAL`, `FATAL`).
   - Root-cause heuristic classification & deduplication.
3. **Auto-Healing & Remediation Executor**:
   - Deterministic execution of registered recovery playbooks (`restart_service`, `drain_traffic`, `clear_cache`, `scale_replicas`, `trip_circuit_breaker`).
   - Flap-prevention circuit breakers & max-retry limits.
4. **Alert Notification & Telemetry Dashboard**:
   - Event broadcast and multichannel alerting.
   - REST API for live topology health snapshots, incident history, and manual remediation overrides.

## 3. Data Models (Phase 1)
- `HealthMetricRule`: Declarative threshold rules for services & nodes.
- `SystemIncident`: Tracked active and resolved system incidents with severity & status.
- `RemediationAction`: Executed or pending self-healing recovery actions.
- `AutoHealingPolicy`: Configured policies linking triggers to remediation workflows.
- `ServiceHealthSnapshot`: Time-series state snapshots of services and components.
- `AlertNotificationLog`: Log of dispatched alert notifications across channels.
