package br.ufpe.cin.tcc.pagamento.dto;

import org.springframework.http.HttpStatus;

/**
 * DTO representando a resposta de um processamento de pagamento.
 * Versão simplificada para V1 (sem fallback).
 */
public record PaymentResponse(
    HttpStatus status,
    String message,
    PaymentOutcome outcome
) {
    /**
     * Enum representando os possíveis resultados do processamento.
     */
    public enum PaymentOutcome {
        /** Pagamento processado com sucesso pelo adquirente */
        SUCCESS,
        /** Falha no processamento */
        FAILURE
    }
    
    /**
     * Cria uma resposta de sucesso.
     */
    public static PaymentResponse success(String message) {
        return new PaymentResponse(HttpStatus.OK, message, PaymentOutcome.SUCCESS);
    }
    
    /**
     * Cria uma resposta de falha.
     */
    public static PaymentResponse failure(String message) {
        return new PaymentResponse(HttpStatus.INTERNAL_SERVER_ERROR, message, PaymentOutcome.FAILURE);
    }
}
