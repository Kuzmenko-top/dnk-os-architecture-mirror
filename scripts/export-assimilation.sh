#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/export-assimilation.sh"
# purpose: "Clones dnk-os-mvp-assimilation, filters and copies all markdown files from ., and pushes them for mentor review."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

set -e

# Define absolute paths
# Define absolute paths dynamically to prevent host environment hardcoding
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DNK_HUB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)" 
TEMP_DIR=$(mktemp -d -t dnk-assimilation-exportXXXXXX)

echo "📦 Creating temporary workspace at: $TEMP_DIR"

# Clone the repository
git clone https://github.com/Kuzmenko-top/dnk-os-mvp-assimilation.git "$TEMP_DIR/repo"

# Clear existing docs and skills in the repo to handle deletions
rm -rf "$TEMP_DIR/repo/docs" "$TEMP_DIR/repo/skills"

# Recreate folders
mkdir -p "$TEMP_DIR/repo/docs"
mkdir -p "$TEMP_DIR/repo/skills"

# Copy markdown files recursively using rsync
# We include directory structures and all .md files, excluding everything else
rsync -am --include="*/" --include="*.md" --exclude="*" "$DNK_HUB_DIR/docs/" "$TEMP_DIR/repo/docs/"
rsync -am --include="*/" --include="*.md" --exclude="*" "$DNK_HUB_DIR/skills/" "$TEMP_DIR/repo/skills/"

# Go to repo and commit/push changes
cd "$TEMP_DIR/repo"

# Check if there are any changes to commit
if [ -n "$(git status --porcelain)" ]; then
    git add .
    git commit -m "Auto-sync updated specifications and skills standard"
    git push origin main
    echo "✅ Successfully exported and pushed markdown specifications to dnk-os-mvp-assimilation!"
else
    echo "ℹ️ No changes detected. Repository is already up to date."
fi

# Cleanup
rm -rf "$TEMP_DIR"
