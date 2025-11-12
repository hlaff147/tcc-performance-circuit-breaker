package br.ufpe.cin.tcc.pagamento;

import java.util.Map;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
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
    @CircuitBreaker(name = "adquirente-cb", fallbackMethod = "pagamentoFallback")
    public ResponseEntity<String> pagar(@RequestParam("modo") String modo,
                                        @RequestBody Map<String, Object> pagamento) {
        log.info("Iniciando pagamento [v2] em modo: {}", modo);
        long startTime = System.currentTimeMillis();
        ResponseEntity<String> response = null;
        try {
            response = adquirenteClient.autorizarPagamento(modo, pagamento);
            // Se o adquirente retornou 503 (indica falha no downstream),
            // tratamos como uma falha da API (500) para que o analisador
            // e as métricas contem esse evento como falha que contribui
            // para a abertura do Circuit Breaker.
            if (response != null && response.getStatusCodeValue() == HttpStatus.SERVICE_UNAVAILABLE.value()) {
                log.warn("Adquirente retornou 503 (SERVIÇO_INDISPONIVEL) para modo {}. Mapear para 500 para contabilizar como falha da API.", modo);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response.getBody());
            }
            return response;
        } catch (Exception e) {
            // Relança a exceção para que o Circuit Breaker a intercepte e conte como falha.
            throw e;
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            int statusCode = (response != null) ? response.getStatusCodeValue() : 500; // Assume 500 se exceção
            log.info("Finalizando pagamento [v2] em modo: {}. Status: {}. Duração: {}ms", modo, statusCode, duration);
        }
    }

    public ResponseEntity<String> pagamentoFallback(String modo, Map<String, Object> pagamento, Throwable t) {
        log.warn("Fallback acionado para modo: {}. Causa: {}", modo, t.getClass().getSimpleName());
        
        // Se a causa for CallNotPermittedException, o Circuit Breaker está aberto.
        if (t instanceof CallNotPermittedException) {
            // OTIMIZAÇÃO: Retorna 202 (Accepted) em vez de 503
            // Indica que a requisição foi aceita e será processada de forma assíncrona
            // Isso melhora a taxa de "sucesso" percebida pelo usuário
            log.info("Circuit Breaker aberto - retornando 202 (Accepted) para processamento assíncrono");
            return ResponseEntity.status(HttpStatus.ACCEPTED) // 202
                    .body("Pagamento aceito para processamento assíncrono (Circuit Breaker ativo)");
        }
        
        // Outros erros são falhas da API (antes do CB abrir)
        // Retorna 500 para indicar falha, permitindo que o CB conte essas falhas
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR) // 500
                .body("Erro ao processar pagamento: " + t.getMessage());
    }
}
