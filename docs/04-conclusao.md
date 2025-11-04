# Conclusão

## Revisão dos Objetivos e do Problema
Este trabalho se propôs a investigar a fragilidade da comunicação síncrona em microsserviços, especificamente o risco de falhas em cascata em um sistema de pagamentos. O objetivo foi avaliar quantitativamente o impacto do padrão Circuit Breaker no desempenho e resiliência, usando um experimento prático e reprodutível com `Docker` e `k6`.

## Síntese dos Resultados
Os resultados experimentais foram conclusivos. A arquitetura Baseline (V1) falhou catastroficamente nos `thresholds` de desempenho e resiliência em cenários de latência e falha total, provando ser inviável para produção. Em contrapartida, a arquitetura V2 (Circuit Breaker) demonstrou robustez absoluta. Ela protegeu o `servico-pagamento`, manteve a vazão estável e garantiu 0% de taxa de erro (percebida pelo usuário) através da degradação graciosa (HTTP 202), passando em todos os `thresholds` definidos no `k6`.

## Conexão com Pinheiro, Dantas, et al. (2024)
Este trabalho experimental dialoga diretamente com os achados teóricos de Pinheiro, Dantas, et al. (2024). Enquanto o referido artigo propõe modelos sofisticados usando Redes de Petri Estocásticas (SPNs) para *analisar* e *prever* o comportamento de Circuit Breakers e o impacto de seus parâmetros nos SLAs, este TCC serviu como sua **contraparte empírica**. Validamos na prática, usando um ecossistema de software real (Java, Spring, `k6`, `Docker`), que os benefícios de desempenho e resiliência modelados teoricamente se traduzem em ganhos mensuráveis e críticos. Onde o artigo de Pinheiro et al. fornece as ferramentas para *modelar* e *garantir* um SLA, este TCC demonstrou *experimentalmente* como o Circuit Breaker (implementado com Resilience4j) é o mecanismo que torna esse SLA alcançável, tratando latência e falhas de forma a evitar a sobrecarga do sistema, exatamente como os modelos previam.

## Trabalhos Futuros
Como trabalho futuro, sugere-se a expansão deste experimento (usando a mesma suíte de testes `k6`) para comparar outros padrões (como Retry e Rate Limiter) ou investigar o impacto dos diferentes parâmetros do Circuit Breaker (ex: `slidingWindowSize`, `waitDurationInOpenState`), algo que se alinha perfeitamente com a análise paramétrica proposta no estudo de Pinheiro et al.
