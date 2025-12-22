# 🏗️ Documentação Técnica Completa - TCC Circuit Breaker

> **Projeto:** Performance e Resiliência em Arquiteturas de Microsserviços  
> **Autor:** Humberto L. A. Fonseca Filho  
> **Instituição:** Centro de Informática - UFPE  
> **Data:** 20 de Dezembro de 2024  
> **Versão:** 3.0

---

## 📚 Índice

1. [Fundamentação Teórica](#1-fundamentação-teórica)
2. [Arquitetura do Projeto](#2-arquitetura-do-projeto)
3. [Serviços Implementados](#3-serviços-implementados)
4. [Infraestrutura Docker](#4-infraestrutura-docker)
5. [Stack de Monitoramento](#5-stack-de-monitoramento)
6. [Análise de Resultados](#6-análise-de-resultados)
7. [Pontos Fortes e Limitações](#7-pontos-fortes-e-limitações)
8. [Conclusões](#8-conclusões)

---

## 1. Fundamentação Teórica

### 1.1 O Problema das Falhas em Cascata

Em arquiteturas de microsserviços, a comunicação síncrona entre serviços cria dependências que podem propagar falhas de forma catastrófica. Quando um serviço downstream (como um gateway de pagamento) fica lento ou indisponível, os efeitos podem se propagar upstream de forma exponencial.

**Cenário típico de falha em cascata:**

```
                    ┌─────────────────┐
                    │   Serviço A     │
                    │ (aguardando...) │
                    └────────┬────────┘
                             │ 10 threads bloqueadas
                    ┌────────▼────────┐
                    │   Serviço B     │
                    │ (aguardando...) │
                    └────────┬────────┘
                             │ 50 threads bloqueadas
                    ┌────────▼────────┐
                    │   Serviço C     │◀── FALHA/LENTO
                    │   (DEGRADADO)   │
                    └─────────────────┘
```

**Consequências:**
- **Thread Pool Starvation:** Threads ficam bloqueadas aguardando respostas
- **Efeito Dominó:** Cada serviço que falha afeta todos que dependem dele
- **Timeout Cascading:** Timeouts se acumulam, aumentando latência total
- **Resource Exhaustion:** Memória e CPU são consumidas por requisições pendentes

### 1.2 O Padrão Circuit Breaker

O **Circuit Breaker** é um padrão de projeto que atua como um "disjuntor" no circuito de chamadas entre serviços. Inspirado em disjuntores elétricos, ele "abre" quando detecta falhas, protegendo o sistema.

**Máquina de Estados:**

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
              ┌───────────┐    Falhas > Threshold     ┌───────┴─────┐
              │  FECHADO  │ ─────────────────────────▶│   ABERTO    │
              │ (Closed)  │                           │   (Open)    │
              └─────┬─────┘                           └──────┬──────┘
                    ▲                                        │
                    │                                        │ Timeout
                    │                                        │ expira
                    │                               ┌────────▼────────┐
                    │          Sucesso nas          │   SEMI-ABERTO   │
                    └────────  chamadas de  ────────│  (Half-Open)    │
                               teste                └─────────────────┘
```

**Estados:**

| Estado | Comportamento |
|--------|---------------|
| **FECHADO** | Todas as requisições passam normalmente. Monitora taxa de falhas. |
| **ABERTO** | Bloqueia todas as requisições. Retorna imediatamente com fallback. |
| **SEMI-ABERTO** | Permite algumas requisições de "teste" para verificar recuperação. |

### 1.3 Resilience4j: A Biblioteca Escolhida

O **Resilience4j** é uma biblioteca leve e modular para resiliência em Java, projetada para Java 8+ e execução funcional. Diferente do Hystrix (Netflix, descontinuado), o Resilience4j:

**Vantagens:**
- ✅ Design modular (compose apenas o que precisa)
- ✅ Integração nativa com Spring Boot 3
- ✅ Métricas prontas para Prometheus/Micrometer
- ✅ Sem dependências pesadas (CircuitBreaker: ~40KB)
- ✅ Suporte a programação reativa e funcional

**Módulos disponíveis:**
- `resilience4j-circuitbreaker` - Proteção contra falhas em cascata
- `resilience4j-retry` - Tentativas automáticas com backoff
- `resilience4j-bulkhead` - Isolamento de recursos
- `resilience4j-ratelimiter` - Controle de taxa
- `resilience4j-timelimiter` - Timeout de operações

### 1.4 Alternativa: Padrão Retry

O **Retry** é outro padrão de resiliência que tenta executar operações múltiplas vezes antes de desistir.

**Características:**
- Útil para falhas **transitórias** (rede instável, spikes momentâneos)
- Usa **backoff exponencial** para evitar sobrecarga
- **Não protege** contra falhas persistentes (amplifica carga 3x)

```
   Tentativa 1          Tentativa 2          Tentativa 3
       │                    │                    │
   [FALHA]──────500ms──────[FALHA]──────1000ms──────[FALHA]──▶ Fallback
       │                    │                    │
       └────────────────────┴────────────────────┘
              Backoff Exponencial (500ms → 1s → 2s)
```

---

## 2. Arquitetura do Projeto

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DOCKER NETWORK: tcc-network                     │
│                                                                         │
│  ┌───────────────┐      ┌─────────────────────┐      ┌───────────────┐  │
│  │   GRAFANA K6  │─────▶│  SERVICO-PAGAMENTO  │─────▶│   SERVICO-    │  │
│  │  Load Tester  │      │     (V1/V2/V3)      │      │  ADQUIRENTE   │  │
│  │  :8080 (int)  │      │       :8080         │      │     :8081     │  │
│  └───────────────┘      └─────────┬───────────┘      └───────────────┘  │
│                                   │                                     │
│         ┌─────────────────────────┼─────────────────────────┐          │
│         │                         │                         │          │
│  ┌──────▼──────┐          ┌───────▼───────┐          ┌──────▼──────┐   │
│  │  cADVISOR   │          │  PROMETHEUS   │          │   GRAFANA   │   │
│  │ Container   │          │   Metrics     │          │  Dashboard  │   │
│  │ Metrics     │          │    :9090      │          │    :3000    │   │
│  │   :8088     │          │               │          │             │   │
│  └─────────────┘          └───────────────┘          └─────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Requisições

```
1. K6 envia requisição com modo (normal/latencia/falha)
   │
   ▼
2. servico-pagamento recebe em /pagar
   │
   ├─► V1: Chama adquirente diretamente (sem proteção)
   │
   ├─► V2: Circuit Breaker avalia estado
   │       ├─ FECHADO/SEMI-ABERTO → Chama adquirente
   │       └─ ABERTO → Retorna fallback (HTTP 202)
   │
   └─► V3: Retry tenta até 3x com backoff
           └─ Todas falhas → Retorna erro (HTTP 500)
   │
   ▼
3. servico-adquirente simula resposta baseada no modo
   │
   ▼
4. Resposta retorna ao k6 → Métricas coletadas
```

---

## 3. Serviços Implementados

### 3.1 Serviço Adquirente (Simulador)

**Localização:** `services/acquirer-service/`

**Descrição:** Simula um gateway de pagamento externo com comportamentos configuráveis para testar diferentes cenários.

**Modos de Operação:**

| Modo | Comportamento | Código HTTP | Uso |
|------|---------------|:-----------:|-----|
| `normal` | Resposta imediata (0-50ms) | 200 | Operação padrão |
| `latencia` | Delay de 2000-3000ms | 200 | Simula carga alta |
| `falha` | Erro imediato | 500 | Simula indisponibilidade |
| `timeout` | Delay de 15s | 200 | Testa timeout do cliente |
| `parcial` | 50% chance sucesso/falha | 200/500 | Testa threshold do CB |
| `degradacao` | Comportamento aleatório | 200/500 | Simula degradação progressiva |

**Código Relevante:**
```java
@PostMapping
public ResponseEntity<String> autorizar(
    @RequestParam(name = "modo", defaultValue = "normal") String modo,
    @RequestBody(required = false) Map<String, Object> payload) {
    
    return switch (modo) {
        case "normal" -> handleNormal();
        case "latencia" -> handleLatency();
        case "falha" -> handleFailure();
        // ...
    };
}
```

### 3.2 Serviço de Pagamento V1 (Baseline)

**Localização:** `services/payment-service-v1/`

**Descrição:** Implementação **ingênua** sem nenhum padrão de resiliência. Serve como **grupo de controle** no experimento.

**Características:**
- ⚠️ Sem Circuit Breaker
- ⚠️ Sem Retry
- ⚠️ Sem Fallback
- ❌ Propaga todas as falhas diretamente ao cliente

**Código:**
```java
public PaymentResponse processPayment(String modo, PaymentRequest request) {
    try {
        ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
        
        if (response.getStatusCode().is5xxServerError()) {
            return PaymentResponse.failure("Erro do adquirente: " + response.getBody());
        }
        
        return PaymentResponse.success(response.getBody());
        
    } catch (Exception e) {
        return PaymentResponse.failure("Erro: " + e.getMessage());
    }
}
```

**Comportamento esperado:**
- Taxa de sucesso ≈ 90% (proporcional ao modo de teste)
- Taxa de falha ≈ 10%
- Sem proteção contra falhas em cascata

### 3.3 Serviço de Pagamento V2 (Circuit Breaker)

**Localização:** `services/payment-service-v2/`

**Descrição:** Implementa o padrão **Circuit Breaker** usando Resilience4j com fallback gracioso.

**Características:**
- ✅ Circuit Breaker ativo
- ✅ Fallback com HTTP 202 (Accepted)
- ✅ Métricas expostas para Prometheus
- ✅ 3 perfis de configuração

**Código:**
```java
@CircuitBreaker(name = "adquirente-cb", fallbackMethod = "processPaymentFallback")
@Timed(value = "payment.processing.time")
public PaymentResponse processPayment(String modo, PaymentRequest request) {
    ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
    
    if (response.getStatusCode() == HttpStatus.SERVICE_UNAVAILABLE) {
        throw new RuntimeException("Serviço indisponível");
    }
    
    return PaymentResponse.success(response.getBody());
}

public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable t) {
    if (t instanceof CallNotPermittedException) {
        return PaymentResponse.circuitBreakerOpen();
    }
    return PaymentResponse.fallback("Aceito para processamento posterior");
}
```

**Perfis de Configuração:**

| Perfil | Threshold | Janela | Wait Time | Filosofia |
|--------|:---------:|:------:|:---------:|-----------|
| **Equilibrado** | 50% | 20 req | 10s | Balanceado entre proteção e throughput |
| **Conservador** | 60% | 30 req | 15s | Prioriza disponibilidade, mais tolerante |
| **Agressivo** | 30% | 10 req | 5s | Proteção máxima, reage rapidamente |

### 3.4 Serviço de Pagamento V3 (Retry)

**Localização:** `services/payment-service-v3/`

**Descrição:** Implementa apenas o padrão **Retry** com backoff exponencial, **sem** Circuit Breaker.

**Características:**
- ✅ Retry com backoff exponencial
- ⚠️ Sem Circuit Breaker
- ❌ Fallback só após esgotar retries
- ❌ Pode amplificar carga 3x em cenários de falha

**Código:**
```java
@Retry(name = "adquirente-retry", fallbackMethod = "processPaymentFallback")
@Timed(value = "payment.processing.time")
public PaymentResponse processPayment(String modo, PaymentRequest request) {
    ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
    
    if (response.getStatusCode().is5xxServerError()) {
        throw new RuntimeException("Erro para acionar retry");
    }
    
    return PaymentResponse.success(response.getBody());
}
```

**Configuração do Retry:**
```yaml
resilience4j:
  retry:
    instances:
      adquirente-retry:
        maxAttempts: 3
        waitDuration: 500ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
        # 500ms → 1000ms → 2000ms
```

---

## 4. Infraestrutura Docker

### 4.1 Composição de Serviços

O arquivo `docker-compose.yml` define toda a infraestrutura:

```yaml
services:
  # ─── CAMADA DE APLICAÇÃO ───
  servico-adquirente:    # Simulador de gateway
  servico-pagamento:     # V1, V2 ou V3 (selecionável)
  servico-pagamento-v2:  # Instância dedicada V2
  servico-pagamento-v3:  # Instância dedicada V3
  
  # ─── CAMADA DE TESTE ───
  k6-tester:             # Grafana k6 para load testing
  
  # ─── CAMADA DE MONITORAMENTO ───
  cadvisor:              # Métricas de containers
  prometheus:            # Coleta e armazena métricas
  grafana:               # Visualização de dashboards
```

### 4.2 Recursos Alocados

| Container | CPU | Memória | Porta |
|-----------|:---:|:-------:|:-----:|
| servico-adquirente | 0.5 | 512MB | 8081 |
| servico-pagamento | 1.0 | 1GB | 8080 |
| k6-tester | 2.0 | 2GB | - |
| prometheus | - | - | 9095 |
| grafana | - | - | 3000 |
| cadvisor | - | - | 8088 |

### 4.3 Seleção de Versão

A versão do serviço de pagamento é selecionada via variável de ambiente:

```bash
# Executa V1 (baseline)
PAYMENT_SERVICE_VERSION=v1 docker compose up

# Executa V2 (Circuit Breaker)
PAYMENT_SERVICE_VERSION=v2 docker compose up

# Executa V3 (Retry)
PAYMENT_SERVICE_VERSION=v3 docker compose up
```

---

## 5. Stack de Monitoramento

### 5.1 Prometheus

**Função:** Coleta e armazena métricas no formato time-series.

**Configuração:**
```yaml
global:
  scrape_interval: 5s  # Alta frequência para testes

scrape_configs:
  - job_name: "servico-pagamento-v1"
    metrics_path: "/actuator/prometheus"
    static_configs:
      - targets: ["servico-pagamento:8080"]
  
  # Métricas específicas do Circuit Breaker:
  # - resilience4j_circuitbreaker_state
  # - resilience4j_circuitbreaker_calls_seconds
  # - resilience4j_circuitbreaker_failure_rate
```

**Métricas Coletadas:**

| Métrica | Descrição |
|---------|-----------|
| `http_server_requests_seconds` | Tempo de resposta HTTP |
| `resilience4j_circuitbreaker_state` | Estado atual do CB (0,1,2) |
| `resilience4j_circuitbreaker_failure_rate` | Taxa de falhas % |
| `container_cpu_usage_seconds_total` | Uso de CPU por container |
| `container_memory_usage_bytes` | Uso de memória |

### 5.2 Grafana

**Função:** Visualização de dashboards em tempo real.

**Acesso:** `http://localhost:3000`

**Dashboards Disponíveis:**
- JVM Micrometer (Spring Boot)
- Resilience4j Dashboard
- Container Metrics (cAdvisor)

### 5.3 cAdvisor

**Função:** Coleta métricas de performance dos containers Docker.

**Métricas:**
- CPU usage per container
- Memory consumption
- Network I/O
- Filesystem usage

---

## 6. Análise de Resultados

### 6.1 Resultados do Cenário Completo (30 min, 500 VUs)

#### 📊 Métricas Principais

| Métrica | V1 (Baseline) | V2 (Circuit Breaker) | V3 (Retry) |
|---------|:-------------:|:--------------------:|:----------:|
| **Requisições Totais** | 400,647 | 521,209 | 356,979 |
| **Disponibilidade** | 89.97% | **100%** ✅ | 89.99% |
| **Taxa de Sucesso** | 89.97% | 28.96% | 89.99% |
| **Taxa de Fallback** | 0% | 71.04% | 0% |
| **Taxa de Falha** | 10.03% | **0%** ✅ | 10.00% |
| **Tempo Médio** | 534 ms | **179 ms** ✅ | 722 ms |
| **Mediana** | 38 ms | **3 ms** ✅ | 84 ms |
| **P95** | 2,771 ms | **2,245 ms** ✅ | 2,808 ms |
| **Throughput** | 222 req/s | **289 req/s** ✅ | 198 req/s |

#### 📈 Análise Estatística

| Teste | Valor | Interpretação |
|-------|:-----:|---------------|
| **Mann-Whitney U** | 413,180,104 | p < 0.001 (significativo) |
| **Kolmogorov-Smirnov** | 0.5153 | Distribuições diferentes |
| **Cliff's Delta** | 0.594 | **Effect Size Grande** |
| **IC Bootstrap 95%** | [340, 370] ms | V2 consistentemente melhor |

### 6.2 Análise por Cenário

| Cenário | V1 Sucesso | V2 Disponibilidade | V2 Fallback | Ganho |
|---------|:----------:|:------------------:|:-----------:|:-----:|
| **Catástrofe** (80% falha) | 35.9% | 100% | 73.2% | **+64.1pp** |
| **Indisponibilidade** | 10.6% | 100% | 98.6% | **+89.4pp** |
| **Rajadas** | 63.0% | 100% | 38.8% | **+37.0pp** |
| **Degradação** | 75.2% | 100% | 63.7% | **+24.8pp** |
| **Normal** | 100% | 100% | 0% | +0pp |

---

## 7. Pontos Fortes e Limitações

### 7.1 ✅ Vantagens do Circuit Breaker (V2)

1. **Disponibilidade Total (100%)**
   - O fallback garante que NENHUMA requisição retorne erro ao cliente
   - HTTP 202 indica "aceito para processamento posterior"
   - Experiência do usuário muito melhor

2. **Fail-Fast: Libera Recursos Rapidamente**
   - Quando CB está ABERTO, resposta é imediata (~6ms)
   - Threads não ficam bloqueadas aguardando timeout
   - Permite processar mais requisições por segundo

3. **Throughput 30% Superior**
   - V2: 289 req/s vs V1: 222 req/s
   - Recursos liberados rapidamente = mais capacidade
   - Menor uso de memória e CPU

4. **Tempo de Resposta 67% Menor**
   - V2 média: 179ms vs V1 média: 534ms
   - Fallback responde em ~6ms
   - Mediana (P50) de 3ms vs 38ms

5. **Proteção em Cenários Extremos**
   - Cenário Catástrofe: V1 = 35.9%, V2 = 100%
   - Indisponibilidade Total: V1 = 10.6%, V2 = 100%

6. **Recuperação Automática**
   - Estado HALF_OPEN permite testar recuperação
   - Transição automática quando serviço volta

### 7.2 ⚠️ Limitações e Trade-offs do Circuit Breaker

1. **Menor Taxa de "Sucesso Real" em Operação Normal**
   - V1: ~90% de sucesso direto
   - V2: ~29% de sucesso direto + 71% fallback
   - O fallback é "sucesso operacional" mas não "processamento real"

2. **Dependência de Fallback Implementado**
   - Se o fallback não existir, CB retorna erro
   - Fallback deve ser cuidadosamente projetado
   - Pode mascarar problemas se não monitorado

3. **Configuração Requer Tuning**
   - Thresholds errados podem:
     - Abrir CB muito cedo (perde throughput)
     - Abrir CB muito tarde (não protege)
   - Requer conhecimento do padrão de tráfego

4. **Atraso na Detecção de Recuperação**
   - `waitDurationInOpenState` pode atrasar retorno
   - Se muito curto: oscilação (bouncing)
   - Se muito longo: desperdício de recursos

5. **Complexidade de Debug**
   - Comportamento não-determinístico pode confundir
   - Requer logging estruturado e métricas
   - Developers precisam entender estados do CB

### 7.3 🔄 Comparativo V3 (Retry)

| Aspecto | Retry (V3) | Circuit Breaker (V2) |
|---------|:----------:|:--------------------:|
| Falhas Transitórias | ✅ Resolve | ⚠️ Pode abrir CB |
| Falhas Persistentes | ❌ Amplifica 3x | ✅ Protege |
| Latência | ↑ 35% maior | ↓ 67% menor |
| Throughput | ↓ 11% menor | ↑ 30% maior |
| Disponibilidade | 90% | 100% |
| Proteção Cascata | ❌ Não | ✅ Sim |

**Conclusão sobre V3:** O padrão Retry sozinho:
- É útil para erros pontuais de rede
- **NÃO substitui** o Circuit Breaker
- **Deve ser combinado** com CB, não usado isoladamente

---

## 8. Conclusões

### 8.1 Principais Descobertas

1. **Circuit Breaker é essencial para disponibilidade**
   - Única implementação que alcançou 100% de disponibilidade
   - Eliminação completa de erros visíveis ao usuário

2. **Fallback é a chave da experiência do usuário**
   - HTTP 202 (Accepted) é melhor que HTTP 500 (Error)
   - Permite graceful degradation

3. **Retry sozinho é insuficiente**
   - Não protege contra falhas persistentes
   - Pode piorar a situação (3x mais carga)
   - Deve ser combinado com CB

4. **Diferença estatisticamente significativa**
   - Effect Size Grande (Cliff's Delta = 0.594)
   - p-valor < 0.001
   - Melhoria não é resultado do acaso

### 8.2 Recomendações Práticas

| Cenário | Recomendação |
|---------|--------------|
| Chamadas síncronas entre serviços | **Sempre usar CB** |
| APIs externas de terceiros | CB + Timeout configurado |
| Falhas transitórias conhecidas | CB + Retry com backoff |
| Operações críticas | CB + Bulkhead para isolamento |
| Alta disponibilidade (SLA 99.9%+) | CB com fallback implementado |

### 8.3 Trabalhos Futuros

- [ ] Comparar com padrão Bulkhead
- [ ] Testar combinação CB + Retry
- [ ] Avaliar impacto do Time Limiter
- [ ] Instrumentar métricas de negócio

---

## 📚 Referências Técnicas

- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Spring Cloud CircuitBreaker](https://spring.io/projects/spring-cloud-circuitbreaker)
- [Release It! Design and Deploy Production-Ready Software](https://pragprog.com/titles/mnee2/)
- [Building Microservices - Sam Newman](https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/)

---

*Documento gerado em 20/12/2024 como parte do TCC sobre Padrões de Resiliência em Microsserviços - UFPE/CIn*
