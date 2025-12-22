# Metodologia e Design do Experimento

## 1. Visão Geral da Metodologia
Este Trabalho de Conclusão de Curso adota uma abordagem de **pesquisa experimental quantitativa**. O método consiste em construir um protótipo controlado que simula um ecossistema de pagamentos composto por dois microsserviços. A investigação compara duas variações arquiteturais do `servico-pagamento`: (i) uma versão Baseline, sem mecanismos avançados de resiliência, e (ii) uma versão com Circuit Breaker implementado via Resilience4j. Ambas as variações serão orquestradas com `Docker Compose` e submetidas a campanhas de testes de carga desenvolvidas em `k6`, permitindo coletar métricas objetivas de desempenho (vazão e latência) e resiliência (taxa de erro) para embasar a análise comparativa.

## 2. Ferramentas e Tecnologias (O Stack)
O experimento será conduzido com um conjunto integrado de ferramentas que sustentam tanto o desenvolvimento quanto a execução controlada dos cenários de teste:

- **Java 17+ e Spring Boot 3:** fundamentos para a implementação dos microsserviços do ecossistema de pagamentos.
- **Spring Cloud OpenFeign:** cliente declarativo utilizado para a comunicação síncrona entre `servico-pagamento` e `servico-adquirente`.
- **Spring Cloud Resilience4j:** biblioteca responsável por fornecer o mecanismo de Circuit Breaker e demais padrões de tolerância a falhas.
- **Docker e Docker Compose:** garantem que o ambiente experimental seja isolado, reproduzível e facilmente provisionado, seguindo a mesma filosofia do arquivo `docker-compose.yml` do projeto de exemplo.
- **Grafana k6:** ferramenta de testes de carga escrita em JavaScript, que permite descrever cenários com usuários virtuais, estágios de carga e `thresholds` semelhantes aos scripts `teste-*.js` do repositório de referência.
- **Micrometer + Prometheus (opcional):** componentes auxiliares que podem ser utilizados para instrumentar e exportar métricas internas, como o estado atual do Circuit Breaker, oferecendo visibilidade complementar às medidas capturadas pelo k6.

## 3. Arquitetura do Sistema Experimental
O ambiente experimental será composto por dois microsserviços desenvolvidos em Spring Boot e empacotados como contêineres Docker.

### 3.1 `servico-adquirente` — Ponto de Falha Controlado
- **Função:** simular um gateway externo de pagamento (por exemplo, Cielo ou Rede) responsável por autorizar transações.
- **Endpoint:** expõe `POST /autorizar` para receber solicitações de autorização.
- **Controle Experimental:** o comportamento é configurável via o parâmetro de query `?modo=`:
  - `modo=normal`: responde em aproximadamente 50 ms com HTTP 200 (OK).
  - `modo=latencia`: responde em 3000 ms (utilizando `Thread.sleep()`) com HTTP 200 (OK).
  - `modo=falha`: responde imediatamente com HTTP 500 (Internal Server Error).

### 3.2 `servico-pagamento` — Sistema Sob Teste
- **Função:** orquestrar o fluxo de pagamento exposto aos clientes finais e consumir o `servico-adquirente` síncronamente.
- **Endpoint:** expõe `POST /pagar`, que será exercitado pelos scripts do k6.
- **Lógica de Negócio:** utiliza um Feign Client para delegar a autorização ao `servico-adquirente`. Este serviço possuirá duas versões, que configuram a variável independente do experimento.

## 4. Variáveis do Experimento

### 4.1 Variável Independente — Estratégia de Resiliência no `servico-pagamento`
- **V1: Baseline (Controle):** implementação ingênua que apenas configura timeouts curtos (por exemplo, 2 segundos) no Feign Client para conexão e leitura.
- **V2: Circuit Breaker + Fallback:** implementação robusta com Resilience4j. O Circuit Breaker é configurado para abrir após detectar, por exemplo, 50% de falhas em uma janela de requisições. Quando o circuito está aberto, um método de fallback devolve HTTP 202 (Accepted) com a mensagem "Pagamento recebido e agendado para processamento posterior.", caracterizando uma degradação graciosa similar ao comportamento validado nos testes `teste-escrita-kafka.js` do projeto de referência.

### 4.2 Variáveis Dependentes — Métricas coletadas via k6
- **`http_reqs`:** número total de requisições processadas, utilizado como medida de vazão.
- **`http_req_duration{p(95)}`:** percentil 95 do tempo de resposta, indicador de latência sob carga.
- **`http_req_failed`:** taxa de requisições consideradas falhas pelo k6, refletindo a resiliência percebida.

## 5. Plano de Execução — Cenários de Teste k6
Três scripts de teste serão desenvolvidos em k6, e cada um deles será executado duas vezes: uma para a versão Baseline (V1) e outra para a versão com Circuit Breaker (V2). Todos os cenários utilizam 50 usuários virtuais (VUs) executando por 1 minuto.

### 5.1 Cenário A — Operação Normal
- **URL invocada:** `POST /pagar?modo=normal`.
- **Objetivo:** verificar a sanidade do sistema quando o `servico-adquirente` opera normalmente.
- **Thresholds:** `http_req_duration{p(95)} < 200ms` e `http_req_failed < 0.01`.

### 5.2 Cenário B — Adquirente com Alta Latência
- **URL invocada:** `POST /pagar?modo=latencia`.
- **Objetivo:** avaliar o comportamento sob latência extrema introduzida pelo `servico-adquirente`.
- **Thresholds:** `http_req_duration{p(95)} < 300ms`. Espera-se que a V1 não cumpra este threshold, enquanto a V2 deve mantê-lo graças ao Circuit Breaker.

### 5.3 Cenário C — Falha Total do Adquirente
- **URL invocada:** `POST /pagar?modo=falha`.
- **Objetivo:** testar a resiliência diante de falha total do `servico-adquirente` (HTTP 500 imediato).
- **Thresholds:** `http_req_failed < 0.01`. A versão Baseline deve falhar, enquanto a versão com Circuit Breaker e fallback deve passar, retornando HTTP 202 e mantendo a disponibilidade do serviço de pagamentos.

Com este design experimental, os resultados quantitativos obtidos pelo k6 permitirão comparar de maneira objetiva o impacto do padrão Circuit Breaker na manutenção de vazão, na redução da latência percebida e na mitigação de falhas durante cenários adversos, fornecendo a validação empírica proposta por este TCC.
