package br.ufpe.cin.tcc.pagamento.service;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import io.github.resilience4j.retry.annotation.Retry;
import io.micrometer.core.annotation.Timed;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * Serviço responsável pelo processamento de pagamentos.
 * 
 * Versão V3 (RETRY-ONLY): Implementação com Retry mas SEM Circuit Breaker.
 * Esta implementação serve para comparação experimental com a versão V2 (CB).
 * 
 * Características:
 * - Retry com backoff exponencial e jitter
 * - Fallback após esgotar tentativas
 * - Métricas de retry expostas via Prometheus
 * - Sem proteção de Circuit Breaker (pode amplificar carga downstream)
 */
@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);
    private static final String RETRY_NAME = "adquirente-retry";

    private final AdquirenteClient acquirerClient;
    private final Counter successCounter;
    private final Counter successAfterRetryCounter;
    private final Counter fallbackCounter;
    private final Counter failureCounter;
    private final Counter retryAttemptCounter;
    
    // ThreadLocal para rastrear tentativas por request
    private final ThreadLocal<AtomicInteger> attemptTracker = ThreadLocal.withInitial(() -> new AtomicInteger(0));

    public PaymentService(AdquirenteClient acquirerClient, MeterRegistry meterRegistry) {
        this.acquirerClient = acquirerClient;
        
        // Métricas customizadas para análise detalhada
        this.successCounter = Counter.builder("payment.outcome")
            .tag("result", "success")
            .tag("version", "v3")
            .description("Pagamentos processados com sucesso (primeira tentativa)")
            .register(meterRegistry);
            
        this.successAfterRetryCounter = Counter.builder("payment.outcome")
            .tag("result", "success_after_retry")
            .tag("version", "v3")
            .description("Pagamentos processados com sucesso após retry")
            .register(meterRegistry);
            
        this.fallbackCounter = Counter.builder("payment.outcome")
            .tag("result", "fallback")
            .tag("version", "v3")
            .description("Pagamentos aceitos via fallback (após esgotar retries)")
            .register(meterRegistry);
            
        this.failureCounter = Counter.builder("payment.outcome")
            .tag("result", "failure")
            .tag("version", "v3")
            .description("Pagamentos que falharam")
            .register(meterRegistry);
            
        this.retryAttemptCounter = Counter.builder("payment.retry.attempts")
            .tag("version", "v3")
            .description("Total de tentativas de retry realizadas")
            .register(meterRegistry);
    }

    /**
     * Processa um pagamento chamando o serviço adquirente.
     * 
     * O Retry monitora as chamadas e:
     * - Tentativa 1: Chamada original
     * - Tentativa 2+: Retries com backoff exponencial
     * - Após maxAttempts: Fallback
     * 
     * ATENÇÃO: Diferente do Circuit Breaker, o Retry NÃO protege contra
     * indisponibilidade prolongada. Cada request gerará até maxAttempts
     * chamadas ao downstream, podendo amplificar a carga.
     *
     * @param modo Modo de operação (normal, latencia, falha)
     * @param request Dados do pagamento
     * @return PaymentResponse com o resultado do processamento
     */
    @Retry(name = RETRY_NAME, fallbackMethod = "processPaymentFallback")
    @Timed(value = "payment.processing.time", description = "Tempo de processamento de pagamento")
    public PaymentResponse processPayment(String modo, PaymentRequest request) {
        int currentAttempt = attemptTracker.get().incrementAndGet();
        
        log.info("Processando pagamento [v3-retry] - modo: {}, cliente: {}, tentativa: {}", 
                modo, request.customerId(), currentAttempt);
        
        if (currentAttempt > 1) {
            retryAttemptCounter.increment();
        }
        
        long startTime = System.currentTimeMillis();
        
        try {
            ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
            long duration = System.currentTimeMillis() - startTime;
            
            // Mapeamento de status: 5xx do adquirente -> exceção para disparar retry
            if (response.getStatusCode().is5xxServerError()) {
                log.warn("Adquirente retornou {}. Disparando retry. Duração: {}ms, Tentativa: {}", 
                        response.getStatusCode(), duration, currentAttempt);
                // Lança exceção para que o Retry contabilize a falha e tente novamente
                throw new AcquirerServiceException("Serviço adquirente retornou erro: " + response.getStatusCode());
            }
            
            log.info("Pagamento processado com sucesso. Status: {}, Duração: {}ms, Tentativa: {}", 
                    response.getStatusCode(), duration, currentAttempt);
            
            // Sucesso - registrar métrica apropriada
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
            // Re-lança para que o Retry capture e tente novamente
            throw e;
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("Erro ao processar pagamento. Duração: {}ms, Tentativa: {}, Erro: {}", 
                    duration, currentAttempt, e.getMessage());
            // Re-lança para que o Retry contabilize a falha
            throw new RuntimeException("Erro ao processar pagamento: " + e.getMessage(), e);
        }
    }

    /**
     * Método de fallback acionado quando todas as tentativas de retry foram esgotadas.
     * 
     * Implementa degradação graciosa retornando HTTP 202 (Accepted),
     * indicando que o pagamento será processado posteriormente.
     *
     * @param modo Modo de operação original
     * @param request Dados do pagamento
     * @param throwable Exceção que causou o fallback
     * @return PaymentResponse com status de fallback
     */
    public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable throwable) {
        int attempts = attemptTracker.get().get();
        resetAttemptTracker();
        
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
    
    /**
     * Exceção customizada para erros do serviço adquirente.
     * Usada para diferenciar erros que devem disparar retry.
     */
    public static class AcquirerServiceException extends RuntimeException {
        public AcquirerServiceException(String message) {
            super(message);
        }
    }
}
