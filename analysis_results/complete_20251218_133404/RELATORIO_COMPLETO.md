# 📊 Relatório Completo de Análise - TCC Circuit Breaker

**Data:** 2025-12-18 14:01:14
**Modo:** Completo

## Resumo da Execução

| Componente | Status |
|------------|--------|
| Comparação de Perfis CB | ✅ |
| Comparação V1 vs V2 vs V3 | ✅ |
| Análise Estatística | ✅ |
| Visualizações | ✅ |

## Arquivos Gerados

### Dados Brutos
- `k6/results/scenarios/*.json`

### Análises
- `analysis_results/complete_20251218_133404/statistics/` - Testes estatísticos
- `analysis_results/complete_20251218_133404/plots/` - Gráficos acadêmicos

## Como Usar os Resultados

### Para o TCC
1. Use os CSVs em `analysis_results/` para tabelas
2. Use os gráficos em `analysis_results/complete_20251218_133404/plots/` (300 DPI)
3. Consulte `ANALISE_FINAL_TCC.md` para interpretação

### Reexecutar Análises
```bash
source .venv/bin/activate
python analysis/scripts/statistical_analysis.py --validate
python analysis/scripts/generate_academic_charts.py --demo
```

---
Gerado automaticamente por run_complete_analysis.sh
