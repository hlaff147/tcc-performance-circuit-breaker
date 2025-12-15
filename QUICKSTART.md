# 🚀 Quick Start - TCC v2.0.0

**Status:** ✅ Código aprovado e pronto para experimento  
**Última Revisão:** 15 de dezembro de 2025

---

## ⚡ Execução Rápida (Teste Piloto)

### 1. Validar correções aplicadas

```bash
./validate_corrections.sh
```

✅ Deve mostrar: "TODAS AS CORREÇÕES CRÍTICAS FORAM APLICADAS"

---

### 2. Executar teste piloto

```bash
# 1 run de cada tratamento × cenário (rápido, ~15-20 min)
./run_comparative_experiment.sh --pilot
```

**O que acontece:**
- Inicia 4 tratamentos sequencialmente (V1, V2, V3, V4)
- Para cada cenário (indisponibilidade-extrema, falha-catastrofica)
- Coleta métricas em `k6/results/comparative/experiment_TIMESTAMP/`

---

### 3. Analisar resultados do piloto

```bash
# Pegar último experimento
LATEST=$(ls -td k6/results/comparative/experiment_* | head -1)

# Rodar análise estatística
python3 analysis/scripts/comparative_analyzer.py "$LATEST"
```

**Outputs gerados:**
- `$LATEST/analysis/summary_by_treatment.csv` - Resumo por tratamento
- `$LATEST/analysis/statistical_comparisons.csv` - Testes Mann-Whitney

---

### 4. Se piloto OK → Experimento completo

```bash
# 5 runs × 2 cenários × 4 tratamentos = 40 runs
# Duração: ~2-3 horas
./run_comparative_experiment.sh
```

---

## 📊 Verificar Serviços Durante Experimento

### Health Check
```bash
curl http://localhost:8080/actuator/health | jq
```

### Métricas Prometheus
```bash
# Taxa de sucesso
curl -s http://localhost:8080/actuator/prometheus | grep 'payment_outcome_total{result="success"}'

# Retries
curl -s http://localhost:8080/actuator/prometheus | grep 'payment_retry_attempts_total'

# Circuit Breaker
curl -s http://localhost:8080/actuator/prometheus | grep 'resilience4j_circuitbreaker_state'
```

### Logs em tempo real
```bash
docker-compose logs -f servico-pagamento
```

---

## 🔍 Estrutura de Resultados

```
k6/results/comparative/experiment_TIMESTAMP/
├── indisponibilidade-extrema_v1_run1.json
├── indisponibilidade-extrema_v1_run1_summary.json
├── indisponibilidade-extrema_v2_run1.json
├── ...
└── analysis/
    ├── summary_by_treatment.csv
    └── statistical_comparisons.csv
```

---

## 📋 Tratamentos Implementados

| ID | Serviço | Padrão | Quando Usar |
|----|---------|--------|-------------|
| V1 | payment-service-v1 | Timeout only | **Baseline** |
| V2 | payment-service-v2 | Circuit Breaker | Falhas sistêmicas |
| V3 | payment-service-v3 | Retry | Falhas transitórias |
| V4 | payment-service-v4 | CB + Retry | Combinação |

---

## 🎯 Hipóteses Testadas

1. **H1:** CB reduz falhas vs baseline (V1 vs V2)
2. **H2:** Retry ajuda em transitórias (V1 vs V3)
3. **H3:** CB supera Retry em indisponibilidade (V2 vs V3)
4. **H4:** CB+Retry supera CB (V2 vs V4)
5. **H5:** CB+Retry supera Retry (V3 vs V4)

**Significância estatística:** p < 0.00167 (Bonferroni para 30 testes)

---

## 🛠️ Troubleshooting

### Serviço não inicia
```bash
# Ver logs
docker-compose logs servico-pagamento

# Verificar porta
lsof -i :8080

# Rebuild
PAYMENT_SERVICE_VERSION=v3 docker-compose up -d --build
```

### Parser não encontra arquivos
```bash
# Verificar nomenclatura
ls k6/results/comparative/experiment_*/

# Deve seguir: cenario_vN_runM_summary.json
```

### Estatística não roda
```bash
# Validar dependências Python
pip3 install numpy pandas scipy

# Testar sintaxe
python3 -m py_compile analysis/scripts/comparative_analyzer.py
```

---

## 📚 Documentação Completa

| Arquivo | Conteúdo |
|---------|----------|
| [CODE_REVIEW_REPORT_V2.md](CODE_REVIEW_REPORT_V2.md) | Relatório de revisão completo (40 páginas) |
| [CODE_REVIEW_SUMMARY.md](CODE_REVIEW_SUMMARY.md) | Sumário executivo da revisão |
| [REVIEW_STATUS.md](REVIEW_STATUS.md) | Status visual com scorecard |
| [CRITICAL_FIXES.md](CRITICAL_FIXES.md) | Guia de correções aplicadas |
| [GUIA_EXECUCAO.md](GUIA_EXECUCAO.md) | Guia de execução original |

---

## ⚙️ Configurações Principais

### V3 (Retry-only)
```yaml
maxAttempts: 3
waitDuration: 500ms
exponentialBackoffMultiplier: 2.0
randomizedWaitFactor: 0.5
```

### V4 (CB + Retry)
```yaml
# Circuit Breaker (mais tolerante)
failureRateThreshold: 60%
waitDurationInOpenState: 5s

# Retry (menos agressivo)
maxAttempts: 2
waitDuration: 300ms
exponentialBackoffMultiplier: 1.5
```

---

## 🔬 Cenários de Teste

### Indisponibilidade Extrema
- Adquirente 100% indisponível por 30s
- Expectativa: CB protege (V2, V4) > Retry amplifica (V3)

### Falha Catastrófica
- Adquirente retorna 500 por período prolongado
- Expectativa: CB fecha rapidamente, Retry falha após N tentativas

---

## 📊 Métricas Coletadas

- `success_rate` - Taxa de sucesso
- `success_after_retry` - Sucesso após retry
- `fallback_rate` - Taxa de fallback
- `cb_open_count` - Vezes que CB abriu
- `avg_duration_ms` - Latência média
- `p95_duration_ms` - Latência P95
- `p99_duration_ms` - Latência P99

---

## ✅ Próximo Comando

```bash
./run_comparative_experiment.sh --pilot
```

🎯 **Boa sorte com o experimento!**
