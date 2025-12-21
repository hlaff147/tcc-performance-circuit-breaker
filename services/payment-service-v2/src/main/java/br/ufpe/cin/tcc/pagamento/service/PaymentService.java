package br.ufpe.cin.tcc.pagamento.service;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
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
 * Encapsula a lógica de negócio e integração com o Circuit Breaker.
 * 
 * Esta classe implementa o padrão Circuit Breaker usando Resilience4j
 * para proteger o sistema contra falhas em cascata quando o serviço
 * adquirente está indisponível.
 */
@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);
    private static final String CIRCUIT_BREAKER_NAME = "adquirente-cb";

    private final AdquirenteClient acquirerClient;
    private final Counter successCounter;
    private final Counter fallbackCounter;
    private final Counter failureCounter;

    public PaymentService(AdquirenteClient acquirerClient, MeterRegistry meterRegistry) {
        this.acquirerClient = acquirerClient;
        
        // Métricas customizadas para análise detalhada
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
    }

    /**
     * Processa um pagamento chamando o serviço adquirente.
     * 
     * O Circuit Breaker monitora as chamadas e:
     * - CLOSED: Permite todas as chamadas, monitorando falhas
     * - OPEN: Bloqueia chamadas e aciona fallback imediatamente
     * - HALF_OPEN: Permite chamadas de teste para verificar recuperação
     *
     * @param modo Modo de operação (normal, latencia, falha)
     * @param request Dados do pagamento
     * @return PaymentResponse com o resultado do processamento
     */
    @CircuitBreaker(name = CIRCUIT_BREAKER_NAME, fallbackMethod = "processPaymentFallback")
    @Timed(value = "payment.processing.time", description = "Tempo de processamento de pagamento")
    public PaymentResponse processPayment(String modo, PaymentRequest request) {
        log.info("Processando pagamento [v2] - modo: {}, cliente: {}", modo, request.customerId());
        
        long startTime = System.currentTimeMillis();
        
        try {
            ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
            long duration = System.currentTimeMillis() - startTime;
            
            // Mapeamento de status: 503 do adquirente -> falha interna para contabilizar no CB
            if (response.getStatusCode() == HttpStatus.SERVICE_UNAVAILABLE) {
                log.warn("Adquirente retornou 503. Mapeando para falha. Duração: {}ms", duration);
                failureCounter.increment();
                throw new RuntimeException("Serviço adquirente indisponível: " + response.getBody());
            }
            
            log.info("Pagamento processado com sucesso. Status: {}, Duração: {}ms", 
                    response.getStatusCode(), duration);
            successCounter.increment();
            return PaymentResponse.success(response.getBody());
            
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("Erro ao processar pagamento. Duração: {}ms, Erro: {}", duration, e.getMessage());
            // Re-lança para que o CB contabilize a falha
            throw e;
        }
    }

    /**
     * Método de fallback acionado quando:
     * 1. O Circuit Breaker está OPEN (CallNotPermittedException)
     * 2. Uma exceção ocorre durante a chamada ao adquirente
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
        if (throwable instanceof CallNotPermittedException) {
            fallbackCounter.increment();
            log.info("Circuit Breaker OPEN - Fallback acionado para cliente: {}", request.customerId());
            return PaymentResponse.circuitBreakerOpen();
        }

        // Fora do cenário de circuito OPEN, não degradar para 202: propagar erro (5xx)
        // para refletir falhas reais antes da abertura do circuito.
        failureCounter.increment();
        log.warn("Falha propagada (sem fallback): {} - Cliente: {}", 
                throwable.getClass().getSimpleName(), request.customerId());

        if (throwable instanceof RuntimeException runtimeException) {
            throw runtimeException;
        }
        throw new RuntimeException(throwable);
    }
}
