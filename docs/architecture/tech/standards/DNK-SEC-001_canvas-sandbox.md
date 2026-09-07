# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/standards/DNK-SEC-001_canvas-sandbox.md"
# purpose: "Concrete Sandbox Topology & Docker-Only Security Rules"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🛡️ SECURITY SPEC: CANVAS & AGENT RUNTIME SECURITY (DNK-SEC-001)

## 🌐 Container Topology
The workspace execution stack operates exclusively via Docker containers:

```
+───────────────────────────────────────────────────────────+
|                       DOCKER COMPOSE                      |
|                                                           |
|  +──────────────────+               +──────────────────+  |
|  |   visual_shell   | <===(HTTP)==> |    kernel_api    |  |
|  |   (Port 3000)    |               |   (Port 8000)    |  |
|  +──────────────────+               +──────────────────+  |
|                                              ║            |
|                                           (gRPC/Unix)     |
|                                              ▼            |
|                                     +──────────────────+  |
|                                     |  sandbox_runner  |  |
|                                     |    (Isolated)    |  |
|                                     +──────────────────+  |
+───────────────────────────────────────────────────────────+
```

## 🔒 Security & Isolation Rules

1. **Zero Host Pollution**:
   - All runtime compilation, NPM/Pip package installations, and execution MUST happen strictly inside the running container context.
2. **Volume Masking**:
   - Host `node_modules` and `.pnpm-store` directories MUST be masked using Docker anonymous volumes:
     ```yaml
     volumes:
       - .:/app
       - /app/node_modules
       - /app/.next
     ```
3. **No Direct Host Mounts**:
   - Direct host path mounts for execution purposes are strictly prohibited to prevent arbitrary local writes.
4. **Network Policies**:
   - The `sandbox_runner` container is network-isolated. No inbound traffic is allowed, and outbound connections are restricted to authorized API gateways only.
