# Remote Git Evidence & Acceptance Verification Checklist

## 1. Quick Verification Commands

```bash
# Check branch existence on remote
git ls-remote origin refs/heads/<branch>

# Check PR head on remote
git ls-remote origin refs/pull/<pr_number>/head

# Trace file commits across all branches
git log --oneline --all -- <file_path>

# Check merge commits in main
git log --oneline origin/main | grep -E "<commit_sha>|<pr_number>"

# Detect duplicate/already-merged PRs (when PR shows dirty/conflicting)
git fetch dnk-mvp main
git log --oneline HEAD..FETCH_HEAD | grep -i "<feature_code>"
```

## 2. Standard Evidence Payload Format

When reporting acceptance or handoff status, always include the full verified provenance block:

```text
Actual Head Commit SHA:  <sha>
Actual Merge Commit SHA: <sha>
Remote repository:       https://github.com/<owner>/<repo>
Feature Branch:          <branch_name>
Target/Base Branch:      main (Base SHA: <base_sha>)
Pull Request:            PR #<pr_number> (https://github.com/<owner>/<repo>/pull/<pr_number>)
PR State:                MERGED
Commit URLs:
  - Branch Commit: https://github.com/<owner>/<repo>/commit/<head_sha>
  - Merge Commit:  https://github.com/<owner>/<repo>/commit/<merge_sha>
Integration Method:      Merge via PR #<pr_number>
Changed Files:
  1. path/to/file1
  2. path/to/file2
```
