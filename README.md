# TCC Performance Circuit Breaker

Um laboratório completo para comparar a resiliência e o desempenho de duas versões de um serviço de pagamento Java: uma versão _baseline_ (sem proteção) e outra com **Resilience4j Circuit Breaker**. O ambiente usa Docker Compose para orquestrar os serviços de pagamento, adquirente, Prometheus, Grafana e k6.

## 🧭 Visão geral do repositório

| Diretório / arquivo | Descrição |
| --- | --- |
| `servico-pagamento-v1/` | Implementação base sem circuit breaker. |
| `servico-pagamento-v2/` | Implementação com Resilience4j Circuit Breaker. |
| `servico-adquirente/` | Simula o provedor externo que responde com diferentes latências/falhas. |
| `k6-scripts/` | Cenários de carga (_normal_, _latência_ e _falha_). |
| `k6-results/` | Pasta montada pelo k6 para armazenar os relatórios `.json`. |
| `grafana-provisioning/`, `prometheus/` | Dashboards e configuração das métricas. |
| `INSTRUCOES.md` | Guia detalhado do experimento e métricas a observar. |

## 🏗️ Arquitetura em alto nível

```
+-------------------+      +--------------------+
| k6 (load testing) | ---> | Serviço de Pagamento|
|                   |      |  V1 ou V2 (Spring) |
+-------------------+      +----------+---------+
                                       |
                                       v
                            +--------------------+
                            | Serviço Adquirente |
                            +--------------------+

Prometheus <---- exporters & métricas ----> Grafana dashboards
```

## 🚀 Passo a passo rápido

1. **Pré-requisitos:** Docker e Docker Compose instalados.
2. **Preparar diretórios:** garanta que `k6-results/` existe na raiz do projeto.
3. **Escolher a versão:** edite `docker-compose.yml` e ajuste `servico-pagamento.build.context` para `./servico-pagamento-v1` (baseline) ou `./servico-pagamento-v2` (circuit breaker).
4. **Subir os serviços:**
   ```bash
   docker-compose up -d --build
   ```
5. **Verificar monitoramento:** Grafana em `http://localhost:3000` (login `admin/admin`) e Prometheus em `http://localhost:9090`.
6. **Rodar os cenários k6** (detalhes abaixo) para gerar `V1_*.json` ou `V2_*.json` em `k6-results/`.
7. **Acompanhar métricas ao vivo:** CPU/memória dos contêineres, threads da JVM e, para a V2, o estado do circuit breaker (`resilience4j_circuitbreaker_state`).
8. **Encerrar a rodada:**
   ```bash
   docker-compose down -v
   ```
9. **Trocar de versão** (V1 ↔ V2) e repetir os cenários para comparar resultados.

## 🧪 Executando os cenários k6

> Os comandos a seguir assumem que você está na raiz do repositório em um terminal Unix-like. Se estiver no Windows use `${PWD}` (PowerShell) ou `%cd%` (CMD) no lugar de `$PWD`.

| Cenário | Comando (V1) | Comando (V2) |
| --- | --- | --- |
| Tráfego normal | `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-A-normal.js --out json=/scripts/results/V1_Normal.json` | `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-A-normal.js --out json=/scripts/results/V2_Normal.json` |
| Latência simulada | `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-B-latencia.js --out json=/scripts/results/V1_Latencia.json` | `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-B-latencia.js --out json=/scripts/results/V2_Latencia.json` |
| Falha do adquirente | `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-C-falha.js --out json=/scripts/results/V1_Falha.json` | `docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network -v $PWD/k6-scripts:/scripts -v $PWD/k6-results:/scripts/results grafana/k6:latest run /scripts/cenario-C-falha.js --out json=/scripts/results/V2_Falha.json` |

### Dicas rápidas
- Aguarde o término de cada cenário antes de iniciar o próximo para evitar sobreposição de métricas.
- Os relatórios JSON ficam em `k6-results/` e podem ser importados em ferramentas como o [k6 Report Viewer](https://github.com/k6io/k6-reporter).
- Se o nome da rede do Docker Compose for diferente, ajuste o parâmetro `--network`. Você pode checar o nome com `docker network ls`.

## 📊 Métricas recomendadas

| Métrica | Onde observar | Por quê |
| --- | --- | --- |
| `container_cpu_usage_seconds_total`, `container_memory_usage_bytes` | Grafana → painel de Docker/Containers | Compara consumo de recursos entre V1 e V2. |
| `tomcat_threads_busy`, `jvm_threads_live`, `jvm_memory_used_bytes` | Grafana → painel JVM | Evidenciam saturação da aplicação sem circuit breaker. |
| `resilience4j_circuitbreaker_state`, `resilience4j_circuitbreaker_calls_total` | Grafana → painel Circuit Breaker | Mostra abertura/fechamento do circuito e chamadas bloqueadas. |

## 🧹 Troubleshooting

- **k6 não encontra scripts**: confirme que está na raiz do projeto ao executar o comando e que a pasta `k6-scripts/` existe.
- **Erro de rede no k6**: valide o nome da rede Docker (`docker network ls`) e troque `tcc-performance-circuit-breaker_tcc-network` se necessário.
- **Grafana vazio**: aguarde alguns segundos após subir os serviços; os dashboards são provisionados automaticamente.

Para detalhes completos do experimento (descrição longa, métricas e interpretações), consulte o arquivo [`INSTRUCOES.md`](INSTRUCOES.md).
