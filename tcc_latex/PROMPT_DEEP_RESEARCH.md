# Prompt para Deep Research — TCC Circuit Breaker

## Contexto do Trabalho

Estou desenvolvendo um **Trabalho de Conclusão de Curso (TCC)** na área de Ciência da Computação na **Universidade Federal de Pernambuco (UFPE)**, com o seguinte título:

> **"Análise de Desempenho e Resiliência em Microsserviços Síncronos: Um Estudo Experimental do Padrão Circuit Breaker"**

### Resumo do TCC

O trabalho investiga o problema de **falhas em cascata** causadas por comunicação síncrona entre microsserviços. O estudo utiliza uma **prova de conceito (POC)** que simula um sistema de pagamentos com dois microsserviços:

- `servico-pagamento`: orquestra a jornada de checkout
- `servico-adquirente`: simula um gateway de pagamento externo (Cielo, Rede, etc.)

Foram implementadas **três versões** do serviço de pagamento:
1. **V1 (Baseline)**: sem mecanismos de resiliência, apenas timeouts básicos
2. **V2 (Circuit Breaker)**: implementa Resilience4j com fallback (HTTP 202)
3. **V3 (Retry)**: implementa retry com backoff exponencial, sem Circuit Breaker

### Tecnologias Utilizadas
- Java 17, Spring Boot 3, Spring Cloud OpenFeign
- Resilience4j (Circuit Breaker, Retry)
- Docker e Docker Compose
- Grafana k6 para testes de carga

### Cenários de Teste Executados
1. **Falha Catastrófica**: 100% de indisponibilidade por 5 minutos
2. **Degradação Gradual**: taxa de falhas crescente (5% → 50%)
3. **Rajadas Intermitentes**: 3 ciclos de 100% falha por 1 minuto
4. **Indisponibilidade Extrema**: 75% do tempo offline
5. **Cenário Normal**: validação de overhead em condições saudáveis

### Principais Resultados Obtidos

| Cenário | V1 Sucesso | V2 Sucesso | Melhoria |
|---------|------------|------------|----------|
| Catástrofe | 35,7% | 95,1% | +59,3pp |
| Degradação | 75,4% | 95,4% | +20,0pp |
| Indisponibilidade | 10,5% | 99,6% | +89,1pp |
| Rajadas | 63,0% | 96,7% | +33,6pp |

- **V3 (Retry)** mostrou-se ineficaz contra falhas persistentes
- **Análise estatística**: teste t (p < 0,0001), Cohen's d = 1,078 (efeito grande)

---

## Objetivo da Pesquisa

Preciso de **referências acadêmicas e técnicas** para embasar meu TCC nas seguintes áreas:

### 1. Arquitetura de Microsserviços
- Definições acadêmicas de microsserviços
- Estudos sobre comunicação síncrona vs assíncrona
- Problemas de acoplamento temporal em sistemas distribuídos
- Artigos sobre falhas em cascata (cascading failures)

### 2. Padrões de Resiliência e Tolerância a Falhas
- Definições formais do padrão Circuit Breaker
- Comparações entre Circuit Breaker, Retry, Bulkhead, Rate Limiter
- Estudos sobre fail-fast e graceful degradation
- Artigos sobre proteção de recursos (thread pool starvation)

### 3. Estudos Empíricos e Experimentais
- Trabalhos que avaliam quantitativamente o Circuit Breaker
- Benchmarks de desempenho em microsserviços
- Estudos de caso em sistemas de pagamentos/e-commerce
- Metodologias de testes de carga e stress testing

### 4. Implementações e Frameworks
- Comparações entre Hystrix e Resilience4j
- Estudos sobre configuração ótima de Circuit Breakers
- Artigos sobre Stochastic Petri Nets para modelagem de CB

### 5. Análise Estatística
- Justificativas para uso de testes não-paramétricos em sistemas distribuídos
- Medidas de effect size (Cohen's d, Cliff's delta)
- Metodologias de análise de dados de performance

---

## Referências que Já Tenho

Para referência, já utilizo as seguintes fontes:

- **Nygard, M.T.** (2018). *Release It! Design and Deploy Production-Ready Software*
- **Newman, S.** (2021). *Building Microservices*
- **Richardson, C.** (2018). *Microservices Patterns*
- **Fowler, M.** (2014). CircuitBreaker (martinfowler.com)
- **Pinheiro, B. & Dantas, J.** (2024). Performance Modeling with Stochastic Petri Nets
- **Netflix Technology Blog** (2016). Making the Netflix API More Resilient

---

## Formato das Referências Desejado

Para cada referência encontrada, forneça:
1. **Citação completa** (autores, título, publicação, ano)
2. **Resumo relevante** para meu TCC
3. **Seção sugerida** do TCC onde usar (Fundamentação, Metodologia, Resultados, etc.)
4. **Link/DOI** quando disponível

---

## Prioridades de Busca

1. **Alta prioridade**: Artigos científicos peer-reviewed (IEEE, ACM, Springer)
2. **Média prioridade**: Livros técnicos reconhecidos na área
3. **Baixa prioridade**: Documentação oficial e blogs técnicos confiáveis

Prefiro referências **recentes (2018-2024)**, mas clássicos fundamentais também são bem-vindos.
