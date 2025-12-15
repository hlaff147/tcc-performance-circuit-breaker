package br.ufpe.cin.tcc.pagamento.service;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

/**
 * Serviço responsável pelo processamento de pagamentos.
 * 
 * Versão V1 (Baseline): Implementação ingênua SEM Circuit Breaker.
 * Apenas delega a chamada para o serviço adquirente e trata exceções básicas.
 * 
 * Esta implementação serve como controle no experimento para comparação
 * com a versão V2 que implementa padrões de resiliência.
 */
@Service
public class PaymentService {

    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

    private final AdquirenteClient acquirerClient;

    public PaymentService(AdquirenteClient acquirerClient) {
        this.acquirerClient = acquirerClient;
    }

    /**
     * Processa um pagamento chamando o serviço adquirente.
     * 
     * Implementação baseline: sem Circuit Breaker, sem fallback.
     * Em caso de falha do adquirente, a exceção é propagada ou o erro é retornado.
     *
     * @param modo Modo de operação (normal, latencia, falha)
     * @param request Dados do pagamento
     * @return PaymentResponse com o resultado do processamento
     */
    public PaymentResponse processPayment(String modo, PaymentRequest request) {
        log.info("Processando pagamento [v1-baseline] - modo: {}, cliente: {}", modo, request.customerId());
        
        long startTime = System.currentTimeMillis();
        
        try {
            ResponseEntity<String> response = acquirerClient.autorizarPagamento(modo, request.toMap());
            long duration = System.currentTimeMillis() - startTime;
            
            // V1 não trata 503 de forma especial - propaga o erro
            if (response.getStatusCode().is5xxServerError()) {
                log.error("Adquirente retornou erro {}. Duração: {}ms", 
                        response.getStatusCode(), duration);
                return PaymentResponse.failure("Erro do adquirente: " + response.getBody());
            }
            
            log.info("Pagamento processado com sucesso. Status: {}, Duração: {}ms", 
                    response.getStatusCode(), duration);
            return PaymentResponse.success(response.getBody());
            
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("Erro ao processar pagamento. Duração: {}ms, Erro: {}", duration, e.getMessage());
            return PaymentResponse.failure("Erro ao processar pagamento: " + e.getMessage());
        }
    }
}
