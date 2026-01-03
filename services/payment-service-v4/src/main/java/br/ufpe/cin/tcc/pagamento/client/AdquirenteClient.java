package br.ufpe.cin.tcc.pagamento.client;

import java.util.Map;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(name = "adquirente-client", url = "${adquirente-client.url:http://servico-adquirente:8081}")
public interface AdquirenteClient {

    @PostMapping(path = "/autorizar")
    ResponseEntity<String> autorizarPagamento(@RequestParam("modo") String modo,
                                              @RequestBody Map<String, Object> pagamento);
}
