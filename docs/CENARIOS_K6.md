# 📊 Cenários de Teste k6 - Explicação Detalhada

## Visão Geral

Os testes simulam diferentes padrões de falha do `servico-adquirente` para avaliar como o Circuit Breaker (V2) protege o `servico-pagamento` comparado à versão Baseline (V1).

### Modos do Serviço Adquirente
| Modo | Comportamento | HTTP Response |
|------|---------------|---------------|
| `normal` | Resposta em ~50ms | 200 OK |
| `latencia` | Resposta em ~3000ms (simula lentidão) | 200 OK |
| `falha` | Resposta imediata com erro | 500 Error |

### Respostas Possíveis do Sistema
| Status | Significado | Quem Retorna |
|--------|-------------|--------------|
| 200/201 | Sucesso real | API funcionou |
| 202 | Fallback (pagamento agendado) | Circuit Breaker aberto (V2) |
| 500 | Erro da API externa | Falha propagada |

---

## 🔴 Cenário 1: Falha Catastrófica

**Objetivo:** Simular queda total do servidor externo (deploy problemático, crash).

### Timeline (13 minutos)
```
0-1min    │████░░░░░░░░░│ Aquecimento (50 VUs)
1-4min    │████████░░░░░│ Normal (100 VUs) - 70% ok, 20% lento, 10% falha
4-9min    │█████████████│ CATÁSTROFE (150 VUs) - 100% FALHA ⚠️
9-12min   │████████░░░░░│ Recuperação (100 VUs) - 60% ok, 25% lento, 15% falha
12-13min  │░░░░░░░░░░░░░│ Cooldown
```

### O que acontece
- **Minutos 4-9:** API externa 100% indisponível
- **V1:** Todas as requisições aguardam timeout (~3s), threads bloqueadas, cascata de falhas
- **V2:** CB detecta falhas em ~10s, abre circuito, retorna fallback (HTTP 202) em <100ms

### Resultado Esperado
| Métrica | V1 | V2 |
|---------|----|----|
| Taxa Sucesso | ~90% | ~94.5% |
| Fallback | N/A | ~59% |
| Tempo Resposta (catástrofe) | ~3000ms | ~85ms |

---

## 🟠 Cenário 2: Degradação Gradual

**Objetivo:** Simular degradação progressiva (memory leak, conexões esgotando, CPU alta).

### Timeline (13 minutos)
```
0-2min    │████░░░░░░░░░│ Saudável (100 VUs) - 5% falha, 15% lento
2-5min    │████████░░░░░│ Degradação (150 VUs) - 20% falha, 30% lento
5-8min    │█████████████│ CRÍTICO (200 VUs) - 50% falha, 40% lento ⚠️
8-12min   │████████░░░░░│ Recuperação (100 VUs) - 15% falha, 25% lento
12-13min  │░░░░░░░░░░░░░│ Cooldown
```

### O que acontece
- Sistema piora gradualmente ao longo do tempo
- Simula situação real de degradação em produção
- **V1:** Degrada junto com a API
- **V2:** CB detecta aumento de falhas e pode isolar antes do colapso

### Resultado Esperado
| Métrica | V1 | V2 |
|---------|----|----|
| Taxa Sucesso | ~94.7% | ~94.9% |
| Fallback | N/A | ~0% |
| Ganho | — | +0.22pp |

> **Nota:** Ganho marginal porque degradação não foi severa o suficiente para acionar CB consistentemente. Demonstra que CB **não introduz overhead** em cenários moderados.

---

## 🟡 Cenário 3: Rajadas Intermitentes

**Objetivo:** Simular falhas em rajadas - períodos de 100% falha alternados com normalidade.

### Timeline (13 minutos)
```
0-1min    │████░░░░░░░░░│ Aquecimento (100 VUs)
1-3min    │████████░░░░░│ Normal (150 VUs) - 80% ok, 15% lento, 5% falha
3-4min    │█████████████│ RAJADA 1 (200 VUs) - 100% FALHA ⚠️
4-6min    │████████░░░░░│ Normal (150 VUs)
6-7min    │█████████████│ RAJADA 2 (200 VUs) - 100% FALHA ⚠️
7-9min    │████████░░░░░│ Normal (150 VUs)
9-10min   │█████████████│ RAJADA 3 (200 VUs) - 100% FALHA ⚠️
10-12min  │████████░░░░░│ Normal (150 VUs)
12-13min  │░░░░░░░░░░░░░│ Cooldown
```

### O que acontece
- 3 rajadas de falha total (1 minuto cada)
- Testa capacidade do CB de abrir/fechar dinamicamente
- **V1:** Sofre com cada rajada, recupera entre elas
- **V2:** CB abre nas rajadas, fecha nos períodos normais (elasticidade)

### Resultado Esperado
| Métrica | V1 | V2 |
|---------|----|----|
| Taxa Sucesso | ~94.9% | ~95.2% |
| Fallback | N/A | ~10.15% |
| Tempo abertura CB | — | ~8s após início da rajada |

---

## ⚫ Cenário 4: Indisponibilidade Extrema (75% OFF)

**Objetivo:** Demonstrar ganho máximo do CB com API majoritariamente indisponível.

### Timeline (9 minutos)
```
0-45s     │███░░░░░░░░░░│ Aquecimento (80 VUs)
45s-1.5min│████░░░░░░░░░│ Operação Saudável (140 VUs)
1.5-5.5min│█████████████│ FALHA PROLONGADA (180 VUs) - 4min contínuos ⚠️
5.5-7.5min│██████████░░░│ Instabilidade (200 VUs) - rajadas adicionais
7.5-8.5min│█████░░░░░░░░│ Recuperação (140 VUs)
8.5-9min  │░░░░░░░░░░░░░│ Cooldown
```

### Padrão de Indisponibilidade
- **75% do tempo:** API indisponível (ciclos de 80s, 60s em falha)
- **Janela crítica (3-7min):** 100% falha contínua por 4 minutos
- Simula manutenção prolongada com curtos períodos de recuperação

### O que acontece
- **V1:** Sistema praticamente inutilizável (~10% sucesso)
- **V2:** CB mantém sistema funcional via fallback (~97% disponibilidade)

### Resultado Esperado
| Métrica | V1 | V2 |
|---------|----|----|
| Taxa Sucesso | ~10.14% | ~97.08% |
| Fallback | N/A | ~92.80% |
| Redução Falhas | — | **-96.77%** |
| Ganho | — | **+86.94pp** |

> **Este é o cenário mais impactante**, demonstrando que o CB transforma um sistema inutilizável em um sistema funcional.

---

## 📈 Comparativo Visual

```
                V1 Sucesso    V2 Sucesso    Ganho
Catastrófica    ████████████  █████████████  +4.47pp
                90.02%        94.49%

Degradação      █████████████ █████████████  +0.22pp
                94.72%        94.94%

Rajadas         █████████████ █████████████  +0.28pp
                94.93%        95.21%

Indisponib.     ██            █████████████  +86.94pp ⭐
                10.14%        97.08%
```

---

## 🔑 Conceitos-Chave

### Por que usar diferentes cenários?
1. **Catastrófica:** Testa resposta a falhas totais súbitas
2. **Degradação:** Testa detecção de problemas graduais
3. **Rajadas:** Testa elasticidade (abrir/fechar dinâmico)
4. **Indisponibilidade:** Testa benefício máximo do fallback

### Métricas Coletadas
- `custom_success_responses` - HTTP 200/201
- `custom_fallback_responses` - HTTP 202 (degradação graciosa)
- `custom_api_failures` - HTTP 500
- `custom_circuit_breaker_open` - HTTP 202
- `custom_success_rate` - Taxa de sucesso real
- `custom_availability_rate` - Disponibilidade percebida (200 + 202)

### Configuração do Circuit Breaker (V2)
```yaml
failureRateThreshold: 50%      # Abre se >50% falhas
slowCallRateThreshold: 70%     # Abre se >70% lentas
slowCallDurationThreshold: 3s  # Define "lenta"
slidingWindowSize: 10          # Janela de análise
waitDurationInOpenState: 10s   # Tempo antes de testar
```
