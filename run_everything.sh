#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Parse argumentos
SCENARIOS="all"
PARALLEL_MODE="${PARALLEL_MODE:-false}"

for arg in "$@"; do
  case "$arg" in
    --parallel)
      PARALLEL_MODE="true"
      ;;
    *)
      SCENARIOS="$arg"
      ;;
  esac
done

SKIP_COMPLETE_SCENARIO="${SKIP_COMPLETE_SCENARIO:-false}"
SKIP_ACADEMIC="${SKIP_ACADEMIC:-false}"
INCLUDE_V3="${INCLUDE_V3:-true}"
export INCLUDE_V3
export PARALLEL_MODE

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
if [ "$PARALLEL_MODE" = "true" ]; then
  echo ">>> Modo: PARALELO (V1, V2, V3, V4 simultâneos) - ~75% mais rápido"
else
  echo ">>> Modo: SEQUENCIAL (use --parallel para execução paralela)"
fi

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

# 1) Execução de Testes (Cenário Completo e/ou Cenários Críticos)
if [ "$PARALLEL_MODE" = "true" ]; then
  echo "=== Executando TODOS os cenários em PARALELO (V1, V2, V3, V4) ==="
  # Em modo paralelo, o orquestrador cuida de todas as ondas (Completo + Críticos)
  bash ./run_all_tests_parallel.sh "${SCENARIOS}"
else
  # Modo Sequencial Tradicional
  if [ "$SKIP_COMPLETE_SCENARIO" != "true" ]; then
    echo "=== Executando cenário completo SEQUENCIAL (V1, V2, V4) ==="
    bash ./run_all_tests.sh
  fi

  echo "=== Executando cenários críticos SEQUENCIAIS (SCENARIOS=${SCENARIOS}) ==="
  bash ./run_scenario_tests.sh "${SCENARIOS}"
fi

# 2) Análises Python
echo "=== Analisando resultados (Python) ==="
if [ "$SKIP_COMPLETE_SCENARIO" != "true" ] || [ "$PARALLEL_MODE" = "true" ]; then
  echo ">>> Analyzer: Cenário Completo"
  "$PYTHON" analysis/scripts/analyzer.py
fi

echo ">>> Scenario Analyzer: Cenários Críticos"
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
