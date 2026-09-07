# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_DNK_USER_WORKSPACE_MVP_004_realtime_collaboration_spec"
# purpose: "Technical Specification for Real-Time Multi-User Workspace Collaboration, WebSocket Synchronization, Presence, Pessimistic Locking, and OCC Mutation Conflict Resolution"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

# Technical Specification: DNK-USER-WORKSPACE-MVP-004 Real-Time Workspace Collaboration

## 1. Overview & Architecture
DNK OS Workspace Real-Time Collaboration provides synchronous multi-user canvas and workspace editing through WebSocket connections, optimistic concurrency control (OCC), presence tracking, live cursors, and granular pessimistic section locking.

```
       +-------------------------------------------------------------+
       |                  FastAPI WebSocket Endpoint                 |
       |                /ws/workspaces/{workspace_id}                |
       +------------------------------+------------------------------+
                                      |
                      +---------------+---------------+
                      |                               |
                      v                               v
       +------------------------------+ +------------------------------+
       |   WorkspaceCollaborationHub  | |    WorkspaceLockManager      |
       | - Presence & Active Users    | | - Pessimistic Section Locks  |
       | - Live Cursor Tracking       | | - Lock Expiry & Auto-Release |
       | - OCC Mutation & Conflict    | | - User Locks Registry        |
       +------------------------------+ +------------------------------+
```

## 2. WebSocket Protocol Contracts

### 2.1 Authentication & Connection
- **Endpoint:** `/ws/workspaces/{workspace_id}?token={jwt_token}`
- Validates JWT signature, tenant isolation, and workspace membership.
- On connect: broadcasts `presence:join` to other workspace peers.
- On disconnect: auto-releases all locks held by the disconnecting user and broadcasts `presence:leave`.

### 2.2 Event Message Schema
1. **Presence Request & Broadcast:**
   - Client sends: `{"type": "workspace:presence"}`
   - Server returns: `{"type": "workspace:presence", "workspace_id": "...", "active_users": [...]}`
   - Peer event: `{"type": "presence:join"}` / `{"type": "presence:leave"}`

2. **Live Cursor Tracking:**
   - Client sends: `{"type": "presence:cursor", "cursor": {"x": 250, "y": 420, "node_id": "..."}}`
   - Broadcast to peers: `{"type": "presence:cursor", "user_id": "...", "cursor": {...}}`

3. **Workspace Full Sync:**
   - Client sends: `{"type": "workspace:sync"}`
   - Server returns: `{"type": "workspace:sync", "workspace_id": "...", "workspace": {...}, "version": int}`

4. **Optimistic Concurrency Control (OCC) Mutations:**
   - Client sends: `{"type": "workspace:mutate", "expected_version": 1, "mutation": {"action": "node:add", "data": {...}}}`
   - Success: `{"type": "workspace:mutated", "version": 2, "mutation": {...}}` broadcast to all peers.
   - Conflict: `{"type": "workspace:conflict", "expected_version": 1, "current_version": 2, "message": "..."}` sent to sender.

5. **Pessimistic Section Locking:**
   - Acquire: `{"type": "lock:acquire", "section_id": "node_hero_01", "ttl_seconds": 60}`
   - Release: `{"type": "lock:release", "section_id": "node_hero_01"}`
   - Broadcasts `lock:acquired` / `lock:released` to peers.
   - Rejects acquisition if section locked by another active user.

## 3. Security & Role-Based Access Control
- **Admin / Developer:** Full read, write, lock acquire, and mutation permissions.
- **Viewer:** Read-only presence and sync. Denied on `workspace:mutate` (`4003 Forbidden`) and `lock:acquire` (`4003 Forbidden`).
- **Multi-Tenant & Multi-Workspace Isolation:** WebSockets strictly isolated by `tenant_id` and `workspace_id`.
