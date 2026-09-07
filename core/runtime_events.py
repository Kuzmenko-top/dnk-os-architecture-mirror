# --- DNK-MRH-HEADER ---
# mrh_id: "core/runtime_events.py"
# purpose: "DTO models representing runtime events, graph execution snapshots, and RuntimeEventBus for Infinite Canvas bridge."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
from datetime import datetime, UTC
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger("RuntimeEventBus")

class RuntimeEvent(BaseModel):
    """Structured runtime event representing execution state transitions."""
    tenant_id: str
    workspace_id: str
    canvas_id: str
    graph_id: str
    thread_id: str
    execution_id: str
    node_id: Optional[str] = None
    event_type: str  # graph.created, graph.started, node.started, node.waiting_human, etc.
    sequence_number: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: Dict[str, Any] = Field(default_factory=dict)

class GraphExecutionSnapshot(BaseModel):
    """Snapshot representation used for client reconnect and resync."""
    tenant_id: str
    workspace_id: str
    canvas_id: str
    graph_id: str
    thread_id: str
    execution_id: str
    current_node: str
    status: str  # start, running, paused, completed, failed, cancelled
    last_sequence_number: int
    node_states: Dict[str, str] = Field(default_factory=dict)  # node_id -> status (running, waiting, etc.)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class RuntimeEventBus:
    """
    Thread-safe / Async-safe Event Bus for routing runtime execution events.
    Supports secure tenant/workspace boundary checks, subscribe/unsubscribe,
    bounded queues with backpressure, and last_event_id reconnect with snapshot fallback.
    """
    _instance: Optional['RuntimeEventBus'] = None

    @classmethod
    def get_instance(cls) -> 'RuntimeEventBus':
        if cls._instance is None:
            cls._instance = RuntimeEventBus()
        return cls._instance

    def __init__(self, max_queue_size: int = 100):
        # Maps execution_id -> list of all historical events emitted in this execution (for reconnect)
        self._history: Dict[str, List[RuntimeEvent]] = {}
        # Active subscribers: execution_id -> Set of (asyncio.Queue, tenant_id, workspace_id)
        self._subscribers: Dict[str, Set[Any]] = {}
        # Active callable listeners: List[Callable[[RuntimeEvent], Any]]
        self._listeners: List[Callable[[RuntimeEvent], Any]] = []
        self.max_queue_size = max_queue_size

    def reset(self):
        """For testing purposes."""
        self._history.clear()
        self._subscribers.clear()
        self._listeners.clear()

    def add_listener(self, callback: Callable[[RuntimeEvent], Any]) -> None:
        """Register a direct listener callback (synchronous or async)."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[RuntimeEvent], Any]) -> None:
        """Remove a previously registered listener callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def publish(self, event: RuntimeEvent) -> None:
        """Publishes an event to the bus and delivers it to matching secure subscribers and listeners."""
        exec_id = event.execution_id
        
        # Save to history
        if exec_id not in self._history:
            self._history[exec_id] = []
        self._history[exec_id].append(event)

        # Notify direct listeners
        for listener in list(self._listeners):
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(res)
                    except RuntimeError:
                        pass
            except Exception as e:
                logger.error("Error in RuntimeEventBus listener: %s", e)

        # Collect execution-specific and wildcard subscribers
        subscribers_to_notify = []
        if exec_id in self._subscribers:
            subscribers_to_notify.extend(list(self._subscribers[exec_id]))
        if "*" in self._subscribers:
            subscribers_to_notify.extend(list(self._subscribers["*"]))

        for queue, tenant_id, workspace_id in subscribers_to_notify:
            # Enforce boundary: fail-closed tenant/workspace checks (allow wildcard "*")
            if tenant_id != "*" and event.tenant_id != tenant_id:
                logger.warning(
                    "Security Boundary Breach Blocked! Event tenant=%s/ws=%s but subscriber has tenant=%s/ws=%s",
                    event.tenant_id, event.workspace_id, tenant_id, workspace_id
                )
                continue
            if workspace_id != "*" and event.workspace_id != workspace_id:
                logger.warning(
                    "Security Boundary Breach Blocked! Event tenant=%s/ws=%s but subscriber has tenant=%s/ws=%s",
                    event.tenant_id, event.workspace_id, tenant_id, workspace_id
                )
                continue

            # Deliver with backpressure / bounded queue check
            def _put():
                if queue.qsize() >= self.max_queue_size:
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                    logger.warning("Queue overflow for execution_id %s, dropping oldest event (bounded queue)", exec_id)
                queue.put_nowait(event)

            try:
                q_loop = getattr(queue, "_loop", None)
            except Exception:
                q_loop = None

            if q_loop and q_loop.is_running():
                try:
                    curr_loop = asyncio.get_running_loop()
                except RuntimeError:
                    curr_loop = None

                if curr_loop is not q_loop:
                    q_loop.call_soon_threadsafe(_put)
                else:
                    _put()
            else:
                _put()

    def subscribe(
        self, 
        execution_id: str, 
        tenant_id: str, 
        workspace_id: str,
        last_event_id: Optional[int] = None
    ) -> asyncio.Queue:
        """
        Subscribes a client to execution_id events under a secure tenant/workspace boundary.
        If last_event_id is provided, replays missed events.
        """
        # Fail-closed validation
        if not tenant_id or not workspace_id or not execution_id:
            raise PermissionError("Fail-Closed Security: Complete credentials are required to subscribe.")

        queue = asyncio.Queue(maxsize=self.max_queue_size)

        if execution_id not in self._subscribers:
            self._subscribers[execution_id] = set()
        
        self._subscribers[execution_id].add((queue, tenant_id, workspace_id))

        # Reconnect logic: Replay missed events if last_event_id is provided
        if last_event_id is not None:
            history = self._history.get(execution_id, [])
            missed_events = [ev for ev in history if ev.sequence_number > last_event_id]
            
            has_gap = False
            if missed_events:
                if missed_events[0].sequence_number > last_event_id + 1:
                    has_gap = True
            elif history and last_event_id < history[-1].sequence_number:
                has_gap = True

            if has_gap:
                fallback_event = {
                    "event_type": "snapshot_fallback",
                    "sequence_number": last_event_id,
                    "payload": {"reason": "missed_events_gap"}
                }
                queue.put_nowait(fallback_event)
            else:
                for ev in missed_events:
                    if ev.tenant_id == tenant_id and ev.workspace_id == workspace_id:
                        queue.put_nowait(ev)

        return queue

    def unsubscribe(self, execution_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribes a client queue from the execution stream."""
        if execution_id in self._subscribers:
            self._subscribers[execution_id] = {
                item for item in self._subscribers[execution_id] if item[0] is not queue
            }
            if not self._subscribers[execution_id]:
                del self._subscribers[execution_id]
