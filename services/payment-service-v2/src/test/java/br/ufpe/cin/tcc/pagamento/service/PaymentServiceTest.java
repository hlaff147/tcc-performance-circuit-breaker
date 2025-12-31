package br.ufpe.cin.tcc.pagamento.service;

import br.ufpe.cin.tcc.pagamento.client.AdquirenteClient;
import br.ufpe.cin.tcc.pagamento.dto.PaymentRequest;
import br.ufpe.cin.tcc.pagamento.dto.PaymentResponse;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.math.BigDecimal;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

/**
 * Testes unitários para PaymentService (V2 com Circuit Breaker).
 * 
 * Valida:
 * - Cenário de sucesso (circuito fechado)
 * - Cenário de falha (dependência indisponível)
 * - Cenário de fallback (Circuit Breaker acionado)
 * - Mapeamento correto de status HTTP
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("PaymentService V2 - Testes Unitários")
class PaymentServiceTest {

    @Mock
    private AdquirenteClient acquirerClient;
    
    private MeterRegistry meterRegistry;
    private PaymentService paymentService;
    
    private PaymentRequest sampleRequest;

    @BeforeEach
    void setUp() {
        meterRegistry = new SimpleMeterRegistry();
        paymentService = new PaymentService(acquirerClient, meterRegistry);
        
        sampleRequest = new PaymentRequest(
            new BigDecimal("100.00"),
            "credit_card",
            "customer-123",
            Map.of("amount", 100.0, "payment_method", "credit_card", "customer_id", "customer-123")
        );
    }

    @Nested
    @DisplayName("Cenário: Sucesso (Circuito Fechado)")
    class SuccessScenarios {

        @Test
        @DisplayName("Deve retornar sucesso quando adquirente responde HTTP 200")
        void shouldReturnSuccessWhenAcquirerReturnsOk() {
            // Arrange
            when(acquirerClient.autorizarPagamento(eq("normal"), any()))
                .thenReturn(ResponseEntity.ok("Pagamento Aprovado"));

            // Act
            PaymentResponse response = paymentService.processPayment("normal", sampleRequest);

            // Assert
            assertThat(response.status()).isEqualTo(HttpStatus.OK);
            assertThat(response.message()).isEqualTo("Pagamento Aprovado");
            assertThat(response.fallback()).isFalse();
            assertThat(response.outcome()).isEqualTo(PaymentResponse.PaymentOutcome.SUCCESS);
            
            verify(acquirerClient, times(1)).autorizarPagamento(eq("normal"), any());
        }

        @Test
        @DisplayName("Deve incrementar contador de sucesso")
        void shouldIncrementSuccessCounter() {
            // Arrange
            when(acquirerClient.autorizarPagamento(any(), any()))
                .thenReturn(ResponseEntity.ok("Pagamento Aprovado"));

            // Act
            paymentService.processPayment("normal", sampleRequest);

            // Assert
            Counter successCounter = meterRegistry.find("payment.outcome")
                .tag("result", "success")
                .counter();
            assertThat(successCounter).isNotNull();
            assertThat(successCounter.count()).isEqualTo(1.0);
        }
    }

    @Nested
    @DisplayName("Cenário: Falha na Dependência")
    class FailureScenarios {

        @Test
        @DisplayName("Deve propagar erro (5xx) quando adquirente retorna 503")
        void shouldPropagateWhenAcquirerReturns503() {
            // Arrange
            when(acquirerClient.autorizarPagamento(eq("falha"), any()))
                .thenReturn(ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body("Serviço indisponível"));

            // Act & Assert
            assertThatThrownBy(() -> paymentService.processPayment("falha", sampleRequest))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("indisponível");
        }

        @Test
        @DisplayName("Deve incrementar contador de falha quando adquirente retorna 503")
        void shouldIncrementFailureCounterOnServiceUnavailable() {
            // Arrange
            when(acquirerClient.autorizarPagamento(any(), any()))
                .thenReturn(ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body("Erro"));

            // Act
            try {
                paymentService.processPayment("falha", sampleRequest);
            } catch (Exception ignored) {
                // esperado
            }

            // Assert
            Counter failureCounter = meterRegistry.find("payment.outcome")
                .tag("result", "failure")
                .counter();
            assertThat(failureCounter).isNotNull();
            assertThat(failureCounter.count()).isEqualTo(1.0);
        }

        @Test
        @DisplayName("Deve propagar exceção quando adquirente lança erro")
        void shouldPropagateExceptionWhenAcquirerThrows() {
            // Arrange
            when(acquirerClient.autorizarPagamento(any(), any()))
                .thenThrow(new RuntimeException("Connection refused"));

            // Act & Assert
            assertThatThrownBy(() -> paymentService.processPayment("normal", sampleRequest))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Connection refused");
        }
    }

    @Nested
    @DisplayName("Cenário: Fallback (Circuit Breaker)")
    class FallbackScenarios {

        @Test
        @DisplayName("Deve retornar HTTP 202 quando Circuit Breaker está aberto")
        void shouldReturnAcceptedWhenCircuitBreakerOpen() {
            // Arrange
            CallNotPermittedException cbException = mock(CallNotPermittedException.class);

            // Act
            PaymentResponse response = paymentService.processPaymentFallback(
                "normal", sampleRequest, cbException);

            // Assert
            assertThat(response.status()).isEqualTo(HttpStatus.ACCEPTED);
            assertThat(response.message()).contains("Circuit Breaker");
            assertThat(response.fallback()).isTrue();
            assertThat(response.outcome()).isEqualTo(PaymentResponse.PaymentOutcome.CIRCUIT_BREAKER_OPEN);
        }

        @Test
        @DisplayName("Deve propagar exceção (5xx) para outras falhas")
        void shouldPropagateForOtherExceptions() {
            // Arrange
            RuntimeException genericException = new RuntimeException("Timeout");

            // Act & Assert
            assertThatThrownBy(() -> paymentService.processPaymentFallback(
                "normal", sampleRequest, genericException))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Timeout");
        }

        @Test
        @DisplayName("Deve incrementar contador de fallback")
        void shouldIncrementFallbackCounter() {
            // Arrange
            CallNotPermittedException cbException = mock(CallNotPermittedException.class);

            // Act
            paymentService.processPaymentFallback("normal", sampleRequest, cbException);

            // Assert
            Counter fallbackCounter = meterRegistry.find("payment.outcome")
                .tag("result", "fallback")
                .counter();
            assertThat(fallbackCounter).isNotNull();
            assertThat(fallbackCounter.count()).isEqualTo(1.0);
        }
    }

    @Nested
    @DisplayName("Cenário: Métricas e Observabilidade")
    class MetricsScenarios {

        @Test
        @DisplayName("Deve registrar todas as métricas de outcome")
        void shouldRegisterAllOutcomeMetrics() {
            // Arrange & Act
            when(acquirerClient.autorizarPagamento(any(), any()))
                .thenReturn(ResponseEntity.ok("OK"));
            paymentService.processPayment("normal", sampleRequest);
            
            when(acquirerClient.autorizarPagamento(any(), any()))
                .thenReturn(ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body("Erro"));
            try {
                paymentService.processPayment("falha", sampleRequest);
            } catch (Exception ignored) {
                // esperado
            }
            
            paymentService.processPaymentFallback("normal", sampleRequest, 
                mock(CallNotPermittedException.class));

            // Assert
            assertThat(meterRegistry.find("payment.outcome").tag("result", "success").counter().count())
                .isEqualTo(1.0);
            assertThat(meterRegistry.find("payment.outcome").tag("result", "failure").counter().count())
                .isEqualTo(1.0);
            assertThat(meterRegistry.find("payment.outcome").tag("result", "fallback").counter().count())
                .isEqualTo(1.0);
        }
    }
}
