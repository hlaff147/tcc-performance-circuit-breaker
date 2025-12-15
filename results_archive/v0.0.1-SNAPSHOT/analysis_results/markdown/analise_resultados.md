# Análise de Performance: V1 vs V2

Gerado em: 2025-11-29 13:33:48

## Resumo das Métricas

| Version   |   Total Requests |   Avg Response Time (ms) |   P95 Response Time (ms) |   Success Rate (%) |   Fallback Rate (%) |   Circuit Breaker Open Rate (%) |   API Failure Rate (%) |
|:----------|-----------------:|-------------------------:|-------------------------:|-------------------:|--------------------:|--------------------------------:|-----------------------:|
| V1        |           381549 |                  612.234 |                  3008.34 |            89.9423 |                   0 |                         0       |               10.0577  |
| V2        |           383071 |                  605.939 |                  3008    |            88.9368 |                   0 |                         1.18281 |                9.88041 |

## Análise Estatística

| Métrica                          | Valor          |
|:---------------------------------|:---------------|
| N (V1)                           | 381549         |
| N (V2)                           | 383071         |
| Média (V1)                       | 612.23 ms      |
| Média (V2)                       | 605.94 ms      |
| Mediana (V1)                     | 4.38 ms        |
| Mediana (V2)                     | 4.26 ms        |
| Desvio Padrão (V1)               | 1201.49 ms     |
| Desvio Padrão (V2)               | 1197.94 ms     |
| P95 (V1)                         | 3008.34 ms     |
| P95 (V2)                         | 3008.00 ms     |
| P99 (V1)                         | 3036.34 ms     |
| P99 (V2)                         | 3030.40 ms     |
| Mann-Whitney U                   | 74211797463.50 |
| p-valor (MW)                     | 9.37e-32       |
| Kolmogorov-Smirnov               | 0.0160         |
| p-valor (KS)                     | 5.37e-43       |
| Cliff's Delta                    | 0.0155         |
| Interpretação Effect Size        | Negligível     |
| IC 95% Diferença (baixo)         | 1.07 ms        |
| IC 95% Diferença (alto)          | 11.77 ms       |
| Diferença Significativa (α=0.05) | Sim            |

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
