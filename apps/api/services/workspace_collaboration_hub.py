# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workspace_collaboration_hub"
# purpose: "Real-Time Workspace Collaboration Hub managing WebSockets, Presence, Cursor tracking, OCC mutations, Conflict events, and Cross-Node Redis PubSub Broadcast"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Set
from fastapi import WebSocket

from apps.api.services.workspace_service import workspace_service
from apps.api.services.workspace_lock_manager import workspace_lock_manager
from apps.api.services.redis_pubsub import pubsub_manager
from apps.api.services.workspace_analytics_service import workspace_analytics_service

logger = logging.getLogger("dnk.workspace.collaboration_hub")


class WorkspaceCollaborationHub:
    """
    Central real-time coordinator for DNK OS multi-user workspace collaboration.
    Coordinates presence, cursors, optimistic OCC mutations, pessimistic section locking,
    conflict resolution, and cross-node distributed synchronization via Redis Pub/Sub.
    """

    def __init__(self):
        # {workspace_id: {websocket: {"user_id": str, "role": str, "joined_at": float, "cursor": dict}}}
        self._connections: Dict[str, Dict[WebSocket, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self.node_id: str = f"node_{uuid.uuid4().hex[:8]}"
        self._subscribed_pubsub_channels: Set[str] = set()

    async def _ensure_pubsub_subscription(self, workspace_id: str) -> None:
        """Subscribes this node to Redis Pub/Sub channel for workspace cross-node events."""
        channel = f"dnk:ws:{{{workspace_id}}}"
        if channel not in self._subscribed_pubsub_channels:
            self._subscribed_pubsub_channels.add(channel)

            async def _cross_node_handler(payload: Dict[str, Any]):
                if payload.get("origin_node") == self.node_id:
                    return  # Ignore events originated by this node
                msg = payload.get("message")
                target_ws = payload.get("workspace_id", workspace_id)
                if msg and target_ws:
                    await self.broadcast(
                        workspace_id=target_ws,
                        message=msg,
                        cross_node=False
                    )

            ps = getattr(self, "pubsub_manager", None) or pubsub_manager
            await ps.subscribe(channel, _cross_node_handler)
            logger.debug("Hub node %s subscribed to cross-node channel %s", self.node_id, channel)

    async def connect(
        self,
        workspace_id: str,
        user_id: str,
        websocket: WebSocket,
        role: str = "developer",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registers a new WebSocket connection, adds user to presence, and notifies existing workspace peers.
        """
        async with self._lock:
            if workspace_id not in self._connections:
                self._connections[workspace_id] = {}

            conn_data = {
                "user_id": user_id,
                "role": role,
                "joined_at": time.time(),
                "cursor": None,
                "metadata": metadata or {}
            }
            self._connections[workspace_id][websocket] = conn_data

        # Ensure cross-node PubSub channel is active for this workspace
        await self._ensure_pubsub_subscription(workspace_id)

        # Broadcast presence:join to OTHER users in the workspace
        active_users = await self.get_active_users(workspace_id)
        await self.broadcast(
            workspace_id=workspace_id,
            message={
                "type": "presence:join",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role": role,
                "active_users": active_users
            },
            exclude_websocket=websocket,
            cross_node=True
        )

        try:
            await workspace_analytics_service.record_user_activity(
                user_id=user_id,
                event_type="user:presence_join",
                workspace_id=workspace_id,
                details={"role": role}
            )
        except Exception as e:
            logger.debug("Failed to record presence_join analytics: %s", e)

        return conn_data

    async def disconnect(self, workspace_id: str, user_id: str, websocket: WebSocket):
        """
        Removes WebSocket connection, auto-releases held locks, and broadcasts presence:leave.
        """
        removed = False
        async with self._lock:
            if workspace_id in self._connections:
                if websocket in self._connections[workspace_id]:
                    del self._connections[workspace_id][websocket]
                    removed = True
                if not self._connections[workspace_id]:
                    del self._connections[workspace_id]

        if removed:
            # Auto-release any pessimistic locks held by this user and broadcast presence:leave
            released_sections = await workspace_lock_manager.release_all_user_locks(workspace_id, user_id)
            active_users = await self.get_active_users(workspace_id)
            await self.broadcast(
                workspace_id=workspace_id,
                message={
                    "type": "presence:leave",
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "active_users": active_users,
                    "released_locks": released_sections
                },
                cross_node=True
            )
            try:
                await workspace_analytics_service.record_user_activity(
                    user_id=user_id,
                    event_type="user:presence_leave",
                    workspace_id=workspace_id
                )
            except Exception as e:
                logger.debug("Failed to record presence_leave analytics: %s", e)

    async def get_active_users(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Returns the deduplicated list of active users currently connected to the workspace on this node.
        """
        users_map: Dict[str, Dict[str, Any]] = {}
        async with self._lock:
            ws_conns = self._connections.get(workspace_id, {})
            for _, info in ws_conns.items():
                uid = info["user_id"]
                if uid not in users_map:
                    users_map[uid] = {
                        "user_id": uid,
                        "role": info["role"],
                        "joined_at": info["joined_at"],
                        "cursor": info.get("cursor"),
                        "connections_count": 1
                    }
                else:
                    users_map[uid]["connections_count"] += 1

        return list(users_map.values())

    async def update_cursor(
        self,
        workspace_id: str,
        user_id: str,
        websocket: WebSocket,
        cursor_data: Dict[str, Any]
    ):
        """
        Updates cursor position and broadcasts to other participants across nodes.
        """
        async with self._lock:
            if workspace_id in self._connections and websocket in self._connections[workspace_id]:
                self._connections[workspace_id][websocket]["cursor"] = cursor_data

        await self.broadcast(
            workspace_id=workspace_id,
            message={
                "type": "presence:cursor",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "cursor": cursor_data
            },
            exclude_websocket=websocket,
            cross_node=True
        )

    async def broadcast(
        self,
        workspace_id: str,
        message: Dict[str, Any],
        exclude_websocket: Optional[WebSocket] = None,
        cross_node: bool = True
    ):
        """
        Broadcasts a JSON message to all active local WebSocket connections in a workspace,
        and optionally publishes across Redis PubSub cluster nodes.
        """
        targets: List[WebSocket] = []
        async with self._lock:
            ws_conns = self._connections.get(workspace_id, {})
            for ws in ws_conns.keys():
                if ws != exclude_websocket:
                    targets.append(ws)

        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug("Error sending message to client: %s", e)

        # Cross-node broadcast via Redis PubSub
        if cross_node:
            channel = f"dnk:ws:{{{workspace_id}}}"
            envelope = {
                "origin_node": self.node_id,
                "workspace_id": workspace_id,
                "message": message
            }
            try:
                ps = getattr(self, "pubsub_manager", None) or pubsub_manager
                await ps.publish(channel, envelope)
            except Exception as e:
                logger.debug("Cross-node publish failed: %s", e)

    async def handle_message(
        self,
        websocket: WebSocket,
        workspace_id: str,
        tenant_id: str,
        user_id: str,
        role: str,
        raw_message: Dict[str, Any]
    ):
        """
        Dispatches and processes client WebSocket events according to DNK OS protocol.
        """
        event_type = raw_message.get("type") or raw_message.get("action")
        topic = raw_message.get("topic", "")

        # 1. Topic Subscription (Legacy & New compatibility)
        if event_type == "subscribe":
            expected_topic = f"workspace:{workspace_id}"
            if topic != expected_topic and not topic.startswith(f"{expected_topic}:"):
                await websocket.send_json({
                    "type": "error",
                    "error_code": "UNAUTHORIZED_TOPIC",
                    "message": f"Subscription to topic [{topic}] denied for workspace [{workspace_id}]"
                })
            else:
                await websocket.send_json({
                    "type": "subscribed",
                    "topic": topic,
                    "event": "SUBSCRIBED"
                })
            return

        # 2. Workspace Full State Sync
        if event_type == "workspace:sync":
            try:
                state = workspace_service.get_workspace_state(workspace_id=workspace_id, tenant_id=tenant_id)
                if isinstance(state, dict):
                    current_version = state.get("metadata", {}).get("version", 1)
                elif hasattr(state, "metadata"):
                    current_version = getattr(state.metadata, "version", 1)
                else:
                    current_version = 1
            except Exception:
                state = None
                current_version = 1

            active_users = await self.get_active_users(workspace_id)
            active_locks = await workspace_lock_manager.get_locks(workspace_id)

            await websocket.send_json({
                "type": "workspace:sync",
                "workspace_id": workspace_id,
                "version": current_version,
                "state": state.dict() if hasattr(state, "dict") else state,
                "active_users": active_users,
                "active_locks": active_locks
            })
            return

        # 3. Presence & Cursor Tracking
        if event_type == "presence:cursor":
            cursor_data = raw_message.get("cursor", {})
            await self.update_cursor(workspace_id, user_id, websocket, cursor_data)
            return

        if event_type == "workspace:presence":
            active_users = await self.get_active_users(workspace_id)
            await websocket.send_json({
                "type": "workspace:presence",
                "workspace_id": workspace_id,
                "active_users": active_users
            })
            return

        # 4. Pessimistic Section Locking
        if event_type == "workspace:lock":
            action = raw_message.get("action", "acquire")
            section_id = raw_message.get("section_id")

            if not section_id:
                await websocket.send_json({
                    "type": "error",
                    "error_code": "INVALID_LOCK_REQUEST",
                    "message": "section_id is required for workspace:lock events"
                })
                return

            if action == "acquire":
                ttl = raw_message.get("ttl_seconds", 60)
                lock_res = await workspace_lock_manager.acquire_lock(
                    workspace_id=workspace_id,
                    section_id=section_id,
                    user_id=user_id,
                    ttl_seconds=ttl
                )
                if lock_res.get("success"):
                    # Broadcast lock acquired to everyone
                    await self.broadcast(
                        workspace_id=workspace_id,
                        message={
                            "type": "workspace:lock",
                            "action": "acquired",
                            "workspace_id": workspace_id,
                            "section_id": section_id,
                            "user_id": user_id,
                            "lock": lock_res.get("lock")
                        },
                        cross_node=True
                    )
                else:
                    # Send conflict notification to the requester
                    await websocket.send_json({
                        "type": "workspace:conflict",
                        "error_code": "SECTION_ALREADY_LOCKED",
                        "workspace_id": workspace_id,
                        "conflict": lock_res.get("conflict")
                    })
                return

            elif action == "release":
                released = await workspace_lock_manager.release_lock(
                    workspace_id=workspace_id,
                    section_id=section_id,
                    user_id=user_id
                )
                if released:
                    await self.broadcast(
                        workspace_id=workspace_id,
                        message={
                            "type": "workspace:lock",
                            "action": "released",
                            "workspace_id": workspace_id,
                            "section_id": section_id,
                            "user_id": user_id
                        },
                        cross_node=True
                    )
                else:
                    await websocket.send_json({
                        "type": "error",
                        "error_code": "LOCK_RELEASE_DENIED",
                        "message": f"Lock on section [{section_id}] is not held by user [{user_id}]"
                    })
                return

            elif action == "list":
                locks = await workspace_lock_manager.get_locks(workspace_id)
                await websocket.send_json({
                    "type": "workspace:lock",
                    "action": "list",
                    "workspace_id": workspace_id,
                    "locks": locks
                })
                return

        # 5. Real-Time Workspace Mutations (with Optimistic OCC & Lock Validation)
        if event_type == "workspace:mutation":
            mutation_payload = raw_message.get("mutation", {})
            section_id = mutation_payload.get("section_id") or mutation_payload.get("target_node_id") or mutation_payload.get("node_id")
            expected_version = raw_message.get("expected_version") or mutation_payload.get("expected_version")

            # Check A: Pessimistic Lock validation
            if section_id:
                lock_conflict = await workspace_lock_manager.is_locked_by_other(workspace_id, section_id, user_id)
                if lock_conflict:
                    try:
                        await workspace_analytics_service.record_error_metric(
                            error_type="SECTION_LOCKED_BY_ANOTHER_USER",
                            status_code=423,
                            message=f"Section {section_id} locked by {lock_conflict.get('user_id')}",
                            workspace_id=workspace_id,
                            user_id=user_id
                        )
                    except Exception:
                        pass
                    await websocket.send_json({
                        "type": "workspace:conflict",
                        "error_code": "SECTION_LOCKED_BY_ANOTHER_USER",
                        "workspace_id": workspace_id,
                        "section_id": section_id,
                        "conflict": lock_conflict
                    })
                    return

            # Check B: Optimistic OCC Version validation
            current_version = 1
            try:
                st = workspace_service.get_workspace_state(workspace_id=workspace_id, tenant_id=tenant_id)
                if isinstance(st, dict):
                    current_version = st.get("metadata", {}).get("version", 1)
                elif hasattr(st, "metadata"):
                    current_version = getattr(st.metadata, "version", 1)
            except Exception:
                pass

            if expected_version is not None and expected_version != current_version:
                # OCC Conflict detected!
                try:
                    await workspace_analytics_service.record_error_metric(
                        error_type="OCC_VERSION_MISMATCH",
                        status_code=409,
                        message=f"OCC collision: client version {expected_version} vs server {current_version}",
                        workspace_id=workspace_id,
                        user_id=user_id
                    )
                except Exception:
                    pass
                await websocket.send_json({
                    "type": "workspace:conflict",
                    "error_code": "OCC_VERSION_MISMATCH",
                    "workspace_id": workspace_id,
                    "expected_version": expected_version,
                    "current_version": current_version,
                    "message": f"OCC collision: client version [{expected_version}] does not match server version [{current_version}]. Mutation rejected, please sync state."
                })
                return

            # Mutation accepted: Increment version and broadcast
            new_version = current_version + 1
            # Update memory workspace version if available
            try:
                ws_entry = workspace_service.WORKSPACES_DB.get(workspace_id)
                if ws_entry:
                    ws_entry["metadata"]["version"] = new_version
                    ws_entry["metadata"]["last_active"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            except Exception:
                pass

            try:
                await workspace_analytics_service.record_workspace_activity(
                    workspace_id=workspace_id,
                    event_type="workspace:mutation",
                    details=mutation_payload,
                    user_id=user_id
                )
            except Exception:
                pass

            # Broadcast mutation to all workspace participants across nodes
            await self.broadcast(
                workspace_id=workspace_id,
                message={
                    "type": "workspace:mutation",
                    "workspace_id": workspace_id,
                    "actor_id": user_id,
                    "role": role,
                    "version": new_version,
                    "mutation": mutation_payload
                },
                cross_node=True
            )
            return

        # 6. Manual / Custom Conflict notification handling
        if event_type == "workspace:conflict":
            # Echo or broadcast conflict
            await self.broadcast(
                workspace_id=workspace_id,
                message={
                    "type": "workspace:conflict",
                    "workspace_id": workspace_id,
                    "actor_id": user_id,
                    "details": raw_message.get("details", {})
                },
                cross_node=True
            )
            return

        # Unrecognized message
        await websocket.send_json({
            "type": "error",
            "error_code": "UNSUPPORTED_EVENT_TYPE",
            "message": f"Event type [{event_type}] is not recognized by Workspace Collaboration Hub"
        })


workspace_collaboration_hub = WorkspaceCollaborationHub()
