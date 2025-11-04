package br.ufpe.cin.tcc.adquirente;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/autorizar")
public class AdquirenteController {

    @PostMapping
    public ResponseEntity<String> autorizar(@RequestParam(name = "modo", defaultValue = "normal") String modo,
                                            @RequestBody(required = false) Map<String, Object> payload) {
        return switch (modo) {
            case "normal" -> ResponseEntity.ok("Pagamento Aprovado");
            case "latencia" -> {
                try {
                    Thread.sleep(3000);
                } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                    yield ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                            .body("Processamento interrompido");
                }
                yield ResponseEntity.ok("Pagamento Aprovado (com latência)");
            }
            case "falha" -> ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body("Erro na Adquirente");
            default -> ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body("Modo inválido: " + modo);
        };
    }
}
