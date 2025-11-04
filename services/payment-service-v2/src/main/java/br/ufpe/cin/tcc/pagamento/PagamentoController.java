package br.ufpe.cin.tcc.pagamento;

import java.util.Map;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;

@RestController
public class PagamentoController {

    private static final Logger log = LoggerFactory.getLogger(PagamentoController.class);

    private final AdquirenteClient adquirenteClient;

    public PagamentoController(AdquirenteClient adquirenteClient) {
        this.adquirenteClient = adquirenteClient;
    }

    @PostMapping(path = "/pagar")
    @CircuitBreaker(name = "adquirente-cb", fallbackMethod = "pagamentoFallback")
    public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                        @RequestBody Map<String, Object> pagamento) {
        return adquirenteClient.autorizarPagamento(modo, pagamento);
    }

    public ResponseEntity<String> pagamentoFallback(String modo, Map<String, Object> pagamento, Throwable t) {
        log.warn("Pagamento em modo {} enviado para contingência devido a falha ao contactar o adquirente.", modo, t);
        return ResponseEntity.status(HttpStatus.ACCEPTED)
                .body("Pagamento recebido. Será processado offline (contingência).");
    }
}
