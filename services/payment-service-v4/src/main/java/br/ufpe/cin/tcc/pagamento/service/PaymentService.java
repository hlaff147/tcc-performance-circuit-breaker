package br.ufpe.cin.tcc.pagamento.service;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.micrometer.core.annotation.Timed;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

/**
 * Serviço responsável pelo processamento de pagamentos.
 * Versão V4: Implementa Composição de Resiliência (Retry + Circuit Breaker).
 * 
 * Esta versão combina o melhor dos dois mundos:
 * 1. Retry: Tenta resolver falhas transitórias (ex: oscilação de rede).
 * 2. Circuit Breaker: Interrompe chamadas em falhas persistentes, protegendo o
 * sistema.
 * 
 * A ordem de precedência no Resilience4j (aspect order) é importante:
 * Normalmente Retry envolve Circuit Breaker.
 */
@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);
    private static final String CIRCUIT_BREAKER_NAME = "adquirente-cb";
    private static final String RETRY_NAME = "adquirente-retry";

    private final AdquirenteClient acquirerClient;
    private final Counter directSuccessCounter;
    private final Counter retrySuccessCounter;
    private final Counter fallbackCounter;
    private final Counter failureCounter;

    public PaymentService(AdquirenteClient acquirerClient, MeterRegistry meterRegistry) {
        this.acquirerClient = acquirerClient;

        // Métricas granulares para análise de eficácia
        this.directSuccessCounter = Counter.builder("payment.outcome")
                .tag("result", "direct_success")
                .description("Sucesso na primeira tentativa")
                .register(meterRegistry);

        this.retrySuccessCounter = Counter.builder("payment.outcome")
                .tag("result", "retry_success")
                .description("Sucesso após retry")
                .register(meterRegistry);

        this.fallbackCounter = Counter.builder("payment.outcome")
                .tag("result", "fallback")
                .description("Pagamentos aceitos via fallback (CB Open)")
                .register(meterRegistry);

        this.failureCounter = Counter.builder("payment.outcome")
                .tag("result", "failure")
                .description("Pagamentos que falharam definitivamente")
                .register(meterRegistry);
    }

    /**
     * Processa um pagamento com Retry e Circuit Breaker.
     */
    @Retry(name = RETRY_NAME)
    @CircuitBreaker(name = CIRCUIT_BREAKER_NAME, fallbackMethod = "processPaymentFallback")
    @Timed(value = "payment.processing.time", description = "Tempo de processamento de pagamento")
    public PaymentResponse processPayment(String modo, PaymentRequest request) {
        log.info("Processando pagamento [v4-composition] - modo: {}, cliente: {}", modo, request.customerId());

        long startTime = System.currentTimeMillis();

        try {
            ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
            long duration = System.currentTimeMillis() - startTime;

            if (response.getStatusCode().is5xxServerError()) {
                log.warn("Adquirente retornou {}. Lançando exceção para resiliência. Duração: {}ms",
                        response.getStatusCode(), duration);
                throw new RuntimeException("Erro no serviço adquirente: " + response.getBody());
            }

            log.info("Pagamento processado com sucesso. Duração: {}ms", duration);

            // Lógica simples para diferenciar sucesso direto vs retry (pode ser refinada
            // com interceptors)
            directSuccessCounter.increment();
            return PaymentResponse.success(response.getBody());

        } catch (Exception e) {
            log.error("Tentativa falhou: {}", e.getMessage());
            throw e;
        }
    }

    /**
     * Fallback acionado quando o CB está OPEN ou após esgotar retries se o CB não
     * abrir.
     */
    public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable throwable) {
        if (throwable instanceof CallNotPermittedException) {
            fallbackCounter.increment();
            log.info("Resilience Composition: Circuit Breaker OPEN - Fallback para cliente: {}", request.customerId());
            return PaymentResponse.circuitBreakerOpen();
        }

        failureCounter.increment();
        log.error("Resilience Composition: Falha definitiva após retries/CB. Erro: {}", throwable.getMessage());
        return PaymentResponse.failure("Falha no processamento: " + throwable.getMessage());
    }
}
