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

/**
 * Serviço responsável pelo processamento de pagamentos.
 * Versão V3: Implementa padrão Retry com Backoff Exponencial.
 * 
 * Esta versão NÃO usa Circuit Breaker, apenas Retry para comparação
 * de estratégias de resiliência no TCC.
 * 
 * Comportamento esperado:
 * - Em falhas transitórias: retry com backoff ajuda
 * - Em falhas catastróficas: retry amplifica o problema (3x mais carga)
 */
@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);
    private static final String RETRY_NAME = "adquirente-retry";

    private final AdquirenteClient acquirerClient;
    private final Counter successCounter;
    private final Counter retryCounter;
    private final Counter failureCounter;

    public PaymentService(AdquirenteClient acquirerClient, MeterRegistry meterRegistry) {
        this.acquirerClient = acquirerClient;
        
        // Métricas customizadas para análise detalhada
        this.successCounter = Counter.builder("payment.outcome")
            .tag("result", "success")
            .description("Pagamentos processados com sucesso")
            .register(meterRegistry);
            
        this.retryCounter = Counter.builder("payment.outcome")
            .tag("result", "retry")
            .description("Pagamentos que precisaram de retry")
            .register(meterRegistry);
            
        this.failureCounter = Counter.builder("payment.outcome")
            .tag("result", "failure")
            .description("Pagamentos que falharam após todos os retries")
            .register(meterRegistry);
    }

    /**
     * Processa um pagamento chamando o serviço adquirente.
     * 
     * O Retry com Backoff Exponencial:
     * - Tenta até 3 vezes
     * - Intervalo inicial: 500ms
     * - Multiplica por 2 a cada tentativa: 500ms -> 1000ms -> 2000ms
     * - Adiciona variação aleatória (±50%) para evitar thundering herd
     *
     * @param modo Modo de operação (normal, latencia, falha)
     * @param request Dados do pagamento
     * @return PaymentResponse com o resultado do processamento
     */
    @Retry(name = RETRY_NAME, fallbackMethod = "processPaymentFallback")
    @Timed(value = "payment.processing.time", description = "Tempo de processamento de pagamento")
    public PaymentResponse processPayment(String modo, PaymentRequest request) {
        log.info("Processando pagamento [v3-retry] - modo: {}, cliente: {}", modo, request.customerId());
        
        long startTime = System.currentTimeMillis();
        
        try {
            ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
            long duration = System.currentTimeMillis() - startTime;
            
            // Mapeamento de status: 503 do adquirente -> falha para retry
            if (response.getStatusCode() == HttpStatus.SERVICE_UNAVAILABLE) {
                log.warn("Adquirente retornou 503. Lançando exceção para retry. Duração: {}ms", duration);
                throw new RuntimeException("Serviço adquirente indisponível: " + response.getBody());
            }
            
            // Mapeamento de status: 500 do adquirente -> falha para retry
            if (response.getStatusCode().is5xxServerError()) {
                log.warn("Adquirente retornou {}. Lançando exceção para retry. Duração: {}ms", 
                        response.getStatusCode(), duration);
                throw new RuntimeException("Erro no serviço adquirente: " + response.getBody());
            }
            
            log.info("Pagamento processado com sucesso. Status: {}, Duração: {}ms", 
                    response.getStatusCode(), duration);
            successCounter.increment();
            return PaymentResponse.success(response.getBody());
            
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.warn("Tentativa falhou após {}ms. Erro: {} - Retry será acionado", duration, e.getMessage());
            retryCounter.increment();
            // Re-lança para que o Retry tente novamente
            throw e;
        }
    }

    /**
     * Método de fallback acionado quando todos os retries falharam.
     * 
     * Diferente do CB, este fallback só é chamado após ESGOTAR todas as tentativas.
     * Não oferece proteção rápida como o Circuit Breaker.
     *
     * @param modo Modo de operação original
     * @param request Dados do pagamento
     * @param throwable Exceção que causou a falha final
     * @return PaymentResponse com status de falha
     */
    public PaymentResponse processPaymentFallback(String modo, PaymentRequest request, Throwable throwable) {
        failureCounter.increment();
        
        log.error("Fallback V3: Todos os {} retries falharam para cliente: {}. Erro: {}", 
                3, request.customerId(), throwable.getMessage());
        
        // V3 não tem fallback gracioso como V2 (CB)
        // Retorna falha porque não há proteção de circuito
        return PaymentResponse.failure(
            "Pagamento falhou após múltiplas tentativas: " + throwable.getMessage()
        );
    }
}
