# Procedimento Experimental de Coleta de Dados

O experimento consiste em 6 execuções de teste (3 cenários x 2 versões). Crie um diretório `k6-results` na raiz do projeto (ele será mapeado pelo `docker-compose.yml`).

## Rodada 1: Testando V1 (Baseline)

1.  **Preparar:** Edite o `docker-compose.yml` (linha 22) para que o `build` do `servico-pagamento` aponte para o diretório da **V1 (Baseline)**.
    * `context: ./servico-pagamento-v1`
2.  **Subir Ambiente:** No terminal, rode `docker-compose up -d --build`. Aguarde ~1 minuto para os serviços iniciarem.
3.  **Acessar Monitoramento:**
    * Abra o **Grafana**: `http://localhost:3000` (login: admin/admin).
    * Abra o **Prometheus**: `http://localhost:9090` (verifique a aba *Targets*).
    * No Grafana, vá em "Explore" e use o *data source* "Prometheus".
4.  **Executar Testes (Coletando JSON):**
    * **Cenário A:** `docker exec k6-tester k6 run /scripts/cenario-A-normal.js --out json=/scripts/results/V1_Normal.json`
    * **Cenário B:** `docker exec k6-tester k6 run /scripts/cenario-B-latencia.js --out json=/scripts/results/V1_Latencia.json`
    * **Cenário C:** `docker exec k6-tester k6 run /scripts/cenario-C-falha.js --out json=/scripts/results/V1_Falha.json`
5.  **Observar:** *Durante* a execução dos cenários B e C, observe os gráficos no Grafana.
    * **Métricas de Desempenho:** `container_cpu_usage_seconds_total` (para `servico-pagamento`), `container_memory_usage_bytes` (para `servico-pagamento`).
    * **Métricas da JVM/Tomcat:** `tomcat_threads_busy` (deve atingir o máximo), `jvm_threads_live` (deve disparar), `jvm_memory_used_bytes` (para picos de GC).
6.  **Limpar:** Rode `docker-compose down -v`. (O `-v` remove os volumes de dados, limpando o estado).

## Rodada 2: Testando V2 (Circuit Breaker)

1.  **Preparar:** Edite o `docker-compose.yml` (linha 22) para que o `build` do `servico-pagamento` aponte para o diretório da **V2 (Circuit Breaker)**.
    * `context: ./servico-pagamento-v2`
2.  **Subir Ambiente:** `docker-compose up -d --build`.
3.  **Acessar Monitoramento:** Abra o Grafana (`http://localhost:3000`).
4.  **Executar Testes (Coletando JSON):**
    * **Cenário A:** `docker exec k6-tester k6 run /scripts/cenario-A-normal.js --out json=/scripts/results/V2_Normal.json`
    * **Cenário B:** `docker exec k6-tester k6 run /scripts/cenario-B-latencia.js --out json=/scripts/results/V2_Latencia.json`
    * **Cenário C:** `docker exec k6-tester k6 run /scripts/cenario-C-falha.js --out json=/scripts/results/V2_Falha.json`
5.  **Observar:** *Durante* os cenários B e C, observe o Grafana.
    * **Métricas Chave do CB:** `resilience4j_circuitbreaker_state` (você verá mudar de 1 (CLOSED) para 0 (OPEN)), `resilience4j_circuitbreaker_calls_total` (observe o aumento de chamadas `failed` e `not_permitted`).
    * **Métricas de Desempenho:** Observe como `tomcat_threads_busy` e `jvm_threads_live` permanecem **baixos e estáveis**. Verifique `container_cpu_usage_seconds_total`, que não deve disparar, provando que o CB está protegendo o serviço.
6.  **Limpar:** Rode `docker-compose down -v`.

**Final:** Você terá 6 arquivos `.json` detalhados em `k6-results` para a análise estatística do `k6`, e terá observado (e pode "printar") os gráficos do Grafana que mostram o comportamento interno (CPU, Memória, Threads, Estado do CB) durante os testes, fornecendo material rico para o TCC.
