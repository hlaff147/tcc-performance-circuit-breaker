package br.ufpe.cin.tcc.pagamento.config;

import io.micrometer.core.aop.TimedAspect;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Configuração de métricas para o serviço de pagamento.
 * 
 * Habilita o aspecto @Timed do Micrometer para coleta automática
 * de métricas de tempo de execução dos métodos anotados.
 */
@Configuration
public class MetricsConfig {

    /**
     * Bean que habilita a anotação @Timed em métodos.
     * Sem este bean, as anotações @Timed são ignoradas.
     */
    @Bean
    public TimedAspect timedAspect(MeterRegistry registry) {
        return new TimedAspect(registry);
    }
}
