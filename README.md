# Circuit Breaker: Análise Experimental de Resiliência em Microsserviços

Este repositório contém o código-fonte e a documentação completa do experimento desenvolvido para meu Trabalho de Conclusão de Curso, que analisa o impacto do padrão Circuit Breaker na resiliência de microsserviços.

## 🎯 Descoberta Importante

**Atualização:** Os testes iniciais mostraram que o Circuit Breaker oferece apenas **~1% de melhoria** em cenários de operação normal com falhas distribuídas (10%). Isto é **esperado e correto** - o CB não é projetado para brilhar em condições normais.

Criamos **3 novos cenários críticos** onde o CB demonstra seu verdadeiro valor:
- 🔥 **Falha Catastrófica:** Ganho esperado de 70-80% em latência
- 📉 **Degradação Gradual:** Ganho esperado de 30-40% em latência  
- 🌊 **Rajadas Intermitentes:** Ganho esperado de 40-50% em latência

## 📚 Documentação

- **[GUIA_EXECUCAO.md](GUIA_EXECUCAO.md)** - Guia rápido de execução e métricas
- **[ANALISE_FINAL_TCC.md](ANALISE_FINAL_TCC.md)** - Análise consolidada final
- **[CB_PERFIS_CONFIGURACAO.md](CB_PERFIS_CONFIGURACAO.md)** - Perfis de configuração do CB
- **[ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md)** - Estrutura completa do projeto
- **[docs/](docs/)** - Documentação acadêmica do TCC

---

## 📖 Visão Geral

O projeto consiste em um experimento controlado que compara duas versões de um microsserviço de pagamentos:

### Serviço de Pagamento V1 (Baseline)
- Implementação básica com timeout
- Sem mecanismos de resiliência avançados
- Características:
  - Timeout fixo de 5 segundos
  - Retry simples (3 tentativas)
  - Falha rápida em caso de erro
  - Sem proteção contra sobrecarga

### Serviço de Pagamento V2 (Circuit Breaker)
- Implementação resiliente usando Resilience4j
- Características:
  - Circuit Breaker configurado com:
    - Sliding Window de 10 chamadas
    - Threshold de falha de 50%
    - Tempo de espera de 30 segundos
  - Retry adaptativo
  - Bulkhead para limitar chamadas concorrentes
  - Fallback para respostas degradadas

### Arquitetura do Experimento

![Arquitetura Geral](docs/images/arquitetura_geral.png)

## 📊 Resultados da Análise

### Taxa de Sucesso
![Taxa de Sucesso](docs/images/success_rate_comparison.png)

### Tempos de Resposta
![Tempos de Resposta](docs/images/response_times_comparison.png)

O ambiente experimental é composto por:

- **Microsserviços**:
  - `payment-service`: Serviço principal (sistema sob teste)
  - `acquirer-service`: Simulador de gateway de pagamento

- **Stack de Monitoramento**:
  - Prometheus: Coleta de métricas
  - Grafana: Visualização
  - cAdvisor: Métricas de container

- **Testes de Carga**:
  - k6: Execução de cenários de teste

## 🏗️ Estrutura do Projeto

```
tcc-performance-circuit-breaker/
├── docs/                      # Documentação
│   ├── images/               # Imagens dos diagramas e screenshots
│   ├── diagramas/            # Arquivos fonte dos diagramas PlantUML
│   └── chapters/             # Capítulos do TCC em Markdown
├── k6/                       # Testes de carga
│   ├── scripts/             # Scripts de teste k6
│   └── results/             # Resultados dos testes
├── monitoring/              # Configurações de monitoramento
│   ├── grafana/            # Dashboards e configurações do Grafana
│   └── prometheus/         # Configurações do Prometheus
├── services/               # Microsserviços
│   ├── payment-service/    # Serviço de Pagamento (V1 e V2)
│   └── acquirer-service/   # Serviço Adquirente
└── analysis/              # Scripts e resultados de análise
    ├── scripts/           # Scripts Python de análise
    ├── data/             # Dados processados (CSV)
    └── reports/          # Relatórios gerados
```

## 🧪 Cenários de Teste

O experimento inclui diversos cenários para avaliar o comportamento do sistema:

1. **Cenário Normal**: Operação padrão sem falhas
2. **Cenário de Latência**: Alta latência no serviço adquirente
3. **Cenário de Falha**: Falhas completas no serviço adquirente
4. **Cenário de Estresse**: Aumento progressivo de carga
5. **Cenário de Recuperação**: Análise de auto-recuperação
6. **Cenário de Falhas Intermitentes**: Padrões variados de falha
7. **Cenário de Alta Concorrência**: Teste de carga extrema

## 🚀 Como Executar

### Pré-requisitos

- Docker e Docker Compose
- Java 17+
- Python 3.9+ (para análise dos resultados)

### Configuração e Execução

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/tcc-performance-circuit-breaker.git
   cd tcc-performance-circuit-breaker
   ```

2. **Inicie os serviços:**
   ```bash
   docker-compose up -d
   ```

3. **Execute os testes (exemplo para V1):**
   ```bash
   docker run --rm -i --network=tcc-performance-circuit-breaker_tcc-network \
     -v $PWD/k6:/k6 \
     grafana/k6:latest run /k6/scripts/cenario-A-normal.js \
     --out json=/k6/results/V1_Normal.json
   ```

4. **Analise os resultados:**
   ```bash
   python analysis/scripts/analyze_results.py
   ```

## 📊 Monitoramento

- **Grafana**: http://localhost:3000 (admin/admin)
  - Dashboard principal: Circuit Breaker Analysis
  - Métricas de performance
  - Estados do Circuit Breaker

- **Prometheus**: http://localhost:9090
  - Métricas brutas
  - Consultas PromQL
  - Alertas e regras

## 📝 Documentação

### 🎯 Documentos Principais (INÍCIO AQUI!)

Para facilitar a escrita do TCC, foram criados documentos organizacionais:

1. **[� COMPARAÇÃO ESPERADA](COMPARACAO_ESPERADA.md)** - ⭐ **NOVO!** Análise detalhada baseline vs crítico
2. **[🎯 GUIA CENÁRIOS CRÍTICOS](GUIA_CENARIOS_CRITICOS.md)** - ⭐ **NOVO!** Como executar e analisar
3. **[�📊 Sumário Executivo](docs/SUMARIO_EXECUTIVO.md)** - Visão geral completa da análise
4. **[📑 Índice Mestre](docs/INDICE_MESTRE.md)** - Navegação por TODOS os documentos do projeto
5. **[📋 Relatório de Incongruências](docs/ANALISE_INCONGRUENCIAS.md)** - Problemas identificados e soluções
6. **[📚 Guia de Organização](docs/GUIA_ORGANIZACAO_TCC.md)** - Estrutura, TODOs e checklists

## 🚀 Início Rápido

### Pré-requisitos
- Docker e Docker Compose
- Python 3.8+
- 8GB RAM disponível

### 🔥 Executar Cenários Críticos (Recomendado para TCC)

```bash
# 1. Subir a infraestrutura
docker-compose up -d

# 2. Executar cenário de falha catastrófica (mais impactante)
./run_and_analyze.sh catastrofe

# 3. Ou executar todos os cenários (~45min)
./run_and_analyze.sh all

# 4. Visualizar relatórios
# Os relatórios HTML abrem automaticamente!
# Veja também: analysis_results/scenarios/csv/consolidated_benefits.csv
```

### 📊 Executar Cenário Baseline (Operação Normal)

```bash
# Executar teste baseline
./run_experiment.py

# Analisar resultados
python3 analysis/scripts/analyzer.py

# Ver relatório
open analysis_results/analysis_report.html
```

### 📂 Estrutura de Resultados

```
analysis_results/
├── scenarios/                          # ⭐ Novos cenários críticos
│   ├── catastrofe_report.html
│   ├── degradacao_report.html
│   ├── rajadas_report.html
│   ├── csv/
│   │   └── consolidated_benefits.csv  # 📊 Use isto no TCC!
│   └── plots/
├── analysis_report.html                # Relatório baseline
└── csv/
    └── summary_analysis.csv
```

### 📖 Conteúdo do TCC

- `docs/chapters/`: Capítulos do TCC em Markdown
  - 01-introducao-e-justificativa.md
  - 02-metodologia-e-design-experimento.md
  - 03-resultados-e-discussao.md
  - 04-conclusao.md
- `docs/images/`: Diagramas e screenshots
- `analysis/reports/`: Relatórios de análise
- `analysis_results/`: Resultados consolidados e gráficos

## 🔄 Fluxos de Execução

### Cenário de Falha (V1)
![Fluxo de Falha V1](docs/images/sequencia_falha_v1.png)

No fluxo V1, quando ocorre uma falha:
1. Cliente faz requisição de pagamento
2. Serviço tenta processar com timeout
3. Adquirente falha ou demora
4. Serviço retenta 3 vezes
5. Cliente recebe erro 500
6. Recursos ficam presos até timeout
7. Sistema pode ficar sobrecarregado

### Cenário com Circuit Breaker (V2)
![Fluxo com Circuit Breaker V2](docs/images/sequencia_resiliencia_v2.png)

No fluxo V2, com Circuit Breaker:
1. Cliente faz requisição de pagamento
2. Circuit Breaker monitora chamadas
3. Se adquirente falha frequentemente:
   - Circuito abre
   - Falhas rápidas sem consumir recursos
   - Resposta degradada quando possível
4. Após período de espera:
   - Circuito meio-aberto
   - Testa recuperação do serviço
5. Sistema se recupera automaticamente

## � Stack de Monitoramento

![Stack de Monitoramento](docs/images/stack_monitoramento.png)

A stack de monitoramento inclui:
- Prometheus para coleta de métricas
- Grafana para dashboards
- cAdvisor para métricas de container
- Métricas customizadas do Circuit Breaker

### Métricas Principais
- Taxa de sucesso/falha
- Tempos de resposta
- Estado do Circuit Breaker
- Uso de recursos
- Throughput

## ⚙️ Componentes do Sistema

![Componentes Internos](docs/images/componentes_internos.png)

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ✨ Contribuições

Contribuições são bem-vindas! Por favor, leia o [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes sobre nosso código de conduta e o processo de submissão de pull requests.