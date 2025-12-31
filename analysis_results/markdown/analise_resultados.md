# Análise de Performance: V1 vs V2

Gerado em: 2025-12-21 00:49:08

## Resumo das Métricas

| Version   |   Total Requests |   Avg Response Time (ms) |   P95 Response Time (ms) |   Success Rate (%) |   Fallback Rate (%) |   Circuit Breaker Open Rate (%) |   API Failure Rate (%) |
|:----------|-----------------:|-------------------------:|-------------------------:|-------------------:|--------------------:|--------------------------------:|-----------------------:|
| V1        |            22881 |                  528.045 |                  2769.49 |            90.1665 |              0      |                               0 |                9.83349 |
| V2        |            22701 |                  331.407 |                  2607    |            56.9402 |             36.8926 |                               0 |                6.16713 |
| V3        |            22810 |                  724.751 |                  2796.54 |            90.2543 |              0      |                               0 |                9.74573 |

## Análise Estatística

| Métrica                          | Valor        |
|:---------------------------------|:-------------|
| N (V1)                           | 22547        |
| N (V2)                           | 22640        |
| Média (V1)                       | 528.04 ms    |
| Média (V2)                       | 331.41 ms    |
| Mediana (V1)                     | 34.14 ms     |
| Mediana (V2)                     | 13.05 ms     |
| Desvio Padrão (V1)               | 1003.24 ms   |
| Desvio Padrão (V2)               | 832.55 ms    |
| P95 (V1)                         | 2769.49 ms   |
| P95 (V2)                         | 2607.00 ms   |
| P99 (V1)                         | 2962.39 ms   |
| P99 (V2)                         | 2924.10 ms   |
| Mann-Whitney U                   | 344860132.00 |
| p-valor (MW)                     | 0.00e+00     |
| Kolmogorov-Smirnov               | 0.3217       |
| p-valor (KS)                     | 0.00e+00     |
| Cliff's Delta                    | 0.3480       |
| Interpretação Effect Size        | Médio        |
| IC 95% Diferença (baixo)         | 179.50 ms    |
| IC 95% Diferença (alto)          | 213.51 ms    |
| Diferença Significativa (α=0.05) | Sim          |

## Gráficos Gerados

- `plots/response_times.png`: Tempo de resposta médio e P95
- `plots/success_failure_rate.png`: Composição das respostas
- `plots/timeline_V1.png` / `timeline_V2.png`: Séries temporais por versão
- `plots/timeline_comparison.png`: Comparação temporal V1 vs V2
- `plots/distributions.png`: Análise de distribuições

## Interpretação

### Significância Estatística
- **Mann-Whitney U Test**: Teste não paramétrico para comparar as distribuições
- **Cliff's Delta**: Medida de effect size (magnitude da diferença)
- **Bootstrap CI**: Intervalo de confiança para a diferença de médias

### Thresholds de Cliff's Delta
| Valor |d| | Interpretação |
|---------|---------------|
| < 0.147 | Negligível    |
| < 0.33  | Pequeno       |
| < 0.474 | Médio         |
| ≥ 0.474 | Grande        |
