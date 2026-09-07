# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_a2a_streaming_engine"
# purpose: "Real-Time SSE/gRPC Streaming Engine with Backpressure & CoT/Token/Artifact Flow (DNK-A2A-004 Phase 2)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Optional

logger = logging.getLogger("dnk.a2a.streaming")


class A2AStreamingEngine:
    """Provides high-throughput asynchronous SSE and streaming channels for Chain-of-Thought (CoT),
    token deltas, tool executions and artifact transfers with backpressure flow control.
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._queues: Dict[str, asyncio.Queue] = {}

    def create_session(
        self,
        workspace_id: str,
        sender_agent_id: str,
        receiver_agent_id: str,
        stream_type: str = "cot_stream",
        backpressure_window_size: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initializes a new streaming session with bounded queue backpressure."""
        session_token = f"stream_tok_{uuid.uuid4().hex[:16]}"
        session_id = f"stream_{uuid.uuid4().hex[:10]}"

        session_record = {
            "id": session_id,
            "session_token": session_token,
            "workspace_id": workspace_id,
            "sender_agent_id": sender_agent_id,
            "receiver_agent_id": receiver_agent_id,
            "stream_type": stream_type,
            "status": "open",
            "backpressure_window_size": backpressure_window_size,
            "messages_streamed": 0,
            "bytes_streamed": 0.0,
            "metadata": metadata or {},
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "closed_at": None,
        }

        self._sessions[session_token] = session_record
        self._queues[session_token] = asyncio.Queue(maxsize=backpressure_window_size)
        logger.info("Opened A2A stream session %s (%s -> %s)", session_token, sender_agent_id, receiver_agent_id)
        return session_record

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_token)

    async def push_event(
        self,
        session_token: str,
        event_type: str,
        data: Dict[str, Any],
        timeout_s: float = 2.0,
    ) -> Dict[str, Any]:
        """Pushes a streaming frame into the bounded session queue with backpressure protection."""
        session = self._sessions.get(session_token)
        if not session or session["status"] not in ("open", "active"):
            return {"success": False, "error": "Stream session not active"}

        queue = self._queues.get(session_token)
        if not queue:
            return {"success": False, "error": "Stream queue not found"}

        event_payload = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "seq": session["messages_streamed"] + 1,
        }

        raw_size = len(json.dumps(event_payload).encode("utf-8"))

        try:
            # Respect backpressure window with timeout
            await asyncio.wait_for(queue.put(event_payload), timeout=timeout_s)
            session["messages_streamed"] += 1
            session["bytes_streamed"] += raw_size
            session["status"] = "active"
            return {"success": True, "seq": event_payload["seq"], "queue_size": queue.qsize()}
        except asyncio.TimeoutError:
            logger.warning("Backpressure limit reached on session %s", session_token)
            return {"success": False, "error": "Backpressure window exceeded (queue full)"}

    async def consume_events(
        self, session_token: str, auto_close: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """Asynchronously yields events from the stream session queue."""
        session = self._sessions.get(session_token)
        if not session:
            return

        queue = self._queues.get(session_token)
        if not queue:
            return

        while session["status"] in ("open", "active"):
            try:
                # Poll with short timeout to handle termination
                event = await asyncio.wait_for(queue.get(), timeout=0.5)
                queue.task_done()
                yield event
                if event.get("event_type") in ("complete", "close"):
                    break
            except asyncio.TimeoutError:
                if session["status"] == "closed":
                    break
                continue

        if auto_close and session["status"] != "closed":
            self.close_session(session_token, reason="stream_ended")

    @staticmethod
    def format_sse_frame(event_type: str, data: Dict[str, Any], event_id: Optional[str] = None) -> str:
        """Formats a standard Server-Sent Events (SSE) wire chunk."""
        lines = []
        if event_id:
            lines.append(f"id: {event_id}")
        lines.append(f"event: {event_type}")
        json_data = json.dumps(data, ensure_ascii=False)
        lines.append(f"data: {json_data}")
        return "\n".join(lines) + "\n\n"

    def close_session(self, session_token: str, reason: str = "completed") -> Dict[str, Any]:
        """Closes the streaming session and releases queue resources."""
        session = self._sessions.get(session_token)
        if not session:
            return {"success": False, "error": "Session not found"}

        session["status"] = "closed"
        session["closed_at"] = datetime.now(timezone.utc).isoformat()
        session["close_reason"] = reason

        # Push sentinel into queue if present to unblock consumers
        queue = self._queues.get(session_token)
        if queue:
            try:
                queue.put_nowait({"event_type": "close", "data": {"reason": reason}})
            except asyncio.QueueFull:
                pass

        logger.info("Closed A2A stream session %s (reason: %s)", session_token, reason)
        return {"success": True, "session": session}
