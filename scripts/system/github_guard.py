#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/github_guard.py"
# purpose: "Safe CLI helper for inspecting GitHub PRs, check-runs, and commit statuses without inline bash quoting traps."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path


def get_github_token() -> str:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        # Try reading from gh cli
        try:
            res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
    return token or ""


def get_repo_slug() -> str:
    try:
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, timeout=5)
        url = res.stdout.strip()
        if "github.com" in url:
            # Handle git@github.com:owner/repo.git or https://github.com/owner/repo.git
            clean = url.replace(".git", "").split("github.com")[-1].lstrip(":/")
            return clean
    except Exception:
        pass
    return "Kuzmenko-top/m-craft.top"


def make_github_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    slug = get_repo_slug()
    url = f"https://api.github.com/repos/{slug}/{endpoint.lstrip('/')}"
    token = get_github_token()

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DNK-OS-GitHubGuard/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"error": f"HTTP {e.code}: {e.reason}", "details": body}
    except Exception as e:
        return {"error": str(e)}


def list_pull_requests(state: str = "open"):
    res = make_github_request(f"pulls?state={state}")
    if isinstance(res, list):
        print(f"📋 Pull Requests (state: {state}, total: {len(res)}):")
        for pr in res:
            print(f"  • PR #{pr.get('number')}: {pr.get('title')} (branch: {pr.get('head', {}).get('ref')}, state: {pr.get('state')})")
    else:
        print("API Response:", json.dumps(res, indent=2))


def check_runs(ref: str = "HEAD"):
    # Resolve ref if HEAD
    if ref == "HEAD":
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        ref = res.stdout.strip()
    
    res = make_github_request(f"commits/{ref}/check-runs")
    if isinstance(res, dict) and "check_runs" in res:
        runs = res["check_runs"]
        print(f"🛡️  Check Runs for commit {ref[:8]} (total: {len(runs)}):")
        for cr in runs:
            print(f"  - {cr.get('name')}: status={cr.get('status')}, conclusion={cr.get('conclusion')}")
    else:
        print("API Response:", json.dumps(res, indent=2))


def main():
    parser = argparse.ArgumentParser(description="DNK OS GitHub Guard CLI")
    parser.add_argument("--prs", choices=["open", "closed", "all"], help="List pull requests by state")
    parser.add_argument("--checks", nargs="?", const="HEAD", help="Get check-runs for commit ref (default: HEAD)")
    parser.add_argument("--slug", action="store_true", help="Print repository slug")

    args = parser.parse_args()

    if args.slug:
        print("Repository:", get_repo_slug())
    elif args.prs:
        list_pull_requests(args.prs)
    elif args.checks:
        check_runs(args.checks)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
