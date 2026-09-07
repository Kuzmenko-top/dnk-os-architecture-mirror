#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/security/security_audit.sh"
# purpose: "Automated security scan and secret hygiene validation for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -e

echo "🔒 DNK OS Security Audit"
echo "========================"

# 1. Check for hardcoded secrets
echo "Checking for hardcoded secrets..."
LEAKS=$(grep -r -E "password\s*=\s*[\"'][^\"']+[\"']" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null \
  | grep -v ".git" | grep -v "node_modules" | grep -v ".venv" | grep -v "\.next" | grep -v "test" | grep -v "example" \
  | grep -v "spec.secret" | grep -v "password=False" | grep -v "password=None" || true)

if [ -n "$LEAKS" ]; then
    echo "❌ Found hardcoded passwords:"
    echo "$LEAKS"
    exit 1
else
    echo "✅ No hardcoded passwords"
fi

# 2. Check for API keys
echo "Checking for API keys..."
KEY_LEAKS=$(grep -r -E "api_key\s*=\s*[\"'][a-zA-Z0-9_\-]{20,}[\"']" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null \
  | grep -v ".git" | grep -v "node_modules" | grep -v ".venv" | grep -v "\.next" | grep -v "test" | grep -v "example" \
  | grep -v "moa-virtual-provider" | grep -v "inspect-only" | grep -v "aws-sdk" || true)

if [ -n "$KEY_LEAKS" ]; then
    echo "❌ Found hardcoded API keys:"
    echo "$KEY_LEAKS"
    exit 1
else
    echo "✅ No hardcoded API keys"
fi

# 3. Check for SQL injection vulnerabilities
echo "Checking for SQL injection..."
if grep -r "execute.*f\"" --include="*.py" apps/api/routers/ 2>/dev/null | grep -v "test"; then
    echo "⚠️ Potential SQL injection (f-strings in execute)"
else
    echo "✅ No obvious SQL injection in routers"
fi

# 4. Check for XSS vulnerabilities
echo "Checking for XSS..."
if grep -r "innerHTML" --include="*.js" --include="*.ts" apps/web/src/ 2>/dev/null | grep -v ".git" | grep -v "node_modules"; then
    echo "⚠️ Potential XSS (innerHTML usage)"
else
    echo "✅ No obvious XSS in frontend application code"
fi

# 5. Check for path traversal
echo "Checking for path traversal..."
if grep -r "open.*request\." --include="*.py" apps/api/ 2>/dev/null | grep -v ".git"; then
    echo "⚠️ Potential path traversal"
else
    echo "✅ No obvious path traversal"
fi

# 6. Check dependencies for vulnerabilities
echo "Checking dependencies..."
PIPAUDIT="$(which pip-audit || echo "$HOME/.local/bin/pip-audit")"
if [ -x "$PIPAUDIT" ]; then
    "$PIPAUDIT" || echo "⚠️ pip-audit completed with findings"
else
    echo "ℹ️ pip-audit not installed, skipping"
fi

# 7. Check file permissions
echo "Checking file permissions..."
find . -name "*.sh" -not -perm 755 -not -path "*/.git/*" -not -path "*/.venv/*" -not -path "*/node_modules/*" || true
echo "✅ File permissions checked"

# 8. Check for .env in git
echo "Checking for .env in git..."
if git ls-files | grep -E "(^|/)\.env$"; then
    echo "❌ .env file is tracked in git!"
    exit 1
else
    echo "✅ .env not tracked in git"
fi

echo ""
echo "🎉 Security Audit Complete!"
