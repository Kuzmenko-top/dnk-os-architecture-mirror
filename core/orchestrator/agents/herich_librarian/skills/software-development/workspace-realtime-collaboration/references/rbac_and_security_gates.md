# Multi-Workspace REST API, RBAC Middleware & Security Gates

## 1. Multi-Workspace RBAC Dependencies
Standard FastAPI dependency hierarchy for workspace operations:
- `require_admin()`: Verifies the authenticated user has the `admin` role for the target workspace and is not an autonomous agent attempting administrative escalation.
- `require_member_or_higher()`: Permits roles in `{"admin", "developer", "member"}` to view resources or execute standard actions while rejecting `viewer` or non-members.
- `can_manage_invitations()`: Admin-only gate for issuing and revoking workspace invitations.

## 2. Mandatory Security Gates
- **Header vs Path Mismatch Gate:** Ensure `X-Workspace-Id` (if supplied by proxy/frontend) strictly matches the path `{workspace_id}` parameter to prevent cross-workspace tampering (return HTTP 403 on mismatch).
- **Nil/Zero UUID Gate:** Explicitly reject `00000000-0000-0000-0000-000000000000` to prevent bypasses against uninitialized foreign key checks (return HTTP 400).
- **Agent Self-Approval & Escalation Block:** Inspect `X-Actor-Type` header and JWT claims (`is_agent: True`); autonomous agents must not self-approve or elevate member permissions (return HTTP 403).
- **Optimistic Concurrency Control (OCC):** On context switching (`/api/v1/users/me/workspace-context`) or document mutation, validate `expected_version` against current stored version and raise HTTP 409 (`OCC_CONFLICT`) on mismatch.
