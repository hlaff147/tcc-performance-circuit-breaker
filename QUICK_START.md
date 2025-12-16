# 🚀 Quick Start - TCC v2.0.0

## Pré-requisitos

- Docker e Docker Compose
- Python 3.9+
- Java 17+ (para build local)
- 8GB RAM disponível

---

## 1. Clonar e Configurar

```bash
git clone https://github.com/seu-usuario/tcc-performance-circuit-breaker.git
cd tcc-performance-circuit-breaker
```

---

## 2. Subir Infraestrutura

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar status
docker ps

# Verificar saúde
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
```

**Serviços disponíveis:**
| Serviço | Porta | Descrição |
|---------|-------|-----------|
| servico-pagamento | 8080 | Serviço principal (V1/V2/V3/V4) |
| servico-adquirente | 8081 | Simulador de gateway |
| prometheus | 9090 | Métricas |
| grafana | 3000 | Dashboards (admin/admin) |

---

## 3. Executar Testes

### 🔬 Experimento Comparativo (CB vs Retry) — NOVO v2.0.0

```bash
# Teste piloto (~30 min)
./run_comparative_experiment.sh --pilot

# Experimento completo com 5 repetições (~4-6h)
./run_comparative_experiment.sh
```

**Tratamentos testados:**
| Versão | Padrão | Cenário |
|--------|--------|---------|
| V1 | Baseline (timeout) | Controle |
| V2 | Circuit Breaker | Falhas sistêmicas |
| V3 | Retry | Falhas transitórias |
| V4 | CB + Retry | Combinação |

### 📊 Cenários Críticos (V1 vs V2)

```bash
# Cenário único
./run_and_analyze.sh catastrofe

# Todos os cenários (~45 min)
./run_and_analyze.sh all
```

**Cenários disponíveis:**
- `catastrofe` — API 100% indisponível por 5 min
- `degradacao` — Degradação progressiva
- `rajadas` — Falhas intermitentes
- `indisponibilidade` — API 75% offline

---

## 4. Analisar Resultados

### Análise Comparativa (v2.0.0)
```bash
python3 analysis/scripts/comparative_analyzer.py k6/results/comparative/experiment_*/
```

### Análise Tradicional
```bash
python3 analysis/scripts/analyzer.py
```

### Ver Relatórios
```bash
# HTML
open analysis_results/analysis_report.html

# CSV consolidado
cat analysis_results/scenarios/csv/consolidated_benefits.csv
```

---

## 5. Trocar Versão do Serviço

```bash
# Usar V1 (baseline)
PAYMENT_SERVICE_VERSION=v1 docker-compose up -d --build servico-pagamento

# Usar V2 (Circuit Breaker)
PAYMENT_SERVICE_VERSION=v2 docker-compose up -d --build servico-pagamento

# Usar V3 (Retry) — NOVO
PAYMENT_SERVICE_VERSION=v3 docker-compose up -d --build servico-pagamento

# Usar V4 (CB + Retry) — NOVO
PAYMENT_SERVICE_VERSION=v4 docker-compose up -d --build servico-pagamento
```

---

## 6. Teste Manual Rápido

```bash
# Modo normal
curl -X POST "http://localhost:8080/pagar?modo=normal" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "customer_id": "test"}'

# Modo falha (para testar CB/Retry)
curl -X POST "http://localhost:8080/pagar?modo=falha" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "customer_id": "test"}'
```

**Respostas esperadas:**
- `200` — Sucesso
- `202` — Fallback (CB aberto ou após retry)
- `500` — Falha

---

## 7. Monitoramento

### Prometheus
```
http://localhost:9090
```

**Queries úteis:**
```promql
# Taxa de sucesso
rate(http_server_requests_seconds_count{status="200"}[1m])

# Estado do Circuit Breaker
resilience4j_circuitbreaker_state

# Retries por segundo
rate(resilience4j_retry_calls_total[1m])
```

### Grafana
```
http://localhost:3000
Usuário: admin
Senha: admin
```

---

## 8. Parar Tudo

```bash
docker-compose down

# Limpar volumes (opcional)
docker-compose down -v
```

---

## Troubleshooting

### Serviço não inicia
```bash
# Ver logs
docker-compose logs servico-pagamento

# Rebuild forçado
docker-compose build --no-cache servico-pagamento
```

### Métricas não aparecem
```bash
# Verificar endpoint
curl http://localhost:8080/actuator/prometheus | grep resilience4j
```

### Porta em uso
```bash
# Verificar quem está usando
lsof -i :8080
```

---

## Documentação Adicional

- [GUIA_EXECUCAO.md](GUIA_EXECUCAO.md) — Guia detalhado de métricas e configuração
- [CODE_REVIEW_V2.md](CODE_REVIEW_V2.md) — Revisão das mudanças v2.0.0
- [ANALISE_FINAL_TCC.md](ANALISE_FINAL_TCC.md) — Análise consolidada
- [CB_PERFIS_CONFIGURACAO.md](CB_PERFIS_CONFIGURACAO.md) — Perfis de Circuit Breaker
