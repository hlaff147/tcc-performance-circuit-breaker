package br.ufpe.cin.tcc.pagamento.dto;

import org.springframework.http.HttpStatus;

/**
 * DTO representando a resposta de um processamento de pagamento.
 * 
 * Versão V4 - Inclui outcomes para CB + Retry combinados.
 */
public record PaymentResponse(
    HttpStatus status,
    String message,
    boolean fallback,
    PaymentOutcome outcome
) {
    public enum PaymentOutcome {
        SUCCESS,
        SUCCESS_AFTER_RETRY,
        ACCEPTED_ASYNC,
        FAILURE_AFTER_RETRY,
        FAILURE,
        CIRCUIT_BREAKER_OPEN
    }
    
    public static PaymentResponse success(String message) {
        return new PaymentResponse(HttpStatus.OK, message, false, PaymentOutcome.SUCCESS);
    }
    
    public static PaymentResponse successAfterRetry(String message, int attempts) {
        return new PaymentResponse(
            HttpStatus.OK, 
            message + " (após " + attempts + " tentativa(s))", 
            false, 
            PaymentOutcome.SUCCESS_AFTER_RETRY
        );
    }
    
    public static PaymentResponse fallback(String message) {
        return new PaymentResponse(HttpStatus.ACCEPTED, message, true, PaymentOutcome.ACCEPTED_ASYNC);
    }
    
    public static PaymentResponse circuitBreakerOpen() {
        return new PaymentResponse(
            HttpStatus.ACCEPTED, 
            "Pagamento aceito para processamento assíncrono (Circuit Breaker ativo)", 
            true, 
            PaymentOutcome.CIRCUIT_BREAKER_OPEN
        );
    }
    
    public static PaymentResponse failureAfterRetry(String message) {
        return new PaymentResponse(
            HttpStatus.INTERNAL_SERVER_ERROR, 
            message, 
            false, 
            PaymentOutcome.FAILURE_AFTER_RETRY
        );
    }
    
    public static PaymentResponse failure(String message) {
        return new PaymentResponse(HttpStatus.INTERNAL_SERVER_ERROR, message, false, PaymentOutcome.FAILURE);
    }
}
