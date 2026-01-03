#!/usr/bin/env bash
# Script para executar apenas a pipeline de análise de dados, estatísticas e gráficos.
# Útil quando os testes já foram rodados e você quer apenas atualizar os relatórios.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  else
    echo python
  fi
}

PYTHON="$(python_cmd)"

echo "=== Pipeline de Análise Dedicada (V1, V2, V3, V4) ==="

# 1) Virtualenv
if [ ! -d ".venv" ]; then
  echo "Ambiente virtual não encontrado. Criando..."
  "$PYTHON" -m venv .venv
fi

if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
elif [ -f ".venv/Scripts/activate" ]; then
  source ".venv/Scripts/activate"
else
  echo "Erro: não achei activate em .venv/bin/activate nem .venv/Scripts/activate" >&2
  exit 1
fi

echo "Verificando dependências..."
"$PYTHON" -m pip install -U pip >/dev/null
"$PYTHON" -m pip install -r requirements.txt >/dev/null

# 2) Execução dos Analisadores Python
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  INICIANDO ANALISE DE DADOS E GERAÇÃO DE GRÁFICOS                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo ">>> 1. Analyzer: Cenário Completo"
"$PYTHON" analysis/scripts/analyzer.py

echo ">>> 2. Scenario Analyzer: Cenários Críticos"
"$PYTHON" analysis/scripts/scenario_analyzer.py

echo ">>> 3. Final Charts: Gráficos Consolidados (V1-V4) - EN"
"$PYTHON" analysis/scripts/generate_final_charts.py --lang en

echo ">>> 3b. Final Charts: Gráficos Consolidados (V1-V4) - PT"
"$PYTHON" analysis/scripts/generate_final_charts.py --lang pt

echo ">>> 4. Statistical Analysis: Testes de Hipótese (ANOVA/Mann-Whitney)"
"$PYTHON" analysis/scripts/statistical_analysis.py

echo ">>> 5. Academic Charts: Gráficos para Publicação"
"$PYTHON" analysis/scripts/generate_academic_charts.py

echo ""
echo "✅ Todos os artefatos de análise foram gerados em 'analysis_results/'"
echo ""
echo "Relatórios principais:"
echo "- analysis_results/analysis_report.html (Cenário Completo)"
echo "- analysis_results/scenarios/*_report.html (Cenários Críticos)"
echo "- analysis_results/final_charts/ (Gráficos Consolidados)"
echo "- analysis_results/statistics/statistical_summary.md (Estatísticas)"
echo "- analysis_results/academic_charts/ (Gráficos Formato IEEE)"
echo ""
