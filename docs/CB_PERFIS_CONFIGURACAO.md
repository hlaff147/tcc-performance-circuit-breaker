# 🎚️ Perfis de Configuração do Circuit Breaker

Este guia apresenta os perfis oficiais utilizados no projeto para calibrar o Circuit Breaker (CB) do `payment-service`. Cada perfil foi testado nos cenários descritos em `ANALISE_FINAL_TCC.md` e pode ser aplicado rapidamente nos ambientes de laboratório ou produção.

## 🧱 Estrutura Geral do Circuit Breaker
Todos os perfis compartilham os mesmos componentes:
- **Janela deslizante** baseada em quantidade de chamadas (`slidingWindowSize`).
- **Threshold de falhas** que dispara a abertura (`failureRateThreshold`).
- **Janela de recuperação** controlada por `waitDurationInOpenState`.
- **Modo half-open** com quantidade limitada de chamadas de teste (`permittedNumberOfCallsInHalfOpenState`).
- **Timeout e limites de chamadas lentas** para evitar saturação.

Os ajustes abaixo definem o comportamento desejado em cada perfil.

---

## ✅ Perfil Equilibrado (Recomendado)
> **Objetivo:** Equilíbrio entre proteção e disponibilidade. Ideal para ambientes com falhas ocasionais e impacto crítico em indisponibilidade.

```yaml
failureRateThreshold: 50
slidingWindowSize: 20
minimumNumberOfCalls: 10
waitDurationInOpenState: 10s
permittedNumberOfCallsInHalfOpenState: 5
slowCallDurationThreshold: 2000ms
slowCallRateThreshold: 80
timeoutDuration: 2500ms
```

### Por que usar
- Mantém mais de 90% de disponibilidade nos três cenários críticos.
- Evita abertura prematura em rajadas curtas.
- Fecha rapidamente após a recuperação do fornecedor externo.

### Indicadores esperados
- **Taxa de sucesso:** 92% ±3%
- **Taxa de abertura do CB:** 25% ±10%
- **Latência média:** até 25% maior que o baseline (trade-off aceitável).

---

## 🛡️ Perfil Conservador (Alta Disponibilidade)
> **Objetivo:** Priorizar disponibilidade mesmo sob falhas frequentes, aceitando algum tráfego defeituoso.

```yaml
failureRateThreshold: 60
slidingWindowSize: 30
minimumNumberOfCalls: 15
waitDurationInOpenState: 15s
permittedNumberOfCallsInHalfOpenState: 10
slowCallDurationThreshold: 3000ms
slowCallRateThreshold: 90
timeoutDuration: 3000ms
```

### Quando aplicar
- Integrações com SLA elevado (99%+).
- Sistemas que podem tolerar respostas lentas temporárias.
- Cenários em que o cliente final prefere uma resposta lenta a uma interrupção.

### Indicadores esperados
- **Taxa de sucesso:** 94% ±2%
- **Taxa de abertura do CB:** 15% ±5%
- **Latência média:** até 35% maior que o baseline.

---

## ⚡ Perfil Agressivo (Proteção Máxima)
> **Objetivo:** Reagir instantaneamente a falhas severas, mesmo sacrificando disponibilidade. Útil apenas em ambientes extremamente instáveis.

```yaml
failureRateThreshold: 30
slidingWindowSize: 10
minimumNumberOfCalls: 5
waitDurationInOpenState: 5s
permittedNumberOfCallsInHalfOpenState: 3
slowCallDurationThreshold: 1500ms
slowCallRateThreshold: 50
timeoutDuration: 1500ms
```

### Riscos conhecidos
- Pode permanecer aberto por longos períodos em cargas normais com ruído.
- Reduz a taxa de sucesso para abaixo de 20% nos cenários de referência.
- Deve ser usado apenas em situações emergenciais e por tempo limitado.

---

## 🔁 Como alternar entre perfis
1. Edite `services/payment-service-v2/src/main/resources/application.yml`.
2. Substitua os valores da instância `adquirente-cb` pelo perfil desejado.
3. Rebuild do serviço:
   ```bash
   docker-compose down
   PAYMENT_SERVICE_VERSION=v2 docker-compose build --no-cache servico-pagamento
   docker-compose up -d
   ```
4. Execute `./run_and_analyze.sh <cenario>` para validar o comportamento.

---

## 📈 Monitoramento recomendado
- **Prometheus:** métricas `resilience4j_circuitbreaker_state` e `resilience4j_circuitbreaker_calls`.
- **Grafana:** dashboards em `monitoring/grafana/dashboards/`.
- **Alertas:** configure limites para a taxa de abertura do CB e para o volume de HTTP 500.

---

## 📚 Referências cruzadas
- **Resultados consolidados:** `ANALISE_FINAL_TCC.md`.
- **Procedimentos de execução e troubleshooting:** `GUIA_EXECUCAO.md`.
- **Estrutura completa do projeto:** `ESTRUTURA_PROJETO.md`.

