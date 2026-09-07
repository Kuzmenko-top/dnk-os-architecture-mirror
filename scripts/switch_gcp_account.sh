#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/switch_gcp_account.sh"
# purpose: "Canonical SSOT switcher for Google Cloud Account, Project ID and Vertex AI Gemini 3.x tokens."
# canonical_source: true
# alters_files: [".dnk_active_project.env", "~/.hermes/.env", "~/.hermes/vertex_token.txt"]
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

NEW_ACCOUNT="${1:-}"
NEW_PROJECT="${2:-}"
NEW_REGION="${3:-global}"

if [ -z "$NEW_ACCOUNT" ]; then
    NEW_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
fi

if [ -z "$NEW_PROJECT" ]; then
    NEW_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
fi

if [ -z "$NEW_ACCOUNT" ] || [ -z "$NEW_PROJECT" ]; then
    echo "❌ Помилка: Вкажіть account та project_id."
    echo "Використання: ./scripts/switch_gcp_account.sh <ACCOUNT_EMAIL> <PROJECT_ID> [REGION]"
    echo "Приклад: ./scripts/switch_gcp_account.sh tech.valleriy@gmail.com project-930a8ed3-3e40-4f43-9d4 global"
    exit 1
fi

echo "========================================================"
echo "🔄 [DNK OS] Ротація Google Cloud / Vertex AI акаунта"
echo "📧 Акаунт:    $NEW_ACCOUNT"
echo "🆔 Проект:     $NEW_PROJECT"
echo "🌍 Регіон:     $NEW_REGION"
echo "========================================================"

# 1. GCloud CLI Context
gcloud config set account "$NEW_ACCOUNT" 2>/dev/null || true
gcloud config set project "$NEW_PROJECT" 2>/dev/null || true

# 2. Update .dnk_active_project.env in HUB root and ~/.hermes
ENV_FILE="$HUB_ROOT/.dnk_active_project.env"
HERMES_DIR="$HOME/.hermes"
mkdir -p "$HERMES_DIR"

cat <<EOF > "$ENV_FILE"
# DNK OS SSOT GCP Configuration
GCP_ACTIVE_ACCOUNT="$NEW_ACCOUNT"
GOOGLE_CLOUD_PROJECT="$NEW_PROJECT"
VERTEX_PROJECT_ID="$NEW_PROJECT"
VERTEX_REGION="$NEW_REGION"
VERTEX_BASE_URL="https://aiplatform.googleapis.com/v1/projects/${NEW_PROJECT}/locations/${NEW_REGION}/publishers/google"
EOF

cp "$ENV_FILE" "$HERMES_DIR/.env"
echo "✅ Оновлено конфігурації в .dnk_active_project.env та ~/.hermes/.env"

PY_BIN="$HUB_ROOT/.venv/bin/python3"
if [ ! -f "$PY_BIN" ]; then
    PY_BIN="python3"
fi

# 3. Synchronize base_url, vertex.project_id across config files and auth.json
"$PY_BIN" -c "
import re
from pathlib import Path

configs = [
    Path('$HERMES_DIR/config.yaml'),
    Path('$HUB_ROOT/core/orchestrator/agents/gerych_prime/config.yaml'),
    Path('$HUB_ROOT/core/orchestrator/agents/herich_librarian/config.yaml')
]

for p in Path('$HUB_ROOT/core/orchestrator/agents').glob('*/config.yaml'):
    if p not in configs:
        configs.append(p)

pattern = re.compile(r'https://aiplatform\.googleapis\.com/v1/projects/[^/]+/locations/[^/]+/publishers/google')
target = 'https://aiplatform.googleapis.com/v1/projects/$NEW_PROJECT/locations/$NEW_REGION/publishers/google'
proj_pattern = re.compile(r'(vertex:\s*\n(?:\s*#[^\n]*\n)*\s*project_id:\s*)[^\s\n]+')

for cfg in configs:
    if cfg.exists():
        content = cfg.read_text(encoding='utf-8')
        new_content = pattern.sub(target, content)
        new_content = proj_pattern.sub(r'\g<1>$NEW_PROJECT', new_content)
        if new_content != content:
            cfg.write_text(new_content, encoding='utf-8')
            print(f'✅ Оновлено Vertex project_id & base_url у {cfg.name}')

auth_file = Path('$HERMES_DIR/auth.json')
if auth_file.exists():
    auth_content = auth_file.read_text(encoding='utf-8')
    auth_new = pattern.sub(target, auth_content)
    if auth_new != auth_content:
        auth_file.write_text(auth_new, encoding='utf-8')
        print('✅ Оновлено Vertex base_url у ~/.hermes/auth.json')

hub_env = Path('$HUB_ROOT/.env')
if hub_env.exists():
    env_content = hub_env.read_text(encoding='utf-8')
    replacements = {
        'GCP_ACTIVE_ACCOUNT': '$NEW_ACCOUNT',
        'GOOGLE_CLOUD_PROJECT': '$NEW_PROJECT',
        'GOOGLE_CLOUD_PROJECT_ID': '$NEW_PROJECT',
        'VERTEX_PROJECT_ID': '$NEW_PROJECT',
        'VERTEX_REGION': '$NEW_REGION',
        'VERTEX_BASE_URL': target,
    }
    for k, v in replacements.items():
        if re.search(rf'^{k}=.*$', env_content, flags=re.MULTILINE):
            env_content = re.sub(rf'^{k}=.*$', f'{k}=\"{v}\"', env_content, flags=re.MULTILINE)
        else:
            env_content += f'\n{k}=\"{v}\"'
    hub_env.write_text(env_content, encoding='utf-8')
    print('✅ Оновлено конфігурації у DNK_HUB/.env')
"

# 4. Check and update Application Default Credentials quota project
ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"
if [ -f "$ADC_FILE" ]; then
    "$PY_BIN" -c "
import json
p = '$ADC_FILE'
try:
    with open(p, 'r') as f:
        d = json.load(f)
    d['quota_project_id'] = '$NEW_PROJECT'
    with open(p, 'w') as f:
        json.dump(d, f, indent=2)
    print('✅ Оновлено quota_project_id в Application Default Credentials')
except Exception as e:
    pass
" || true
fi

# 4. Generate fresh OAuth2 token strictly for NEW_ACCOUNT
TOKEN=""
if command -v gcloud &>/dev/null; then
    TOKEN=$(gcloud auth print-access-token "$NEW_ACCOUNT" 2>/dev/null || true)
fi

if [ -n "$TOKEN" ] && [[ "$TOKEN" == ya29.* ]]; then
    echo "$TOKEN" > "$HERMES_DIR/vertex_token.txt"
    echo "⚡ Успішно отримано та збережено OAuth2 токен для $NEW_ACCOUNT (${TOKEN:0:10}...${TOKEN: -5})"
    
    # 5. Enable Vertex AI API if not enabled
    echo "🔧 Перевірка та активація Vertex AI API на проекті $NEW_PROJECT..."
    gcloud services enable aiplatform.googleapis.com --project="$NEW_PROJECT" 2>/dev/null || true
    
    echo "✅ [SSOT Switcher] Успішно налаштовано! Проект $NEW_PROJECT готовий до роботи з Gemini 3.x"
else
    echo "⚠️  Увага: Токен для $NEW_ACCOUNT ще НЕ авторизований у gcloud CLI на цьому Mac."
    echo "👉 Будь ласка, виконайте у терміналі:"
    echo "   gcloud auth login $NEW_ACCOUNT"
    echo "   gcloud auth application-default login"
    exit 1
fi
