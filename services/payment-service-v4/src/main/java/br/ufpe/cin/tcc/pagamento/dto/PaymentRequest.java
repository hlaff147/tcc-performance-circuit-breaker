package br.ufpe.cin.tcc.pagamento.dto;

import java.math.BigDecimal;
import java.util.Map;

public record PaymentRequest(
    BigDecimal amount,
    String paymentMethod,
    String customerId,
    Map<String, Object> additionalData
) {
    public static PaymentRequest fromMap(Map<String, Object> map) {
        BigDecimal amount = map.get("amount") != null 
            ? new BigDecimal(map.get("amount").toString()) 
            : BigDecimal.ZERO;
        String paymentMethod = (String) map.getOrDefault("payment_method", "unknown");
        String customerId = (String) map.getOrDefault("customer_id", "anonymous");
        
        return new PaymentRequest(amount, paymentMethod, customerId, map);
    }
    
    public Map<String, Object> toMap() {
        return additionalData != null ? additionalData : Map.of(
            "amount", amount,
            "payment_method", paymentMethod,
            "customer_id", customerId
        );
    }
}
