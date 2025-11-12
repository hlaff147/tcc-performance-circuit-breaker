# 📁 Estrutura do Projeto - TCC Circuit Breaker

> **Última atualização:** 12 de novembro de 2025  
> **Objetivo:** Documentar a organização de pastas, arquivos e seu propósito no projeto.

---

## 🗂️ Estrutura de Pastas

```
tcc-performance-circuit-breaker/
├── 📄 Documentação (.md)
├── 📊 Código de Análise (analysis/)
├── 🧪 Resultados de Análise (analysis_results/) [GITIGNORE]
├── 📖 Documentação Acadêmica (docs/)
├── 🐳 Infraestrutura (docker-compose.yml)
├── 📈 Testes de Carga (k6/)
├── 🔍 Monitoramento (monitoring/)
├── ☕ Serviços Java (services/)
└── 🛠️ Scripts de Automação (.sh, .py)
```

---

## 📄 Arquivos .md na Raiz (Documentação Operacional)

### ✅ Principais (Manter Sempre)

| Arquivo | Descrição | Quando Usar |
|---------|-----------|-------------|
| **README.md** | Documentação principal do projeto | Primeiro acesso ao projeto |
| **ANALISE_FINAL_TCC.md** | Análise consolidada dos 3 cenários com resultados reais | Resultados finais para o TCC |
| **CB_PERFIS_CONFIGURACAO.md** | Perfis de configuração do CB (agressivo, equilibrado, otimizado) | Configurar o Circuit Breaker |

### 📚 Guias e Referências

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| **GUIA_RAPIDO.md** | Guia rápido de execução dos testes | Ativo |
| **GUIA_CENARIOS_CRITICOS.md** | Explicação dos 3 cenários (catástrofe, degradação, rajadas) | Ativo |
| **INSTRUCOES.md** | Instruções detalhadas de setup e execução | Ativo |
| **METRICAS_CIRCUIT_BREAKER.md** | Documentação das métricas coletadas | Referência |
| **OTIMIZACAO_ALTA_DISPONIBILIDADE.md** | Estratégia de otimização do CB para alta disponibilidade | Histórico/Referência |

### 🔧 Documentos Técnicos/Históricos

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| **COMPARACAO_ESPERADA.md** | Expectativas vs realidade dos testes | Referência histórica |
| **MUDANCA_CENARIO_UNICO.md** | Histórico da mudança para múltiplos cenários | Histórico |
| **SOLUCAO_EXIT99.md** | Solução para bug do k6 (exit code 99) | Referência técnica |
| **SUMARIO_EXECUTIVO_ATUALIZADO.md** | Sumário executivo dos resultados | Referência |
| **PLANO_LIMPEZA.md** | Plano de organização dos arquivos .md | Organização interna |
| **ORGANIZATION.md** | Organização antiga do projeto | Obsoleto/Histórico |
| **RESUMO_CORRECOES.md** | Resumo de correções aplicadas | Histórico |

---

## 📊 `/analysis/` - Código de Análise Python

Scripts Python para processar resultados dos testes k6 e gerar relatórios.

| Arquivo/Pasta | Descrição | Entrada | Saída |
|---------------|-----------|---------|-------|
| **scripts/analyzer.py** | Analisador antigo (baseline vs V1/V2) | k6/results/*.json | analysis_results/ |
| **scripts/scenario_analyzer.py** | Analisador dos 3 cenários críticos | k6/results/scenarios/*.json | analysis_results/scenarios/ |
| **scripts/analyze_results.py** | Script de análise complementar | Variável | analysis_results/ |
| **scripts/extract_cb_metrics.py** | Extração de métricas específicas do CB | Logs/JSON | CSV |

---

## 🧪 `/analysis_results/` - Resultados Gerados [GITIGNORE]

**⚠️ Esta pasta NÃO é versionada (está no .gitignore)**

Contém resultados gerados automaticamente pelos scripts de análise.

### Estrutura:

```
analysis_results/
├── csv/                          # CSVs consolidados
│   ├── response_times_analysis.csv
│   ├── statistical_analysis.csv
│   └── summary_analysis.csv
├── plots/                        # Gráficos PNG
│   ├── response_times.png
│   ├── success_failure_rate.png
│   └── ...
├── scenarios/                    # Análise dos 3 cenários
│   ├── csv/
│   │   ├── catastrofe_*.csv
│   │   ├── degradacao_*.csv
│   │   ├── rajadas_*.csv
│   │   └── consolidated_benefits.csv
│   ├── plots/
│   │   ├── catastrofe/
│   │   ├── degradacao/
│   │   └── rajadas/
│   ├── catastrofe_report.html
│   ├── degradacao_report.html
│   └── rajadas_report.html
├── analysis_report.html         # Relatório consolidado
└── report.html                   # Relatório principal
```

### Como regenerar:

```bash
# Análise dos cenários
python3 analysis/scripts/scenario_analyzer.py [cenario]

# Ou executar testes + análise
./run_and_analyze.sh all
```

---

## 📖 `/docs/` - Documentação Acadêmica (TCC)

Documentação estruturada do Trabalho de Conclusão de Curso.

| Arquivo/Pasta | Descrição |
|---------------|-----------|
| **README.md** | Índice da documentação do TCC |
| **chapters/01-introducao-e-justificativa.md** | Cap. 1: Introdução e Justificativa |
| **chapters/02-metodologia-e-design-experimento.md** | Cap. 2: Metodologia e Design do Experimento |
| **chapters/03-resultados-e-discussao.md** | Cap. 3: Resultados e Discussão |
| **chapters/04-conclusao.md** | Cap. 4: Conclusão |
| **diagramas/** | Diagramas PlantUML e imagens |
| **SUMARIO_EXECUTIVO.md** | Sumário executivo |
| **ACOES_PRIORITARIAS.md** | Ações prioritárias (histórico) |
| **ANALISE_INCONGRUENCIAS.md** | Análise de incongruências (histórico) |
| **GUIA_ORGANIZACAO_TCC.md** | Guia de organização |
| **INDICE_MESTRE.md** | Índice mestre |

---

## 🐳 Infraestrutura e Docker

| Arquivo | Descrição |
|---------|-----------|
| **docker-compose.yml** | Orquestração dos serviços (payment-v1, payment-v2, acquirer, prometheus, grafana) |
| **services/payment-service-v1/** | Serviço de pagamento SEM Circuit Breaker (baseline) |
| **services/payment-service-v2/** | Serviço de pagamento COM Circuit Breaker (Resilience4j) |
| **services/acquirer-service/** | Serviço simulador da API externa (adquirente) com modos de falha |

---

## 📈 `/k6/` - Testes de Carga

### `/k6/scripts/` - Scripts de Teste

| Arquivo | Descrição | Cenário |
|---------|-----------|---------|
| **cenario-falha-catastrofica.js** | API 100% fora por 5 minutos | Catástrofe |
| **cenario-degradacao-gradual.js** | Degradação progressiva (5% → 50% falhas) | Degradação |
| **cenario-rajadas-intermitentes.js** | 3 rajadas de 100% falha | Rajadas |
| **cenario-completo.js** | Teste completo antigo | Obsoleto |
| **cenario-A-normal.js** ... **cenario-G-alta-concorrencia.js** | Cenários antigos individuais | Obsoletos |

### `/k6/results/` - Resultados dos Testes [GITIGNORE]

**⚠️ Arquivos JSON grandes NÃO versionados**

```
k6/results/
├── V1_Completo.json (~1.4 GB)        # [GITIGNORE]
├── V2_Completo.json (~1.4 GB)        # [GITIGNORE]
└── scenarios/
    ├── catastrofe_V1.json (192 MB)   # [GITIGNORE]
    ├── catastrofe_V2.json (256 MB)   # [GITIGNORE]
    ├── degradacao_V1.json (272 MB)   # [GITIGNORE]
    ├── degradacao_V2.json (272 MB)   # [GITIGNORE]
    ├── rajadas_V1.json (320 MB)      # [GITIGNORE]
    ├── rajadas_V2.json (336 MB)      # [GITIGNORE]
    ├── *_summary.json                # Sumários (OK para versionar - 4KB)
    └── ...
```

**Por que não versionar?**
- Arquivos muito grandes (192 MB - 1.4 GB cada)
- Regeneráveis executando os testes
- Causa problemas de performance no Git
- Melhor armazenar em artifact storage ou local

**Como regenerar:**
```bash
./run_and_analyze.sh catastrofe  # ou degradacao, rajadas, all
```

---

## 🔍 `/monitoring/` - Prometheus e Grafana

| Arquivo/Pasta | Descrição |
|---------------|-----------|
| **prometheus/prometheus.yml** | Configuração do Prometheus |
| **grafana/** | Configuração do Grafana e datasources |
| **prometheus_queries.txt** | Queries úteis do Prometheus |
| **scripts/export_prometheus_data.sh** | Script para exportar dados |

---

## 🛠️ Scripts de Automação (Raiz)

| Script | Descrição | Uso |
|--------|-----------|-----|
| **run_and_analyze.sh** | **PRINCIPAL**: Executa testes + análise + abre relatórios | `./run_and_analyze.sh [cenario]` |
| **run_scenario_tests.sh** | Executa apenas os testes k6 | `./run_scenario_tests.sh [cenario]` |
| **run_all_tests.sh** | Executa todos os testes | `./run_all_tests.sh` |
| **switch_cb_profile.sh** | Troca perfil do Circuit Breaker | `./switch_cb_profile.sh [perfil]` |
| **validate_environment.sh** | Valida ambiente (Docker, Python, etc.) | `./validate_environment.sh` |
| **help.sh** | Help/ajuda sobre os scripts | `./help.sh` |
| **run_experiment.py** | Script Python para experimentos | Uso específico |
| **rerun_high_concurrency.sh** | Re-executa teste de alta concorrência | Específico |

---

## 🚫 Arquivos no .gitignore

### Por que estão ignorados?

| Path/Pattern | Motivo | Tamanho Típico |
|--------------|--------|----------------|
| **k6/results/*.json** | Arquivos muito grandes, regeneráveis | 192 MB - 1.4 GB |
| **k6/results/scenarios/*.json** | Arquivos muito grandes, regeneráveis | 192 MB - 336 MB |
| **analysis_results/** | Gerados automaticamente | Variável |
| **.venv/** | Virtual environment Python | ~50-100 MB |
| **target/** | Build artifacts do Maven | Variável |
| **prometheus/data/** | Dados do Prometheus | Cresce continuamente |
| **grafana/data/** | Dados do Grafana | Cresce continuamente |

### Exceções (permitidos mesmo dentro de pastas ignoradas):

| Pattern | Motivo |
|---------|--------|
| `!k6/results/scenarios/*_summary.json` | Sumários pequenos (4 KB) úteis para referência |

---

## 📦 Dependências

### Python
```bash
# Arquivo: requirements.txt
pandas
matplotlib
seaborn
jinja2
numpy
```

### Java/Maven
- Spring Boot 3.2.5
- Resilience4j 2.x
- Spring Cloud OpenFeign

### Docker
- Eclipse Temurin JDK 17
- Prometheus
- Grafana
- k6 (Grafana k6)

---

## 🔄 Workflow Típico

### 1. Executar Testes e Gerar Relatórios

```bash
# Validar ambiente
./validate_environment.sh

# Executar todos os cenários (catástrofe + degradação + rajadas)
./run_and_analyze.sh all

# Ou executar apenas um cenário
./run_and_analyze.sh catastrofe
```

### 2. Trocar Perfil do Circuit Breaker

```bash
# Perfis: agressivo, equilibrado, otimizado
./switch_cb_profile.sh otimizado
```

### 3. Analisar Resultados Existentes

```bash
# Sem re-executar testes, apenas análise
python3 analysis/scripts/scenario_analyzer.py catastrofe
```

### 4. Consultar Documentação

- **Resultados finais:** `ANALISE_FINAL_TCC.md`
- **Configuração CB:** `CB_PERFIS_CONFIGURACAO.md`
- **Guia rápido:** `GUIA_RAPIDO.md`
- **TCC acadêmico:** `docs/chapters/*.md`

---

## 🎯 Arquivos Importantes para o TCC

### Para Escrever o TCC:

1. `ANALISE_FINAL_TCC.md` - Resultados consolidados
2. `docs/chapters/*.md` - Capítulos estruturados
3. `analysis_results/scenarios/csv/consolidated_benefits.csv` - Dados para tabelas
4. `analysis_results/scenarios/*_report.html` - Gráficos e análises visuais

### Para Apresentação:

1. `analysis_results/scenarios/plots/` - Gráficos PNG
2. `CB_PERFIS_CONFIGURACAO.md` - Explicar configurações
3. `GUIA_CENARIOS_CRITICOS.md` - Explicar cenários de teste

---

## 📝 Notas Importantes

### Sobre Arquivos JSON Grandes

- **NÃO commitar** arquivos `k6/results/**/*.json` (exceto *_summary.json)
- **São regeneráveis** executando `./run_and_analyze.sh`
- **Tamanho total:** ~3.5 GB (se incluir V1_Completo e V2_Completo)
- **Alternativa:** Usar Git LFS (Large File Storage) se realmente necessário versionar

### Sobre analysis_results/

- Pasta **gerada automaticamente**
- **Não versionar** (está no .gitignore)
- Pode ser deletada sem problemas (regenerável)
- Contém relatórios HTML, CSVs e PNGs

### Sobre .venv/

- Virtual environment do Python
- **Não versionar** (está no .gitignore)
- Recriar com: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

---

## 🗑️ Limpeza de Arquivos Grandes

Se precisar limpar arquivos grandes localmente:

```bash
# Deletar resultados de testes (regeneráveis)
rm -f k6/results/*.json
rm -f k6/results/scenarios/*.json

# Manter apenas sumários
# (os *_summary.json ficam preservados)

# Deletar análises (regeneráveis)
rm -rf analysis_results/

# Regenerar quando necessário
./run_and_analyze.sh all
```

---

## ✅ Checklist de Commit

Antes de fazer commit, verificar:

- [ ] Arquivos JSON grandes NÃO estão no stage (`git status`)
- [ ] analysis_results/ NÃO está no stage
- [ ] .venv/ NÃO está no stage
- [ ] Apenas código, scripts e documentação (.md) estão sendo commitados
- [ ] .gitignore está atualizado

```bash
# Verificar o que está staged
git status --short

# Verificar tamanho dos arquivos staged
git diff --cached --name-only | xargs du -h

# Remover do stage se necessário
git reset HEAD -- k6/results/*.json
git reset HEAD -- analysis_results/
```

---

**Status:** ✅ Documentação completa da estrutura do projeto
**Próximos passos:** Consultar esta documentação ao navegar no projeto
