# Procedimento Experimental de Coleta de Dados

O experimento consiste em 6 execuções de teste (3 cenários x 2 versões). Crie um diretório `k6-results` na raiz do projeto (ele será mapeado pelo `docker-compose.yml`).

## Passo a passo rápido

1. **Preparar diretórios:** garanta que `k6-results/` existe na raiz do projeto.
2. **Escolher a versão do serviço:** defina a variável de ambiente `PAYMENT_SERVICE_VERSION` como `v1` ou `v2` (o padrão é `v1`).
   * Exemplo: `export PAYMENT_SERVICE_VERSION=v2`
3. **Subir o ambiente:** `docker-compose up -d --build`.
4. **Conferir monitoramento:** Grafana em `http://localhost:3000` (admin/admin) e Prometheus em `http://localhost:9090`.
5. **Rodar cenário k6:** execute o comando `docker run ... cenario-completo.js` indicado abaixo, salvando a saída em `V1_Completo.json` ou `V2_Completo.json` dependendo do serviço que estiver ativo.
6. **Acompanhar métricas:** use o Grafana para observar CPU, memória, threads e, na V2, o estado do circuit breaker.
7. **Encerrar a rodada:** `docker-compose down -v`.
8. **Trocar de versão:** ajuste novamente o `build.context` para a outra pasta (`servico-pagamento-v1` ↔ `servico-pagamento-v2`).
9. **Repetir os testes k6** para gerar o segundo conjunto de relatórios JSON.
10. **Consolidar resultados:** reúna os seis arquivos em `k6-results/` e exporte gráficos do Grafana, se necessário.

## Rodada 1: Testando V1 (Baseline)

1.  **Preparar:** Certifique-se de que `PAYMENT_SERVICE_VERSION=v1`.
2.  **Subir Ambiente:** No terminal, rode `docker-compose up -d --build`. Aguarde ~1 minuto para os serviços iniciarem.
3.  **Acessar Monitoramento:**
    * Abra o **Grafana**: `http://localhost:3000` (login: admin/admin).
    * Abra o **Prometheus**: `http://localhost:9090` (verifique a aba *Targets*).
    * No Grafana, vá em "Explore" e use o *data source* "Prometheus".
4.  **Executar Testes (Coletando JSON):** – rode cada cenário em sequência utilizando a imagem oficial do k6. Os comandos abaixo assumem que você está na raiz do projeto em um ambiente Unix-like (para Windows PowerShell troque `$PWD` por `${PWD}` e, no CMD, por `%cd%`).
    * **Cenário A:** `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-A-normal.js --out json=/scripts/results/V1_Normal.json`
    * **Cenário B:** `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-B-latencia.js --out json=/scripts/results/V1_Latencia.json`
    * **Cenário C:** `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-C-falha.js --out json=/scripts/results/V1_Falha.json`
5.  **Observar:** *Durante* a execução dos cenários B e C, observe os gráficos no Grafana.
    * **Métricas de Desempenho:** `container_cpu_usage_seconds_total` (para `servico-pagamento`), `container_memory_usage_bytes` (para `servico-pagamento`).
    * **Métricas da JVM/Tomcat:** `tomcat_threads_busy` (deve atingir o máximo), `jvm_threads_live` (deve disparar), `jvm_memory_used_bytes` (para picos de GC).
6.  **Limpar:** Rode `docker-compose down -v`. (O `-v` remove os volumes de dados, limpando o estado).

## Rodada 2: Testando V2 (Circuit Breaker)

1.  **Preparar:** Certifique-se de que `PAYMENT_SERVICE_VERSION=v2`.
2.  **Subir Ambiente:** `docker-compose up -d --build`.
3.  **Acessar Monitoramento:** Abra o Grafana (`http://localhost:3000`).
4.  **Executar Testes (Coletando JSON):**
    * **Cenário Completo:** `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6/scripts:/scripts -v $PWD/k6/results:/results grafana/k6:latest run /scripts/cenario-completo.js --out json=/results/V2_Completo.json`
5.  **Observar:** *Durante* os cenários B e C, observe o Grafana.
    * **Métricas Chave do CB:** `resilience4j_circuitbreaker_state` (você verá mudar de 1 (CLOSED) para 0 (OPEN)), `resilience4j_circuitbreaker_calls_total` (observe o aumento de chamadas `failed` e `not_permitted`).
    * **Métricas de Desempenho:** Observe como `tomcat_threads_busy` e `jvm_threads_live` permanecem **baixos e estáveis**. Verifique `container_cpu_usage_seconds_total`, que não deve disparar, provando que o CB está protegendo o serviço.
6.  **Limpar:** Rode `docker-compose down -v`.

## Automatizando as 6 execuções

Para evitar a alternância manual entre as versões, utilize o script `run_all_tests.sh` na raiz do projeto. Ele:

1. Sobe o ambiente para a V1 (`PAYMENT_SERVICE_VERSION=v1`), executa os três cenários (`Normal`, `Latência` e `Falha`) e salva os arquivos JSON correspondentes em `k6-results/`.
2. Reinicia o ambiente com a V2 (`PAYMENT_SERVICE_VERSION=v2`) e repete os mesmos cenários, gerando os arquivos `V2_*.json`.
3. Encerra os containers ao final.

Execute:

```bash
./run_all_tests.sh
```

É possível customizar alguns parâmetros via variáveis de ambiente, por exemplo:

```bash
COMPOSE_PROJECT_NAME=tcc-performance-circuit-breaker \
COMPOSE_NETWORK_NAME=tcc-performance-circuit-breaker_tcc-network \
K6_IMAGE=grafana/k6:latest \
./run_all_tests.sh
```

> Observação: se você já utiliza diretórios `k6-scripts/` e `k6-results/` na raiz, o script os detecta automaticamente. Caso contrário, ele usa `k6/scripts/` e `k6/results/`, criando-os quando necessário.

**Final:** Você terá 6 arquivos `.json` detalhados em `k6-results` para a análise estatística do `k6`, e terá observado (e pode "printar") os gráficos do Grafana que mostram o comportamento interno (CPU, Memória, Threads, Estado do CB) durante os testes, fornecendo material rico para o TCC.
