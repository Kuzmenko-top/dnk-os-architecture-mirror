# GitHub Diff Closeout Verification Guidelines

When performing a security closeout review:

1. **Exact Pattern SSOT**:
   Ensure GitHub classic PAT pattern strictly enforces the literal delimiter:
   `\bgh[pousr]_[A-Za-z0-9_]{20,}\b`

2. **Negative Boundary Validation**:
   - `ghpABCDEFGHIJKLMNOPQRSTUVWXYZ123456` -> Negative (0 matches, missing delimiter `_`)
   - `ghp-example-placeholder` -> Negative (wrong delimiter `-`)
   - `ghp_` -> Negative (below minimum length 20)
   - `xghp_...` -> Negative (word boundary violation)

3. **Required Closeout Outputs**:
   - Pull Request URL
   - Head Commit SHA
   - GitHub file diff links
   - CI Workflow status / runs
   - Non-sensitive JSON evidence
