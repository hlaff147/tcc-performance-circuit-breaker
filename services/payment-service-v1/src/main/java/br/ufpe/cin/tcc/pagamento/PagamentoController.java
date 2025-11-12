package br.ufpe.cin.tcc.pagamento;

import java.util.Map;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PagamentoController {

    private static final Logger log = LoggerFactory.getLogger(PagamentoController.class);
    private final AdquirenteClient adquirenteClient;

    public PagamentoController(AdquirenteClient adquirenteClient) {
        this.adquirenteClient = adquirenteClient;
    }

    @PostMapping(path = "/pagar")
    public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                        @RequestBody Map<String, Object> pagamento) {
        log.info("Iniciando pagamento [v1] em modo: {}", modo);
        long startTime = System.currentTimeMillis();
        ResponseEntity<String> response = null;
        try {
            response = adquirenteClient.autorizarPagamento(modo, pagamento);
            return response;
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            int statusCode = (response != null) ? response.getStatusCodeValue() : -1;
            log.info("Finalizando pagamento [v1] em modo: {}. Status: {}. Duração: {}ms", modo, statusCode, duration);
        }
    }
}
