# Análise de Performance: V1 vs V2

Gerado em: 2025-12-19 21:17:27

## Resumo das Métricas

| Version   |   Total Requests |   Avg Response Time (ms) |   P95 Response Time (ms) |   Success Rate (%) |   Fallback Rate (%) |   Circuit Breaker Open Rate (%) |   API Failure Rate (%) |
|:----------|-----------------:|-------------------------:|-------------------------:|-------------------:|--------------------:|--------------------------------:|-----------------------:|
| V1        |            22650 |                  529.607 |                  2768.63 |            90.2252 |              0      |                               0 |                9.77483 |
| V2        |            22470 |                  174.864 |                  2226.31 |            28.9987 |             71.0013 |                               0 |                0       |
| V3        |            22628 |                  724.61  |                  2820.78 |            89.9593 |              0      |                               0 |               10.0407  |

## Análise Estatística

| Métrica                          | Valor        |
|:---------------------------------|:-------------|
| N (V1)                           | 22657        |
| N (V2)                           | 22881        |
| Média (V1)                       | 529.61 ms    |
| Média (V2)                       | 174.86 ms    |
| Mediana (V1)                     | 38.14 ms     |
| Mediana (V2)                     | 3.25 ms      |
| Desvio Padrão (V1)               | 997.39 ms    |
| Desvio Padrão (V2)               | 616.42 ms    |
| P95 (V1)                         | 2768.63 ms   |
| P95 (V2)                         | 2226.31 ms   |
| P99 (V1)                         | 2971.71 ms   |
| P99 (V2)                         | 2874.19 ms   |
| Mann-Whitney U                   | 413180104.00 |
| p-valor (MW)                     | 0.00e+00     |
| Kolmogorov-Smirnov               | 0.5153       |
| p-valor (KS)                     | 0.00e+00     |
| Cliff's Delta                    | 0.5940       |
| Interpretação Effect Size        | Grande       |
| IC 95% Diferença (baixo)         | 339.74 ms    |
| IC 95% Diferença (alto)          | 370.12 ms    |
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
