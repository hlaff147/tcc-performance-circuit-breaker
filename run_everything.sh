#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

SCENARIOS="${1:-all}"
SKIP_COMPLETE_SCENARIO="${SKIP_COMPLETE_SCENARIO:-false}"
SKIP_ACADEMIC="${SKIP_ACADEMIC:-false}"
INCLUDE_V3="${INCLUDE_V3:-true}"
export INCLUDE_V3

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  else
    echo python
  fi
}

PYTHON="$(python_cmd)"

docker_compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    docker compose "$@"
  fi
}

echo "=== Pipeline completa (tests + cenários + análises + plots) ==="

# Docker precisa estar rodando
if ! docker info >/dev/null 2>&1; then
  echo "Erro: Docker não está rodando." >&2
  exit 1
fi

# Virtualenv
if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
fi

if [ -f ".venv/bin/activate" ]; then
  # linux/mac
  source ".venv/bin/activate"
elif [ -f ".venv/Scripts/activate" ]; then
  # Git Bash (Windows)
  source ".venv/Scripts/activate"
else
  echo "Erro: não achei activate em .venv/bin/activate nem .venv/Scripts/activate" >&2
  exit 1
fi

"$PYTHON" -m pip install -U pip >/dev/null
"$PYTHON" -m pip install -r requirements.txt >/dev/null

# 1) Cenário completo (V1/V2) + análise baseline
if [ "$SKIP_COMPLETE_SCENARIO" != "true" ]; then
  echo "=== Executando cenário completo (V1 e V2) ==="
  bash ./run_all_tests.sh

  echo "=== Analisando cenário completo (analysis/scripts/analyzer.py) ==="
  "$PYTHON" analysis/scripts/analyzer.py
fi

# 2) Cenários críticos + análise por cenário
echo "=== Executando cenários críticos (SCENARIOS=${SCENARIOS}) ==="
bash ./run_scenario_tests.sh "$SCENARIOS"

echo "=== Analisando cenários críticos (analysis/scripts/scenario_analyzer.py) ==="
if [ "$SCENARIOS" = "all" ]; then
  "$PYTHON" analysis/scripts/scenario_analyzer.py
else
  "$PYTHON" analysis/scripts/scenario_analyzer.py "$SCENARIOS"
fi

echo "=== Gerando gráficos consolidados finais (analysis/scripts/generate_final_charts.py) ==="
"$PYTHON" analysis/scripts/generate_final_charts.py

# 3) Estatística + charts acadêmicos
if [ "$SKIP_ACADEMIC" != "true" ]; then
  echo "=== Análise estatística (analysis/scripts/statistical_analysis.py) ==="
  "$PYTHON" analysis/scripts/statistical_analysis.py \
    --data-dir analysis_results \
    --output-dir analysis_results/statistics \
    --validate

  echo "=== Gráficos acadêmicos (analysis/scripts/generate_academic_charts.py) ==="
  "$PYTHON" analysis/scripts/generate_academic_charts.py \
    --data-dir analysis_results \
    --output-dir analysis_results/academic_charts \
    --demo
fi

echo "OK. Artefatos gerados em:"
echo "- analysis_results/analysis_report.html"
echo "- analysis_results/scenarios/*_report.html"
echo "- analysis_results/final_charts/*.png"
echo "- analysis_results/academic_charts/*"
echo "- analysis_results/statistics/*"
