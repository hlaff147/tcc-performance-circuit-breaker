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
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * Serviço responsável pelo processamento de pagamentos.
 * 
 * Versão V4 (CB + RETRY): Implementação com AMBOS os padrões combinados.
 * 
 * ORDEM DOS DECORADORES (importante!):
 * 1. CircuitBreaker (mais externo) - avalia primeiro se pode prosseguir
 * 2. Retry (mais interno) - só executa se CB permitir
 * 
 * Comportamento:
 * - CB CLOSED: Retry funciona normalmente (até maxAttempts)
 * - CB OPEN: Fallback imediato, Retry NÃO é executado
 * - CB HALF_OPEN: Retry pode ajudar na validação de recuperação
 * 
 * Esta implementação testa a hipótese H3: combinação pode superar isolados.
 */
@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);
    private static final String CIRCUIT_BREAKER_NAME = "adquirente-cb";
    private static final String RETRY_NAME = "adquirente-retry";

    private final AdquirenteClient acquirerClient;
    private final Counter successCounter;
    private final Counter successAfterRetryCounter;
    private final Counter fallbackCounter;
    private final Counter cbOpenCounter;
    private final Counter failureCounter;
    private final Counter retryAttemptCounter;
    
    private final ThreadLocal<AtomicInteger> attemptTracker = ThreadLocal.withInitial(() -> new AtomicInteger(0));

    public PaymentService(AdquirenteClient acquirerClient, MeterRegistry meterRegistry) {
        this.acquirerClient = acquirerClient;
        
        this.successCounter = Counter.builder("payment.outcome")
            .tag("result", "success")
            .tag("version", "v4")
            .description("Pagamentos com sucesso (primeira tentativa)")
            .register(meterRegistry);
            
        this.successAfterRetryCounter = Counter.builder("payment.outcome")
            .tag("result", "success_after_retry")
            .tag("version", "v4")
            .description("Pagamentos com sucesso após retry")
            .register(meterRegistry);
            
        this.fallbackCounter = Counter.builder("payment.outcome")
            .tag("result", "fallback")
            .tag("version", "v4")
            .description("Pagamentos via fallback (após esgotar retries)")
            .register(meterRegistry);
            
        this.cbOpenCounter = Counter.builder("payment.outcome")
            .tag("result", "circuit_breaker_open")
            .tag("version", "v4")
            .description("Pagamentos bloqueados por CB aberto")
            .register(meterRegistry);
            
        this.failureCounter = Counter.builder("payment.outcome")
            .tag("result", "failure")
            .tag("version", "v4")
            .description("Pagamentos que falharam")
            .register(meterRegistry);
            
        this.retryAttemptCounter = Counter.builder("payment.retry.attempts")
            .tag("version", "v4")
            .description("Total de tentativas de retry realizadas")
            .register(meterRegistry);
    }

    /**
     * Processa um pagamento com Circuit Breaker + Retry combinados.
     * 
     * A ordem das anotações define a ordem de execução:
     * @CircuitBreaker (externo) -> @Retry (interno)
     * 
     * Isso significa que o CB avalia primeiro se a chamada é permitida.
     * Se permitida, o Retry pode executar até maxAttempts tentativas.
     */
    @CircuitBreaker(name = CIRCUIT_BREAKER_NAME, fallbackMethod = "processPaymentFallback")
    @Retry(name = RETRY_NAME)
    @Timed(value = "payment.processing.time", description = "Tempo de processamento de pagamento")
    public PaymentResponse processPayment(String modo, PaymentRequest request) {
        int currentAttempt = attemptTracker.get().incrementAndGet();
        
        log.info("Processando pagamento [v4-cb+retry] - modo: {}, cliente: {}, tentativa: {}", 
                modo, request.customerId(), currentAttempt);
        
        if (currentAttempt > 1) {
            retryAttemptCounter.increment();
        }
        
        long startTime = System.currentTimeMillis();
        
        try {
            ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
            long duration = System.currentTimeMillis() - startTime;
            
            if (response.getStatusCode().is5xxServerError()) {
                log.warn("Adquirente retornou {}. Disparando retry. Duração: {}ms, Tentativa: {}", 
                        response.getStatusCode(), duration, currentAttempt);
                throw new AcquirerServiceException("Serviço adquirente retornou erro: " + response.getStatusCode());
            }
            
            log.info("Pagamento processado com sucesso. Status: {}, Duração: {}ms, Tentativa: {}", 
                    response.getStatusCode(), duration, currentAttempt);
            
            if (currentAttempt == 1) {
                successCounter.increment();
                resetAttemptTracker();
                return PaymentResponse.success(response.getBody());
            } else {
                successAfterRetryCounter.increment();
                int attempts = currentAttempt;
                resetAttemptTracker();
                return PaymentResponse.successAfterRetry(response.getBody(), attempts);
            }
            
        } catch (AcquirerServiceException e) {
            throw e;
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("Erro ao processar pagamento. Duração: {}ms, Tentativa: {}, Erro: {}", 
                    duration, currentAttempt, e.getMessage());
            throw new RuntimeException("Erro ao processar pagamento: " + e.getMessage(), e);
        }
    }

    /**
     * Fallback unificado para CB aberto e retries esgotados.
     */
    public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable throwable) {
        int attempts = attemptTracker.get().get();
        resetAttemptTracker();
        
        if (throwable instanceof CallNotPermittedException) {
            cbOpenCounter.increment();
            log.info("Circuit Breaker OPEN - Fallback imediato para cliente: {}", request.customerId());
            return PaymentResponse.circuitBreakerOpen();
        }
        
        fallbackCounter.increment();
        log.warn("Fallback acionado após {} tentativas. Erro: {} - Cliente: {}", 
                attempts, throwable.getClass().getSimpleName(), request.customerId());
        
        return PaymentResponse.fallback(
            "Pagamento aceito para processamento posterior após " + attempts + " tentativa(s). " +
            "Motivo: " + throwable.getMessage()
        );
    }
    
    private void resetAttemptTracker() {
        attemptTracker.get().set(0);
        attemptTracker.remove();  // Previne memory leak em thread pools
    }
    
    public static class AcquirerServiceException extends RuntimeException {
        public AcquirerServiceException(String message) {
            super(message);
        }
    }
}
