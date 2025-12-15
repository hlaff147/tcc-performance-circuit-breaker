package br.ufpe.cin.tcc.pagamento;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

/**
 * Aplicação principal do serviço de pagamento V3.
 * 
 * Esta versão implementa apenas RETRY (sem Circuit Breaker) para
 * comparação experimental com a versão V2 que usa Circuit Breaker.
 */
@SpringBootApplication
@EnableFeignClients
public class PagamentoApplication {

    public static void main(String[] args) {
        SpringApplication.run(PagamentoApplication.class, args);
    }
}
