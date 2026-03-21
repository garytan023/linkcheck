#!/bin/bash
set -euo pipefail

SRC="/Users/garytan/.openclaw/workspace-dev"
MIRROR="$HOME/.openclaw/openclaw-text-backup"
BACKUP_SCRIPT="$SRC/skills/openclaw-backup/scripts/backup.sh"
REPO_URL="https://github.com/garytan023/openclaw-text-backup.git"
STAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')

log() {
  echo "[$STAMP] $1"
}

log "Starting weekly OpenClaw backup + GitHub text sync"

# 1) Full local backup
bash "$BACKUP_SCRIPT"

# 2) Prepare mirror repo
mkdir -p "$MIRROR"
cd "$MIRROR"
if [ ! -d .git ]; then
  git init -b main
fi
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

# 3) Clean mirror content but preserve .git
find "$MIRROR" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +

# 4) Copy selected text assets
rsync -a --delete "$SRC/AGENTS.md" "$MIRROR/"
rsync -a --delete "$SRC/SOUL.md" "$MIRROR/"
rsync -a --delete "$SRC/IDENTITY.md" "$MIRROR/"
rsync -a --delete "$SRC/USER.md" "$MIRROR/"
rsync -a --delete "$SRC/HEARTBEAT.md" "$MIRROR/"
rsync -a --delete "$SRC/MEMORY.md" "$MIRROR/"
rsync -a --delete "$SRC/TOOLS.md" "$MIRROR/"
rsync -a --delete \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  "$SRC/memory/" "$MIRROR/memory/"
rsync -a --delete \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  "$SRC/scripts/" "$MIRROR/scripts/"

mkdir -p "$MIRROR/skills"
find "$SRC/skills" -mindepth 1 -maxdepth 1 -type d | while read -r dir; do
  name=$(basename "$dir")
  if [ -d "$dir/.git" ]; then
    echo "Skipping embedded git repo: $name"
    continue
  fi
  rsync -a --delete \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "$dir/" "$MIRROR/skills/$name/"
done

if [ -d "$SRC/docs" ]; then
  rsync -a --delete \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "$SRC/docs/" "$MIRROR/docs/"
fi

cat > "$MIRROR/.gitignore" <<'EOF'
.DS_Store
*.log
*.tar.gz
*.zip
*.sqlite
*.db
*.png
*.jpg
*.jpeg
*.webp
*.gif
*.mp4
*.mov
*.pdf
node_modules/
tmp/
config/
credentials/
telegram/
cron/
completions/
**/__pycache__/
**/*.pyc
**/.env
**/.env.*
**/*token*
**/*secret*
**/*credential*
EOF

# 5) Commit and push only when changed
cd "$MIRROR"
git add .
if git diff --cached --quiet; then
  log "No text-backup changes to commit"
else
  git commit -m "Weekly text backup sync: $(date '+%Y-%m-%d %H:%M')"
  git push origin main
  log "Pushed updated text backup to GitHub"
fi

log "Weekly backup + sync completed"
