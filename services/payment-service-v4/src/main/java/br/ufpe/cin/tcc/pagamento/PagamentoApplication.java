package br.ufpe.cin.tcc.pagamento;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

/**
 * Aplicação principal do serviço de pagamento V4.
 * 
 * Esta versão implementa CIRCUIT BREAKER + RETRY combinados para
 * testar a hipótese de sinergia entre os dois padrões.
 */
@SpringBootApplication
@EnableFeignClients
public class PagamentoApplication {

    public static void main(String[] args) {
        SpringApplication.run(PagamentoApplication.class, args);
    }
}
