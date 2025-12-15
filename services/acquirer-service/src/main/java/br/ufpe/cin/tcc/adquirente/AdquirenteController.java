package br.ufpe.cin.tcc.adquirente;

import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Controller que simula um gateway de pagamento (adquirente).
 * 
 * Suporta diferentes modos de operação para simular cenários de teste:
 * - normal: resposta imediata com sucesso
 * - latencia: resposta com atraso variável (jitter) para simular carga real
 * - falha: retorna erro 503 (Service Unavailable)
 * - timeout: atraso extremo para forçar timeout no cliente
 * - parcial: 50% de chance de sucesso ou falha (para testes de resiliência)
 */
@RestController
@RequestMapping("/autorizar")
public class AdquirenteController {

    private static final Logger log = LoggerFactory.getLogger(AdquirenteController.class);
    
    // Configurações de latência com Jitter para evitar sincronização artificial
    private static final int LATENCY_BASE_MS = 2500;
    private static final int LATENCY_JITTER_MS = 1000; // ±500ms de variação
    private static final int TIMEOUT_DELAY_MS = 15000; // 15 segundos para forçar timeout

    @PostMapping
    public ResponseEntity<String> autorizar(@RequestParam(name = "modo", defaultValue = "normal") String modo,
                                            @RequestBody(required = false) Map<String, Object> payload) {
        long startTime = System.currentTimeMillis();
        
        ResponseEntity<String> response = switch (modo) {
            case "normal" -> handleNormal();
            case "latencia" -> handleLatency();
            case "falha" -> handleFailure();
            case "timeout" -> handleTimeout();
            case "parcial" -> handlePartial();
            case "degradacao" -> handleDegradation();
            default -> ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body("Modo inválido: " + modo);
        };
        
        long duration = System.currentTimeMillis() - startTime;
        log.info("Requisição processada - modo: {}, status: {}, duração: {}ms", 
                modo, response.getStatusCode().value(), duration);
        
        return response;
    }
    
    /**
     * Endpoint de health check para validar disponibilidade do serviço.
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "acquirer-service",
            "timestamp", String.valueOf(System.currentTimeMillis())
        ));
    }
    
    /**
     * Modo normal: resposta imediata com sucesso.
     * Adiciona pequeno jitter (0-50ms) para simular processamento real.
     */
    private ResponseEntity<String> handleNormal() {
        // Pequeno jitter para evitar respostas artificialmente síncronas
        sleep(ThreadLocalRandom.current().nextInt(0, 50));
        return ResponseEntity.ok("Pagamento Aprovado");
    }
    
    /**
     * Modo latência: simula carga no serviço com atraso variável.
     * Usa jitter para evitar sincronização de threads (thundering herd).
     */
    private ResponseEntity<String> handleLatency() {
        int jitter = ThreadLocalRandom.current().nextInt(-LATENCY_JITTER_MS/2, LATENCY_JITTER_MS/2);
        int delay = LATENCY_BASE_MS + jitter;
        
        log.debug("Simulando latência: {}ms (base: {}, jitter: {})", delay, LATENCY_BASE_MS, jitter);
        sleep(delay);
        
        return ResponseEntity.ok("Pagamento Aprovado (com latência: " + delay + "ms)");
    }
    
    /**
     * Modo falha: retorna erro 503 imediatamente.
     * Simula indisponibilidade do serviço.
     */
    private ResponseEntity<String> handleFailure() {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body("Erro na Adquirente: Serviço temporariamente indisponível");
    }
    
    /**
     * Modo timeout: atraso extremo para forçar timeout no cliente.
     * Útil para testar configurações de timeout e Circuit Breaker.
     */
    private ResponseEntity<String> handleTimeout() {
        log.warn("Modo timeout ativado - aguardando {}ms", TIMEOUT_DELAY_MS);
        sleep(TIMEOUT_DELAY_MS);
        return ResponseEntity.ok("Pagamento Aprovado (após timeout extremo)");
    }
    
    /**
     * Modo parcial: 50% de chance de sucesso ou falha.
     * Útil para testar comportamento do Circuit Breaker próximo ao threshold.
     */
    private ResponseEntity<String> handlePartial() {
        boolean success = ThreadLocalRandom.current().nextBoolean();
        if (success) {
            sleep(ThreadLocalRandom.current().nextInt(50, 200));
            return ResponseEntity.ok("Pagamento Aprovado (modo parcial)");
        } else {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body("Erro na Adquirente: Falha aleatória (modo parcial)");
        }
    }
    
    /**
     * Modo degradação: latência crescente simulando degradação progressiva.
     * A cada chamada, há chance de aumentar a latência ou falhar.
     */
    private ResponseEntity<String> handleDegradation() {
        int random = ThreadLocalRandom.current().nextInt(100);
        
        if (random < 20) {
            // 20% de chance de falha
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body("Erro na Adquirente: Sistema degradado");
        } else if (random < 50) {
            // 30% de chance de latência alta
            int delay = ThreadLocalRandom.current().nextInt(2000, 4000);
            sleep(delay);
            return ResponseEntity.ok("Pagamento Aprovado (degradado: " + delay + "ms)");
        } else {
            // 50% de operação normal
            sleep(ThreadLocalRandom.current().nextInt(100, 500));
            return ResponseEntity.ok("Pagamento Aprovado");
        }
    }
    
    /**
     * Helper method para sleep com tratamento de interrupção.
     */
    private void sleep(int millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            log.warn("Sleep interrompido");
        }
    }
}
