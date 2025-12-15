#!/usr/bin/env zsh
# Script seguro para remover do índice do Git arquivos/pastas grandes
# Mantém os arquivos localmente (não apaga do disco) e comita a atualização do .gitignore

set -euo pipefail

echo "This script will:"
echo " - stop tracking k6/results, .venv and docs/diagramas/plantuml.jar (if tracked)"
echo " - add .gitignore and commit the changes"
echo "Files will stay on disk. Run from repository root."

# Paths to untrack (modify if you want different targets)
TARGETS=("k6/results" ".venv" "docs/diagramas/plantuml.jar")

for path in "${TARGETS[@]}"; do
  if git ls-files --error-unmatch "$path" > /dev/null 2>&1; then
    echo "Untracking: $path"
    git rm -r --cached "$path" || true
  else
    echo "Not tracked (skipping): $path"
  fi
done

echo "Adding .gitignore"
git add .gitignore || true

if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  git commit -m "Stop tracking large artifacts: k6 results, venv, plantuml.jar"
fi

echo
echo "Done. Current git status:" 
git status --porcelain

echo
echo "If you need to remove large files from the remote history, see instructions in the repository or ask me to prepare 'git filter-repo' steps." 
