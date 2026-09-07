# --- DNK-MRH-HEADER ---
# mrh_id: "RN-012_agent-plugins-spec-research"
# purpose: "Reverse Engineering and License Audit of upstream agentplugins/agent-plugins-spec for DNK OS Assimilation."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ASSIM-012"]
# status: "Draft - Pending Mentor Audit"
# version: "1.0.0"
# updated_at: "2026-08-13"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# RN-012: Reverse Engineering & License Audit — agentplugins/agent-plugins-spec

## 1. Upstream Provenance & Metadata

```yaml
upstream_repository: agentplugins/agent-plugins-spec
upstream_ref: "bd383552095128f6effe895b9257cfd580a6d179"
upstream_date: "2026-08-06"
spec_version: "1.0.0"
spec_status: "Published"
license_summary: "Dual-license: CC-BY-4.0 (Docs/Spec) + Apache-2.0 (Schemas/Code)"
```

---

## 2. License Matrix & Legal Audit

| Component | Upstream Path | License | DNK Usage | Attribution Requirement | Decision |
|---|---|---|---|---|---|
| Specification Text | `spec/1.0.0.md` | CC-BY-4.0 | Reference / Adapt | Required (Attribute upstream in DNK specs) | **REUSE** |
| Manifest JSON Schema | `schemas/1.0.0/plugin.schema.json` | Apache-2.0 | Reuse / Adapt | Required (Include Apache 2.0 notice in adapter header) | **REUSE** |
| MCP JSON Schema | `schemas/1.0.0/mcp.schema.json` | Apache-2.0 | Reuse | Required (Include Apache 2.0 notice in loader header) | **REUSE** |
| Agent Instructions | `AGENTS.md` | CC-BY-4.0 | Reference | Reference only in documentation | **REFERENCE** |
| Governance & Meta | `GOVERNANCE.md`, `FUTURE_CONSIDERATIONS.md` | CC-BY-4.0 | Reference | None | **REFERENCE** |
| External Dependencies | N/A | None | Zero external runtime dependencies | N/A | **N/A** |

### License Compliance Note
- **CC-BY-4.0**: Permits copying, adapting, and redistributing specification text for any purpose, provided appropriate credit is given to the `agentplugins` project and changes are indicated.
- **Apache-2.0**: Permits royalty-free reuse, modification, and distribution of JSON schemas and software assets. Compatible with DNK OS MIT / proprietary core architecture.

---

## 3. Upstream Repository Structure & Layout

```text
agent-plugins-spec/
├── .git/
├── AGENTS.md                   # Agent design instructions and editorial discipline
├── CONTRIBUTING.md             # Contribution guidelines
├── FUTURE_CONSIDERATIONS.md    # Roadmap (out-of-scope for v1)
├── GOVERNANCE.md               # Project charter and technical committee governance
├── LICENSE.md                  # Dual licensing declaration
├── LICENSES/
│   ├── Apache-2.0.txt          # Code/Schema license text
│   └── CC-BY-4.0.txt           # Spec/Documentation license text
├── MAINTAINERS.md              # Maintainer registry
├── README.md                   # Project overview
├── schemas/
│   └── 1.0.0/
│       ├── mcp.schema.json     # MCP server configuration schema
│       └── plugin.schema.json  # Plugin manifest closed schema
└── spec/
    └── 1.0.0.md                # Normative Agent Plugins v1.0.0 Specification
```

---

## 4. Specification v1.0.0 Deep-Dive Architecture

### 4.1 Manifest Specification (`plugin.json`)
The root `plugin.json` is a **closed schema**. Any top-level property not listed below violates the core specification schema:
- **`$schema`** (required): Must equal `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
- **`name`** (required): String (1-64 chars), pattern `^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$`.
- **`version`**: SemVer string (e.g. `1.0.0`).
- **`description`**: Opaque text string.
- **`author`**: Object with `name`, `email`, `url`.
- **`homepage`**, **`repository`**, **`license`**: Text/URL strings.
- **`keywords`**: Array of strings.
- **`extensions`**: Object mapping reverse-domain namespaces (e.g., `com.dnk-os.plugin`) to client-defined manifest objects.

### 4.2 Component Discovery Rules
1. **Agent Skills**: Fixed location `skills/`. Immediate subdirectories containing a valid `SKILL.md` file (conforming to `agentskills.io` spec). No nested discovery below child subdirectories.
2. **MCP Servers**: Fixed location `mcp.json`. Configures Model Context Protocol servers.

### 4.3 MCP Packaging Architecture (`mcp.json`)
Requires `$schema: "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"`.
Defines `mcpServers` object supporting 3 transport variants:
1. **`stdio`**:
   - `command` (required): Executable token (resolved relative to plugin root or system PATH).
   - `args`: Array of string arguments.
   - `env`: Key-value environment variables. (Reserved keys forbidden: `PLUGIN_ROOT`, `PLUGIN_DATA`).
   - `cwd`: Working directory. Must start with `./`, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}`.
2. **`streamable-http`**:
   - `url` (required): HTTP endpoint URL.
   - `headers`: Key-value HTTP header map.
3. **`sse`** (legacy):
   - `url` (required): SSE endpoint URL.
   - `headers`: Key-value HTTP header map.

### 4.4 Environment Variables & Placeholder Expansion
- **`PLUGIN_ROOT`**: Absolute filesystem path to the resolved root directory of the plugin.
- **`PLUGIN_DATA`**: Absolute filesystem path to a client-managed, persistent data directory dedicated to the plugin instance (used for `node_modules`, venvs, database files).
- Variable expansion `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` is mandatory in `args`, `env`, and `cwd`.

### 4.5 Package Containment & Path Safety
- All package relative paths MUST start with `./` and resolve strictly within `PLUGIN_ROOT`.
- Path traversal outside `PLUGIN_ROOT` (e.g., `../bin/server` or symlink escapes) is strictly prohibited and MUST cause immediate client rejection of the component/plugin.

---

## 5. Security Gap Analysis (Upstream Missing Capabilities)

The `agentplugins/agent-plugins-spec` explicitly limits itself to a **packaging and discovery floor**. It leaves critical runtime security and governance entirely unspecified:

1. **No Permission / Capability Model**: Upstream spec does not define permissions (file system access, network egress, IPC, canvas controls). Stdio servers execute arbitrary commands with whatever ambient permissions the client host process provides.
2. **No Sandboxing Contract**: Upstream does not specify subprocess isolation (Docker containers, WASM, cgroups, macOS sandbox).
3. **No Code / Package Signature & Trust Policy**: Upstream has no checksum verification, cryptographic signing, or publisher identity verification.
4. **No Lifecycle / Distribution Protocol**: No mechanism for remote package resolution, dependency conflict handling, lockfiles, or secure update hooks.
5. **No Workspace / Multi-Tenant Isolation**: Upstream assumes a single local developer machine with unrestricted filesystem access.

---

## 6. DNK OS Compatibility & Extension Architecture

### 6.1 Bridging Upstream Manifest with DNK OS Native Contract
To assimilate Agent Plugins 1.0 without breaking upstream compatibility or compromising DNK OS enterprise security, DNK OS will use the native `extensions` object in `plugin.json` (`com.dnk-os.plugin` namespace) or inject default fallback governance metadata at runtime:

```yaml
# Extension object inside plugin.json -> extensions["com.dnk-os.plugin"]
dnk:
  risk_level: "L1" # L1 (read-only) to L4 (full host execution)
  permissions:
    - "canvas.read"
    - "artifact.create"
    - "mcp.stdio.execute"
  workspace_scope: "required"
  approval_required: false
  sandbox:
    required: true
    type: "docker" # or "process_isolated"
  provenance:
    source: "github"
    verified: false
  runtime:
    type: "mcp"
    transport: "stdio"
```

### 6.2 Comparison Matrix: Upstream Agent Plugins vs. DNK OS Native Plugin System

| Feature | Upstream `agentplugins` 1.0 | DNK OS Native Plugin Architecture | Assimilation Strategy |
|---|---|---|---|
| **Package Layout** | `plugin.json`, `skills/`, `mcp.json` | MRH headers, Python modules, JSON specs | **REUSE** upstream layout via standard parser |
| **Manifest Schema** | Closed schema `plugin.json` | Dynamic MRH + Python class metadata | **REUSE** closed schema + map via `extensions["com.dnk-os.plugin"]` |
| **Skill Discovery** | `skills/*/SKILL.md` | `skills/<skill_name>/SKILL.md` | **REUSE** (100% compatible with DNK skill compiler) |
| **MCP Integration** | `mcp.json` (stdio, http, sse) | FastMCP / standard MCP client | **REUSE** (Parse `mcp.json` into FastMCP / DNK MCP router) |
| **Permissions** | Unspecified / None | MRH / L1-L4 Security Matrix | **REIMPLEMENT** (DNK Security Gate overlays upstream spec) |
| **Sandboxing** | Unspecified | Docker / Isolated Venv / Process Sandbox | **REIMPLEMENT** (DNK Subprocess Launcher with `PLUGIN_ROOT` & `PLUGIN_DATA`) |

---

## 7. Assimilation Module Decisions (REUSE / REIMPLEMENT / REFERENCE / REJECT)

| Module / Asset | Action | Justification |
|---|---|---|
| `schemas/1.0.0/plugin.schema.json` | **REUSE** | Direct validation of incoming third-party Agent Plugins manifests. |
| `schemas/1.0.0/mcp.schema.json` | **REUSE** | Direct validation of `mcp.json` configs for MCP server loading. |
| `spec/1.0.0.md` (Skills & MCP Rules) | **REUSE** | Adopt standard discovery (`skills/*/SKILL.md`, `mcp.json`) and variable expansion (`${PLUGIN_ROOT}`, `${PLUGIN_DATA}`). |
| Upstream Closed Manifest Schema | **REUSE** | Keep core `plugin.json` clean and place all DNK-specific fields under `extensions["com.dnk-os.plugin"]`. |
| Subprocess Execution & Security | **REIMPLEMENT** | Build DNK-native sandboxed subprocess runner (`PluginSandboxLauncher`) enforcing L1-L4 risk policies. |
| Upstream Scripts & Tooling | **REFERENCE** | No upstream python/shell scripts exist in spec repo; zero code to copy. |
| Non-portable Spec Extensions | **REJECT** | Reject unvalidated third-party extension namespaces until explicitly permitted. |

---

## 8. Verification & Document Checks

- [x] MRH Header verified (`# author: "DNK-e.com Maksym"`).
- [x] Upstream commit SHA & License files audited.
- [x] License matrix completed with CC-BY-4.0 & Apache-2.0 requirements.
- [x] Manifest schema & discovery rules fully documented.
- [x] Security gaps explicitly identified and mitigation strategy formulated.
- [x] Zero production code modified in `core/plugins/`, `plugins/`, `tests/`, `scripts/`.
- [x] Working branch verified clean: `mentor/plugins/DNK-ASSIM-012-agent-plugins-spec`.

---

## 9. Handoff & Next Steps

This Research Report (`RN-012`) is ready for mentor audit. 

**Next Gate**:
Upon approval of `RN-012`, proceed to create Architecture Spec `DNK-ARCH-012` (`docs/tech/specs/DNK-ARCH-012-agent-plugins-architecture.md`) and Contracts Spec `DNK-COMP-012`.
