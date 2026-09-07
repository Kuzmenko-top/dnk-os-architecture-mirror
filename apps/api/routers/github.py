# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_github"
# purpose: "Read-only GitHub REST API router exposing PRs, CI checks, and diff file inspection for Cabinet UX."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from apps.api.services.github_adapter import GitHubAdapter
from apps.api.services.github_models import GitHubAdapterResult

router = APIRouter(prefix="/api/github", tags=["github"])
_adapter_instance: GitHubAdapter = GitHubAdapter()
github_adapter: GitHubAdapter = _adapter_instance


def _get_adapter() -> GitHubAdapter:
    """Retrieve active adapter instance (supports test mocking via _adapter_instance)."""
    return _adapter_instance


def _handle_result(res: GitHubAdapterResult) -> GitHubAdapterResult:
    """Check adapter result invariants and raise HTTP exceptions when required."""
    if res.error_code == "forbidden_repo":
        raise HTTPException(status_code=403, detail="Forbidden repository")
    return res


@router.get("/prs/{owner}/{repo_name}", response_model=GitHubAdapterResult)
def list_pull_requests(
    owner: str,
    repo_name: str,
    state: str = Query("all", description="PR state filter: open, closed, all"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """List pull requests for a repository."""
    repo = f"{owner}/{repo_name}"
    res = _get_adapter().list_pull_requests(
        repo=repo,
        state=state,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/pr/{owner}/{repo_name}/{pr_number}", response_model=GitHubAdapterResult)
def get_pull_request(
    owner: str,
    repo_name: str,
    pr_number: int,
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Retrieve details of a single pull request."""
    repo = f"{owner}/{repo_name}"
    res = _get_adapter().get_pull_request(
        repo=repo,
        pr_number=pr_number,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/pr/{owner}/{repo_name}/{pr_number}/checks", response_model=GitHubAdapterResult)
def get_check_runs(
    owner: str,
    repo_name: str,
    pr_number: int,
    ref: Optional[str] = Query(None, description="Commit SHA or branch ref to check"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Retrieve CI/CD check runs for a pull request."""
    repo = f"{owner}/{repo_name}"
    adapter = _get_adapter()
    if not ref:
        pr_result = adapter.get_pull_request(
            repo=repo,
            pr_number=pr_number,
            allow_fixture_fallback=allow_fixture_fallback
        )
        if pr_result.error_code == "forbidden_repo":
            raise HTTPException(status_code=403, detail="Forbidden repository")
        if pr_result.error_code or not pr_result.data:
            if allow_fixture_fallback:
                return _handle_result(adapter.get_check_runs(
                    repo=repo,
                    ref="head",
                    allow_fixture_fallback=True
                ))
            raise HTTPException(
                status_code=404,
                detail=f"PR #{pr_number} not found in {repo}"
            )
        ref = str(pr_result.data.get("head_sha", "main"))

    res = adapter.get_check_runs(
        repo=repo,
        ref=ref,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/prs/{owner}/{repo_name}/{pr_number}/checks", response_model=GitHubAdapterResult)
def get_check_runs_alias(
    owner: str,
    repo_name: str,
    pr_number: int,
    ref: Optional[str] = Query(None, description="Commit SHA or branch ref to check"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Alias for check runs under /prs."""
    return get_check_runs(
        owner=owner,
        repo_name=repo_name,
        pr_number=pr_number,
        ref=ref,
        allow_fixture_fallback=allow_fixture_fallback
    )


@router.get("/pr/{owner}/{repo_name}/{pr_number}/files", response_model=GitHubAdapterResult)
def get_changed_files(
    owner: str,
    repo_name: str,
    pr_number: int,
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Retrieve list of changed files for a pull request."""
    repo = f"{owner}/{repo_name}"
    res = _get_adapter().get_changed_files(
        repo=repo,
        pr_number=pr_number,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/prs/{owner}/{repo_name}/{pr_number}/files", response_model=GitHubAdapterResult)
def get_changed_files_alias(
    owner: str,
    repo_name: str,
    pr_number: int,
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Alias for changed files under /prs."""
    return get_changed_files(
        owner=owner,
        repo_name=repo_name,
        pr_number=pr_number,
        allow_fixture_fallback=allow_fixture_fallback
    )


@router.get("/pr/{owner}/{repo_name}/{pr_number}/diff", response_model=GitHubAdapterResult)
def get_pr_diff(
    owner: str,
    repo_name: str,
    pr_number: int,
    include_chunks: bool = Query(True, description="Whether to include full chunk diffs or just file structure"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Retrieve structured diff tree for a pull request."""
    repo = f"{owner}/{repo_name}"
    res = _get_adapter().get_pr_diff(
        repo=repo,
        pr_number=pr_number,
        include_chunks=include_chunks,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/prs/{owner}/{repo_name}/{pr_number}/diff", response_model=GitHubAdapterResult)
def get_pr_diff_alias(
    owner: str,
    repo_name: str,
    pr_number: int,
    include_chunks: bool = Query(True, description="Whether to include full chunk diffs or just file structure"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Alias for PR diff under /prs."""
    return get_pr_diff(
        owner=owner,
        repo_name=repo_name,
        pr_number=pr_number,
        include_chunks=include_chunks,
        allow_fixture_fallback=allow_fixture_fallback
    )


@router.get("/pr/{owner}/{repo_name}/{pr_number}/diff/file", response_model=GitHubAdapterResult)
def get_pr_file_diff(
    owner: str,
    repo_name: str,
    pr_number: int,
    path: Optional[str] = Query(None, description="Target file path inside the PR repository"),
    filename: Optional[str] = Query(None, description="Alias for target file path"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Retrieve detailed hunk diff for a specific file in a pull request."""
    target_path = path or filename or ""
    repo = f"{owner}/{repo_name}"
    res = _get_adapter().get_pr_file_diff(
        repo=repo,
        pr_number=pr_number,
        filename=target_path,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/prs/{owner}/{repo_name}/{pr_number}/diff/file", response_model=GitHubAdapterResult)
def get_pr_file_diff_alias(
    owner: str,
    repo_name: str,
    pr_number: int,
    path: Optional[str] = Query(None, description="Target file path inside the PR repository"),
    filename: Optional[str] = Query(None, description="Alias for target file path"),
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Alias for PR file diff under /prs."""
    return get_pr_file_diff(
        owner=owner,
        repo_name=repo_name,
        pr_number=pr_number,
        path=path,
        filename=filename,
        allow_fixture_fallback=allow_fixture_fallback
    )


@router.get("/pr/{owner}/{repo_name}/{pr_number}/ast-diff", response_model=GitHubAdapterResult)
def get_pr_ast_diff(
    owner: str,
    repo_name: str,
    pr_number: int,
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Retrieve AST symbol changes (classes, functions, MRH headers) for a pull request."""
    repo = f"{owner}/{repo_name}"
    res = _get_adapter().get_pr_ast_diff(
        repo=repo,
        pr_number=pr_number,
        allow_fixture_fallback=allow_fixture_fallback
    )
    return _handle_result(res)


@router.get("/prs/{owner}/{repo_name}/{pr_number}/ast-diff", response_model=GitHubAdapterResult)
def get_pr_ast_diff_alias(
    owner: str,
    repo_name: str,
    pr_number: int,
    allow_fixture_fallback: bool = Query(False, description="Allow falling back to fixture data if offline or unauthorized")
):
    """Alias for PR AST diff under /prs."""
    return get_pr_ast_diff(
        owner=owner,
        repo_name=repo_name,
        pr_number=pr_number,
        allow_fixture_fallback=allow_fixture_fallback
    )
