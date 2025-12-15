# 📋 Revisão de Código - TCC v2.0.0: CB vs Retry

## 🎯 Objetivo da Melhoria

Adicionar um **eixo experimental comparativo** entre Circuit Breaker e Retry ao TCC, aumentando a credibilidade metodológica com:
- Tratamentos claramente definidos (BASE, CB, RETRY, CB+RETRY)
- Métricas de retry expostas via Prometheus
- Replicações controladas (N ≥ 5)
- Análise estatística (IC 95%, Mann-Whitney)

---

## 📁 Arquivos Criados

### Serviço V3: Retry-only

| Arquivo | Propósito | Revisar |
|---------|-----------|---------|
| `services/payment-service-v3/pom.xml` | Dependências Resilience4j Retry | ✅ Versões compatíveis |
| `services/payment-service-v3/Dockerfile` | Build do serviço | ✅ Jar name correto |
| `services/payment-service-v3/src/main/resources/application.yml` | Config Retry | ⚠️ **Parâmetros críticos** |
| `services/payment-service-v3/src/main/java/.../PagamentoApplication.java` | Main class | ✅ Simples |
| `services/payment-service-v3/src/main/java/.../PagamentoController.java` | REST endpoint | ✅ Igual V2 |
| `services/payment-service-v3/src/main/java/.../client/AdquirenteClient.java` | Feign client | ✅ Igual V2 |
| `services/payment-service-v3/src/main/java/.../dto/PaymentRequest.java` | DTO | ✅ Igual V2 |
| `services/payment-service-v3/src/main/java/.../dto/PaymentResponse.java` | DTO com outcomes retry | ⚠️ Novos outcomes |
| `services/payment-service-v3/src/main/java/.../service/PaymentService.java` | **@Retry + métricas** | ⚠️ **CRÍTICO** |
| `services/payment-service-v3/src/main/java/.../config/MetricsConfig.java` | @Timed aspect | ✅ Simples |

### Serviço V4: CB + Retry

| Arquivo | Propósito | Revisar |
|---------|-----------|---------|
| `services/payment-service-v4/pom.xml` | Dependências CB + Retry | ✅ Igual V2 |
| `services/payment-service-v4/Dockerfile` | Build do serviço | ✅ Jar name correto |
| `services/payment-service-v4/src/main/resources/application.yml` | Config CB + Retry | ⚠️ **Parâmetros críticos** |
| `services/payment-service-v4/src/main/java/.../PagamentoApplication.java` | Main class | ✅ Simples |
| `services/payment-service-v4/src/main/java/.../PagamentoController.java` | REST endpoint | ✅ Igual V2 |
| `services/payment-service-v4/src/main/java/.../client/AdquirenteClient.java` | Feign client | ✅ Igual V2 |
| `services/payment-service-v4/src/main/java/.../dto/PaymentRequest.java` | DTO | ✅ Igual V2 |
| `services/payment-service-v4/src/main/java/.../dto/PaymentResponse.java` | DTO completo | ✅ Combina V2+V3 |
| `services/payment-service-v4/src/main/java/.../service/PaymentService.java` | **@CB + @Retry** | ⚠️ **CRÍTICO** |
| `services/payment-service-v4/src/main/java/.../config/MetricsConfig.java` | @Timed aspect | ✅ Simples |

### Scripts de Experimento

| Arquivo | Propósito | Revisar |
|---------|-----------|---------|
| `run_comparative_experiment.sh` | Orquestra N runs × 4 tratamentos | ⚠️ **Lógica complexa** |
| `analysis/scripts/comparative_analyzer.py` | IC 95% + Mann-Whitney | ⚠️ **Estatística** |

---

## 📝 Arquivos Modificados

| Arquivo | Alteração | Revisar |
|---------|-----------|---------|
| `VERSION` | 1.0.0 → 2.0.0 + changelog | ✅ |
| `services/acquirer-service/pom.xml` | version 2.0.0 | ✅ |
| `services/acquirer-service/Dockerfile` | jar 2.0.0 | ✅ |
| `services/payment-service-v1/pom.xml` | version 2.0.0 | ✅ |
| `services/payment-service-v1/Dockerfile` | jar 2.0.0 | ✅ |
| `services/payment-service-v2/pom.xml` | version 2.0.0 | ✅ |
| `services/payment-service-v2/Dockerfile` | jar 2.0.0 | ✅ |

---

## ⚠️ Pontos Críticos para Revisão

### 1. Configuração do Retry (V3)
**Arquivo:** `services/payment-service-v3/src/main/resources/application.yml`

```yaml
resilience4j.retry.instances.adquirente-retry:
  maxAttempts: 3           # Verificar se adequado
  waitDuration: 500ms      # Verificar se adequado
  exponentialBackoffMultiplier: 2.0
  randomizedWaitFactor: 0.5  # jitter
```

**Perguntas:**
- [ ] maxAttempts=3 é comparável com a literatura?
- [ ] waitDuration=500ms faz sentido para o cenário?
- [ ] Exponential backoff está correto?

---

### 2. Configuração Combinada CB + Retry (V4)
**Arquivo:** `services/payment-service-v4/src/main/resources/application.yml`

```yaml
# CB mais tolerante porque Retry absorve transitórios
resilience4j.circuitbreaker.instances.adquirente-cb:
  failureRateThreshold: 60  # Era 50 no V2
  waitDurationInOpenState: 5s

# Retry menos agressivo porque CB protege
resilience4j.retry.instances.adquirente-retry:
  maxAttempts: 2  # Menos que V3
  waitDuration: 300ms
```

**Perguntas:**
- [ ] A combinação de parâmetros faz sentido?
- [ ] Ordem dos decoradores (@CB antes de @Retry) está correta?

---

### 3. Lógica do PaymentService (V3 e V4)
**Arquivos:**
- `services/payment-service-v3/.../service/PaymentService.java`
- `services/payment-service-v4/.../service/PaymentService.java`

**Pontos:**
- [ ] ThreadLocal para tracking de tentativas é thread-safe?
- [ ] AcquirerServiceException sendo capturada corretamente?
- [ ] Métricas de retry estão sendo incrementadas?
- [ ] Fallback está retornando HTTP 202?

---

### 4. Script de Experimento
**Arquivo:** `run_comparative_experiment.sh`

**Pontos:**
- [ ] Loop de tratamentos × cenários × runs está correto?
- [ ] wait_for_healthy() funciona?
- [ ] Output files seguem padrão esperado?
- [ ] Seeds são únicos por run?

---

### 5. Análise Estatística
**Arquivo:** `analysis/scripts/comparative_analyzer.py`

**Pontos:**
- [ ] Cálculo de IC 95% está correto?
- [ ] Mann-Whitney está sendo usado corretamente?
- [ ] p < 0.05 como threshold de significância?

---

## 📊 Matriz de Tratamentos

| ID | Serviço | Padrão | Uso |
|----|---------|--------|-----|
| v1 | payment-service-v1 | Timeout only | Baseline (controle) |
| v2 | payment-service-v2 | Circuit Breaker | Falhas sistêmicas |
| v3 | payment-service-v3 | Retry | Falhas transitórias |
| v4 | payment-service-v4 | CB + Retry | Combinação |

---

## 🧪 Verificações a Fazer

### Build
```bash
# Compilar todos os serviços
cd services/payment-service-v1 && mvn clean compile
cd services/payment-service-v2 && mvn clean compile
cd services/payment-service-v3 && mvn clean compile
cd services/payment-service-v4 && mvn clean compile
cd services/acquirer-service && mvn clean compile
```

### Smoke Test
```bash
# Testar cada tratamento
for v in v1 v2 v3 v4; do
  PAYMENT_SERVICE_VERSION=$v docker-compose up -d --build
  sleep 15
  curl -X POST "http://localhost:8080/pagar?modo=normal" \
    -H "Content-Type: application/json" \
    -d '{"amount": 100}'
  docker-compose down
done
```

### Métricas Prometheus
```bash
# Verificar métricas de retry expostas
curl http://localhost:8080/actuator/prometheus | grep resilience4j_retry
```

---

## 📚 Hipóteses do Experimento

| ID | Hipótese | Como Testar |
|----|----------|-------------|
| H1 | CB reduz falhas vs baseline | Comparar V1 vs V2 |
| H2 | Retry ajuda em transientes | Comparar V1 vs V3 |
| H3 | CB supera Retry em indisponibilidade | Comparar V2 vs V3 |
| H4 | CB+Retry supera CB isolado | Comparar V2 vs V4 |
| H5 | CB+Retry supera Retry isolado | Comparar V3 vs V4 |

---

## ✅ Checklist Final

- [ ] Todos os serviços compilam sem erro
- [ ] Dockerfiles referenciam jar 2.0.0
- [ ] application.yml tem parâmetros documentados
- [ ] PaymentService tem métricas corretas
- [ ] run_comparative_experiment.sh é executável
- [ ] comparative_analyzer.py carrega arquivos corretamente
- [ ] VERSION está em 2.0.0

---

## 📎 Commit Sugerido

```
feat(v2.0.0): add CB vs Retry comparative analysis

New services:
- payment-service-v3: Retry-only (maxAttempts=3, exponential backoff)
- payment-service-v4: Circuit Breaker + Retry combined

Experiment infrastructure:
- run_comparative_experiment.sh: N replications across all treatments
- comparative_analyzer.py: 95% CI + Mann-Whitney statistical tests

Version bump: 1.0.0 → 2.0.0 for all services

Hypotheses tested:
- H1: CB reduces failures vs baseline
- H2: Retry helps with transient failures
- H3: CB vs Retry in prolonged unavailability
- H4: CB+Retry synergy vs isolated patterns
```
