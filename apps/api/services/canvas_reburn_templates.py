# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_reburn_templates"
# purpose: "Pre-built E-Commerce and ReBurn Hardware Integration Workflow Templates for Visual Canvas (DNK-CANVAS-001 Phase 4)"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from apps.api.schemas.workflow_dag_schemas import (
    WorkflowDAG,
    WorkflowNode,
    WorkflowEdge,
    WorkflowNodeType,
    NodePosition
)


class WorkflowTemplateMetadata(BaseModel):
    template_id: str
    name: str
    category: str = Field(description="e_commerce | hardware | hybrid")
    description: str
    tags: List[str] = Field(default_factory=list)
    nodes_count: int
    edges_count: int


class CanvasTemplateRegistry:
    """Registry providing out-of-the-box pre-configured workflows for Shopify & ReBurn Hardware."""

    def __init__(self):
        self._templates: Dict[str, WorkflowDAG] = {}
        self._metadata: Dict[str, WorkflowTemplateMetadata] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        # 1. Shopify Automated Order Fulfillment Template
        shopify_fulfillment = WorkflowDAG(
            id="template-shopify-fulfillment",
            name="Shopify Automated Order Fulfillment",
            description="End-to-end Shopify order webhook listener, A2A fraud & inventory check, and automated fulfillment creation.",
            workspace_id="ws-alpha-001",
            version=1,
            nodes=[
                WorkflowNode(
                    id="trig-order-created",
                    type=WorkflowNodeType.EVENT_TRIGGER,
                    label="Shopify Order Created Webhook",
                    position=NodePosition(x=200, y=50),
                    config={
                        "stream_topic": "shopify-orders",
                        "event_type": "orders/create",
                        "debounce_ms": 50
                    }
                ),
                WorkflowNode(
                    id="agent-order-audit",
                    type=WorkflowNodeType.A2A_AGENT,
                    label="A2A Fraud & Risk Auditor",
                    position=NodePosition(x=200, y=200),
                    config={
                        "agent_id": "gerych_auditor",
                        "role": "auditor",
                        "task_prompt": "Audit incoming order for risk flags and stock availability.",
                        "consensus_threshold": 0.85
                    }
                ),
                WorkflowNode(
                    id="act-create-fulfillment",
                    type=WorkflowNodeType.SHOPIFY_ACTION,
                    label="Shopify Create Fulfillment",
                    position=NodePosition(x=200, y=350),
                    config={
                        "shop_domain": "reburn-lab.myshopify.com",
                        "action_type": "order_create",
                        "api_version": "2026-01"
                    }
                )
            ],
            edges=[
                WorkflowEdge(id="e-t-a", source="trig-order-created", target="agent-order-audit"),
                WorkflowEdge(id="e-a-s", source="agent-order-audit", target="act-create-fulfillment")
            ]
        )
        self._register(
            template_id="template-shopify-fulfillment",
            dag=shopify_fulfillment,
            category="e_commerce",
            description="End-to-end Shopify order webhook listener, A2A fraud & inventory check, and automated fulfillment creation.",
            tags=["shopify", "orders", "a2a", "fulfillment"]
        )

        # 2. Shopify Real-Time Inventory Sync Template
        shopify_inventory_sync = WorkflowDAG(
            id="template-shopify-inventory-sync",
            name="Shopify Real-Time Inventory Sync",
            description="Synchronizes warehouse stock levels with Shopify catalog inventory via batch delta computing.",
            workspace_id="ws-alpha-001",
            version=1,
            nodes=[
                WorkflowNode(
                    id="trig-inv-stream",
                    type=WorkflowNodeType.EVENT_TRIGGER,
                    label="Warehouse Stock Stream",
                    position=NodePosition(x=250, y=50),
                    config={
                        "stream_topic": "warehouse-inventory-stream",
                        "event_type": "inventory/level_changed",
                        "debounce_ms": 100
                    }
                ),
                WorkflowNode(
                    id="batch-reconcile",
                    type=WorkflowNodeType.BATCH_TASK,
                    label="Batch Delta Calculator",
                    position=NodePosition(x=250, y=200),
                    config={
                        "batch_job_type": "inventory_delta_reconciliation",
                        "payload_template": {"mode": "reconcile_all"}
                    }
                ),
                WorkflowNode(
                    id="act-shopify-inv-update",
                    type=WorkflowNodeType.SHOPIFY_ACTION,
                    label="Shopify Inventory Adjust",
                    position=NodePosition(x=250, y=350),
                    config={
                        "shop_domain": "reburn-lab.myshopify.com",
                        "action_type": "inventory_sync",
                        "api_version": "2026-01"
                    }
                )
            ],
            edges=[
                WorkflowEdge(id="e-inv-1", source="trig-inv-stream", target="batch-reconcile"),
                WorkflowEdge(id="e-inv-2", source="batch-reconcile", target="act-shopify-inv-update")
            ]
        )
        self._register(
            template_id="template-shopify-inventory-sync",
            dag=shopify_inventory_sync,
            category="e_commerce",
            description="Synchronizes warehouse stock levels with Shopify catalog inventory via batch delta computing.",
            tags=["shopify", "inventory", "batch", "sync"]
        )

        # 3. ReBurn IoT Sensor Monitoring & Diagnostic Template
        reburn_sensor_monitor = WorkflowDAG(
            id="template-reburn-sensor-monitor",
            name="ReBurn IoT Sensor Monitor & Diagnostics",
            description="Reads ReBurn hardware sensors, passes telemetry to diagnostic agent, and dynamically triggers actuators.",
            workspace_id="ws-alpha-001",
            version=1,
            nodes=[
                WorkflowNode(
                    id="hw-thermal-sensor",
                    type=WorkflowNodeType.HARDWARE_ACTION,
                    label="ReBurn Thermal & Pressure Sensors",
                    position=NodePosition(x=200, y=50),
                    config={
                        "device_id": "reburn-chamber-sensor-01",
                        "action_type": "read_sensor",
                        "pin": 18,
                        "payload": {"channels": ["temp_celsius", "pressure_kpa"]}
                    }
                ),
                WorkflowNode(
                    id="agent-telemetry-eval",
                    type=WorkflowNodeType.A2A_AGENT,
                    label="Diagnostic AI Agent",
                    position=NodePosition(x=200, y=200),
                    config={
                        "agent_id": "dnk_security_guard",
                        "role": "diagnostics",
                        "task_prompt": "Evaluate telemetry metrics and detect anomaly spikes.",
                        "consensus_threshold": 0.9
                    }
                ),
                WorkflowNode(
                    id="hw-actuator-coolant",
                    type=WorkflowNodeType.HARDWARE_ACTION,
                    label="Coolant Pump Actuator",
                    position=NodePosition(x=200, y=350),
                    config={
                        "device_id": "reburn-actuator-coolant-01",
                        "action_type": "trigger_actuator",
                        "pin": 23,
                        "payload": {"mode": "adaptive_cooling", "target_temp": 45.0}
                    }
                )
            ],
            edges=[
                WorkflowEdge(id="e-reburn-1", source="hw-thermal-sensor", target="agent-telemetry-eval"),
                WorkflowEdge(id="e-reburn-2", source="agent-telemetry-eval", target="hw-actuator-coolant")
            ]
        )
        self._register(
            template_id="template-reburn-sensor-monitor",
            dag=reburn_sensor_monitor,
            category="hardware",
            description="Reads ReBurn hardware sensors, passes telemetry to diagnostic agent, and dynamically triggers actuators.",
            tags=["reburn", "hardware", "iot", "sensors", "actuators"]
        )

        # 4. ReBurn Emergency Valve Shutdown & Incident Alert Template
        reburn_emergency_shutdown = WorkflowDAG(
            id="template-reburn-emergency-shutdown",
            name="ReBurn Emergency Safety Shutdown & Incident Alert",
            description="Instant hardware fail-safe valve release and parallel A2A agent mesh incident escalation.",
            workspace_id="ws-alpha-001",
            version=1,
            nodes=[
                WorkflowNode(
                    id="trig-panic-event",
                    type=WorkflowNodeType.EVENT_TRIGGER,
                    label="Emergency Stop Stream Trigger",
                    position=NodePosition(x=250, y=50),
                    config={
                        "stream_topic": "reburn-safety-stream",
                        "event_type": "emergency/overpressure",
                        "debounce_ms": 0
                    }
                ),
                WorkflowNode(
                    id="hw-shutoff-valve",
                    type=WorkflowNodeType.HARDWARE_ACTION,
                    label="Emergency Pressure Relief Valve",
                    position=NodePosition(x=120, y=220),
                    config={
                        "device_id": "reburn-safety-valve-01",
                        "action_type": "gpio_write",
                        "pin": 4,
                        "payload": {"state": "OPEN_VENT", "fail_safe": True}
                    }
                ),
                WorkflowNode(
                    id="agent-incident-commander",
                    type=WorkflowNodeType.A2A_AGENT,
                    label="A2A Incident Commander",
                    position=NodePosition(x=380, y=220),
                    config={
                        "agent_id": "gerych_auditor",
                        "role": "incident_commander",
                        "task_prompt": "Log tamper-evident safety audit incident and notify operators.",
                        "consensus_threshold": 0.95
                    }
                )
            ],
            edges=[
                WorkflowEdge(id="e-em-1", source="trig-panic-event", target="hw-shutoff-valve"),
                WorkflowEdge(id="e-em-2", source="trig-panic-event", target="agent-incident-commander")
            ]
        )
        self._register(
            template_id="template-reburn-emergency-shutdown",
            dag=reburn_emergency_shutdown,
            category="hardware",
            description="Instant hardware fail-safe valve release and parallel A2A agent mesh incident escalation.",
            tags=["reburn", "hardware", "safety", "emergency", "fail-safe"]
        )

    def _register(self, template_id: str, dag: WorkflowDAG, category: str, description: str, tags: List[str]):
        self._templates[template_id] = dag
        self._metadata[template_id] = WorkflowTemplateMetadata(
            template_id=template_id,
            name=dag.name,
            category=category,
            description=description,
            tags=tags,
            nodes_count=len(dag.nodes),
            edges_count=len(dag.edges)
        )

    def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplateMetadata]:
        if category:
            return [m.model_copy(deep=True) for m in self._metadata.values() if m.category == category]
        return [m.model_copy(deep=True) for m in self._metadata.values()]

    def get_template(self, template_id: str) -> Optional[WorkflowDAG]:
        dag = self._templates.get(template_id)
        if dag is None:
            return None
        return dag.model_copy(deep=True)


_template_registry_instance: Optional[CanvasTemplateRegistry] = None


def get_template_registry() -> CanvasTemplateRegistry:
    global _template_registry_instance
    if _template_registry_instance is None:
        _template_registry_instance = CanvasTemplateRegistry()
    return _template_registry_instance
