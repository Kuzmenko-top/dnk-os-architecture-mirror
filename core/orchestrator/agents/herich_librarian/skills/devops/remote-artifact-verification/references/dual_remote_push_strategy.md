# Dual Remote Push & Sync Strategy

When a workspace maintains multiple git remotes (e.g. `dnk-mvp` for the upstream repository and `origin` for secondary/backup repository), ensure both remotes receive the feature branch and commits.

## Push Command Pattern

```bash
# Push feature branch to primary and secondary remotes
git push -u dnk-mvp <branch-name> && git push -u origin <branch-name>
```

## Verification Checklist

1. Confirm both remotes are configured in git:
   ```bash
   git remote -v
   ```
2. Verify branch head on both remotes after push:
   ```bash
   git ls-remote dnk-mvp refs/heads/<branch-name>
   git ls-remote origin refs/heads/<branch-name>
   ```
