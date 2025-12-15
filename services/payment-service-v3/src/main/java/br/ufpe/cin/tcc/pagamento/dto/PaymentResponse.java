package br.ufpe.cin.tcc.pagamento.dto;

import org.springframework.http.HttpStatus;

/**
 * DTO representando a resposta de um processamento de pagamento.
 * 
 * Versão V3 - Adiciona outcomes específicos para Retry.
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
        /** Pagamento com sucesso após retries */
        SUCCESS_AFTER_RETRY,
        /** Pagamento aceito para processamento assíncrono (fallback ativo) */
        ACCEPTED_ASYNC,
        /** Falha no processamento após esgotar retries */
        FAILURE_AFTER_RETRY,
        /** Falha no processamento (sem retry) */
        FAILURE
    }
    
    /**
     * Cria uma resposta de sucesso.
     */
    public static PaymentResponse success(String message) {
        return new PaymentResponse(HttpStatus.OK, message, false, PaymentOutcome.SUCCESS);
    }
    
    /**
     * Cria uma resposta de sucesso após retry.
     */
    public static PaymentResponse successAfterRetry(String message, int attempts) {
        return new PaymentResponse(
            HttpStatus.OK, 
            message + " (após " + attempts + " tentativa(s))", 
            false, 
            PaymentOutcome.SUCCESS_AFTER_RETRY
        );
    }
    
    /**
     * Cria uma resposta de fallback (após esgotar retries).
     */
    public static PaymentResponse fallback(String message) {
        return new PaymentResponse(HttpStatus.ACCEPTED, message, true, PaymentOutcome.ACCEPTED_ASYNC);
    }
    
    /**
     * Cria uma resposta de falha após esgotar retries.
     */
    public static PaymentResponse failureAfterRetry(String message) {
        return new PaymentResponse(
            HttpStatus.INTERNAL_SERVER_ERROR, 
            message, 
            false, 
            PaymentOutcome.FAILURE_AFTER_RETRY
        );
    }
    
    /**
     * Cria uma resposta de falha.
     */
    public static PaymentResponse failure(String message) {
        return new PaymentResponse(HttpStatus.INTERNAL_SERVER_ERROR, message, false, PaymentOutcome.FAILURE);
    }
}
