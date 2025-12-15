package br.ufpe.cin.tcc.pagamento.dto;

import java.math.BigDecimal;
import java.util.Map;

/**
 * DTO representando uma requisição de pagamento.
 * Encapsula os dados recebidos do cliente para processamento.
 */
public record PaymentRequest(
    BigDecimal amount,
    String paymentMethod,
    String customerId,
    Map<String, Object> additionalData
) {
    /**
     * Construtor de conveniência para criação a partir de um Map genérico.
     */
    public static PaymentRequest fromMap(Map<String, Object> map) {
        BigDecimal amount = map.get("amount") != null 
            ? new BigDecimal(map.get("amount").toString()) 
            : BigDecimal.ZERO;
        String paymentMethod = (String) map.getOrDefault("payment_method", "unknown");
        String customerId = (String) map.getOrDefault("customer_id", "anonymous");
        
        return new PaymentRequest(amount, paymentMethod, customerId, map);
    }
    
    /**
     * Converte o DTO para Map para envio ao serviço adquirente.
     */
    public Map<String, Object> toMap() {
        return additionalData != null ? additionalData : Map.of(
            "amount", amount,
            "payment_method", paymentMethod,
            "customer_id", customerId
        );
    }
}
