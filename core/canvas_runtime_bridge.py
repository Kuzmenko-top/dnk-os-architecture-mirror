# --- DNK-MRH-HEADER ---
# mrh_id: "core/canvas_runtime_bridge.py"
# purpose: "Runtime bridge connecting Infinite Canvas node lifecycle and selection events with Redis and EventBus."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    import redis  # type: ignore[import-not-found]
except ImportError:
    redis = None  # type: ignore[assignment]

from core.runtime_events import GraphExecutionSnapshot, RuntimeEvent, RuntimeEventBus

logger = logging.getLogger(__name__)


class CanvasRuntimeBridge:
    """
    Bidirectional Runtime Bridge between Canvas visual nodes and execution backends.
    Publishes lifecycle events ('node.created', 'node.executed') to both RuntimeEventBus
    and Redis Pub/Sub channels, providing real-time synchronization and selection execution.
    """

    def __init__(
        self,
        event_bus: Optional[RuntimeEventBus] = None,
        redis_client: Optional[Any] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_channel: str = "dnk:canvas:events",
        default_tenant_id: str = "default",
        default_workspace_id: str = "default",
        default_canvas_id: str = "default",
    ) -> None:
        self.event_bus: RuntimeEventBus = event_bus or RuntimeEventBus.get_instance()
        self.redis_channel = redis_channel
        self.default_tenant_id = default_tenant_id
        self.default_workspace_id = default_workspace_id
        self.default_canvas_id = default_canvas_id

        self._sequence_counters: Dict[str, int] = {}
        self.published_events: List[RuntimeEvent] = []
        self.redis_published_messages: List[Dict[str, Any]] = []

        # Initialize or assign Redis client with non-blocking graceful fallback
        if redis_client is not None:
            self.redis_client = redis_client
            self.redis_connected = True
        elif redis is not None:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True,
                    socket_connect_timeout=0.5,
                )
                self.redis_client.ping()
                self.redis_connected = True
            except Exception as e:
                logger.debug("Redis unreachable, operating in local fallback mode: %s", e)
                self.redis_client = None
                self.redis_connected = False
        else:
            self.redis_client = None
            self.redis_connected = False

    def _next_sequence(self, thread_id: str) -> int:
        seq = self._sequence_counters.get(thread_id, 0) + 1
        self._sequence_counters[thread_id] = seq
        return seq

    def _publish_to_redis(self, event: RuntimeEvent) -> bool:
        payload_dict = event.model_dump(mode="json")
        self.redis_published_messages.append(payload_dict)

        if self.redis_client is not None and self.redis_connected:
            try:
                self.redis_client.publish(self.redis_channel, json.dumps(payload_dict))
                return True
            except Exception as exc:
                logger.warning("Failed to publish event to Redis: %s", exc)
                return False
        return False

    def publish_node_created(
        self,
        node_id: str,
        name: str,
        node_type: str = "task",
        canvas_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RuntimeEvent:
        """
        Publishes 'node.created' event to RuntimeEventBus and Redis.
        """
        t_id = thread_id or execution_id or f"th_{uuid4().hex[:8]}"
        exec_id = execution_id or f"exec_{t_id}"
        seq = self._next_sequence(t_id)

        data_payload = {
            "node_name": name,
            "node_type": node_type,
            "status": "created",
            **(payload or {}),
        }

        event = RuntimeEvent(
            tenant_id=tenant_id or self.default_tenant_id,
            workspace_id=workspace_id or self.default_workspace_id,
            canvas_id=canvas_id or self.default_canvas_id,
            graph_id=f"graph_{t_id}",
            thread_id=t_id,
            execution_id=exec_id,
            node_id=node_id,
            event_type="node.created",
            sequence_number=seq,
            payload=data_payload,
        )

        self.event_bus.publish(event)
        self.published_events.append(event)
        self._publish_to_redis(event)
        return event

    def publish_node_executed(
        self,
        node_id: str,
        status: str = "completed",
        canvas_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        execution_result: Optional[Any] = None,
        payload: Optional[Dict[str, Any]] = None,
        event_type: Optional[str] = None,
    ) -> RuntimeEvent:
        """
        Publishes execution status update event ('node.executed', 'node.started', 'node.completed', 'node.error')
        to RuntimeEventBus and Redis.
        """
        t_id = thread_id or execution_id or f"th_{uuid4().hex[:8]}"
        exec_id = execution_id or f"exec_{t_id}"
        seq = self._next_sequence(t_id)

        data_payload = {
            "status": status,
            "result": execution_result,
            **(payload or {}),
        }

        resolved_event_type = event_type or ("node.executed" if status == "completed" else f"node.{status}")

        event = RuntimeEvent(
            tenant_id=tenant_id or self.default_tenant_id,
            workspace_id=workspace_id or self.default_workspace_id,
            canvas_id=canvas_id or self.default_canvas_id,
            graph_id=f"graph_{t_id}",
            thread_id=t_id,
            execution_id=exec_id,
            node_id=node_id,
            event_type=resolved_event_type,
            sequence_number=seq,
            payload=data_payload,
        )

        self.event_bus.publish(event)
        self.published_events.append(event)
        self._publish_to_redis(event)
        return event

    def execute_selection_scenario(
        self,
        selection_id: str,
        selected_nodes: List[Dict[str, Any]],
        selection_bounds: Optional[Dict[str, float]] = None,
        canvas_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a targeted test scenario for Canvas selection:
        1. Emits 'node.created' for each node inside selection.
        2. Executes node processing pipeline (simulated or task-driven).
        3. Emits 'node.executed' for each node inside selection.
        4. Produces GraphExecutionSnapshot.
        """
        t_id = thread_id or f"sel_{selection_id}_{uuid4().hex[:6]}"
        exec_id = execution_id or f"exec_{t_id}"
        c_id = canvas_id or self.default_canvas_id
        ten_id = tenant_id or self.default_tenant_id
        ws_id = workspace_id or self.default_workspace_id
        bounds = selection_bounds or {"x": 0.0, "y": 0.0, "width": 500.0, "height": 300.0}

        events_batch: List[RuntimeEvent] = []
        node_states: Dict[str, str] = {}

        # 1. Ingest selection parser node
        selection_parser_id = f"parser_{selection_id}"
        parser_event = self.publish_node_created(
            node_id=selection_parser_id,
            name="CanvasSelectionParser",
            node_type="selection_parser",
            canvas_id=c_id,
            thread_id=t_id,
            execution_id=exec_id,
            tenant_id=ten_id,
            workspace_id=ws_id,
            payload={"selection_bounds": bounds, "source_count": len(selected_nodes)},
        )
        events_batch.append(parser_event)
        node_states[selection_parser_id] = "created"

        # 2. Register selected nodes
        for node in selected_nodes:
            nid = node.get("id", f"node_{uuid4().hex[:6]}")
            nname = node.get("name", f"Node_{nid}")
            ntype = node.get("type", "canvas_element")
            ev = self.publish_node_created(
                node_id=nid,
                name=nname,
                node_type=ntype,
                canvas_id=c_id,
                thread_id=t_id,
                execution_id=exec_id,
                tenant_id=ten_id,
                workspace_id=ws_id,
                payload={"node_config": node},
            )
            events_batch.append(ev)
            node_states[nid] = "created"

        # 3. Execute parser node
        parser_exec_event = self.publish_node_executed(
            node_id=selection_parser_id,
            status="completed",
            canvas_id=c_id,
            thread_id=t_id,
            execution_id=exec_id,
            tenant_id=ten_id,
            workspace_id=ws_id,
            execution_result={"parsed_nodes": len(selected_nodes), "bounds_validated": True},
        )
        events_batch.append(parser_exec_event)
        node_states[selection_parser_id] = "completed"

        # 4. Execute each selected node
        for node in selected_nodes:
            nid = node.get("id", "")
            exec_res = {
                "action": "canvas_selection_task_processed",
                "node_id": nid,
                "timestamp": time.time(),
            }
            ev = self.publish_node_executed(
                node_id=nid,
                status="completed",
                canvas_id=c_id,
                thread_id=t_id,
                execution_id=exec_id,
                tenant_id=ten_id,
                workspace_id=ws_id,
                execution_result=exec_res,
            )
            events_batch.append(ev)
            node_states[nid] = "completed"

        snapshot = GraphExecutionSnapshot(
            tenant_id=ten_id,
            workspace_id=ws_id,
            canvas_id=c_id,
            graph_id=f"graph_{t_id}",
            thread_id=t_id,
            execution_id=exec_id,
            current_node=selected_nodes[-1]["id"] if selected_nodes else selection_parser_id,
            status="completed",
            last_sequence_number=self._sequence_counters[t_id],
            node_states=node_states,
            messages=[],
        )

        return {
            "status": "success",
            "selection_id": selection_id,
            "thread_id": t_id,
            "execution_id": exec_id,
            "events_count": len(events_batch),
            "events": [e.model_dump() for e in events_batch],
            "node_states": node_states,
            "snapshot": snapshot.model_dump(),
            "redis_published_count": len(self.redis_published_messages),
        }

    def publish_graph_snapshot(
        self,
        canvas_id: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        thread_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RuntimeEvent:
        """
        Publishes a graph snapshot event ('canvas.graph_snapshot') to RuntimeEventBus and Redis.
        """
        t_id = thread_id or execution_id or f"th_{uuid4().hex[:8]}"
        exec_id = execution_id or f"exec_{t_id}"
        seq = self._next_sequence(t_id)

        data_payload = {
            "nodes": nodes or [],
            "edges": edges or [],
            **(payload or {}),
        }

        event = RuntimeEvent(
            tenant_id=tenant_id or self.default_tenant_id,
            workspace_id=workspace_id or self.default_workspace_id,
            canvas_id=canvas_id or self.default_canvas_id,
            graph_id=f"graph_{t_id}",
            thread_id=t_id,
            execution_id=exec_id,
            node_id=f"snapshot_{t_id}",
            event_type="canvas.graph_snapshot",
            sequence_number=seq,
            payload=data_payload,
        )

        self.event_bus.publish(event)
        self.published_events.append(event)
        self._publish_to_redis(event)
        return event

    def publish_selection_batch(
        self,
        canvas_id: Optional[str] = None,
        node_ids: Optional[List[str]] = None,
        action: str = "select",
        thread_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RuntimeEvent:
        """
        Publishes a selection batch event ('canvas.selection_batch') to RuntimeEventBus and Redis.
        """
        t_id = thread_id or execution_id or f"th_{uuid4().hex[:8]}"
        exec_id = execution_id or f"exec_{t_id}"
        seq = self._next_sequence(t_id)

        data_payload = {
            "node_ids": node_ids or [],
            "action": action,
            **(payload or {}),
        }

        event = RuntimeEvent(
            tenant_id=tenant_id or self.default_tenant_id,
            workspace_id=workspace_id or self.default_workspace_id,
            canvas_id=canvas_id or self.default_canvas_id,
            graph_id=f"graph_{t_id}",
            thread_id=t_id,
            execution_id=exec_id,
            node_id=f"selection_{t_id}",
            event_type="canvas.selection_batch",
            sequence_number=seq,
            payload=data_payload,
        )

        self.event_bus.publish(event)
        self.published_events.append(event)
        self._publish_to_redis(event)
        return event

