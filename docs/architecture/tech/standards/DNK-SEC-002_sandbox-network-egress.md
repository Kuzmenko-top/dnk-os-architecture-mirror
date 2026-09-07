# 🛡️ Security Standard: Sandbox Network Egress & Volume Masking
# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-SEC-002_sandbox-network-egress.md"
# purpose: "Establish Network Policy and Host Protection Configurations for DNK OS Sandboxes."
# author: "Maxim"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

## 📌 1. Container Topology for `sandbox_runner`

The `sandbox_runner` image is a hardened, stripped-down Linux container (Alpine-based or distroless Python) engineered strictly for running dynamic tools.

```
       [ Local Host Bridge (docker0) ]
                      │
   ┌──────────────────┴──────────────────┐
   ▼                                     ▼
[ Host DNS (dnsmasq) ]          [ Egress Gateway IP Filter ]
   │ (Allowlist Routing)                 │ (iptables BLOCK defaults)
   ▼                                     ▼
[ allow: api.openai.com ]       [ drop: 0.0.0.0/0 (Default DROP) ]
```

### Security Hardening Parameters
- **Non-Root Execution:** Evaluates code using `USER dnk_worker` (`uid: 10001`, `gid: 10001`).
- **Read-Only Root Filesystem:** Configured with `read_only: true` on the container root. Only `/tmp` is writeable via standard memory limits.
- **Resource Limits:**
  - `nano_cpus: 500000000` (Max 0.5 CPU cores)
  - `memory: 512m` (Hard limit 512MB RAM)
  - `pids_limit: 100` (Protects against Fork Bomb vulnerabilities)

---

## 🔒 2. Egress Network Policy (Allowlist Filtering)

By default, all outgoing traffic from the `sandbox_runner` container is set to `DROP`. Outbound calls must match the verified target domains/IPs mapped in the policy routing.

### Network Policy Configuration (Kubernetes / Calico equivalent):
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sandbox-runner-egress-policy
  namespace: dnk-os-sandboxes
spec:
  podSelector:
    matchLabels:
      app: sandbox-runner
  policyTypes:
    - Egress
  egress:
    # 1. DNS Resolution (Port 53 TCP/UDP) strictly to local dnsmasq
    - to:
        - ipBlock:
            cidr: 127.0.0.1/32
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # 2. Allow list of Model Provider Gateways (HTTPS Port 443)
    - to:
        - dns: integrate.api.nvidia.com
        - dns: api.openai.com
        - dns: api.anthropic.com
        - dns: *.myshopify.com
      ports:
        - protocol: TCP
          port: 443
```

### Host-Level Docker Firewall Rules (iptables)
If executed natively via Docker bridge networks on macOS/Linux, the runtime injects the following rules upon container initialization:
```bash
# 1. Clear any pre-existing egress rules for sandbox bridge
iptables -F FORWARD

# 2. Set default policy to DROP for sandbox bridge packets
iptables -P FORWARD DROP

# 3. Allow established connections (TCP state tracking)
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 4. Explicitly allow out of bridge for verified hosts only
iptables -A FORWARD -o eth0 -d integrate.api.nvidia.com -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -o eth0 -d api.openai.com -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -o eth0 -d *.myshopify.com -p tcp --dport 443 -j ACCEPT
```

---

## 🚫 3. Host Protection: Volume Masking Configuration

To protect the host MacBook Pro filesystem from pollution, unwanted file mutations, and cross-compilation errors (which occur when macOS ARM64 and Linux compiled dependencies clash in shared folders), we implement **Volume Masking**.

```
Host (macOS ARM64)                  Sandbox Container (Linux x86_64)
  DNK OS/ ───────────────────────► /workspace/ (Bind Mount)
    ├── node_modules/ ──────────────► [ MASKED via Anonymous Volume ]
    ├── .venv/ ─────────────────────► [ MASKED via Anonymous Volume ]
    └── .next/ ─────────────────────► [ MASKED via Anonymous Volume ]
```

### Docker-Compose Configuration Schema
The volume configuration is declared as follows in `docker-compose.dev.yml`:
```yaml
version: "3.8"

services:
  sandbox_runner:
    image: dnk-sandbox-runner:latest
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:size=64M,uid=10001,gid=10001,mode=1777
    volumes:
      # 1. Bind mount the project root code as read-only
      - ${PROJECT_ROOT:-.}:/workspace:ro
      
      # 2. Mask hazardous local folders to prevent host leakage and cross-compilation crashes
      - /workspace/node_modules
      - /workspace/.next
      - /workspace/.venv
      - /workspace/.pnpm-store
```

By applying these anonymous volume overrides, the Docker daemon hides the host's `/node_modules`, `/next`, and `/venv` folders from the container filesystem. The container runs with its own fresh, isolated dependencies, ensuring zero host pollution and a completely reliable multi-platform development loop.
