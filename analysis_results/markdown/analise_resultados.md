# Análise de Performance: V1 vs V2

Gerado em: 2026-01-03 02:30:19

## Resumo das Métricas

| Version   |   Total Requests |   Avg Response Time (ms) |   P95 Response Time (ms) |   Success Rate (%) |   Fallback Rate (%) |   Circuit Breaker Open Rate (%) |   API Failure Rate (%) |
|:----------|-----------------:|-------------------------:|-------------------------:|-------------------:|--------------------:|--------------------------------:|-----------------------:|
| V1        |            22859 |                 1281.44  |                  3943.94 |            89.6846 |              0      |                               0 |               10.3154  |
| V2        |            22584 |                  437.673 |                  2595.53 |            24.1764 |             73.1668 |                               0 |                2.65675 |
| V3        |            22726 |                 1984.69  |                  5384.44 |            89.743  |              0      |                               0 |               10.257   |
| V4        |            22933 |                  472.391 |                  2678.4  |            27.0135 |             69.908  |                               0 |                3.07853 |

## Análise Estatística

| Métrica                          | Valor        |
|:---------------------------------|:-------------|
| N (V1)                           | 22801        |
| N (V2)                           | 22754        |
| Média (V1)                       | 1281.44 ms   |
| Média (V2)                       | 437.67 ms    |
| Mediana (V1)                     | 784.79 ms    |
| Mediana (V2)                     | 87.02 ms     |
| Desvio Padrão (V1)               | 1330.71 ms   |
| Desvio Padrão (V2)               | 873.04 ms    |
| P95 (V1)                         | 3943.94 ms   |
| P95 (V2)                         | 2595.53 ms   |
| P99 (V1)                         | 5115.88 ms   |
| P99 (V2)                         | 4187.69 ms   |
| Mann-Whitney U                   | 388802098.00 |
| p-valor (MW)                     | 0.00e+00     |
| Kolmogorov-Smirnov               | 0.4360       |
| p-valor (KS)                     | 0.00e+00     |
| Cliff's Delta                    | 0.5002       |
| Interpretação Effect Size        | Grande       |
| IC 95% Diferença (baixo)         | 823.42 ms    |
| IC 95% Diferença (alto)          | 863.95 ms    |
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
