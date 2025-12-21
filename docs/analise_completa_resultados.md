# 🎓 Análise Completa dos Resultados - TCC Performance Circuit Breaker

> **Autor:** Humberto L. A. Fonseca Filho  
> **Data:** 20 de Dezembro de 2024  
> **Versão:** 2.0

---

## 📋 Sumário Executivo

Este documento apresenta a análise completa dos resultados dos testes de carga realizados para o Trabalho de Conclusão de Curso (TCC) sobre **Padrões de Resiliência em Arquiteturas de Microsserviços**, focando especificamente no padrão **Circuit Breaker**.

### Versões Testadas

| Versão | Descrição | Padrão de Resiliência |
|--------|-----------|----------------------|
| **V1** | Baseline (sem resiliência) | Nenhum |
| **V2** | Circuit Breaker | Resilience4j com fallback |
| **V3** | Retry com Backoff | Resilience4j Retry |

### Principais Descobertas

| Métrica | V1 | V2 | V3 |
|---------|:--:|:--:|:--:|
| **Disponibilidade** | 89.98% | **100%** | 89.99% |
| **Taxa de Fallback** | 0% | 71.04% | 0% |
| **Taxa de Falha** | 10.03% | **0%** | 10.00% |
| **Tempo Médio (ms)** | 534.3 | **178.5** | 722.4 |
| **P95 (ms)** | 2,771 | **2,245** | 2,808 |
| **Throughput (req/s)** | 222.5 | **289.2** | 198.0 |

---

## 🔬 Metodologia de Teste

### Infraestrutura

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                            │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │   k6 Load    │───▶│ servico-pagamento │───▶│ servico-  │  │
│  │   Tester     │    │   (V1/V2/V3)      │    │ adquirente│  │
│  └──────────────┘    └──────────────────┘    └───────────┘  │
│                              │                               │
│                      ┌───────┴───────┐                      │
│                      ▼               ▼                      │
│              ┌──────────────┐ ┌────────────┐               │
│              │  Prometheus  │ │  Grafana   │               │
│              └──────────────┘ └────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Parâmetros do Teste

| Parâmetro | Valor |
|-----------|-------|
| **Duração** | 30 minutos |
| **VUs Máximo** | 500 (ramp-up gradual) |
| **Distribuição de Modos** | normal:70%, latência:20%, falha:10% |
| **Recursos do Container** | 1 CPU, 1GB RAM |

### Comportamento do Adquirente

- **Modo Normal (70%):** Resposta imediata com HTTP 200
- **Modo Latência (20%):** Delay de 500-2500ms + HTTP 200
- **Modo Falha (10%):** Resposta imediata com HTTP 500

---

## 📊 Resultados Detalhados

### Cenário Completo (30 minutos, 500 VUs)

#### V1 - Baseline (Sem Resiliência)

```
Total de Requisições: 400,647
Taxa de Sucesso:      89.97% (360,447 req)
Taxa de Falha:        10.03% (40,200 req)
Tempo Médio:          534.34 ms
Mediana:              38.16 ms
P95:                  2,771.10 ms
P99:                  2,971.71 ms
Throughput:           222.45 req/s
```

**Observações:**
- Sem mecanismo de proteção, cada falha do adquirente propaga diretamente
- Tempo médio alto devido às requisições que aguardam timeout
- ~10% das requisições resultam em erro 500 para o cliente

#### V2 - Circuit Breaker (Resilience4j)

```
Total de Requisições: 521,209
Taxa de Sucesso:      28.96% (150,939 req)
Taxa de Fallback:     71.04% (370,270 req)
Taxa de Falha:        0% (0 req)
Tempo Médio:          178.54 ms
Mediana:              3.32 ms
P95:                  2,245.05 ms
P99:                  2,874.19 ms
Throughput:           289.22 req/s
```

**Observações:**
- **100% de disponibilidade** - nenhuma requisição falhou
- Circuit Breaker ativa fallback rapidamente (5.76ms em média)
- Throughput 30% maior que V1 devido à liberação rápida de threads
- Tempo médio 67% menor que V1

#### V3 - Retry com Backoff Exponencial

```
Total de Requisições: 356,979
Taxa de Sucesso:      89.99% (321,277 req)
Taxa de Fallback:     0%
Taxa de Falha:        10.00% (35,702 req)
Tempo Médio:          722.35 ms
Mediana:              84.24 ms
P95:                  2,808.06 ms
P99:                  3,127.89 ms
Throughput:           198.04 req/s
```

**Observações:**
- Mesma taxa de sucesso que V1 (~90%)
- Tempo médio 35% maior que V1 devido às retentativas
- Retries consomem recursos mas não melhoram disponibilidade neste cenário
- Throughput menor que V1 e V2

---

## 📈 Análise Estatística

### Teste de Significância (V1 vs V2)

| Teste | Estatística | p-valor | Conclusão |
|-------|:-----------:|:-------:|-----------|
| **Mann-Whitney U** | 413,180,104 | < 0.001 | Diferença significativa |
| **Kolmogorov-Smirnov** | 0.5153 | < 0.001 | Distribuições diferentes |

### Effect Size

| Métrica | Valor | Interpretação |
|---------|:-----:|---------------|
| **Cliff's Delta** | 0.594 | **Grande** |
| **IC Bootstrap 95%** | [339.74, 370.12] ms | Melhoria consistente |

> **Cliff's Delta Thresholds:**
> - |d| < 0.147: Negligível
> - |d| < 0.33: Pequeno
> - |d| < 0.474: Médio
> - |d| ≥ 0.474: **Grande**

### Interpretação

A diferença entre V1 e V2 é **estatisticamente significativa** (p < 0.001) e o **effect size é grande** (δ = 0.594), indicando que o Circuit Breaker produz uma melhoria substancial e não trivial na performance do sistema.

---

## 🎯 Análise por Cenários Críticos

Os testes também foram executados em cenários específicos para avaliar o comportamento sob diferentes condições de stress:

### Tabela Resumo por Cenário

| Cenário | V1 Sucesso | V2 Sucesso | V2 Fallback | Ganho | Redução Falhas |
|---------|:----------:|:----------:|:-----------:|:-----:|:--------------:|
| **Catástrofe** | 35.9% | 100% | 73.2% | +64.1pp | -100% |
| **Degradação** | 75.2% | 100% | 63.7% | +24.8pp | -100% |
| **Indisponibilidade** | 10.6% | 100% | 98.6% | +89.4pp | -100% |
| **Normal** | 100% | 100% | 0% | +0pp | -0% |
| **Rajadas** | 63.0% | 100% | 38.8% | +37.0pp | -100% |

### Análise por Cenário

#### Cenário Catástrofe
- **Condição:** 80% de falhas
- **V1:** Apenas 35.9% de sucesso
- **V2:** 100% de disponibilidade com 73.2% de fallbacks
- **Conclusão:** CB essencial em cenários de alta falha

#### Cenário Indisponibilidade
- **Condição:** Serviço completamente indisponível
- **V1:** Apenas 10.6% de sucesso
- **V2:** 100% de disponibilidade (98.6% via fallback)
- **Conclusão:** Graceful degradation funciona perfeitamente

#### Cenário Rajadas
- **Condição:** Tráfego em bursts
- **V1:** 63% de sucesso
- **V2:** 100% de disponibilidade
- **Conclusão:** CB absorve picos de carga eficientemente

---

## 📁 Artefatos Gerados

### Estrutura de Arquivos

```
analysis_results/
├── csv/
│   ├── summary_analysis.csv
│   ├── statistical_analysis.csv
│   └── timeline_*.csv
├── plots/
│   ├── response_times.png
│   ├── success_failure_rate.png
│   ├── distributions.png
│   ├── timeline_V1.png
│   ├── timeline_V2.png
│   ├── timeline_V3.png
│   └── timeline_comparison.png
├── final_charts/
│   ├── 01_success_rates_comparison.png
│   ├── 02_failure_reduction.png
│   ├── 03_response_time_percentiles.png
│   ├── 04_throughput_comparison.png
│   ├── 05_status_distribution.png
│   ├── 06_consolidated_metrics_radar.png
│   ├── 07_catastrofe_timeline.png
│   ├── 08_fallback_contribution.png
│   └── ...
├── latex/
│   ├── tabela_resumo.tex
│   ├── tabela_estatistica.tex
│   └── figuras_analise.tex
├── markdown/
│   └── analise_resultados.md
└── analysis_report.html
```

### Gráficos Principais

1. **response_times.png** - Comparação de tempos médios e P95
2. **success_failure_rate.png** - Composição das respostas
3. **distributions.png** - Análise estatística das distribuições
4. **timeline_comparison.png** - Evolução temporal V1 vs V2

---

## 🔧 Correções e Melhorias Implementadas

### 1. Correção de Versão do Resilience4j (V3)

**Problema:** O serviço V3 falhava ao iniciar com erro:
```
ClassNotFoundException: io.github.resilience4j.spring6.micrometer.configure.TimerConfigurationProperties
```

**Causa:** Incompatibilidade entre Resilience4j 2.2.0 e Spring Boot 3.2.5

**Solução:** Downgrade para Resilience4j 2.1.0 em `pom.xml`:
```xml
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot3</artifactId>
    <version>2.1.0</version>  <!-- Era 2.2.0 -->
</dependency>
```

### 2. Otimização do Analyzer para Arquivos Grandes

**Problema:** Script `analyzer.py` era morto (OOM) ao processar arquivos de 2GB+

**Causa:** Carregamento de todos os datapoints em memória

**Solução:** Implementação de **Reservoir Sampling**:
```python
def load_data(self, max_sample_size=500000):
    # Usa amostragem para arquivos > 100MB
    if file_size_mb > 100:
        # Reservoir sampling mantém distribuição estatística
        if len(all_points) < max_sample_size:
            all_points.append(point_data)
        else:
            j = random.randint(0, line_count - 1)
            if j < max_sample_size:
                all_points[j] = point_data
```

---

## 🎓 Conclusões

### Principais Descobertas

1. **Circuit Breaker é essencial para disponibilidade**
   - V2 alcança 100% de disponibilidade vs 90% do V1
   - Elimina completamente falhas visíveis ao cliente

2. **Fallback rápido melhora performance**
   - Tempo médio de resposta 67% menor com CB
   - Throughput 30% maior devido à liberação rápida de recursos

3. **Retry sozinho não resolve**
   - V3 tem mesma taxa de sucesso que V1
   - Tempo de resposta ainda maior devido às retentativas
   - Não melhora disponibilidade quando o serviço está degradado

4. **Effect size estatisticamente grande**
   - Cliff's Delta = 0.594 (categorizado como "Grande")
   - Diferença não é resultado do acaso (p < 0.001)

### Recomendações

1. **Sempre implementar Circuit Breaker** em chamadas síncronas entre microsserviços
2. **Combinar CB + Fallback** para graceful degradation
3. **Retry pode complementar** mas não substitui o Circuit Breaker
4. **Monitorar métricas** do CB para ajustar thresholds

---

## 📚 Referências dos Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `k6/results/V*_Completo_summary.json` | Métricas agregadas por versão |
| `analysis_results/csv/summary_analysis.csv` | Resumo comparativo |
| `analysis_results/csv/statistical_analysis.csv` | Testes estatísticos |
| `services/payment-service-v*/` | Código fonte das versões |
| `tcc_latex/main.tex` | Documento LaTeX do TCC |

---

*Documento gerado em 20/12/2024 como parte do TCC sobre Padrões de Resiliência em Microsserviços.*
