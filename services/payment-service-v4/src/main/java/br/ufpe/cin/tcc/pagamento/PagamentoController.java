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
 * Versão V4 - Implementa CIRCUIT BREAKER + RETRY combinados
 * para testar sinergia entre os padrões.
 */
@RestController
public class PagamentoController {

    private static final Logger log = LoggerFactory.getLogger(PagamentoController.class);

    private final PaymentService paymentService;

    public PagamentoController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    @PostMapping(path = "/pagar")
    public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                        @RequestBody Map<String, Object> pagamento) {
        log.debug("Requisição recebida [v4-cb+retry] - modo: {}", modo);
        
        PaymentRequest request = PaymentRequest.fromMap(pagamento);
        PaymentResponse response = paymentService.processPayment(modo, request);
        
        log.debug("Resposta enviada - status: {}, fallback: {}", response.status(), response.fallback());
        
        return ResponseEntity.status(response.status()).body(response.message());
    }
}
