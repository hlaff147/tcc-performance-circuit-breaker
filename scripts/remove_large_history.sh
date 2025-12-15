#!/usr/bin/env bash
# Safe helper to remove large/generated files from Git history using git-filter-repo
# This script DOES NOT push changes to any remote. It creates a mirror backup, runs
# the rewrite on the mirror, and prints verification/push steps for you to run.

set -euo pipefail

# Ensure standard system paths are available when the script runs from constrained environments
export PATH="/bin:/usr/bin:/usr/local/bin:${PATH:-}"

REPO_DIR=$(pwd)
TIMESTAMP=$(/bin/date +%Y%m%d_%H%M%S)
MIRROR_DIR="${REPO_DIR}-mirror-${TIMESTAMP}.git"

echo "Will create a mirror backup and rewrite history in: ${MIRROR_DIR}"
echo "Files/paths that will be removed from history:"
echo " - k6/results/"
echo " - docs/diagramas/plantuml.jar"
echo " - .venv/"

read -p "Proceed? (type YES to continue): " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
  echo "Aborting."; exit 1
fi

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo is not installed. Install it first (example):"
  echo "  brew install git-filter-repo    # macOS (Homebrew)"
  echo "  or pip install git-filter-repo"
  exit 1
fi

echo "Creating a mirrored clone (safe backup)..."
git clone --mirror "$REPO_DIR" "$MIRROR_DIR"

echo "Running git-filter-repo on mirror (removing specified paths)..."
cd "$MIRROR_DIR"

# Remove the listed paths from all history
git filter-repo \
  --invert-paths \
  --path k6/results \
  --path docs/diagramas/plantuml.jar \
  --path .venv || true

echo
echo "Rewrite finished. Inspect the mirror repository at: ${MIRROR_DIR}"
echo
echo "VERIFYING (recommended):"
echo " - cd ${MIRROR_DIR} && git log --stat | less" 
echo " - grep for removed paths: git rev-list --objects --all | grep 'k6/results\|plantuml.jar\|.venv'"
echo
echo "If everything looks good, you can push the rewritten mirror to origin (FORCE PUSH)."
echo "WARNING: This rewrites remote history. All collaborators must re-clone after this."
echo
echo "Example push commands (run only after you verified the mirror):"
echo "  cd ${MIRROR_DIR}"
echo "  git remote add origin <URL-OF-REMOTE>   # if not already set"
echo "  git push --force --all origin"
echo "  git push --force --tags origin"

echo
echo "Alternative (safer) workflow:"
echo " - Create a new clean clone from the mirror and switch your working copy to it," 
echo "   or coordinate with teammates to avoid mid-push conflicts."

echo
echo "Done. Keep your original repository directory untouched at: ${REPO_DIR}"
