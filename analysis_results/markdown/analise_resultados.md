# Análise de Performance: V1 vs V2

Gerado em: 2025-12-06 19:57:17

## Resumo das Métricas

| Version   |   Total Requests |   Avg Response Time (ms) |   P95 Response Time (ms) |   Success Rate (%) |   Fallback Rate (%) |   Circuit Breaker Open Rate (%) |   API Failure Rate (%) |
|:----------|-----------------:|-------------------------:|-------------------------:|-------------------:|--------------------:|--------------------------------:|-----------------------:|
| V1        |           353639 |                  735.045 |                  2975.17 |            90.0447 |              0      |                               0 |                9.95535 |
| V2        |           415927 |                  477.602 |                  2745.21 |            77.7095 |             22.2905 |                               0 |                0       |

## Análise Estatística

| Métrica                          | Valor           |
|:---------------------------------|:----------------|
| N (V1)                           | 353639          |
| N (V2)                           | 415927          |
| Média (V1)                       | 735.05 ms       |
| Média (V2)                       | 477.60 ms       |
| Mediana (V1)                     | 160.56 ms       |
| Mediana (V2)                     | 35.69 ms        |
| Desvio Padrão (V1)               | 1085.40 ms      |
| Desvio Padrão (V2)               | 952.68 ms       |
| P95 (V1)                         | 2975.17 ms      |
| P95 (V2)                         | 2745.21 ms      |
| P99 (V1)                         | 3613.63 ms      |
| P99 (V2)                         | 2977.47 ms      |
| Mann-Whitney U                   | 101610477156.50 |
| p-valor (MW)                     | 0.00e+00        |
| Kolmogorov-Smirnov               | 0.3490          |
| p-valor (KS)                     | 0.00e+00        |
| Cliff's Delta                    | 0.3816          |
| Interpretação Effect Size        | Médio           |
| IC 95% Diferença (baixo)         | 252.84 ms       |
| IC 95% Diferença (alto)          | 262.03 ms       |
| Diferença Significativa (α=0.05) | Sim             |

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
