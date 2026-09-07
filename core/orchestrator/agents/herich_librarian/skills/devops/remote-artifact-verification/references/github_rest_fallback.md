# GitHub REST API Fallback for Remote PR & Merge Verification

When `gh` CLI or GraphQL tools fail due to missing scope privileges (e.g. `read:org`, `read:discussion` missing on a standard repo-scoped PAT), use the direct GitHub REST API using Python.

## Token Extraction Pattern

Extract the token from git remote or fall back to environment variables (`GH_TOKEN` / `GITHUB_TOKEN`):

```python
import urllib.parse, urllib.request, subprocess, json, os

url = subprocess.check_output(['git', 'remote', 'get-url', 'dnk-mvp']).decode().strip()
token = ''
if '@' in url:
    auth = url.split('://')[1].split('@')[0]
    token = auth.split(':')[1] if ':' in auth else auth

if not token:
    token = os.environ.get('GH_TOKEN', os.environ.get('GITHUB_TOKEN', ''))
```

## 1. Create PR via REST API

When `gh pr create` fails due to unauthenticated CLI or MCP subprocess timeout, create the PR directly:

```python
payload = json.dumps({
    'title': 'feat(scope): <title>',
    'head': '<branch-name>',
    'base': 'main',
    'body': '## Summary\n...\n## Verification\n...'
}).encode('utf-8')

req = urllib.request.Request(
    'https://api.github.com/repos/<owner>/<repo>/pulls',
    data=payload,
    headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Gerych-Bot'
    },
    method='POST'
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print("Created PR #" + str(data.get("number")) + " (" + data.get("html_url") + ")")
```

## 2. Query PR Details via REST API

```python
req = urllib.request.Request(
    'https://api.github.com/repos/<owner>/<repo>/pulls/<pr_number>',
    headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Gerych-Bot'
    }
)
with urllib.request.urlopen(req) as resp:
    pr_data = json.loads(resp.read().decode())
    print("State:", pr_data.get("state"), "Merged:", pr_data.get("merged"))
```

## 2. Execute PR Merge via REST API

```python
payload = json.dumps({
    'commit_title': 'Merge PR #<pr_number>: <title>',
    'merge_method': 'squash'  # 'squash', 'merge', or 'rebase'
}).encode('utf-8')

req = urllib.request.Request(
    'https://api.github.com/repos/<owner>/<repo>/pulls/<pr_number>/merge',
    data=payload,
    headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Gerych-Bot'
    },
    method='PUT'
)
with urllib.request.urlopen(req) as resp:
    print("Merge Output:", json.loads(resp.read().decode()))
```

## 3. Post-Merge Local Main Reset (Submodules & Dual Remotes)

After merging a PR on GitHub, local `main` may have unpushed commits that cause rebase conflicts during `git pull`. Reset `main` cleanly to the remote branch:

```bash
# 1. Reset root main to merged remote state
git checkout main
git fetch dnk-mvp
git reset --hard dnk-mvp/main

# 2. Reset submodules if present (e.g., DNK OS)
cd .
git checkout main
git fetch origin
git reset --hard origin/main
cd ..

# 3. Verify Quality Gate
bash scripts/verify_all.sh
```
