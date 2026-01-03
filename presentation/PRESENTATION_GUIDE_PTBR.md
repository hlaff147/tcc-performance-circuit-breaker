# Guia de Apresentação do TCC - Avaliação do Padrão Circuit Breaker
## Roteiro e Explicação de Conteúdo (PT-BR)

**Autor:** Humberto Laff  
**Orientador:** Prof. Jamilson Ramalho Dantas  
**Instituição:** Centro de Informática (CIn) - UFPE  
**Data:** Janeiro de 2026  
**Duração Estimada:** 20-25 minutos  
**Idioma dos Slides:** Inglês  
**Idioma da Fala:** Português (com termos técnicos em Inglês)

---

## Sumário

1. [Visão Geral](#visão-geral)
2. [Estrutura da Apresentação](#estrutura-da-apresentação)
3. [Notas de Fala por Slide](#notas-de-fala-por-slide)
4. [Mensagens Chave para Enfatizar](#mensagens-chave-para-enfatizar)
5. [Perguntas e Respostas Antecipadas](#perguntas-e-respostas-antecipadas)
6. [Dicas de Apresentação](#dicas-de-apresentação)

---

## Visão Geral

### Sua Pesquisa em uma Frase
"Este trabalho fornece a primeira avaliação quantitativa abrangente do padrão **Circuit Breaker** em microsserviços, demonstrando melhorias de disponibilidade de até 89 pontos percentuais através de experimentação controlada com mais de 380.000 requisições em cinco cenários de falha realistas."

### Contribuição Principal
- **Evidência empírica** (não apenas teórica) da eficácia do **Circuit Breaker**.
- **Métricas quantitativas** com validação estatística.
- **Análise comparativa** de quatro estratégias de resiliência.
- **Metodologia reproduzível** usando Docker + k6.

---

## Estrutura da Apresentação

### Alocação de Tempo (Total: ~20-25 minutos)

| Seção | Duração | Propósito |
|---------|----------|---------|
| **Introdução** | 5 min | Motivar o problema e a solução |
| **Metodologia** | 5 min | Explicar o design experimental |
| **Resultados** | 10 min | Apresentar os achados com evidências |
| **Discussão** | 3 min | Interpretar as implicações |
| **Conclusão** | 2 min | Resumir as contribuições |

---

## Notas de Fala por Slide

### SLIDE DE TÍTULO (0:00 - 0:30)

**O que dizer:**
> "Bom dia/boa tarde a todos os membros da banca. Meu nome é Humberto Laff e hoje vou apresentar meu trabalho de conclusão de curso intitulado 'Avaliação Quantitativa do Padrão Circuit Breaker em Microsserviços: Um Estudo Empírico sobre Resiliência e Performance', orientado pelo Professor Jamilson Ramalho Dantas aqui no CIn-UFPE."

---

### SLIDE DE OUTLINE (0:30 - 1:00)

**O que dizer:**
> "Esta apresentação está estruturada em cinco seções principais. Começaremos com a introdução ao problema de **cascading failures** em microsserviços. Em seguida, descreverei a metodologia experimental. Na terceira parte, apresentarei os resultados quantitativos. Depois, discutiremos as implicações práticas e, por fim, concluiremos com as contribuições e trabalhos futuros."

---

## SEÇÃO 1: INTRODUÇÃO (1:00 - 6:00)

### Slide: Context - Microservices Architecture (1:00 - 2:30)

**O que dizer:**
> "A arquitetura de microsserviços tornou-se o padrão para sistemas distribuídos modernos. Ela oferece benefícios claros como deploy independente, escalabilidade seletiva e autonomia para os times. No entanto, essa independência lógica depende de comunicação síncrona — tipicamente REST via HTTP — o que cria um forte acoplamento temporal entre os serviços."

**Enfatize o desafio:**
> "O grande desafio aqui é o risco de **cascading failures** (falhas em cascata). Quando um serviço dependente falha ou fica lento, o serviço consumidor fica bloqueado esperando o **timeout**. Isso pode levar à exaustão do **thread pool** e derrubar o sistema inteiro."

**Impacto Financeiro:**
> "O custo do **downtime** é altíssimo. No setor bancário, estima-se perdas de até 9 mil dólares por minuto. Por isso, resiliência não é apenas um detalhe técnico, é um imperativo de negócio."

---

### Slide: The Problem - Cascading Failures (2:30 - 3:30)

**O que dizer:**
> "Vamos ilustrar o problema das falhas em cascata. Imagine que o Serviço A chama o Serviço B. Se o Serviço B falha, as threads do Serviço A ficam presas esperando o **timeout** (geralmente 2 a 3 segundos). Sob carga alta, todas as threads disponíveis se esgotam. Isso é o que chamamos de **Thread Pool Starvation**. O resultado? Até os endpoints saudáveis do Serviço A param de responder, e o sistema colapsa como um dominó."

---

### Slide: The Solution - Circuit Breaker Pattern (3:30 - 4:30)

**O que dizer:**
> "A solução é o padrão **Circuit Breaker**. A analogia é com o disjuntor elétrico da nossa casa: ele detecta um surto de falhas e 'desarma' para proteger o sistema. Ele opera em três estados:
> - **Closed**: Operação normal.
> - **Open**: Modo **Fail-Fast**, onde as requisições são rejeitadas imediatamente com um **fallback**.
> - **Half-Open**: Um estado de teste para verificar se o serviço se recuperou."

**Benefícios:**
> "Os principais benefícios são o **Fail-Fast** (resposta imediata), proteção de recursos (liberação de threads) e a degradação graciosa através do **fallback** (usando HTTP 202 Accepted)."

---

### Slide: Research Objectives (4:30 - 6:00)

**O que dizer:**
> "Apesar de muito discutido, há poucos estudos quantitativos sobre o impacto real do **Circuit Breaker**. Meu objetivo foi medir esse impacto: Qual a melhoria real na disponibilidade? Como ele se compara ao padrão **Retry**? Qual a redução na latência? E como ele protege os recursos do sistema?"

---

## SEÇÃO 2: METODOLOGIA (6:00 - 11:00)

### Slide: Experimental Architecture (6:00 - 7:00)

**O que dizer:**
> "Para este estudo, desenvolvi uma **Proof of Concept (POC)** com dois microsserviços Spring Boot rodando em Docker. O **payment-service** consome o **acquirer-service**. Usei o **k6** para gerar carga e simular cenários de falha. A POC é minimalista (sem banco de dados ou cache) justamente para isolar o efeito do **Circuit Breaker** como única variável."

---

### Slide: Four Service Versions (7:00 - 8:30)

**O que dizer:**
> "Comparamos quatro versões:
> - **V1 (Baseline)**: Apenas **timeouts** básicos.
> - **V2 (Circuit Breaker)**: Implementação com **Resilience4j**.
> - **V3 (Retry)**: Três tentativas com **exponential backoff**.
> - **V4 (Composition)**: A estratégia mais robusta, combinando **Retry** e **Circuit Breaker** em camadas."

---

### Slide: Test Scenarios (8:30 - 9:30)

**O que dizer:**
> "Criamos cinco cenários realistas: desde operação normal até **indisponibilidade extrema** (75% de falhas), passando por rajadas de falhas e catástrofes totais. No total, analisamos mais de 380 mil requisições."

---

## SEÇÃO 3: RESULTADOS (11:00 - 21:00)

### Slide: Key Results - Availability Gains (11:00 - 13:30)

**O que dizer:**
> "Este é o resultado mais impactante: No cenário de **Extreme Unavailability**, a versão sem proteção (V1) teve apenas 10.3% de disponibilidade. Com o **Circuit Breaker** (V2/V4), subimos para mais de 99%. Isso é uma melhoria de quase 10 vezes na disponibilidade percebida pelo usuário!"

---

### Slide: Statistical Validation (15:30 - 17:00)

**O que dizer:**
> "Validamos os dados estatisticamente. O teste **Mann-Whitney U** mostrou um p-valor menor que 0.0001, indicando alta significância. O **Cliff's Delta** de 0.500 confirma um **Large Effect Size** (grande tamanho de efeito), provando que a melhoria não é apenas estatística, mas tem relevância prática enorme no mundo real."

---

### Slide: V3 (Retry) vs V2 (Circuit Breaker) (18:45 - 19:30)

**O que dizer:**
> "Um ponto crucial: o **Retry** sozinho (V3) pode ser perigoso. Ele causa **Load Amplification**, enviando ainda mais requisições para um serviço que já está sofrendo. Isso pode gerar um efeito de **Victim DoS**, impedindo a recuperação do serviço. O **Circuit Breaker** resolve isso ao interromper o tráfego e permitir que o serviço se recupere."

---

## SEÇÃO 4: CONCLUSÃO (23:30 - 25:30)

### Slide: Final Message (27:00 - 27:45)

**O que dizer:**
> "Para concluir, o **Circuit Breaker** é essencial para microsserviços críticos. Ele transforma falhas catastróficas em degradação graciosa. Minha recomendação principal é usar a estratégia **V4 (Composition)**, que une o melhor dos dois mundos: o **Retry** absorve instabilidades momentâneas e o **Circuit Breaker** protege contra falhas persistentes."

---

## Dicas de Apresentação

- **Termos Técnicos:** Use termos como *Fail-Fast*, *Fallback*, *Thread Pool*, *Starvation*, *Throughput* e *Latency* naturalmente, mas explique o conceito se sentir que a banca não é da área.
- **Foco nos Gráficos:** Quando mostrar o gráfico de **State Transitions**, aponte para as áreas vermelhas (circuito aberto) e mostre como a latência cai para quase zero.
- **Postura:** Mantenha contato visual com todos os membros da banca. Use as mãos para explicar a analogia do disjuntor.
- **Tempo:** Se estiver sobrando tempo, detalhe mais a configuração do **Resilience4j**. Se estiver acabando, foque direto no ganho de 89 pontos percentuais de disponibilidade.
