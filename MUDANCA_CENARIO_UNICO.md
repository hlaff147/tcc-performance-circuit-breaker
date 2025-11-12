# 📋 Mudança para Cenário Único Completo

## 🎯 Objetivo

Simplificar a execução e análise dos testes, consolidando todos os cenários anteriores em um único cenário completo que abrange:
- Aquecimento (ramp-up)
- Carga normal
- Pico de estresse
- Manutenção sob alta carga
- Recuperação (ramp-down)
- Carga leve pós-estresse
- Desaceleração

## 📝 Alterações Realizadas

### 1. Scripts de Execução

#### `run_experiment.py`
- ✅ Modificado para executar apenas o `cenario-completo.js`
- ✅ Adicionada função `run_k6_test()` que estava faltando
- ✅ Gera arquivos `V1_Completo.json` e `V2_Completo.json`

#### `run_all_tests.sh`
- ✅ Lista de cenários reduzida para apenas `"Completo:cenario-completo.js"`
- ✅ Mantém toda a infraestrutura de execução e validação

#### `rerun_high_concurrency.sh`
- ✅ Renomeado conceitualmente para executar o cenário completo
- ✅ Atualizado para usar `cenario-completo.js`
- ✅ Gera e analisa `V1_Completo.json` e `V2_Completo.json`
- ✅ Duração estimada: ~12 minutos por versão

### 2. Scripts de Análise

#### `analysis/analyze_and_report.py`
- ✅ `SCENARIO_CONFIGS` reduzido para apenas `"Completo"`
- ✅ Limite de linhas aumentado para 300.000 (cenário mais longo)
- ✅ Mensagens atualizadas para refletir cenário único

#### `analysis/scripts/analyze_results.py`
- ✅ Loop de cenários alterado para `["Completo"]`
- ✅ Processa apenas arquivos `V1_Completo.json` e `V2_Completo.json`

#### `analysis/scripts/extract_cb_metrics.py`
- ✅ Exemplo de uso atualizado para usar `V1_Completo.json` e `V2_Completo.json`
- ✅ Mantém toda a lógica de extração de métricas do Circuit Breaker

#### `analysis/scripts/analyze_high_concurrency.py`
- ✅ Caminhos atualizados para `k6/results/V1_Completo.json` e `V2_Completo.json`
- ✅ Arquivos de saída renomeados:
  - `complete_scenario_analysis.png`
  - `complete_scenario_stats.csv`

### 3. Documentação

#### `GUIA_RAPIDO.md`
- ✅ Atualizado para refletir o cenário único
- ✅ Comandos de análise atualizados
- ✅ Duração estimada corrigida (~12 min por versão)

## 📊 Estrutura do Cenário Completo

O `cenario-completo.js` possui 7 estágios que abrangem todos os aspectos dos testes anteriores:

```javascript
stages: [
  { duration: '1m', target: 50 },   // 1. Aquecimento
  { duration: '3m', target: 50 },   // 2. Carga Normal
  { duration: '1m', target: 200 },  // 3. Pico de Estresse
  { duration: '3m', target: 200 },  // 4. Manutenção do Estresse
  { duration: '1m', target: 50 },   // 5. Recuperação
  { duration: '2m', target: 50 },   // 6. Carga Leve Pós-Estresse
  { duration: '1m', target: 0 },    // 7. Desaceleração
]
```

**Duração total:** 12 minutos por versão (V1 e V2)

## 🎯 Benefícios

1. **Simplicidade:** Um único cenário ao invés de 7 cenários separados
2. **Completude:** O cenário único abrange todos os aspectos dos testes anteriores
3. **Eficiência:** ~24 minutos para executar ambas versões (V1 + V2)
4. **Manutenção:** Menos arquivos para gerenciar e analisar
5. **Análise:** Mais fácil comparar V1 vs V2 em um único contexto

## 📁 Arquivos Gerados

Após a execução, você terá:

```
k6/results/
├── V1_Completo.json    # Resultado do V1 (Baseline)
└── V2_Completo.json    # Resultado do V2 (Circuit Breaker)

analysis_results/
├── plots/
│   ├── complete_scenario_analysis.png
│   └── ...
└── csv/
    ├── complete_scenario_stats.csv
    └── ...
```

## 🚀 Como Executar

### Opção 1: Script Shell Rápido
```bash
./rerun_high_concurrency.sh
```

### Opção 2: Script Python Completo
```bash
python3 run_experiment.py
```

### Opção 3: Execução Manual
```bash
# Subir os serviços
docker-compose up -d

# Executar V1
docker exec k6 run /scripts/cenario-completo.js \
  --out json=/results/V1_Completo.json

# Executar V2 (modificar URL conforme necessário)
docker exec k6 run /scripts/cenario-completo.js \
  --out json=/results/V2_Completo.json
```

## 📊 Análise dos Resultados

```bash
# 1. Extrair métricas do Circuit Breaker
python3 analysis/scripts/extract_cb_metrics.py \
  k6/results/V1_Completo.json \
  k6/results/V2_Completo.json

# 2. Análise detalhada com gráficos
python3 analysis/scripts/analyze_high_concurrency.py

# 3. Relatório completo
python3 analysis/analyze_and_report.py
```

## ✅ Validação

O Circuit Breaker V2 deve apresentar:
- ✅ Taxa de erro real: 10-20% (NÃO 0%!)
- ✅ Taxa de fallback: 70-85%
- ✅ Mudanças de estado do CB: 100+
- ✅ Tempo de resposta P95 melhor que V1 durante falhas
- ✅ Recuperação mais rápida após picos de estresse

## 📚 Documentos Relacionados

- `GUIA_RAPIDO.md` - Guia de execução rápida
- `METRICAS_CIRCUIT_BREAKER.md` - Explicação das métricas
- `RESUMO_CORRECOES.md` - Correções anteriores
- `k6/scripts/cenario-completo.js` - Script do cenário

## ⚠️ Observações

- Os cenários antigos ainda existem em `k6/scripts/` mas não são mais executados por padrão
- Os scripts de análise focam apenas no cenário completo
- Backup dos resultados antigos é feito automaticamente quando reexecutar
- O cenário completo consome ~300.000 linhas de log por versão

---

**Data da mudança:** 7 de novembro de 2025
**Autor:** Sistema de automação TCC
