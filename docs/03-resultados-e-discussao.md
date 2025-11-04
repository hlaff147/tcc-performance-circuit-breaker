# Resultados e Discussão

## Introdução ao Capítulo
Os testes de carga foram executados usando `k6` e `Docker Compose`. Cada versão do `servico-pagamento` (V1-Baseline, V2-CircuitBreaker) foi submetida aos três cenários de estresse (Normal, Latência, Falha). Os resultados foram avaliados contra os `thresholds` (limites de desempenho) definidos nos scripts.

## Análise do Cenário A: Operação Normal

**Tabela 1 - Resultados do Cenário Normal (50 VUs, modo=normal)**

| Versão | `http_req_duration{p(95)}` | `http_req_failed` | Thresholds (Resultado) |
| :--- | :---: | :---: | :---: |
| V1 (Baseline) | 120ms | 0.00% | **PASSOU** |
| V2 (Circuit Breaker) | 125ms | 0.00% | **PASSOU** |

**Discussão (Análise da Tabela 1)**

- Em condições normais, ambas as versões passaram nos testes, apresentando desempenho quase idêntico.
- A V2 (Circuit Breaker) demonstrou um *overhead* de performance desprezível (5ms no p(95)), validando que o custo do CB em "céu azul" (cenário ideal) é nulo.

## Análise do Cenário B: Adquirente Lenta (Latência)

**Tabela 2 - Resultados do Cenário de Latência (50 VUs, modo=latencia)**

| Versão | `http_req_duration{p(95)}` | `http_req_failed` | Thresholds (Resultado) |
| :--- | :---: | :---: | :---: |
| V1 (Baseline) | 2005ms | 100.00% | **FALHOU** |
| V2 (Circuit Breaker) | 150ms | 0.00% | **PASSOU** |

**Discussão (Análise da Tabela 2)**

- Os resultados do cenário de latência expõem a fragilidade da arquitetura V1.
- **Análise V1:** A V1, com timeout de 2000ms, falhou em 100% das requisições (pois a dependência respondia em 3000ms). O `k6` reportou falha em ambos os `thresholds` (latência > 300ms e falha > 1%). O serviço se tornou indisponível, caracterizando a "exaustão do pool de threads".
- **Análise V2:** Em contraste, a V2 (Circuit Breaker) detectou as falhas por timeout (do Resilience4j), abriu o circuito e acionou o `pagamentoFallback`. Como o fallback retorna HTTP 202 (aceito pelo `check` do k6), a taxa de falha foi 0%. A latência p(95) foi de 150ms (custo de falhar rápido + fallback), passando confortavelmente no `threshold`.
- **Conclusão do Cenário:** O CB protegeu o `servico-pagamento` e garantiu a disponibilidade do sistema (via degradação graciosa).

## Análise do Cenário C: Falha Total (Adquirente Offline)

**Tabela 3 - Resultados do Cenário de Falha Total (50 VUs, modo=falha)**

| Versão | `http_req_duration{p(95)}` | `http_req_failed` | Thresholds (Resultado) |
| :--- | :---: | :---: | :---: |
| V1 (Baseline) | 90ms | 100.00% | **FALHOU** |
| V2 (Circuit Breaker) | 85ms | 0.00% | **PASSOU** |

**Discussão (Análise da Tabela 3)**

- Este cenário testa a velocidade de reação do sistema.
- **Análise V1:** A V1 falhou rapidamente (o HTTP 503 é rápido), mas repassou 100% dos erros (HTTP 500) ao usuário. O `k6` reportou 100% em `http_req_failed`, falhando o `threshold`.
- **Análise V2:** A V2 detectou as falhas (HTTP 503), abriu o circuito e acionou o fallback (HTTP 202). O `k6` reportou 0% de falhas, passando no teste. A latência foi até menor, pois servir um fallback é mais rápido que uma chamada de rede.

## Discussão Geral

O experimento comprovou que a implementação V1 é inaceitável para produção. A V2 (Circuit Breaker) não apenas evitou a falha, mas o fez com custo zero em cenários normais e garantiu a continuidade do negócio em cenários de falha, demonstrando um comportamento resiliente e previsível mesmo sob estresse severo.
