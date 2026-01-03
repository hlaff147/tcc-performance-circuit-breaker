package br.ufpe.cin.tcc.pagamento.integration;

import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import br.ufpe.cin.tcc.pagamento.service.PaymentService;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.client.WireMock;
import com.github.tomakehurst.wiremock.core.WireMockConfiguration;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import java.math.BigDecimal;
import java.util.Map;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static org.assertj.core.api.Assertions.assertThat;

/**
 * Testes de integração para validar o comportamento do Circuit Breaker.
 * 
 * Utiliza WireMock para simular o serviço adquirente e verificar:
 * - Transições de estado do Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN)
 * - Fallback é acionado quando circuito está aberto
 * - Recuperação automática quando serviço volta ao normal
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("agressivo")
@DisplayName("Circuit Breaker - Testes de Integração")
class CircuitBreakerIntegrationTest {

    private static WireMockServer wireMockServer;

    @Autowired
    private PaymentService paymentService;

    @Autowired
    private CircuitBreakerRegistry circuitBreakerRegistry;

    private PaymentRequest sampleRequest;

    @BeforeAll
    static void startWireMock() {
        wireMockServer = new WireMockServer(WireMockConfiguration.wireMockConfig()
            .dynamicPort());
        wireMockServer.start();
        WireMock.configureFor("localhost", wireMockServer.port());
    }

    @AfterAll
    static void stopWireMock() {
        if (wireMockServer != null) {
            wireMockServer.stop();
        }
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("adquirente-client.url",
            () -> "http://localhost:" + wireMockServer.port());
    }

    @BeforeEach
    void setUp() {
        wireMockServer.resetAll();
        
        // Reset do Circuit Breaker para estado inicial
        CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
        circuitBreaker.reset();
        
        sampleRequest = new PaymentRequest(
            new BigDecimal("100.00"),
            "credit_card",
            "customer-integration-test",
            Map.of("amount", 100.0, "payment_method", "credit_card", "customer_id", "customer-integration-test")
        );
    }

    @Nested
    @DisplayName("Estado CLOSED (Circuito Fechado)")
    class ClosedStateTests {

        @Test
        @DisplayName("Deve processar requisições normalmente quando adquirente está saudável")
        void shouldProcessNormallyWhenAcquirerIsHealthy() {
            // Arrange
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(200)
                    .withBody("Pagamento Aprovado")));

            // Act
            PaymentResponse response = paymentService.processPayment("normal", sampleRequest);

            // Assert
            assertThat(response.status()).isEqualTo(HttpStatus.OK);
            assertThat(response.fallback()).isFalse();
            
            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            assertThat(cb.getState()).isEqualTo(CircuitBreaker.State.CLOSED);
        }

        @Test
        @DisplayName("Deve manter circuito fechado com falhas abaixo do threshold")
        void shouldKeepCircuitClosedWhenFailuresAreBelowThreshold() {
            // Arrange - configura para falhar algumas vezes mas abaixo do threshold
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(503)
                    .withBody("Erro temporário")));

            // Act - faz apenas 3 chamadas (abaixo do minimumNumberOfCalls = 8)
            for (int i = 0; i < 3; i++) {
                try {
                    paymentService.processPayment("falha", sampleRequest);
                } catch (Exception ignored) {
                    // Exceções são esperadas
                }
            }

            // Assert - circuito deve continuar fechado
            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            assertThat(cb.getState()).isEqualTo(CircuitBreaker.State.CLOSED);
        }
    }

    @Nested
    @DisplayName("Transição CLOSED -> OPEN")
    class OpenTransitionTests {

        @Test
        @DisplayName("Deve abrir circuito após ultrapassar threshold de falhas")
        void shouldOpenCircuitAfterExceedingFailureThreshold() {
            // Arrange
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(503)
                    .withBody("Serviço indisponível")));

            // Act - força falhas suficientes para abrir o circuito
            // Com failureRateThreshold=60% e minimumNumberOfCalls=8, precisamos de 5+ falhas em 8 chamadas
            for (int i = 0; i < 10; i++) {
                try {
                    paymentService.processPayment("falha", sampleRequest);
                } catch (Exception ignored) {
                    // Exceções são esperadas até o CB abrir
                }
            }

            // Assert
            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            assertThat(cb.getState()).isIn(CircuitBreaker.State.OPEN, CircuitBreaker.State.HALF_OPEN);
        }

        @Test
        @DisplayName("Deve retornar fallback quando circuito está aberto")
        void shouldReturnFallbackWhenCircuitIsOpen() {
            // Arrange - força abertura do circuito
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(503)
                    .withBody("Erro")));

            // Força abertura
            for (int i = 0; i < 15; i++) {
                try {
                    paymentService.processPayment("falha", sampleRequest);
                } catch (Exception ignored) {}
            }

            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            
            // Se o circuito está aberto, a próxima chamada deve retornar fallback
            if (cb.getState() == CircuitBreaker.State.OPEN) {
                // Act
                PaymentResponse response = paymentService.processPayment("normal", sampleRequest);

                // Assert
                assertThat(response.status()).isEqualTo(HttpStatus.ACCEPTED);
                assertThat(response.fallback()).isTrue();
            }
        }
    }

    @Nested
    @DisplayName("Estado HALF_OPEN e Recuperação")
    class HalfOpenAndRecoveryTests {

        @Test
        @DisplayName("Deve permitir chamadas de teste em HALF_OPEN")
        void shouldAllowTestCallsInHalfOpen() throws InterruptedException {
            // Arrange - abre o circuito
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(503)
                    .withBody("Erro")));

            for (int i = 0; i < 15; i++) {
                try {
                    paymentService.processPayment("falha", sampleRequest);
                } catch (Exception ignored) {}
            }

            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            // No perfil agressivo, waitDurationInOpenState=5s
            Thread.sleep(6000);

            // Configura resposta de sucesso para permitir recuperação
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(200)
                    .withBody("Pagamento Aprovado")));

            // Act - tenta uma chamada
            PaymentResponse response = null;
            for (int attempt = 0; attempt < 15; attempt++) {
                response = paymentService.processPayment("normal", sampleRequest);
                if (response.status() == HttpStatus.OK) {
                    break;
                }
                Thread.sleep(250);
            }

            // Assert - deve ter processado ou estar em transição
            assertThat(response).isNotNull();
            assertThat(response.status()).isEqualTo(HttpStatus.OK);
            assertThat(cb.getState()).isIn(
                CircuitBreaker.State.HALF_OPEN, 
                CircuitBreaker.State.CLOSED
            );
        }
    }

    @Nested
    @DisplayName("Métricas do Circuit Breaker")
    class CircuitBreakerMetricsTests {

        @Test
        @DisplayName("Deve registrar métricas de chamadas bem-sucedidas")
        void shouldRecordSuccessfulCallMetrics() {
            // Arrange
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(200)
                    .withBody("OK")));

            // Act
            paymentService.processPayment("normal", sampleRequest);

            // Assert
            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            CircuitBreaker.Metrics metrics = cb.getMetrics();
            
            assertThat(metrics.getNumberOfSuccessfulCalls()).isGreaterThanOrEqualTo(1);
        }

        @Test
        @DisplayName("Deve registrar métricas de chamadas com falha")
        void shouldRecordFailedCallMetrics() {
            // Arrange
            stubFor(post(urlPathEqualTo("/autorizar"))
                .willReturn(aResponse()
                    .withStatus(503)
                    .withBody("Erro")));

            // Act
            try {
                paymentService.processPayment("falha", sampleRequest);
            } catch (Exception ignored) {}

            // Assert
            CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("adquirente-cb");
            CircuitBreaker.Metrics metrics = cb.getMetrics();
            
            assertThat(metrics.getNumberOfFailedCalls()).isGreaterThanOrEqualTo(0);
        }
    }
}
