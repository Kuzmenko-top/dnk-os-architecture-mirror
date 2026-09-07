# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_github_adapter"
# purpose: "Server-side read-only GitHub API adapter with transport isolation, 60s caching, and security invariants"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, Set, List

from apps.api.services.github_transport import (
    BaseGitHubTransport,
    HttpGitHubTransport,
    DEFAULT_TIMEOUT_SECONDS
)
from apps.api.services.github_models import (
    GitHubAdapterResult,
    NormalizedPullRequest,
    NormalizedCheckRun,
    NormalizedChangedFile,
    NormalizedBranch
)
from apps.api.services.diff_parser import parse_file_patch, build_diff_tree
from apps.api.services.ast_diff import analyze_file_ast_diff

# Strict security allowlists & invariants
ALLOWED_REPOSITORIES: Set[str] = {
    "Kuzmenko-top/DNK_OS_MVP",
    "DNKShopify/DNK-e.com",
    "Kuzmenko-top/dnk-os-mvp-assimilation"
}
DEFAULT_CACHE_TTL_SECONDS: int = 60


class GitHubAdapter:
    """Server-side read-only adapter connecting to GitHub REST API via dedicated transport."""

    def __init__(
        self,
        transport: Optional[BaseGitHubTransport] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS
    ):
        self._transport = transport or HttpGitHubTransport()
        self._cache_ttl = cache_ttl
        # In-memory cache structure: {cache_key: (data_obj, fetched_at_ts, expires_at_ts)}
        self._cache: Dict[str, Tuple[Any, float, float]] = {}

    def _validate_repo(self, repo: str) -> bool:
        return repo in ALLOWED_REPOSITORIES

    def get_pull_request(
        self,
        repo: str,
        pr_number: int,
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch and normalize Pull Request status with cache and failure isolation."""
        now_ts = time.time()
        now_iso = datetime.fromtimestamp(now_ts, tz=timezone.utc).isoformat()
        expires_iso = datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat()

        if not self._validate_repo(repo):
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code="forbidden_repo"
            )

        cache_key = f"pr:{repo}:{pr_number}"
        cached_entry = self._cache.get(cache_key)

        # 0. Fixture mode override (enforces zero network egress when requested)
        if os.getenv("FIXTURE_MODE", "false").lower() == "true":
            fixture_data = NormalizedPullRequest(
                number=pr_number,
                title=f"Task Pull Request #{pr_number}",
                state="MERGED",
                head_sha="ea59b1c14e79ace62c58a300c4d68cd4ac88218f",
                base_branch="main",
                checks_status="SUCCESS",
                mergeable=True,
                checks=[]
            ).model_dump()
            return GitHubAdapterResult(
                data=fixture_data,
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        # 1. Check valid cache
        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            if now_ts < expires_at:
                return GitHubAdapterResult(
                    data=cached_data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                    error_code=None
                )

        # 2. Outbound request to GitHub API via transport
        raw_data, status, error_code = self._transport.get(f"repos/{repo}/pulls/{pr_number}")

        if status == 200 and isinstance(raw_data, dict):
            state_val = "MERGED" if raw_data.get("merged") else (
                "OPEN" if raw_data.get("state") == "open" else "CLOSED"
            )
            norm_pr = NormalizedPullRequest(
                number=raw_data.get("number", pr_number),
                title=raw_data.get("title", ""),
                state=state_val,
                head_sha=raw_data.get("head", {}).get("sha", ""),
                base_branch=raw_data.get("base", {}).get("ref", "main"),
                checks_status="SUCCESS" if state_val == "MERGED" else "PENDING",
                mergeable=raw_data.get("mergeable", True),
                merged_at=raw_data.get("merged_at"),
                changed_files_count=raw_data.get("changed_files"),
                checks=[]
            ).model_dump()

            self._cache[cache_key] = (norm_pr, now_ts, now_ts + self._cache_ttl)
            return GitHubAdapterResult(
                data=norm_pr,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        # 3. Security fail-closed for auth errors (401/403) - do NOT use fixture fallback
        if status in (401, 403) or error_code in ("unauthorized", "forbidden"):
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=error_code or "unauthorized"
            )

        # 4. Stale cache fallback if available
        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            return GitHubAdapterResult(
                data=cached_data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                error_code=error_code or "cache_stale"
            )

        # 5. Fallback to fixture if explicit fallback permitted
        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true":
            fixture_data = NormalizedPullRequest(
                number=pr_number,
                title=f"Task Pull Request #{pr_number}",
                state="MERGED",
                head_sha="6e87df1fea33b02517d9f39cbf6059b55b302760",
                base_branch="main",
                checks_status="SUCCESS",
                mergeable=True,
                checks=[]
            ).model_dump()
            return GitHubAdapterResult(
                data=fixture_data,
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=error_code
            )

        return GitHubAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=expires_iso,
            error_code=error_code or "upstream_failure"
        )

    def get_check_runs(
        self,
        repo: str,
        ref: str,
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch check runs and commit status for a ref/SHA."""
        now_ts = time.time()
        now_iso = datetime.fromtimestamp(now_ts, tz=timezone.utc).isoformat()
        expires_iso = datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat()

        if not self._validate_repo(repo):
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code="forbidden_repo"
            )

        cache_key = f"checks:{repo}:{ref}"
        cached_entry = self._cache.get(cache_key)

        if os.getenv("FIXTURE_MODE", "false").lower() == "true":
            fixture_data = {
                "ref": ref,
                "total_count": 1,
                "overall_status": "SUCCESS",
                "check_runs": [
                    NormalizedCheckRun(
                        name="ci/pytest",
                        status="completed",
                        conclusion="success",
                        started_at=now_iso,
                        completed_at=now_iso
                    ).model_dump()
                ]
            }
            return GitHubAdapterResult(
                data=fixture_data,
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            if now_ts < expires_at:
                return GitHubAdapterResult(
                    data=cached_data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                    error_code=None
                )

        raw_data, status, error_code = self._transport.get(f"repos/{repo}/commits/{ref}/check-runs")

        if status == 200 and isinstance(raw_data, dict):
            raw_check_runs = raw_data.get("check_runs", [])
            normalized_runs = []
            overall_status = "SUCCESS" if raw_check_runs else "NEUTRAL"
            
            for cr in raw_check_runs:
                c_status = cr.get("status", "completed")
                c_conclusion = cr.get("conclusion")
                if c_conclusion in ("failure", "timed_out", "action_required", "cancelled"):
                    overall_status = "FAILURE"
                elif c_status != "completed" and overall_status != "FAILURE":
                    overall_status = "PENDING"
                
                normalized_runs.append(
                    NormalizedCheckRun(
                        name=cr.get("name", "unknown_check"),
                        status="completed" if c_status == "completed" else "in_progress",
                        conclusion=c_conclusion,
                        started_at=cr.get("started_at"),
                        completed_at=cr.get("completed_at"),
                        html_url=cr.get("html_url")
                    ).model_dump()
                )

            result_data = {
                "ref": ref,
                "total_count": raw_data.get("total_count", len(normalized_runs)),
                "overall_status": overall_status,
                "check_runs": normalized_runs
            }

            self._cache[cache_key] = (result_data, now_ts, now_ts + self._cache_ttl)
            return GitHubAdapterResult(
                data=result_data,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if error_code == "unauthorized":
            if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true":
                return GitHubAdapterResult(
                    data={
                        "total_count": 2,
                        "check_runs": [
                            {
                                "id": 1001,
                                "name": "quality-gate / verify-all",
                                "status": "completed",
                                "conclusion": "success",
                                "started_at": now_iso,
                                "completed_at": now_iso,
                                "html_url": f"https://github.com/{repo}/actions/runs/1001",
                                "app": {"name": "GitHub Actions", "slug": "github-actions"}
                            },
                            {
                                "id": 1002,
                                "name": "security / static-analysis",
                                "status": "completed",
                                "conclusion": "success",
                                "started_at": now_iso,
                                "completed_at": now_iso,
                                "html_url": f"https://github.com/{repo}/actions/runs/1002",
                                "app": {"name": "GitHub Actions", "slug": "github-actions"}
                            }
                        ]
                    },
                    data_source="fixture",
                    stale=False,
                    fetched_at=now_iso,
                    expires_at=expires_iso
                )
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code="unauthorized"
            )

        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            return GitHubAdapterResult(
                data=cached_data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                error_code=error_code or "cache_stale"
            )

        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true":
            fixture_data = {
                "ref": ref,
                "total_count": 1,
                "overall_status": "SUCCESS",
                "check_runs": [
                    NormalizedCheckRun(
                        name="ci/pytest",
                        status="completed",
                        conclusion="success",
                        started_at=now_iso,
                        completed_at=now_iso
                    ).model_dump()
                ]
            }
            return GitHubAdapterResult(
                data=fixture_data,
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=error_code
            )

        return GitHubAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=expires_iso,
            error_code=error_code or "upstream_failure"
        )

    def get_changed_files(
        self,
        repo: str,
        pr_number: int,
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch changed files list for a Pull Request."""
        now_ts = time.time()
        now_iso = datetime.fromtimestamp(now_ts, tz=timezone.utc).isoformat()
        expires_iso = datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat()

        if not self._validate_repo(repo):
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code="forbidden_repo"
            )

        cache_key = f"files:{repo}:{pr_number}"
        cached_entry = self._cache.get(cache_key)

        if os.getenv("FIXTURE_MODE", "false").lower() == "true":
            fixture_files = [
                NormalizedChangedFile(
                    filename="apps/api/services/diff_parser.py",
                    status="added",
                    additions=25,
                    deletions=0,
                    changes=25,
                    patch="@@ -0,0 +1,25 @@\n+# --- DNK-MRH-HEADER ---\n+# mrh_id: \"apps_api_services_diff_parser\"\n+class DiffParser:\n+    def parse(self):\n+        pass\n+async def parse_diff_hunk():\n+    return []"
                ).model_dump(),
                NormalizedChangedFile(
                    filename="apps/web/components/cabinet/PRInspectorTab.tsx",
                    status="modified",
                    additions=12,
                    deletions=3,
                    changes=15,
                    patch="@@ -10,6 +10,15 @@\n export const PRInspectorTab = () => {\n-  return <div>Old Tab</div>;\n+  const [diff, setDiff] = useState(null);\n+  return (\n+    <div className=\"pr-inspector\">\n+      <FileDiffTree />\n+    </div>\n+  );\n }"
                ).model_dump(),
                NormalizedChangedFile(
                    filename="tests/dnk_ux_003/test_diff.py",
                    status="added",
                    additions=15,
                    deletions=0,
                    changes=15,
                    patch="@@ -0,0 +1,15 @@\n+def test_diff_tree():\n+    assert True"
                ).model_dump()
            ]
            fixture_data = {
                "pr_number": pr_number,
                "file_count": len(fixture_files),
                "files": fixture_files
            }
            return GitHubAdapterResult(
                data=fixture_data,
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            if now_ts < expires_at:
                return GitHubAdapterResult(
                    data=cached_data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                    error_code=None
                )

        raw_data, status, error_code = self._transport.get(f"repos/{repo}/pulls/{pr_number}/files")

        if status == 200 and isinstance(raw_data, list):
            normalized_files = []
            for f in raw_data:
                normalized_files.append(
                    NormalizedChangedFile(
                        filename=f.get("filename", ""),
                        status=f.get("status", "modified"),
                        additions=f.get("additions", 0),
                        deletions=f.get("deletions", 0),
                        changes=f.get("changes", 0),
                        patch=f.get("patch")
                    ).model_dump()
                )

            result_data = {
                "pr_number": pr_number,
                "file_count": len(normalized_files),
                "files": normalized_files
            }

            self._cache[cache_key] = (result_data, now_ts, now_ts + self._cache_ttl)
            return GitHubAdapterResult(
                data=result_data,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true":
            fixture_files = [
                NormalizedChangedFile(
                    filename="apps/api/services/diff_parser.py",
                    status="added",
                    additions=25,
                    deletions=0,
                    changes=25,
                    patch="@@ -0,0 +1,25 @@\n+# --- DNK-MRH-HEADER ---\n+# mrh_id: \"apps_api_services_diff_parser\"\n+class DiffParser:\n+    def parse(self):\n+        pass\n+async def parse_diff_hunk():\n+    return []"
                ).model_dump(),
                NormalizedChangedFile(
                    filename="apps/web/components/cabinet/PRInspectorTab.tsx",
                    status="modified",
                    additions=12,
                    deletions=3,
                    changes=15,
                    patch="@@ -10,6 +10,15 @@\n export const PRInspectorTab = () => {\n-  return <div>Old Tab</div>;\n+  const [diff, setDiff] = useState(null);\n+  return (\n+    <div className=\"pr-inspector\">\n+      <FileDiffTree />\n+    </div>\n+  );\n }"
                ).model_dump(),
            ]
            return GitHubAdapterResult(
                data={
                    "pr_number": pr_number,
                    "file_count": len(fixture_files),
                    "files": fixture_files
                },
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            return GitHubAdapterResult(
                data=cached_data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                error_code=error_code or "cache_stale"
            )

        return GitHubAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=expires_iso,
            error_code=error_code or "upstream_failure"
        )

    def list_pull_requests(
        self,
        repo: str,
        state: str = "all",
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch list of normalized Pull Requests for a repository."""
        now_ts = time.time()
        now_iso = datetime.fromtimestamp(now_ts, tz=timezone.utc).isoformat()
        expires_iso = datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat()

        if not self._validate_repo(repo):
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code="forbidden_repo"
            )

        cache_key = f"prs:{repo}:{state}"
        cached_entry = self._cache.get(cache_key)

        # Fixture mode or explicit fixture fallback
        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true" or not getattr(self.transport, "token", None):
            fixture_prs = [
                NormalizedPullRequest(
                    number=30,
                    title="feat(cabinet): Working Cabinet UX Polish — PR Inspector & Checks (DNK-UX-002)",
                    state="OPEN",
                    head_sha="e8210f92a401928371191029312389a0c1028123",
                    base_branch="main",
                    checks_status="PENDING",
                    mergeable=True,
                    changed_files_count=5,
                    checks=[
                        {"name": "fast-syntax-check", "status": "completed", "conclusion": "success"},
                        {"name": "pytest-regression", "status": "in_progress", "conclusion": None}
                    ]
                ).model_dump(),
                NormalizedPullRequest(
                    number=29,
                    title="feat(adapter): Shopify Admin API read-only adapter & Theme Asset Inspector (DNK-OS-003)",
                    state="MERGED",
                    head_sha="a1604f10cccd5a72ce6226b80b4c812ae11304f1",
                    base_branch="main",
                    checks_status="SUCCESS",
                    mergeable=True,
                    merged_at="2026-08-28T10:15:00Z",
                    changed_files_count=8,
                    checks=[
                        {"name": "fast-syntax-check", "status": "completed", "conclusion": "success"},
                        {"name": "pytest-regression", "status": "completed", "conclusion": "success"},
                        {"name": "relative-path-gate", "status": "completed", "conclusion": "success"}
                    ]
                ).model_dump(),
                NormalizedPullRequest(
                    number=28,
                    title="feat(analytics): Anomaly Detection & SLO Monitoring (DNK-ANALYTICS-002)",
                    state="MERGED",
                    head_sha="4872ce018b10928374191029312389a0c1028123",
                    base_branch="main",
                    checks_status="SUCCESS",
                    mergeable=True,
                    merged_at="2026-08-27T16:30:00Z",
                    changed_files_count=14,
                    checks=[
                        {"name": "fast-syntax-check", "status": "completed", "conclusion": "success"},
                        {"name": "pytest-regression", "status": "completed", "conclusion": "success"}
                    ]
                ).model_dump(),
                NormalizedPullRequest(
                    number=27,
                    title="feat(analytics): Workspace Analytics & Metrics Dashboard (DNK-ANALYTICS-001)",
                    state="MERGED",
                    head_sha="f59a089b0110928374191029312389a0c1028123",
                    base_branch="main",
                    checks_status="SUCCESS",
                    mergeable=True,
                    merged_at="2026-08-26T14:10:00Z",
                    changed_files_count=11,
                    checks=[
                        {"name": "fast-syntax-check", "status": "completed", "conclusion": "success"}
                    ]
                ).model_dump()
            ]
            return GitHubAdapterResult(
                data=fixture_prs,
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            if now_ts < expires_at:
                return GitHubAdapterResult(
                    data=cached_data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                    error_code=None
                )

        raw_data, status, error_code = self._transport.get(f"repos/{repo}/pulls?state={state}&per_page=20")

        if status == 200 and isinstance(raw_data, list):
            normalized_prs = []
            for item in raw_data:
                state_val = "MERGED" if item.get("merged") or item.get("merged_at") else (
                    "OPEN" if item.get("state") == "open" else "CLOSED"
                )
                normalized_prs.append(
                    NormalizedPullRequest(
                        number=item.get("number", 0),
                        title=item.get("title", ""),
                        state=state_val,
                        head_sha=item.get("head", {}).get("sha", ""),
                        base_branch=item.get("base", {}).get("ref", "main"),
                        checks_status="SUCCESS" if state_val == "MERGED" else "PENDING",
                        mergeable=item.get("mergeable", True),
                        merged_at=item.get("merged_at"),
                        changed_files_count=item.get("changed_files"),
                        checks=[]
                    ).model_dump()
                )

            self._cache[cache_key] = (normalized_prs, now_ts, now_ts + self._cache_ttl)
            return GitHubAdapterResult(
                data=normalized_prs,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code=None
            )

        if error_code == "unauthorized":
            if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true":
                return GitHubAdapterResult(
                    data={
                        "total_count": 2,
                        "check_runs": [
                            {
                                "id": 1001,
                                "name": "quality-gate / verify-all",
                                "status": "completed",
                                "conclusion": "success",
                                "started_at": now_iso,
                                "completed_at": now_iso,
                                "html_url": f"https://github.com/{repo}/actions/runs/1001",
                                "app": {"name": "GitHub Actions", "slug": "github-actions"}
                            },
                            {
                                "id": 1002,
                                "name": "security / static-analysis",
                                "status": "completed",
                                "conclusion": "success",
                                "started_at": now_iso,
                                "completed_at": now_iso,
                                "html_url": f"https://github.com/{repo}/actions/runs/1002",
                                "app": {"name": "GitHub Actions", "slug": "github-actions"}
                            }
                        ]
                    },
                    data_source="fixture",
                    stale=False,
                    fetched_at=now_iso,
                    expires_at=expires_iso
                )
            return GitHubAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=expires_iso,
                error_code="unauthorized"
            )

        if cached_entry:
            cached_data, fetched_at, expires_at = cached_entry
            return GitHubAdapterResult(
                data=cached_data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(fetched_at, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
                error_code=error_code or "cache_stale"
            )

        if allow_fixture_fallback:
            return self.list_pull_requests(repo, state, allow_fixture_fallback=True)

        return GitHubAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=expires_iso,
            error_code=error_code or "upstream_failure"
        )

    def get_pr_diff(
        self,
        repo: str,
        pr_number: int,
        include_chunks: bool = True,
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch full PR diff with structured file tree and parsed hunks/lines."""
        files_result = self.get_changed_files(
            repo=repo,
            pr_number=pr_number,
            allow_fixture_fallback=allow_fixture_fallback
        )
        if files_result.error_code or not files_result.data:
            return files_result

        files = files_result.data.get("files", [])
        parsed_files = []
        for f in files:
            parsed = parse_file_patch(
                filename=f.get("filename", ""),
                patch_text=f.get("patch") or "",
                status=f.get("status", "modified")
            )
            parsed_files.append(parsed)

        tree = build_diff_tree(parsed_files)
        total_add = sum(f.get("additions", 0) for f in parsed_files)
        total_del = sum(f.get("deletions", 0) for f in parsed_files)

        diff_data = {
            "pr_number": pr_number,
            "total_files": len(parsed_files),
            "total_additions": total_add,
            "total_deletions": total_del,
            "tree": tree,
            "files": parsed_files
        }

        return GitHubAdapterResult(
            data=diff_data,
            data_source=files_result.data_source,
            stale=files_result.stale,
            fetched_at=files_result.fetched_at,
            expires_at=files_result.expires_at,
            error_code=None
        )

    def get_pr_file_diff(
        self,
        repo: str,
        pr_number: int,
        filename: str,
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch detailed diff for a single file in a PR."""
        files_result = self.get_changed_files(
            repo=repo,
            pr_number=pr_number,
            allow_fixture_fallback=allow_fixture_fallback
        )
        if files_result.error_code or not files_result.data:
            return files_result

        files = files_result.data.get("files", [])
        target_file = None
        for f in files:
            if f.get("filename") == filename:
                target_file = f
                break

        if not target_file:
            return GitHubAdapterResult(
                data=None,
                data_source=files_result.data_source,
                stale=files_result.stale,
                fetched_at=files_result.fetched_at,
                expires_at=files_result.expires_at,
                error_code="file_not_found"
            )

        file_diff = parse_file_patch(
            filename=target_file.get("filename", ""),
            patch_text=target_file.get("patch") or "",
            status=target_file.get("status", "modified")
        )

        return GitHubAdapterResult(
            data={
                "pr_number": pr_number,
                "filename": filename,
                "file_diff": file_diff
            },
            data_source=files_result.data_source,
            stale=files_result.stale,
            fetched_at=files_result.fetched_at,
            expires_at=files_result.expires_at,
            error_code=None
        )

    def get_pr_ast_diff(
        self,
        repo: str,
        pr_number: int,
        filename: Optional[str] = None,
        allow_fixture_fallback: bool = False
    ) -> GitHubAdapterResult:
        """Fetch AST symbol changes (classes, functions, methods, MRH headers) for PR files."""
        files_result = self.get_changed_files(
            repo=repo,
            pr_number=pr_number,
            allow_fixture_fallback=allow_fixture_fallback
        )
        if files_result.error_code or not files_result.data:
            return files_result

        files = files_result.data.get("files", [])
        if filename:
            files = [f for f in files if f.get("filename") == filename]

        ast_results = []
        for f in files:
            fname = f.get("filename", "")
            patch = f.get("patch") or ""
            ast_info = analyze_file_ast_diff(
                filename=fname,
                patch_text=patch
            )
            ast_results.append(ast_info)

        return GitHubAdapterResult(
            data={
                "pr_number": pr_number,
                "ast_diffs": ast_results
            },
            data_source=files_result.data_source,
            stale=files_result.stale,
            fetched_at=files_result.fetched_at,
            expires_at=files_result.expires_at,
            error_code=None
        )
