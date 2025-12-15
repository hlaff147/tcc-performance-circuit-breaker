package br.ufpe.cin.tcc.pagamento;

import java.util.Map;

import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import br.ufpe.cin.tcc.pagamento.service.PaymentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Controller REST para processamento de pagamentos.
 * 
 * Responsabilidades:
 * - Receber requisições HTTP
 * - Converter entrada para DTO
 * - Delegar processamento ao PaymentService
 * - Converter resposta do serviço para ResponseEntity
 * 
 * A lógica de negócio e integração com Circuit Breaker está no PaymentService.
 */
@RestController
public class PagamentoController {

    private static final Logger log = LoggerFactory.getLogger(PagamentoController.class);

    private final PaymentService paymentService;

    public PagamentoController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    /**
     * Endpoint para processamento de pagamentos.
     * 
     * @param modo Modo de operação do serviço adquirente (normal, latencia, falha)
     * @param pagamento Dados do pagamento em formato Map
     * @return ResponseEntity com o resultado do processamento
     */
    @PostMapping(path = "/pagar")
    public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                        @RequestBody Map<String, Object> pagamento) {
        log.debug("Requisição recebida - modo: {}", modo);
        
        PaymentRequest request = PaymentRequest.fromMap(pagamento);
        PaymentResponse response = paymentService.processPayment(modo, request);
        
        log.debug("Resposta enviada - status: {}, fallback: {}", response.status(), response.fallback());
        
        return ResponseEntity.status(response.status()).body(response.message());
    }
}
