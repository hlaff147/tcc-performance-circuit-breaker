package br.ufpe.cin.tcc.pagamento.dto;

import org.springframework.http.HttpStatus;

/**
 * DTO representando a resposta de um processamento de pagamento.
 * Inclui informações sobre o status e se foi um fallback.
 */
public record PaymentResponse(
    HttpStatus status,
    String message,
    boolean fallback,
    PaymentOutcome outcome
) {
    /**
     * Enum representando os possíveis resultados do processamento.
     */
    public enum PaymentOutcome {
        /** Pagamento processado com sucesso pelo adquirente */
        SUCCESS,
        /** Pagamento aceito para processamento assíncrono (fallback ativo) */
        ACCEPTED_ASYNC,
        /** Falha no processamento */
        FAILURE,
        /** Circuit Breaker aberto - requisição não foi enviada */
        CIRCUIT_BREAKER_OPEN
    }
    
    /**
     * Cria uma resposta de sucesso.
     */
    public static PaymentResponse success(String message) {
        return new PaymentResponse(HttpStatus.OK, message, false, PaymentOutcome.SUCCESS);
    }
    
    /**
     * Cria uma resposta de fallback (Circuit Breaker ativo).
     */
    public static PaymentResponse fallback(String message) {
        return new PaymentResponse(HttpStatus.ACCEPTED, message, true, PaymentOutcome.ACCEPTED_ASYNC);
    }
    
    /**
     * Cria uma resposta de Circuit Breaker aberto.
     */
    public static PaymentResponse circuitBreakerOpen() {
        return new PaymentResponse(
            HttpStatus.ACCEPTED, 
            "Pagamento aceito para processamento assíncrono (Circuit Breaker ativo)", 
            true, 
            PaymentOutcome.CIRCUIT_BREAKER_OPEN
        );
    }
    
    /**
     * Cria uma resposta de falha.
     */
    public static PaymentResponse failure(String message) {
        return new PaymentResponse(HttpStatus.INTERNAL_SERVER_ERROR, message, false, PaymentOutcome.FAILURE);
    }
}
