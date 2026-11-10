#!/bin/bash
#
# manage-agent-branches.sh
# Real automation script for Sovereign agent workspaces
# ara-hardened | claude | gpt | copilot
#
# This script is meant to be run locally by the owner.
# It creates missing agent branches and ensures proper README headers.

set -e

REPO="Sovereignty-One/SuperGrok-Heavy-4-2-Skeleton"
AGENT_BRANCHES=("ara-hardened" "claude" "gpt" "copilot")

create_clean_claude_branch() {
    if git show-ref --verify --quiet refs/heads/claude; then
        echo "[INFO] clean 'claude' branch already exists"
        return
    fi

    echo "[CREATE] Creating clean 'claude' branch from main..."
    git checkout main
    git pull origin main
    git checkout -b claude

    # Add clean README header
    cat > README.md << 'EOF'
# @claude — Claude's Workspace

This is Claude's dedicated branch.
All changes made by Claude must be done here.

Do not push directly to main. Create a Pull Request for review.
EOF

    git add README.md
    git commit -m "Initialize clean claude workspace with ownership header"
    git push origin claude
    echo "[DONE] Clean 'claude' branch created and pushed."
}

ensure_agent_headers() {
    echo "[INFO] Ensuring agent headers on all branches..."
    for branch in "${AGENT_BRANCHES[@]}"; do
        if git show-ref --verify --quiet refs/remotes/origin/$branch; then
            echo "[CHECK] $branch exists on remote"
        else
            echo "[MISSING] $branch does not exist on remote"
        fi
    done
}

show_status() {
    echo "=== Current Agent Branches ==="
    git branch -a | grep -E 'ara-hardened|claude|gpt|copilot' || echo "No agent branches found"
}

case "$1" in
    create)
        create_clean_claude_branch
        ;;
    status)
        show_status
        ;;
    update)
        ensure_agent_headers
        ;;
    *)
        echo "Usage: $0 {create|status|update}"
        echo "  create  - Create missing clean agent branches (especially claude)"
        echo "  status  - Show current agent branch status"
        echo "  update  - Check header status on agent branches"
        exit 1
        ;;
esac
