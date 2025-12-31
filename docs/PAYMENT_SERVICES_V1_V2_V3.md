# Documentação dos Serviços de Pagamento (v1, v2, v3)

Esta documentação descreve **as três versões do serviço de pagamento** usadas no experimento (TCC), incluindo:

- API HTTP exposta (endpoints, parâmetros, payloads, respostas)
- Fluxo de integração com o serviço adquirente
- Diferenças de resiliência entre as versões (baseline, Circuit Breaker, Retry)
- Observabilidade (Actuator, métricas, Prometheus) e logging
- Exemplos completos de uso (curl + exemplos Java/Spring)

> Escopo: este arquivo cobre os serviços em:
> - services/payment-service-v1
> - services/payment-service-v2
> - services/payment-service-v3

---

## Changelog

### v2.0.0 (2025-12-20)

**Mudanças no Serviço V2 (Circuit Breaker):**

1. **Propagação de erros antes do CB abrir:** O fallback retorna HTTP 202 (Accepted) apenas quando o Circuit Breaker está OPEN (`CallNotPermittedException`). Antes de abrir, exceções são **propagadas como 5xx (HTTP 500)** para garantir contabilização correta das falhas.

2. **URL dinâmica do Feign Client:** A URL do adquirente agora é configurável via propriedade `adquirente-client.url`:
   ```java
   @FeignClient(name = "adquirente-client", url = "${adquirente-client.url:http://servico-adquirente:8081}")
   ```

3. **Testes atualizados:** 
   - `CircuitBreakerIntegrationTest` ajustado para perfil `agressivo` 
   - `PaymentServiceTest` atualizado para verificar propagação de exceções

---

## 1) Visão geral

### 1.1 Arquitetura (alto nível)

Fluxo principal:

1. Cliente (k6 / usuário / outro sistema) chama o **serviço de pagamento** via HTTP.
2. O serviço de pagamento chama o **serviço adquirente** via **OpenFeign**.
3. O adquirente simula comportamentos (normal/latência/falha) controlados por query param `modo`.

Integração com o adquirente:

- O Feign client chama `POST /autorizar?modo=...` no serviço adquirente.
- O host/porta usados nos 3 serviços estão hard-coded no Feign:
  - `http://servico-adquirente:8081` (ideal para execução via Docker Compose, na mesma rede).

### 1.2 Tabela comparativa

| Versão | Objetivo | Resiliência | Dependências principais | Observabilidade |
|-------:|----------|-------------|-------------------------|----------------|
| v1 | Baseline (controle) | Sem CB/Retry | Spring Web, OpenFeign, Actuator | Health (Actuator) |
| v2 | Circuit Breaker (Resilience4j) | `@CircuitBreaker` + fallback (202) | Spring Cloud Circuit Breaker (Resilience4j), Micrometer Prometheus, AOP | Health + Circuit Breaker endpoints + métricas + Prometheus |
| v3 | Retry (Backoff Exponencial) | `@Retry` + fallback após esgotar tentativas | Resilience4j Retry, Micrometer Prometheus, AOP | Health + Retry endpoints + métricas + Prometheus |

---

## 2) API HTTP (comum às 3 versões)

### 2.1 Endpoint: `POST /pagar`

- Path: `/pagar`
- Método: `POST`
- Query params:
  - `modo`: controla o comportamento do adquirente
    - valores esperados: `normal`, `latencia`, `falha`
- Body: JSON (objeto) com chaves livres, mas com três campos esperados:
  - `amount` (número ou string)
  - `payment_method` (string)
  - `customer_id` (string)

Observação importante:

- O Controller recebe o body como `Map<String,Object>` e converte para `PaymentRequest`.
- Campos extras podem ser enviados; o DTO carrega tudo em `additionalData`.

#### Exemplo (curl)

```bash
curl -i -X POST "http://localhost:8080/pagar?modo=normal" \
  -H 'Content-Type: application/json' \
  -d '{
        "amount": 100.00,
        "payment_method": "credit_card",
        "customer_id": "customer-123",
        "order_id": "order-999"
      }'
```

### 2.2 Respostas e semântica por versão

#### v1 (baseline)

- **200 OK**: quando o adquirente responde sem erro 5xx.
- **500 Internal Server Error**: quando há erro 5xx ou exceção.

#### v2 (Circuit Breaker)

- **200 OK**: sucesso.
- **202 Accepted**: fallback **apenas** quando o Circuit Breaker está OPEN (`CallNotPermittedException`).
- **500 Internal Server Error**: erro do adquirente (5xx) ou exceção - falhas são **propagadas** para contabilizar no CB.

> [!IMPORTANT]
> Em v2, o fallback (202) só é acionado quando o circuito está **OPEN**. Antes de abrir, falhas são propagadas como 5xx (HTTP 500) para serem corretamente contabilizadas pelo Circuit Breaker.

#### v3 (Retry)

- **200 OK**: sucesso.
- **500 Internal Server Error**: falha final após esgotar retries.

> Em v3, o fallback só é chamado **após** as tentativas; não há “proteção rápida” como no Circuit Breaker.

---

## 3) DTOs (estrutura de dados)

### 3.1 `PaymentRequest`

Campos:

- `amount`: `BigDecimal`
- `paymentMethod`: `String`
- `customerId`: `String`
- `additionalData`: `Map<String,Object>`

Conversão a partir do body:

- `amount`: se ausente, vira `0`
- `payment_method`: default `"unknown"`
- `customer_id`: default `"anonymous"`

Payload sugerido:

```json
{
  "amount": 100.00,
  "payment_method": "credit_card",
  "customer_id": "customer-123"
}
```

### 3.2 `PaymentResponse`

#### v1

- `status`: `HttpStatus`
- `message`: `String`
- `outcome`: `SUCCESS | FAILURE`

#### v2/v3

- `status`: `HttpStatus`
- `message`: `String`
- `fallback`: `boolean`
- `outcome`: `SUCCESS | ACCEPTED_ASYNC | FAILURE | CIRCUIT_BREAKER_OPEN`

> Nota: o enum contém `CIRCUIT_BREAKER_OPEN` mesmo na v3 (Retry). Isso não impede a execução, mas a semântica desse outcome é “herdada” da v2.

---

## 4) Versão v1 — Baseline (sem resiliência)

### 4.1 Objetivo

A v1 serve como **grupo de controle**: implementação direta (ingênua), sem Circuit Breaker e sem Retry.

### 4.2 Classes principais

- Controller: services/payment-service-v1/src/main/java/br/ufpe/cin/tcc/pagamento/PagamentoController.java
- Service: services/payment-service-v1/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java
- Feign: services/payment-service-v1/src/main/java/br/ufpe/cin/tcc/pagamento/client/AdquirenteClient.java
- DTOs: services/payment-service-v1/src/main/java/br/ufpe/cin/tcc/pagamento/dto

### 4.3 Exemplo de código (fluxo principal)

Controller:

```java
@PostMapping(path = "/pagar")
public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                    @RequestBody Map<String, Object> pagamento) {
    PaymentRequest request = PaymentRequest.fromMap(pagamento);
    PaymentResponse response = paymentService.processPayment(modo, request);
    return ResponseEntity.status(response.status()).body(response.message());
}
```

Service (baseline):

- Faz uma chamada Feign
- Em 5xx retorna failure
- Em exceção retorna failure

```java
ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
if (response.getStatusCode().is5xxServerError()) {
    return PaymentResponse.failure("Erro do adquirente: " + response.getBody());
}
return PaymentResponse.success(response.getBody());
```

### 4.3.1 Exemplo de código (Feign Client)

O client Feign (v1) que integra com o adquirente:

```java
@FeignClient(name = "adquirente-client", url = "http://servico-adquirente:8081")
public interface AdquirenteClient {

  @PostMapping(path = "/autorizar")
  ResponseEntity<String> autorizarPagamento(@RequestParam("modo") String modo,
                        @RequestBody Map<String, Object> pagamento);
}
```

### 4.3.2 Exemplo de código (DTOs)

`PaymentRequest` (mapeia o `Map<String,Object>` do JSON):

```java
public record PaymentRequest(
  BigDecimal amount,
  String paymentMethod,
  String customerId,
  Map<String, Object> additionalData
) {
  public static PaymentRequest fromMap(Map<String, Object> map) {
    BigDecimal amount = map.get("amount") != null
      ? new BigDecimal(map.get("amount").toString())
      : BigDecimal.ZERO;
    String paymentMethod = (String) map.getOrDefault("payment_method", "unknown");
    String customerId = (String) map.getOrDefault("customer_id", "anonymous");

    return new PaymentRequest(amount, paymentMethod, customerId, map);
  }

  public Map<String, Object> toMap() {
    return additionalData != null ? additionalData : Map.of(
      "amount", amount,
      "payment_method", paymentMethod,
      "customer_id", customerId
    );
  }

`PaymentResponse` (v1):

```java
public record PaymentResponse(
  HttpStatus status,
  String message,
  PaymentOutcome outcome
) {
  public enum PaymentOutcome {
    SUCCESS,
    FAILURE
  }

  public static PaymentResponse success(String message) {
    return new PaymentResponse(HttpStatus.OK, message, PaymentOutcome.SUCCESS);
  }

  public static PaymentResponse failure(String message) {
    return new PaymentResponse(HttpStatus.INTERNAL_SERVER_ERROR, message, PaymentOutcome.FAILURE);
  }
}
```

### 4.4 Configuração

Arquivo: services/payment-service-v1/src/main/resources/application.yml

- Porta: `8080`
- Timeout Feign:
  - `connectTimeout: 2000`
  - `readTimeout: 2000`
- Actuator expõe apenas: `health`

Trecho do `application.yml` (v1):

```yaml
server:
  port: 8080

feign:
  client:
    config:
      default:
        connectTimeout: 2000
        readTimeout: 2000

management:
  endpoints:
    web:
      exposure:
        include: health
  endpoint:
    health:
      show-details: always
```

### 4.5 Observabilidade

Endpoints típicos:

- `GET /actuator/health`

Exemplo:

```bash
curl -s http://localhost:8080/actuator/health | jq
```

---

## 5) Versão v2 — Circuit Breaker (Resilience4j)

### 5.1 Objetivo

A v2 implementa **Circuit Breaker** para evitar falhas em cascata quando o adquirente degrada.

Características:

- `@CircuitBreaker(name = "adquirente-cb", fallbackMethod = "processPaymentFallback")`
- Fallback rápido quando o circuito está OPEN
- Métricas via Micrometer + Prometheus
- Logging com profile (dev legível / docker JSON)

### 5.2 Classes principais

- Controller: services/payment-service-v2/src/main/java/br/ufpe/cin/tcc/pagamento/PagamentoController.java
- Service (CB): services/payment-service-v2/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java
- Métricas (@Timed): services/payment-service-v2/src/main/java/br/ufpe/cin/tcc/pagamento/config/MetricsConfig.java
- Configuração CB: services/payment-service-v2/src/main/resources/application.yml
- Logging: services/payment-service-v2/src/main/resources/logback-spring.xml

### 5.3 Exemplo de código (Circuit Breaker + fallback)

Circuit Breaker no método:

```java
@CircuitBreaker(name = "adquirente-cb", fallbackMethod = "processPaymentFallback")
@Timed(value = "payment.processing.time")
public PaymentResponse processPayment(String modo, PaymentRequest request) {
    log.info("Processando pagamento [v2] - modo: {}, cliente: {}", modo, request.customerId());
    
    ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
    
    // Mapeamento de status: 5xx do adquirente -> lança exceção para contabilizar no CB
    if (response.getStatusCode().is5xxServerError()) {
      log.warn("Adquirente retornou 5xx. Mapeando para falha.");
        failureCounter.increment();
      throw new RuntimeException("Erro no serviço adquirente: " + response.getBody());
    }
    
    successCounter.increment();
    return PaymentResponse.success(response.getBody());
}
```

Fallback:

- Se `CallNotPermittedException` (circuito OPEN): responde 202 e outcome `CIRCUIT_BREAKER_OPEN`
- Para outras exceções: **propaga o erro** (5xx / HTTP 500) para contabilização correta no CB

```java
public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable throwable) {
    if (throwable instanceof CallNotPermittedException) {
        fallbackCounter.increment();
        log.info("Circuit Breaker OPEN - Fallback acionado para cliente: {}", request.customerId());
        return PaymentResponse.circuitBreakerOpen();
    }

    // Fora do cenário de circuito OPEN: propagar erro (5xx)
    // para refletir falhas reais antes da abertura do circuito.
    failureCounter.increment();
    log.warn("Falha propagada (sem fallback): {} - Cliente: {}", 
            throwable.getClass().getSimpleName(), request.customerId());

    if (throwable instanceof RuntimeException runtimeException) {
        throw runtimeException;
    }
    throw new RuntimeException(throwable);
}
```

> [!NOTE]
> **Mudança importante (v2.0.0):** O fallback retorna 202 quando o CB está OPEN. Antes de abrir, erros são propagados (5xx / HTTP 500) para garantir que o CB contabilize corretamente as falhas e abra no threshold configurado.

### 5.3.1 Exemplo de código (métricas customizadas)

Além de `@Timed`, a v2 cria contadores `payment.outcome` para medir o resultado lógico do pagamento:

```java
this.successCounter = Counter.builder("payment.outcome")
  .tag("result", "success")
  .description("Pagamentos processados com sucesso")
  .register(meterRegistry);

this.fallbackCounter = Counter.builder("payment.outcome")
  .tag("result", "fallback")
  .description("Pagamentos aceitos via fallback")
  .register(meterRegistry);

this.failureCounter = Counter.builder("payment.outcome")
  .tag("result", "failure")
  .description("Pagamentos que falharam")
  .register(meterRegistry);
```

### 5.4 Perfis de Circuit Breaker

A v2 define perfis no `application.yml` e usa variável de ambiente para ativá-los:

- `equilibrado` (default)
- `conservador`
- `agressivo`

No Docker Compose:

- serviço `servico-pagamento-v2` usa `SPRING_PROFILES_ACTIVE=${CB_PROFILE:-equilibrado}`.

Exemplo para subir com perfil agressivo:

```bash
CB_PROFILE=agressivo docker compose up --build servico-adquirente servico-pagamento-v2
```

#### 5.4.1 Trecho do `application.yml` (seleção de perfil)

```yaml
spring:
  profiles:
    active: ${CB_PROFILE:equilibrado}
```

#### 5.4.2 Trecho do `application.yml` (perfil `equilibrado`)

```yaml
resilience4j:
  circuitbreaker:
    instances:
      adquirente-cb:
        failureRateThreshold: 50
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 20
        minimumNumberOfCalls: 10
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 5
        slowCallDurationThreshold: 2000ms
        slowCallRateThreshold: 80
        automaticTransitionFromOpenToHalfOpenEnabled: true
```

#### 5.4.3 Trecho do `application.yml` (Actuator + Prometheus)

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,circuitbreakers,circuitbreakerevents,metrics,prometheus
  metrics:
    tags:
      application: payment-service-v2
      version: v2
      experiment: circuit-breaker-tcc
```

### 5.5 Observabilidade

A v2 expõe Actuator com endpoints adicionais:

- `GET /actuator/health`
- `GET /actuator/metrics`
- `GET /actuator/prometheus`
- `GET /actuator/circuitbreakers`
- `GET /actuator/circuitbreakerevents`

Exemplo:

```bash
curl -s http://localhost:8082/actuator/circuitbreakers | jq
curl -s http://localhost:8082/actuator/prometheus | head
```

### 5.5.1 Exemplo de logging (logback-spring.xml)

Em `docker/prod`, a v2 usa logs estruturados em JSON (Logstash Encoder). Trecho:

```xml
<appender name="CONSOLE_JSON" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LogstashEncoder">
    <customFields>{"service":"${appName}","version":"${appVersion}","experiment":"circuit-breaker-tcc"}</customFields>
    <timestampPattern>yyyy-MM-dd'T'HH:mm:ss.SSSZ</timestampPattern>
  </encoder>
</appender>
```

### 5.6 Métricas customizadas do experimento

A v2 registra contadores em `payment.outcome` com tags:

- `result=success`
- `result=failure`
- `result=fallback`

Exemplo de consulta via Prometheus:

- `payment_outcome_total{result="fallback"}`

### 5.7 Testes

- Unit tests: `PaymentServiceTest`
- Integração (WireMock + transições do CB): `CircuitBreakerIntegrationTest`

Com Maven (na pasta do serviço):

```bash
cd services/payment-service-v2
mvn test
```

---

## 6) Versão v3 — Retry com Backoff Exponencial (Resilience4j)

### 6.1 Objetivo

A v3 implementa **Retry com backoff exponencial** (sem Circuit Breaker), para comparar o efeito de retries em cenários de latência e falha.

Características:

- `@Retry(name = "adquirente-retry", fallbackMethod = "processPaymentFallback")`
- Re-tenta em exceções configuradas
- Backoff exponencial: 500ms → 1000ms → 2000ms (com aleatoriedade)
- Métricas via Micrometer + Prometheus
- Logging estruturado (logback-spring.xml)

### 6.2 Classes principais

- Controller: services/payment-service-v3/src/main/java/br/ufpe/cin/tcc/pagamento/PagamentoController.java
- Service (Retry): services/payment-service-v3/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java
- Métricas (@Timed): services/payment-service-v3/src/main/java/br/ufpe/cin/tcc/pagamento/config/MetricsConfig.java
- Configuração Retry: services/payment-service-v3/src/main/resources/application.yml
- Logging: services/payment-service-v3/src/main/resources/logback-spring.xml

### 6.3 Exemplo de código (Retry)

Retry no método:

```java
@Retry(name = "adquirente-retry", fallbackMethod = "processPaymentFallback")
@Timed(value = "payment.processing.time")
public PaymentResponse processPayment(String modo, PaymentRequest request) {
    ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());

    if (response.getStatusCode() == HttpStatus.SERVICE_UNAVAILABLE) {
        throw new RuntimeException("Serviço adquirente indisponível: " + response.getBody());
    }

    if (response.getStatusCode().is5xxServerError()) {
        throw new RuntimeException("Erro no serviço adquirente: " + response.getBody());
    }

    return PaymentResponse.success(response.getBody());
}
```

Fallback final (após esgotar tentativas):

```java
public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable t) {
    return PaymentResponse.failure("Pagamento falhou após múltiplas tentativas: " + t.getMessage());
}
```

### 6.3.1 Exemplo de código (métricas de retry)

A v3 registra `payment.outcome` com `result=retry` para observar quantas chamadas precisaram de nova tentativa:

```java
this.retryCounter = Counter.builder("payment.outcome")
  .tag("result", "retry")
  .description("Pagamentos que precisaram de retry")
  .register(meterRegistry);
```

### 6.4 Configuração do Retry

Arquivo: services/payment-service-v3/src/main/resources/application.yml

- `maxAttempts: 3`
- `waitDuration: 500ms`
- `enableExponentialBackoff: true`
- `exponentialBackoffMultiplier: 2`
- `enableRandomizedWait: true`
- `randomizedWaitFactor: 0.5`

Trecho do `application.yml` (v3):

```yaml
resilience4j:
  retry:
    instances:
      adquirente-retry:
        maxAttempts: 3
        waitDuration: 500ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
        enableRandomizedWait: true
        randomizedWaitFactor: 0.5
        retryExceptions:
          - java.net.SocketTimeoutException
          - java.net.ConnectException
          - java.io.IOException
          - feign.FeignException$ServiceUnavailable
          - feign.FeignException$InternalServerError
```

Trecho do Actuator + Prometheus (v3):

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,retries,retryevents,metrics,prometheus
  metrics:
    tags:
      application: payment-service-v3
      version: v3
      experiment: retry-tcc
```

Exemplo (Prometheus endpoint):

```bash
curl -s http://localhost:8083/actuator/prometheus | head
```

### 6.5 Observabilidade

A v3 expõe endpoints relacionados a retry:

- `GET /actuator/retries`
- `GET /actuator/retryevents`

### 6.5.1 Exemplo de logging (logback-spring.xml)

A v3 também usa Logstash Encoder para logs JSON em `docker/prod`. Trecho:

```xml
<appender name="CONSOLE_JSON" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LogstashEncoder">
    <customFields>{"service":"${appName}","version":"${appVersion}"}</customFields>
    <timestampPattern>yyyy-MM-dd'T'HH:mm:ss.SSSZ</timestampPattern>
  </encoder>
</appender>
```

### 6.6 Testes

Existe um teste unitário em:

- services/payment-service-v3/src/test/java/br/ufpe/cin/tcc/pagamento/service/PaymentServiceTest.java

Execução:

```bash
cd services/payment-service-v3
mvn test
```

---

## 7) Exemplos de consumo (clientes)

### 7.1 Exemplo (curl) — cenários do experimento

Normal:

```bash
curl -i -X POST "http://localhost:8082/pagar?modo=normal" \
  -H 'Content-Type: application/json' \
  -d '{"amount": 42.00, "payment_method": "pix", "customer_id": "c-1"}'
```

Falha (forçando comportamento do adquirente):

```bash
curl -i -X POST "http://localhost:8082/pagar?modo=falha" \
  -H 'Content-Type: application/json' \
  -d '{"amount": 42.00, "payment_method": "pix", "customer_id": "c-2"}'
```

Latência:

```bash
curl -i -X POST "http://localhost:8083/pagar?modo=latencia" \
  -H 'Content-Type: application/json' \
  -d '{"amount": 10.00, "payment_method": "boleto", "customer_id": "c-3"}'
```

### 7.2 Exemplo (Java/Spring) — cliente HTTP simples

Se você quiser chamar o serviço de pagamento de outro serviço Spring:

```java
public class PaymentClient {
  private final RestClient rest;

  public PaymentClient(RestClient.Builder builder) {
    this.rest = builder.baseUrl("http://localhost:8080").build();
  }

  public String pagarNormal() {
    Map<String, Object> body = Map.of(
      "amount", 100.0,
      "payment_method", "credit_card",
      "customer_id", "customer-123"
    );

    return rest.post()
      .uri(uriBuilder -> uriBuilder.path("/pagar").queryParam("modo", "normal").build())
      .body(body)
      .retrieve()
      .body(String.class);
  }
}
```

---

## 8) Execução via Docker Compose (recomendado)

O [docker-compose.yml](../docker-compose.yml) já define:

- `servico-adquirente` na porta **8081** (host)
- `servico-pagamento` (variável `PAYMENT_SERVICE_VERSION`) na porta **8080** (host)
- `servico-pagamento-v2` na porta **8082** (host)
- `servico-pagamento-v3` na porta **8083** (host)

Trecho do `docker-compose.yml` (mapeamento de portas):

```yaml
  servico-pagamento-v2:
    ports:
      - "8082:8080"

  servico-pagamento-v3:
    ports:
      - "8083:8080"
```

### 8.1 Subir v1 (usando serviço genérico `servico-pagamento`)

```bash
PAYMENT_SERVICE_VERSION=v1 docker compose up --build servico-adquirente servico-pagamento
```

### 8.2 Subir v2 (Circuit Breaker)

```bash
CB_PROFILE=equilibrado docker compose up --build servico-adquirente servico-pagamento-v2
```

### 8.3 Subir v3 (Retry)

```bash
docker compose up --build servico-adquirente servico-pagamento-v3
```

---

## 9) Referências rápidas de código

- v1 Controller: services/payment-service-v1/src/main/java/br/ufpe/cin/tcc/pagamento/PagamentoController.java
- v1 Service: services/payment-service-v1/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java

- v2 Service (Circuit Breaker): services/payment-service-v2/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java
- v2 Config (CB profiles): services/payment-service-v2/src/main/resources/application.yml

- v3 Service (Retry): services/payment-service-v3/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java
- v3 Config (Retry): services/payment-service-v3/src/main/resources/application.yml
