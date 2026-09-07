// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_client"
// purpose: "Typed read-only API client with fallback adapters for Working Cabinet (DNK-VISUAL-OS-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

export interface SystemHealth {
  status: "HEALTHY" | "DEGRADED" | "DOWN";
  uptime_seconds: number;
  active_agents: number;
  active_workers: number;
  pending_approvals: number;
  trusted_plugins_count: number;
  event_bus_status: "CONNECTED" | "DISCONNECTED";
  memory_usage_mb: number;
  cpu_percent: number;
}

export interface ValidationGate {
  name: string;
  passed: boolean;
  message?: string;
}

export interface TaskTreeItem {
  id: string;
  title: string;
  plant_scale: "Project_Field" | "Sector_Zone" | "Epic_Tree" | "Feature_Bush" | "Task_Flower";
  status: "pending" | "in_progress" | "completed" | "failed";
  parent_id?: string;
  assigned_agent?: string;
  dod_criteria: string[];
  dod_progress: number;
  validation_gates: ValidationGate[];
  cycle_report_path?: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  level: "INFO" | "WARNING" | "ERROR" | "SECURITY" | "SUCCESS";
  category: "TASK" | "AGENT" | "SUPERVISOR" | "SECURITY" | "WORKER" | "build" | "deployment" | "adapter" | "governance" | "quality_gate";
  source: string;
  message: string;
  title?: string;
  summary?: string;
  details?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface GitHubAdapterEnvelope<T> {
  data: T;
  data_source: "live" | "cache" | "fixture";
  stale: boolean;
  fetched_at: string;
  expires_at: string;
  error_code?: string | null;
}

export interface GitHubPRListItem {
  number: number;
  title: string;
  state: "OPEN" | "CLOSED" | "MERGED";
  head_sha: string;
  base_branch: string;
  head_branch?: string;
  user_login?: string;
  additions?: number;
  deletions?: number;
  checks_status: string;
  mergeable: boolean;
  merged_at?: string | null;
  changed_files_count?: number | null;
  checks?: Array<{
    name: string;
    status: string;
    conclusion?: string | null;
  }>;
}

export interface GitHubCheckRun {
  id?: string | number;
  name: string;
  app_name?: string | null;
  status: string;
  conclusion?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  html_url?: string | null;
  details?: Record<string, any> | null;
}

export interface GitHubChangedFile {
  filename: string;
  status: "added" | "modified" | "deleted" | "renamed";
  additions: number;
  deletions: number;
  changes: number;
  patch?: string;
}

export interface DiffLine {
  type: "context" | "add" | "delete";
  old_line_number?: number | null;
  new_line_number?: number | null;
  content: string;
}

export interface DiffHunk {
  old_start: number;
  old_lines: number;
  new_start: number;
  new_lines: number;
  header: string;
  lines: DiffLine[];
}

export interface ParsedFileDiff {
  filename: string;
  old_path?: string;
  new_path?: string;
  status: "added" | "modified" | "deleted" | "renamed";
  additions: number;
  deletions: number;
  changes: number;
  is_binary: boolean;
  hunks: DiffHunk[];
}

export interface DiffTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  status?: string;
  file_count?: number;
  additions: number;
  deletions: number;
  changes: number;
  is_binary?: boolean;
  children?: DiffTreeNode[];
}

export interface PRDiffResponse {
  pr_number: number;
  total_files: number;
  total_additions: number;
  total_deletions: number;
  tree: DiffTreeNode;
  files: ParsedFileDiff[];
}

export interface PRFileDiffResponse {
  pr_number: number;
  filename: string;
  file_diff: ParsedFileDiff;
}

export interface ASTSymbolChange {
  name: string;
  kind: "class" | "function" | "method" | "header";
  change_type: "added" | "modified" | "deleted";
  line_start?: number;
  line_end?: number;
  details?: string;
}

export interface ASTFileDiff {
  filename: string;
  language: string;
  symbols: ASTSymbolChange[];
  added_count: number;
  modified_count: number;
  deleted_count: number;
}

export interface PRASTDiffResponse {
  pr_number: number;
  ast_diffs: ASTFileDiff[];
}

export interface TimelineEnvelope {
  data: TimelineEvent[];
  total_count: number;
  data_source: string;
  stale: boolean;
  fetched_at: string;
  expires_at: string;
  error_code?: string | null;
}

export interface ApprovalRequest {
  id: string;
  task_id: string;
  title: string;
  requester: string;
  gate_type: "HITL" | "SECURITY" | "DEPLOYMENT" | "SCHEMA_CHANGE";
  status: "pending" | "approved" | "rejected";
  created_at: string;
  preview_payload: Record<string, unknown>;
  justification?: string;
}

export interface PluginTrustStatus {
  id: string;
  name: string;
  version: string;
  trusted: boolean;
  signer: string;
  signature_verified: boolean;
  capabilities: string[];
  last_audit_at?: string;
}

export interface ShopifyDiffPreview {
  theme_id: string;
  changes_count: number;
  diff_entries: Array<{
    file_path: string;
    change_type: "added" | "modified" | "deleted";
    simulated_patch_preview: string;
  }>;
  dry_run_passed: boolean;
  reconciliation_plan: string[];
}

export interface CanvasResearchTopic {
  id: string;
  topic: string;
  active_subagents: string[];
  artifacts_count: number;
  last_updated: string;
  summary: string;
}

export class DNKCabinetApiClient {
  private baseUrl: string;
  private workspaceId: string;

  constructor(baseUrl: string = "/api", workspaceId: string = "ws-alpha-001") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.workspaceId = workspaceId;
  }

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Workspace-ID": this.workspaceId,
      },
    });

    if (!res.ok) {
      throw new Error(`DNK API Error [${res.status}]: ${res.statusText} at ${path}`);
    }

    return res.json();
  }

  async getHealth(): Promise<SystemHealth> {
    try {
      return await this.get<SystemHealth>("/cabinet/health");
    } catch (e) {
      console.warn("Fallback to fixture for health due to error:", e);
      return {
        status: "HEALTHY",
        uptime_seconds: 14280,
        active_agents: 3,
        active_workers: 4,
        pending_approvals: 2,
        trusted_plugins_count: 5,
        event_bus_status: "CONNECTED",
        memory_usage_mb: 248.5,
        cpu_percent: 4.2,
      };
    }
  }

  async getTasks(): Promise<TaskTreeItem[]> {
    try {
      return await this.get<TaskTreeItem[]>("/cabinet/tasks");
    } catch (e) {
      console.warn("Fallback to fixture for tasks due to error:", e);
      return [
        {
          id: "task-field-001",
          title: "DNK OS Production Runtime",
          plant_scale: "Project_Field",
          status: "in_progress",
          assigned_agent: "Hermes (Gerych)",
          dod_criteria: ["Docker runtimes green", "Fail-closed auth", "Zero liquid diff verified"],
          dod_progress: 85,
          validation_gates: [
            { name: "Security Gate", passed: true },
            { name: "MRH Header Compliance", passed: true },
            { name: "Zero Host Pollution", passed: true },
          ],
          cycle_report_path: "docs/reports/execution_cycles/CYCLE-001.md",
        },
        {
          id: "task-flower-003",
          title: "Working Cabinet Visual MVP",
          plant_scale: "Task_Flower",
          status: "in_progress",
          parent_id: "task-field-001",
          assigned_agent: "dnk-dev-01",
          dod_criteria: ["App Shell", "TaskDNA Timeline", "Approval Inbox", "Shopify Diff Viewer"],
          dod_progress: 90,
          validation_gates: [
            { name: "Component Unit Tests", passed: true },
            { name: "Read-Only Invariant", passed: true },
          ],
          cycle_report_path: "docs/reports/execution_cycles/CYCLE-003.md",
        },
      ];
    }
  }

  async getTimeline(): Promise<TimelineEvent[]> {
    try {
      return await this.get<TimelineEvent[]>("/cabinet/timeline");
    } catch (e) {
      console.warn("Fallback to fixture for timeline due to error:", e);
      return [
        {
          id: "evt-001",
          timestamp: new Date().toISOString(),
          level: "INFO",
          category: "SUPERVISOR",
          source: "Antigravity",
          message: "TaskDNA architectural contract approved (DNK-OS-001).",
        },
        {
          id: "evt-002",
          timestamp: new Date().toISOString(),
          level: "INFO",
          category: "WORKER",
          source: "Hermes",
          message: "Dispatched subagent flower dnk-dev-01 for Cabinet UI.",
        },
        {
          id: "evt-003",
          timestamp: new Date().toISOString(),
          level: "SECURITY",
          category: "SECURITY",
          source: "FailClosedMiddleware",
          message: "Validated JWT & workspace tenancy token with 0 mutations.",
        },
      ];
    }
  }

  async getApprovals(): Promise<ApprovalRequest[]> {
    try {
      return await this.get<ApprovalRequest[]>("/cabinet/approvals");
    } catch (e) {
      console.warn("Fallback to fixture for approvals due to error:", e);
      return [
        {
          id: "appr-001",
          task_id: "task-flower-003",
          title: "Approve Theme Patch Simulation Manifest",
          requester: "Hermes",
          gate_type: "HITL",
          status: "pending",
          created_at: new Date().toISOString(),
          preview_payload: {
            target: "shopify_theme_preview",
            simulated_files_count: 2,
            dry_run: true,
            mutations_allowed: false,
          },
        },
        {
          id: "appr-002",
          task_id: "task-field-001",
          title: "Verify ED25519 Plugin Signature for Shopify Adapter",
          requester: "dnk_governance_companion",
          gate_type: "SECURITY",
          status: "pending",
          created_at: new Date().toISOString(),
          preview_payload: {
            plugin_name: "dnk_shopify_adapter",
            signer_key_id: "key-ed25519-0941",
            verified: true,
          },
        },
      ];
    }
  }

  async getPlugins(): Promise<PluginTrustStatus[]> {
    try {
      return await this.get<PluginTrustStatus[]>("/cabinet/plugins");
    } catch (e) {
      console.warn("Fallback to fixture for plugins due to error:", e);
      return [
        {
          id: "plug-01",
          name: "dnk_governance_companion",
          version: "1.2.0",
          trusted: true,
          signer: "DNK Core Authority (ED25519)",
          signature_verified: true,
          capabilities: ["read_telemetry", "validate_mrh", "audit_checks"],
        },
        {
          id: "plug-02",
          name: "dnk_shopify_read_adapter",
          version: "2.0.0",
          trusted: true,
          signer: "DNK Core Authority (ED25519)",
          signature_verified: true,
          capabilities: ["read_theme_liquid", "dry_run_simulation"],
        },
        {
          id: "plug-03",
          name: "dnk_canvas_research_agent",
          version: "1.0.4",
          trusted: true,
          signer: "DNK Core Authority (ED25519)",
          signature_verified: true,
          capabilities: ["canvas_graph_query", "arxiv_synthesis"],
        },
      ];
    }
  }

  async getShopifyDiff(): Promise<ShopifyDiffPreview> {
    try {
      return await this.get<ShopifyDiffPreview>("/cabinet/shopify/diff");
    } catch (e) {
      console.warn("Fallback to fixture for shopify diff due to error:", e);
      return {
        theme_id: "main-prod-dawn-theme",
        changes_count: 2,
        diff_entries: [
          {
            file_path: "sections/cart-drawer.liquid",
            change_type: "modified",
            simulated_patch_preview: "@@ -12,4 +12,6 @@\n+ <div class=\"dnk-cart-badge\" data-status=\"simulated\">\n+   <span>DNK OS Safe Preview</span>\n+ </div>",
          },
          {
            file_path: "snippets/dnk-telemetry-hook.liquid",
            change_type: "added",
            simulated_patch_preview: "@@ -0,0 +1,5 @@\n+ {% comment %} DNK Safe Telemetry Listener {% endcomment %}\n+ <script>console.log('DNK OS Read-Only Hook Active');</script>",
          },
        ],
        dry_run_passed: true,
        reconciliation_plan: [
          "1. Static syntax check via pytest",
          "2. Shadow DOM render in Docker",
          "3. Zero-mutation validation gate",
        ],
      };
    }
  }

  async getCanvasResearch(): Promise<CanvasResearchTopic[]> {
    try {
      return await this.get<CanvasResearchTopic[]>("/cabinet/canvas/research");
    } catch (e) {
      console.warn("Fallback to fixture for canvas research due to error:", e);
      return [
        {
          id: "res-01",
          topic: "Multi-Agent Graph Orchestration (TaskDNA v2)",
          active_subagents: ["rick", "dnk-dev-01"],
          artifacts_count: 4,
          last_updated: new Date().toISOString(),
          summary: "Synthesized architecture inventory and formal TaskDNA contract. Passed verification with 0 schema drift.",
        },
        {
          id: "res-02",
          topic: "Zero Host Pollution Container Isolation",
          active_subagents: ["dnk_governance_companion"],
          artifacts_count: 2,
          last_updated: new Date().toISOString(),
          summary: "Enforced volume masking on /app/node_modules and isolated ARM64 / Linux build artifacts.",
        },
      ];
    }
  }

  async getGitHubPRs(owner: string = "Kuzmenko-top", repo: string = "DNK_OS_MVP", state: string = "all"): Promise<GitHubAdapterEnvelope<GitHubPRListItem[]>> {
    try {
      return await this.get<GitHubAdapterEnvelope<GitHubPRListItem[]>>(`/github/prs/${owner}/${repo}?state=${state}&allow_fixture_fallback=true`);
    } catch (e) {
      console.warn("Fallback to fixture for getGitHubPRs due to error:", e);
      return {
        data: [
          {
            number: 30,
            title: "feat(cabinet): Working Cabinet UX Polish — PR Inspector & Checks (DNK-UX-002)",
            state: "OPEN",
            head_sha: "e8210f92a401928371191029312389a0c1028123",
            base_branch: "main",
            checks_status: "PENDING",
            mergeable: true,
            changed_files_count: 5,
            checks: [
              { name: "fast-syntax-check", status: "completed", conclusion: "success" },
              { name: "pytest-regression", status: "in_progress", conclusion: null }
            ]
          },
          {
            number: 29,
            title: "feat(adapter): Shopify Admin API read-only adapter & Theme Asset Inspector (DNK-OS-003)",
            state: "MERGED",
            head_sha: "a1604f10cccd5a72ce6226b80b4c812ae11304f1",
            base_branch: "main",
            checks_status: "SUCCESS",
            mergeable: true,
            merged_at: "2026-08-28T10:15:00Z",
            changed_files_count: 8,
            checks: [
              { name: "fast-syntax-check", status: "completed", conclusion: "success" },
              { name: "pytest-regression", status: "completed", conclusion: "success" }
            ]
          }
        ],
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }

  async getGitHubPRChecks(owner: string = "Kuzmenko-top", repo: string = "DNK_OS_MVP", prNumber: number, ref?: string): Promise<GitHubAdapterEnvelope<{ pr_number: number; target_ref: string; total_count: number; check_runs: GitHubCheckRun[] }>> {
    try {
      const refParam = ref ? `&ref=${ref}` : "";
      return await this.get<GitHubAdapterEnvelope<any>>(`/github/pr/${owner}/${repo}/${prNumber}/checks?allow_fixture_fallback=true${refParam}`);
    } catch (e) {
      console.warn("Fallback to fixture for getGitHubPRChecks due to error:", e);
      return {
        data: {
          pr_number: prNumber,
          target_ref: ref || "e8210f92a",
          total_count: 3,
          check_runs: [
            { name: "fast-syntax-check", status: "completed", conclusion: "success", started_at: "2026-08-28T10:00:00Z", completed_at: "2026-08-28T10:01:12Z" },
            { name: "pytest-regression", status: "completed", conclusion: "success", started_at: "2026-08-28T10:01:15Z", completed_at: "2026-08-28T10:04:30Z" },
            { name: "relative-path-gate", status: "completed", conclusion: "success", started_at: "2026-08-28T10:04:32Z", completed_at: "2026-08-28T10:04:45Z" }
          ]
        },
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }

  async getGitHubPRFiles(owner: string = "Kuzmenko-top", repo: string = "DNK_OS_MVP", prNumber: number): Promise<GitHubAdapterEnvelope<{ pr_number: number; file_count: number; files: GitHubChangedFile[] }>> {
    try {
      return await this.get<GitHubAdapterEnvelope<any>>(`/github/pr/${owner}/${repo}/${prNumber}/files?allow_fixture_fallback=true`);
    } catch (e) {
      console.warn("Fallback to fixture for getGitHubPRFiles due to error:", e);
      return {
        data: {
          pr_number: prNumber,
          file_count: 2,
          files: [
            { filename: "apps/web/components/cabinet/PRInspectorTab.tsx", status: "added", additions: 180, deletions: 0, changes: 180 },
            { filename: "apps/api/routers/github.py", status: "modified", additions: 25, deletions: 2, changes: 27 }
          ]
        },
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }

  async getGitHubPRDiff(owner: string = "Kuzmenko-top", repo: string = "DNK_OS_MVP", prNumber: number): Promise<GitHubAdapterEnvelope<PRDiffResponse>> {
    try {
      return await this.get<GitHubAdapterEnvelope<PRDiffResponse>>(`/github/pr/${owner}/${repo}/${prNumber}/diff?allow_fixture_fallback=true`);
    } catch (e) {
      console.warn("Fallback to fixture for getGitHubPRDiff due to error:", e);
      return {
        data: {
          pr_number: prNumber,
          total_files: 2,
          total_additions: 32,
          total_deletions: 5,
          tree: {
            name: "root",
            path: "",
            type: "directory",
            file_count: 2,
            additions: 32,
            deletions: 5,
            changes: 37,
            children: [
              {
                name: "apps",
                path: "apps",
                type: "directory",
                file_count: 2,
                additions: 32,
                deletions: 5,
                changes: 37,
                children: [
                  {
                    name: "api",
                    path: "apps/api",
                    type: "directory",
                    file_count: 1,
                    additions: 25,
                    deletions: 0,
                    changes: 25,
                    children: [
                      {
                        name: "services",
                        path: "apps/api/services",
                        type: "directory",
                        file_count: 1,
                        additions: 25,
                        deletions: 0,
                        changes: 25,
                        children: [
                          { name: "diff_parser.py", path: "apps/api/services/diff_parser.py", type: "file", status: "added", additions: 25, deletions: 0, changes: 25 }
                        ]
                      }
                    ]
                  },
                  {
                    name: "web",
                    path: "apps/web",
                    type: "directory",
                    file_count: 1,
                    additions: 7,
                    deletions: 5,
                    changes: 12,
                    children: [
                      {
                        name: "components",
                        path: "apps/web/components",
                        type: "directory",
                        file_count: 1,
                        additions: 7,
                        deletions: 5,
                        changes: 12,
                        children: [
                          {
                            name: "cabinet",
                            path: "apps/web/components/cabinet",
                            type: "directory",
                            file_count: 1,
                            additions: 7,
                            deletions: 5,
                            changes: 12,
                            children: [
                              { name: "PRInspectorTab.tsx", path: "apps/web/components/cabinet/PRInspectorTab.tsx", type: "file", status: "modified", additions: 7, deletions: 5, changes: 12 }
                            ]
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            ]
          },
          files: [
            {
              filename: "apps/api/services/diff_parser.py",
              status: "added",
              additions: 25,
              deletions: 0,
              changes: 25,
              is_binary: false,
              hunks: [
                {
                  old_start: 0,
                  old_lines: 0,
                  new_start: 1,
                  new_lines: 7,
                  header: "@@ -0,0 +1,7 @@",
                  lines: [
                    { type: "add", new_line_number: 1, content: "# --- DNK-MRH-HEADER ---" },
                    { type: "add", new_line_number: 2, content: "# mrh_id: \"apps_api_services_diff_parser\"" },
                    { type: "add", new_line_number: 3, content: "class DiffParser:" },
                    { type: "add", new_line_number: 4, content: "    def parse(self):" },
                    { type: "add", new_line_number: 5, content: "        pass" }
                  ]
                }
              ]
            },
            {
              filename: "apps/web/components/cabinet/PRInspectorTab.tsx",
              status: "modified",
              additions: 7,
              deletions: 5,
              changes: 12,
              is_binary: false,
              hunks: [
                {
                  old_start: 10,
                  old_lines: 6,
                  new_start: 10,
                  new_lines: 8,
                  header: "@@ -10,6 +10,8 @@",
                  lines: [
                    { type: "context", old_line_number: 10, new_line_number: 10, content: "export const PRInspectorTab = () => {" },
                    { type: "delete", old_line_number: 11, content: "  return <div>Old</div>;" },
                    { type: "add", new_line_number: 11, content: "  return <FileDiffTree />;" }
                  ]
                }
              ]
            }
          ]
        },
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }

  async getGitHubPRFileDiff(owner: string = "Kuzmenko-top", repo: string = "DNK_OS_MVP", prNumber: number, filename: string): Promise<GitHubAdapterEnvelope<PRFileDiffResponse>> {
    try {
      return await this.get<GitHubAdapterEnvelope<PRFileDiffResponse>>(`/github/pr/${owner}/${repo}/${prNumber}/diff/file?filename=${encodeURIComponent(filename)}&allow_fixture_fallback=true`);
    } catch (e) {
      console.warn("Fallback to fixture for getGitHubPRFileDiff due to error:", e);
      return {
        data: {
          pr_number: prNumber,
          filename: filename,
          file_diff: {
            filename: filename,
            status: "modified",
            additions: 10,
            deletions: 2,
            changes: 12,
            is_binary: false,
            hunks: []
          }
        },
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }

  async getGitHubPRASTDiff(owner: string = "Kuzmenko-top", repo: string = "DNK_OS_MVP", prNumber: number, filename?: string): Promise<GitHubAdapterEnvelope<PRASTDiffResponse>> {
    try {
      const q = filename ? `&filename=${encodeURIComponent(filename)}` : "";
      return await this.get<GitHubAdapterEnvelope<PRASTDiffResponse>>(`/github/pr/${owner}/${repo}/${prNumber}/ast-diff?allow_fixture_fallback=true${q}`);
    } catch (e) {
      console.warn("Fallback to fixture for getGitHubPRASTDiff due to error:", e);
      return {
        data: {
          pr_number: prNumber,
          ast_diffs: [
            {
              filename: "apps/api/services/diff_parser.py",
              language: "python",
              symbols: [
                { name: "MRH Header (apps_api_services_diff_parser)", kind: "header", change_type: "added" },
                { name: "DiffParser", kind: "class", change_type: "added" },
                { name: "parse_diff_hunk", kind: "function", change_type: "added" }
              ],
              added_count: 3,
              modified_count: 0,
              deleted_count: 0
            }
          ]
        },
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }

  async getTimelineStream(source?: string, category?: string, level?: string): Promise<TimelineEnvelope> {
    try {
      const params = new URLSearchParams();
      if (source && source !== "all") params.append("source", source);
      if (category && category !== "all") params.append("category", category);
      if (level && level !== "all") params.append("level", level);
      const queryStr = params.toString() ? `?${params.toString()}` : "";
      return await this.get<TimelineEnvelope>(`/timeline/events${queryStr}`);
    } catch (e) {
      console.warn("Fallback to fixture for getTimelineStream due to error:", e);
      return {
        data: [
          {
            id: "evt-300",
            title: "PR #29 Merged Successfully",
            timestamp: new Date().toISOString(),
            source: "github",
            category: "governance",
            level: "SUCCESS",
            summary: "PR #29 'feat(adapter): Shopify Admin API read-only adapter & Theme Asset Inspector' merged to main.",
            message: "PR #29 merged into main"
          },
          {
            id: "evt-299",
            title: "Shopify Asset Inspection Executed",
            timestamp: new Date().toISOString(),
            source: "shopify",
            category: "adapter",
            level: "INFO",
            summary: "Read-only Theme Asset Inspector completed inspection of 42 liquid assets.",
            message: "Inspected 42 assets"
          }
        ],
        total_count: 2,
        data_source: "fixture",
        stale: false,
        fetched_at: new Date().toISOString(),
        expires_at: new Date().toISOString()
      };
    }
  }
}

export const cabinetApi = new DNKCabinetApiClient();
