# 📊 Cenários de Teste k6 - TCC Circuit Breaker

Este diretório contém os scripts de teste de carga k6 utilizados para avaliar o desempenho do padrão Circuit Breaker em microserviços de pagamento.

## 🎯 Objetivo

Os cenários foram projetados para demonstrar as **vantagens do Circuit Breaker** em situações de crise, onde ele faz diferença significativa na resiliência do sistema.

## 📁 Estrutura dos Scripts

```
k6/scripts/
├── cenario-operacao-normal.js      # Baseline - 100% disponibilidade
├── cenario-falha-catastrofica.js   # API completamente fora do ar
├── cenario-degradacao-gradual.js   # Lentidão progressiva da API
├── cenario-rajadas-intermitentes.js # Falhas em ondas
└── cenario-indisponibilidade-extrema.js # 75% de indisponibilidade
```

## 🔬 Descrição dos Cenários

### 1. Operação Normal (`cenario-operacao-normal.js`)

**Propósito**: Estabelecer baseline de performance e validar "overhead zero" do Circuit Breaker.

| Parâmetro | Valor |
|-----------|-------|
| Duração | 5 minutos |
| VUs | 50 (constantes) |
| Taxa de falha | 0% |
| Modo API | 100% `normal` |

**Métricas esperadas**:
- Latência P95 < 200ms
- Taxa de sucesso > 99%
- Comportamento idêntico entre V1 e V2

---

### 2. Falha Catastrófica (`cenario-falha-catastrofica.js`)

**Propósito**: Simular indisponibilidade total da API externa (servico-adquirente).

| Fase | Duração | Modo API | Descrição |
|------|---------|----------|-----------|
| Warmup | 30s | normal | Aquecimento |
| Crise | 2min | error | API 100% erro 500 |
| Recuperação | 1min | slow_recovery | API voltando gradualmente |
| Estabilização | 30s | normal | Operação normal |

**O que demonstra**:
- V1: Todas as requisições falham durante a crise
- V2: Circuit Breaker abre rapidamente, protegendo recursos

---

### 3. Degradação Gradual (`cenario-degradacao-gradual.js`)

**Propósito**: Simular API ficando cada vez mais lenta (típico de memory leak, sobrecarga).

| Fase | Duração | Latência API | Descrição |
|------|---------|--------------|-----------|
| Normal | 1min | 50ms | Baseline |
| Lentidão leve | 1min | 500ms | Início da degradação |
| Lentidão moderada | 1min | 1500ms | Degradação perceptível |
| Lentidão severa | 1min | 3000ms | Timeouts começam |
| Recuperação | 1min | 50ms | API recuperada |

**O que demonstra**:
- V1: Latência P95 sobe linearmente com a API
- V2: Circuit Breaker detecta slow calls e protege o sistema

---

### 4. Rajadas Intermitentes (`cenario-rajadas-intermitentes.js`)

**Propósito**: Simular instabilidade típica de rede/infraestrutura (falhas em ondas).

| Ciclo | Padrão |
|-------|--------|
| 1 | 20s normal → 10s falha |
| 2 | 20s normal → 10s falha |
| 3 | 20s normal → 10s falha |
| 4 | 20s normal → 10s falha |

**O que demonstra**:
- V1: Usuários afetados a cada onda de falha
- V2: CB abre/fecha conforme o estado da API, minimizando impacto

---

### 5. Indisponibilidade Extrema (`cenario-indisponibilidade-extrema.js`)

**Propósito**: Simular API com alta taxa de erro mas não totalmente fora.

| Parâmetro | Valor |
|-----------|-------|
| Duração | 4 minutos |
| Taxa de erro | 75% |
| Modo API | `high_error_rate` |

**O que demonstra**:
- V1: 75% das requisições falham
- V2: CB abre após threshold, retorna fallback rápido

---

## 🏷️ Métricas Customizadas

Todos os cenários coletam métricas adicionais:

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `requisicoes_sucesso` | Counter | Total de respostas 200 |
| `requisicoes_fallback` | Counter | Total de respostas 202 (contingência) |
| `requisicoes_falha` | Counter | Total de respostas 5xx |
| `tempo_resposta_sucesso` | Trend | Latência de requisições bem-sucedidas |
| `tempo_resposta_fallback` | Trend | Latência quando CB está aberto |
| `taxa_sucesso` | Rate | Proporção de sucessos |
| `cb_ativado` | Rate | Proporção de fallbacks (CB atuando) |

## 🏃 Execução

### Via Script

```bash
# Todos os cenários
./run_scenario_tests.sh all

# Cenário específico
./run_scenario_tests.sh catastrofe
./run_scenario_tests.sh degradacao
./run_scenario_tests.sh rajadas
./run_scenario_tests.sh indisponibilidade
./run_scenario_tests.sh normal
```

### Via Makefile

```bash
make test                    # Todos os cenários
make test-catastrofe         # Falha catastrófica
make test-degradacao         # Degradação gradual
make test-rajadas            # Rajadas intermitentes
make test-indisponibilidade  # Indisponibilidade extrema
make test-normal             # Operação normal
```

### Via Docker direto

```bash
docker-compose exec k6-tester k6 run \
    --out json="/scripts/results/output.json" \
    -e PAYMENT_BASE_URL=http://servico-pagamento:8080 \
    /scripts/cenario-falha-catastrofica.js
```

## 📤 Saída

Os resultados são salvos em:

```
k6/results/
├── scenarios/
│   ├── catastrofe_V1.json
│   ├── catastrofe_V1_summary.json
│   ├── catastrofe_V2.json
│   ├── catastrofe_V2_summary.json
│   ├── degradacao_V1.json
│   └── ...
└── ...
```

## 🔍 Tags Disponíveis

Cada requisição é tagueada para análise posterior:

| Tag | Valores | Uso |
|-----|---------|-----|
| `cenario` | nome do cenário | Filtrar por cenário |
| `versao` | V1, V2 | Comparar versões |
| `modo` | normal, error, slow, etc. | Fase do teste |
| `fase` | warmup, crise, recuperacao, etc. | Etapa do cenário |

## 📊 Análise

Após executar os testes, use o analyzer:

```bash
make analyze

# Ou diretamente:
python3 analysis/scripts/analyzer.py
python3 analysis/scripts/scenario_analyzer.py
```

## 🎛️ Configuração da API de Teste

O `servico-adquirente` aceita o parâmetro `modo` para simular diferentes estados:

| Modo | Comportamento |
|------|---------------|
| `normal` | Resposta em ~50ms, 100% sucesso |
| `error` | Retorna HTTP 500 |
| `slow` | Resposta em 2-3 segundos |
| `slow_recovery` | 50% lento, 50% normal |
| `high_error_rate` | 75% erro, 25% sucesso |
| `intermittent` | 30% erro, 70% sucesso |

## 📈 Thresholds

| Cenário | P95 Esperado V1 | P95 Esperado V2 | Taxa Sucesso V1 | Taxa Sucesso V2 |
|---------|-----------------|-----------------|-----------------|-----------------|
| Normal | < 200ms | < 200ms | > 99% | > 99% |
| Catastrófica | > 5s | < 500ms | ~0% | > 60% |
| Degradação | > 3s | < 1s | < 50% | > 70% |
| Rajadas | Variável | < 500ms | ~70% | > 85% |
| Indisponibilidade | > 3s | < 500ms | ~25% | > 60% |

## 🔗 Referências

- [k6 Documentation](https://k6.io/docs/)
- [Resilience4j Circuit Breaker](https://resilience4j.readme.io/docs/circuitbreaker)
- [TCC - Capítulo de Metodologia](../docs/chapters/02-metodologia-e-design-experimento.md)
