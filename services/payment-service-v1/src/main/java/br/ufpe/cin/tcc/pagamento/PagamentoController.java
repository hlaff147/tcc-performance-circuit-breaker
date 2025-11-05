package br.ufpe.cin.tcc.pagamento;

import java.util.Map;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PagamentoController {

    private final AdquirenteClient adquirenteClient;

    public PagamentoController(AdquirenteClient adquirenteClient) {
        this.adquirenteClient = adquirenteClient;
    }

    @PostMapping(path = "/pagar")
    public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                        @RequestBody Map<String, Object> pagamento) {
        return adquirenteClient.autorizarPagamento(modo, pagamento);
    }
}
