# Guia de Organização para Escrita do TCC

**Projeto**: Análise de Desempenho e Resiliência em Microsserviços - Circuit Breaker  
**Objetivo**: Facilitar a escrita e revisão do Trabalho de Conclusão de Curso  
**Última Atualização**: 05/11/2025

---

## 📚 ÍNDICE NAVEGÁVEL

### 1. Estrutura de Diretórios
- [Visão Geral da Estrutura](#estrutura-de-diretórios)
- [Mapa de Localização de Arquivos](#mapa-de-localização)

### 2. Documentação do Experimento
- [Capítulos do TCC](#capítulos-do-tcc)
- [Dados e Resultados](#dados-e-resultados)
- [Diagramas e Imagens](#diagramas-e-imagens)

### 3. Código e Implementação
- [Serviços](#serviços)
- [Testes](#testes)
- [Análise](#análise)

### 4. Guias de Referência
- [Como Executar Experimentos](#como-executar-experimentos)
- [Como Gerar Análises](#como-gerar-análises)
- [Como Atualizar Documentação](#como-atualizar-documentação)

---

## 📁 ESTRUTURA DE DIRETÓRIOS

```
tcc-performance-circuit-breaker/
│
├── 📄 README.md                        # Visão geral do projeto
├── 📄 ORGANIZATION.md                  # Convenções e organização
├── 📄 INSTRUCOES.md                    # Procedimentos experimentais
├── 📄 docker-compose.yml               # Orquestração do ambiente
├── 📄 requirements.txt                 # Dependências Python
├── 📄 run_all_tests.sh                 # Script automação testes
│
├── 📂 docs/                            # ⭐ DOCUMENTAÇÃO DO TCC
│   ├── 📄 ANALISE_INCONGRUENCIAS.md   # Relatório de problemas (NOVO)
│   ├── 📄 GUIA_ORGANIZACAO_TCC.md     # Este arquivo (NOVO)
│   │
│   ├── 📂 chapters/                    # ⭐ CAPÍTULOS DO TCC (Markdown)
│   │   ├── 01-introducao-e-justificativa.md
│   │   ├── 02-metodologia-e-design-experimento.md
│   │   ├── 03-resultados-e-discussao.md
│   │   └── 04-conclusao.md
│   │
│   ├── 📂 diagramas/                   # Arquivos fonte PlantUML
│   │   ├── generate_diagrams.py
│   │   └── puml/
│   │       ├── arquitetura_geral.puml
│   │       ├── componentes_internos.puml
│   │       ├── sequencia_falha_v1.puml
│   │       ├── sequencia_resiliencia_v2.puml
│   │       └── stack_monitoramento.puml
│   │
│   └── 📂 images/                      # ⭐ IMAGENS PARA O TCC
│       ├── arquitetura_geral.png
│       ├── componentes_internos.png
│       ├── sequencia_falha_v1.png
│       ├── sequencia_resiliencia_v2.png
│       └── stack_monitoramento.png
│
├── 📂 k6/                              # ⭐ TESTES DE CARGA
│   ├── 📂 scripts/                     # Scripts JavaScript k6
│   │   ├── cenario-A-normal.js
│   │   ├── cenario-B-latencia.js
│   │   ├── cenario-C-falha.js
│   │   ├── cenario-D-estresse-crescente.js
│   │   ├── cenario-E-recuperacao.js
│   │   ├── cenario-F-falhas-intermitentes.js
│   │   └── cenario-G-alta-concorrencia.js
│   │
│   └── 📂 results/                     # ⭐ DADOS BRUTOS (JSON)
│       ├── V1_Normal.json              # 10.92 MB
│       ├── V1_Latencia.json            # 2.87 MB
│       ├── V1_Falha.json               # 11.62 MB
│       ├── V1_Alta_Concorrencia.json   # 233.70 MB
│       ├── V1_Estresse.json            # 7.8 GB ⚠️
│       ├── V1_FalhasIntermitentes.json # 316.31 MB
│       ├── V1_Recuperacao.json         # 208.12 MB
│       ├── V2_Normal.json              # 11.10 MB
│       ├── V2_Latencia.json            # 2.87 MB
│       ├── V2_Falha.json               # 11.07 MB
│       ├── V2_Alta_Concorrencia.json   # 226.39 MB
│       ├── V2_Estresse.json            # 6.1 GB ⚠️
│       ├── V2_FalhasIntermitentes.json # 312.89 MB
│       └── V2_Recuperacao.json         # 204.89 MB
│
├── 📂 analysis/                        # ⭐ ANÁLISE DOS RESULTADOS
│   ├── 📄 analyze_and_report.py        # Script principal de análise
│   ├── 📄 VALIDATION_CHECKLIST.md      # Checklist de validação
│   │
│   ├── 📂 scripts/
│   │   ├── analyze_high_concurrency.py
│   │   └── analyze_results.py
│   │
│   ├── 📂 reports/                     # Relatórios específicos
│   │   ├── high_concurrency_analysis.md
│   │   ├── high_concurrency_stats.csv
│   │   └── csv/
│   │       ├── response_times_analysis.csv
│   │       └── statistical_analysis.csv
│   │
│   └── 📂 data/                        # Dados intermediários
│
├── 📂 analysis_results/                # ⭐ RESULTADOS CONSOLIDADOS
│   ├── 📄 summary_metrics.csv          # Todas as métricas (CSV)
│   │
│   ├── 📂 markdown/
│   │   └── analysis_report.md          # ⭐ RELATÓRIO PRINCIPAL
│   │
│   └── 📂 plots/                       # ⭐ GRÁFICOS PARA O TCC
│       ├── response_times.png
│       ├── error_rates.png
│       ├── distribution_boxplot.png
│       └── statistical_variability.png
│
├── 📂 services/                        # ⭐ CÓDIGO DOS MICROSSERVIÇOS
│   ├── 📂 payment-service-v1/          # Baseline (sem CB)
│   │   ├── Dockerfile
│   │   ├── pom.xml
│   │   └── src/main/
│   │       ├── java/br/ufpe/cin/tcc/pagamento/
│   │       │   ├── PagamentoController.java
│   │       │   └── client/AdquirenteClient.java
│   │       └── resources/
│   │           └── application.yml
│   │
│   ├── 📂 payment-service-v2/          # Com Circuit Breaker
│   │   ├── Dockerfile
│   │   ├── pom.xml
│   │   └── src/main/
│   │       ├── java/br/ufpe/cin/tcc/pagamento/
│   │       │   ├── PagamentoController.java  # @CircuitBreaker
│   │       │   └── client/AdquirenteClient.java
│   │       └── resources/
│   │           └── application.yml      # Resilience4j config
│   │
│   └── 📂 acquirer-service/            # Simulador de gateway
│       ├── Dockerfile
│       ├── pom.xml
│       └── src/main/java/br/ufpe/cin/tcc/adquirente/
│           └── AdquirenteController.java  # Modos: normal/latencia/falha
│
└── 📂 monitoring/                      # Stack de observabilidade
    ├── 📂 grafana/
    │   └── datasources/
    │       └── datasource.yml
    └── 📂 prometheus/
        └── prometheus.yml
```

---

## 📖 CAPÍTULOS DO TCC

### Capítulo 1: Introdução e Justificativa
**Arquivo**: `docs/chapters/01-introducao-e-justificativa.md`

**Conteúdo Atual**:
- ✅ Contextualização (Era dos Microsserviços)
- ✅ Definição do Problema (Sistema de Pagamento)
- ✅ Solução Proposta (Circuit Breaker)
- ✅ Conexão com Pinheiro et al. (2024)
- ✅ Objetivos (Geral + Específicos)
- ✅ Estrutura do Documento

**📝 TODOs Identificados**:
1. ⚠️ Atualizar objetivos específicos para incluir 7 cenários (não apenas 3)
2. ⚠️ Adicionar objetivo sobre análise de alta concorrência
3. 💡 Considerar mencionar limitações da abordagem

**Referências no Arquivo**:
- Pinheiro, Dantas, et al. (2024) - SPNs
- Nygard (implícito, adicionar explicitamente)

---

### Capítulo 2: Metodologia e Design do Experimento
**Arquivo**: `docs/chapters/02-metodologia-e-design-experimento.md`

**Conteúdo Atual**:
- ✅ Visão Geral da Metodologia
- ✅ Ferramentas e Tecnologias (Stack)
- ✅ Arquitetura do Sistema Experimental
- ✅ Variáveis (Independente + Dependentes)
- ✅ Plano de Execução - **3 cenários** (Normal, Latência, Falha)

**📝 TODOs CRÍTICOS**:
1. 🔴 **ADICIONAR Seção 5.4**: "Cenários Estendidos"
   - Alta Concorrência (500 VUs)
   - Estresse Crescente
   - Falhas Intermitentes
   - Recuperação Automática

2. 🔴 **ADICIONAR Seção 2.X**: "Parametrização do Circuit Breaker"
   ```markdown
   ### 2.X Configuração do Circuit Breaker

   #### Parâmetros Escolhidos
   - `failureRateThreshold: 50%` - Threshold conservador
   - `slidingWindowSize: 20` - Janela de monitoramento
   - `minimumNumberOfCalls: 10` - Chamadas antes de avaliar
   - `waitDurationInOpenState: 10s` - Tempo de "esfriamento"
   - `timeoutDuration: 2500ms` - Timeout por requisição

   #### Justificativa
   - Baseado em [Nygard, 2007] e documentação Resilience4j
   - Threshold 50% permite tolerância a falhas esporádicas
   - Wait duration alinhado com tempo de restart de containers
   ```

3. ⚠️ Adicionar nota metodológica sobre amostragem (se usar para Estresse)

**Diagramas Relacionados**:
- `docs/images/arquitetura_geral.png`
- `docs/images/componentes_internos.png`
- `docs/images/sequencia_falha_v1.png`
- `docs/images/sequencia_resiliencia_v2.png`

---

### Capítulo 3: Resultados e Discussão
**Arquivo**: `docs/chapters/03-resultados-e-discussao.md`

**Conteúdo Atual**:
- ✅ Tabelas comparativas (Normal, Latência, Falha)
- ✅ Discussão de cada cenário
- ⚠️ Análise focada em apenas 3 cenários

**📝 TODOs CRÍTICOS**:
1. 🔴 **EXPANDIR** para incluir 7 cenários:
   - Usar dados de `analysis_results/markdown/analysis_report.md`
   - Incluir Alta_Concorrencia, FalhasIntermitentes, Recuperacao
   - Decidir sobre Estresse (incluir com amostragem OU justificar exclusão)

2. 🔴 **ADICIONAR Seção 3.X**: "Validação Estatística"
   ```markdown
   ### 3.X Validação Estatística

   Para validar a significância das diferenças observadas, aplicamos:

   #### Teste t de Student
   - Hipótese nula: μ(V1) = μ(V2)
   - Nível de confiança: 95% (α = 0.05)

   | Cenário | Métrica | p-value | Significante? |
   |---------|---------|---------|---------------|
   | Alta_Concorrencia | Média | < 0.001 | ✅ Sim |
   | Alta_Concorrencia | P95 | < 0.001 | ✅ Sim |
   | Falha | Taxa de Erro | < 0.001 | ✅ Sim |

   #### Tamanho do Efeito (Cohen's d)
   - Alta_Concorrencia: d = 1.85 (efeito grande)
   - Falha: d = 2.32 (efeito muito grande)

   **Conclusão**: As melhorias observadas são estatisticamente significativas.
   ```

3. ⚠️ **ADICIONAR Seção 3.Y**: "Análise de Throughput"
   - Requisições por segundo (RPS)
   - Impacto do CB na vazão
   - Gráfico comparativo

4. ⚠️ **MELHORAR** seção "Automação da Observabilidade"
   - Atual: instruções genéricas
   - Necessário: resultados concretos do Prometheus/Grafana

**Dados de Referência**:
- `analysis_results/markdown/analysis_report.md` - Relatório principal
- `analysis_results/summary_metrics.csv` - Todas as métricas
- `analysis/reports/high_concurrency_analysis.md` - Análise específica

**Gráficos Disponíveis**:
- `analysis_results/plots/response_times.png`
- `analysis_results/plots/error_rates.png`
- `analysis_results/plots/distribution_boxplot.png`
- `analysis_results/plots/statistical_variability.png`

---

### Capítulo 4: Conclusão
**Arquivo**: `docs/chapters/04-conclusao.md`

**Conteúdo Atual**:
- ✅ Revisão dos objetivos
- ✅ Síntese dos resultados
- ✅ Conexão com Pinheiro et al.
- ✅ Trabalhos futuros

**📝 TODOs**:
1. ⚠️ **ADICIONAR Seção**: "Limitações do Estudo"
   ```markdown
   ### Limitações do Estudo

   1. **Ambiente Controlado**: Testes em Docker local, não em produção
   2. **Carga Sintética**: k6 simula usuários, mas não padrões reais
   3. **Configuração Única**: Testamos apenas uma parametrização do CB
   4. **Análise Limitada**: Cenário Estresse não processado por restrições técnicas
   ```

2. ⚠️ **EXPANDIR** "Trabalhos Futuros":
   - Análise de sensibilidade de parâmetros do CB
   - Comparação com outros padrões (Retry, Rate Limiter)
   - Testes em ambiente de produção
   - Integração com Kubernetes/service mesh

3. 💡 **ADICIONAR**: "Contribuições"
   - Validação empírica do modelo SPN
   - Benchmark reproduzível
   - Configuração de referência para Resilience4j

---

## 📊 DADOS E RESULTADOS

### Dados Brutos (k6)
**Localização**: `k6/results/`

| Arquivo | Tamanho | Status | Cenário |
|---------|---------|--------|---------|
| V1_Normal.json | 10.92 MB | ✅ Processado | Operação normal |
| V2_Normal.json | 11.10 MB | ✅ Processado | Operação normal |
| V1_Latencia.json | 2.87 MB | ✅ Processado | Alta latência (3000ms) |
| V2_Latencia.json | 2.87 MB | ✅ Processado | Alta latência (3000ms) |
| V1_Falha.json | 11.62 MB | ✅ Processado | Falha total (503) |
| V2_Falha.json | 11.07 MB | ✅ Processado | Falha total (503) |
| V1_Alta_Concorrencia.json | 233.70 MB | ✅ Processado | 500 VUs |
| V2_Alta_Concorrencia.json | 226.39 MB | ✅ Processado | 500 VUs |
| V1_FalhasIntermitentes.json | 316.31 MB | ✅ Processado | Padrão variado |
| V2_FalhasIntermitentes.json | 312.89 MB | ✅ Processado | Padrão variado |
| V1_Recuperacao.json | 208.12 MB | ✅ Processado | Auto-recuperação |
| V2_Recuperacao.json | 204.89 MB | ✅ Processado | Auto-recuperação |
| V1_Estresse.json | 7.8 GB | ⚠️ **PENDENTE** | Carga crescente |
| V2_Estresse.json | 6.1 GB | ⚠️ **PENDENTE** | Carga crescente |

**Total**: ~14.7 GB de dados experimentais

---

### Resultados Processados
**Localização**: `analysis_results/`

#### Relatório Principal
- **Arquivo**: `markdown/analysis_report.md`
- **Conteúdo**:
  - Sumário executivo
  - Métricas de tempo de resposta (média, P95)
  - Análise de confiabilidade (taxas de erro)
  - Análise estatística (CV, percentis)
  - Análise detalhada por cenário

#### Métricas CSV
- **Arquivo**: `summary_metrics.csv`
- **Colunas**: version, scenario, total_requests, failed_requests, error_rate, avg_response_time, p50, p75, p90, p95, p99, cv, etc.
- **Uso**: Análises adicionais, gráficos customizados

#### Gráficos
- `plots/response_times.png` - Tempos médio e P95
- `plots/error_rates.png` - Taxas de erro comparativas
- `plots/distribution_boxplot.png` - Distribuição dos tempos
- `plots/statistical_variability.png` - Coeficiente de Variação

---

## 🎨 DIAGRAMAS E IMAGENS

### Diagramas PlantUML (Fontes)
**Localização**: `docs/diagramas/puml/`

1. **arquitetura_geral.puml**
   - Visão geral do sistema
   - Componentes: payment-service, acquirer-service, k6, monitoring

2. **componentes_internos.puml**
   - Detalhamento interno dos serviços
   - Feign Client, Circuit Breaker, Resilience4j

3. **sequencia_falha_v1.puml**
   - Fluxo de falha sem CB
   - Timeout, retries, thread starvation

4. **sequencia_resiliencia_v2.puml**
   - Fluxo com CB
   - Estados do circuito, fallback

5. **stack_monitoramento.puml**
   - Prometheus, Grafana, cAdvisor
   - Métricas coletadas

**Como gerar imagens**:
```bash
cd docs/diagramas
python generate_diagrams.py
```

---

### Imagens Geradas (PNG)
**Localização**: `docs/images/`

Usar nos capítulos com:
```markdown
![Arquitetura Geral](../images/arquitetura_geral.png)
```

---

## 💻 CÓDIGO DOS SERVIÇOS

### Payment Service V1 (Baseline)
**Localização**: `services/payment-service-v1/`

**Características**:
- Spring Boot 3
- Feign Client com timeout 2s
- SEM Circuit Breaker
- Responde 200 (sucesso) ou 500 (erro)

**Arquivos Chave**:
```
src/main/java/br/ufpe/cin/tcc/pagamento/
├── PagamentoController.java      # Endpoint /pagar
└── client/AdquirenteClient.java  # Feign @FeignClient

src/main/resources/
└── application.yml                # Apenas timeout config
```

**Endpoint**:
```java
@PostMapping("/pagar")
public ResponseEntity<String> pagar(
    @RequestParam("modo") String modo,
    @RequestBody Map<String, Object> pagamento
) {
    return adquirenteClient.autorizarPagamento(modo, pagamento);
}
```

---

### Payment Service V2 (Circuit Breaker)
**Localização**: `services/payment-service-v2/`

**Características**:
- Spring Boot 3
- Feign Client + Resilience4j
- Circuit Breaker configurado
- Fallback retorna 202 (Accepted)

**Arquivos Chave**:
```
src/main/java/br/ufpe/cin/tcc/pagamento/
├── PagamentoController.java      # @CircuitBreaker + fallback
└── client/AdquirenteClient.java  # Feign @FeignClient

src/main/resources/
└── application.yml                # Resilience4j config
```

**Endpoint com CB**:
```java
@PostMapping("/pagar")
@CircuitBreaker(name = "adquirente-cb", fallbackMethod = "pagamentoFallback")
public ResponseEntity<String> pagar(
    @RequestParam("modo") String modo,
    @RequestBody Map<String, Object> pagamento
) {
    return adquirenteClient.autorizarPagamento(modo, pagamento);
}

public ResponseEntity<String> pagamentoFallback(
    String modo, 
    Map<String, Object> pagamento, 
    Throwable t
) {
    return ResponseEntity.status(HttpStatus.ACCEPTED)
        .body("Pagamento recebido. Será processado offline.");
}
```

**Configuração CB**:
```yaml
resilience4j:
  circuitbreaker:
    instances:
      adquirente-cb:
        failureRateThreshold: 50
        slidingWindowSize: 20
        minimumNumberOfCalls: 10
        waitDurationInOpenState: 10s
```

---

### Acquirer Service (Simulador)
**Localização**: `services/acquirer-service/`

**Características**:
- Simula gateway de pagamento
- Modos controláveis via query param

**Modos Disponíveis**:
```java
?modo=normal    → 50ms, HTTP 200
?modo=latencia  → 3000ms, HTTP 200
?modo=falha     → 10ms, HTTP 503
```

**Uso nos testes k6**:
```javascript
// Cenário Normal
http.post('http://servico-pagamento:8080/pagar?modo=normal', ...)

// Cenário Latência
http.post('http://servico-pagamento:8080/pagar?modo=latencia', ...)

// Cenário Falha
http.post('http://servico-pagamento:8080/pagar?modo=falha', ...)
```

---

## 🧪 TESTES (k6)

### Scripts de Teste
**Localização**: `k6/scripts/`

#### Cenários Básicos (Documentados no TCC)
1. **cenario-A-normal.js**
   - 50 VUs, 1 minuto
   - modo=normal
   - Threshold: P95 < 200ms

2. **cenario-B-latencia.js**
   - 50 VUs, 1 minuto
   - modo=latencia (3000ms)
   - Threshold: P95 < 300ms

3. **cenario-C-falha.js**
   - 50 VUs, 1 minuto
   - modo=falha (503)
   - Threshold: error_rate < 1%

#### Cenários Estendidos (ADICIONAR no TCC)
4. **cenario-G-alta-concorrencia.js**
   - 500 VUs, múltiplos estágios
   - modo=normal
   - Avalia escalabilidade

5. **cenario-F-falhas-intermitentes.js**
   - Padrão de falha variado
   - Testa robustez do CB

6. **cenario-E-recuperacao.js**
   - Falha → Recuperação
   - Testa auto-recuperação do CB

7. **cenario-D-estresse-crescente.js**
   - Carga crescente (ramp-up)
   - **PENDENTE**: decidir inclusão

---

### Como Executar Testes

#### Manualmente (um cenário)
```bash
# 1. Subir ambiente
export PAYMENT_SERVICE_VERSION=v1  # ou v2
docker-compose up -d --build

# 2. Executar teste
docker run --rm -i \
  --network=tcc-performance-circuit-breaker_tcc-network \
  -v $PWD/k6:/k6 \
  grafana/k6:latest run /k6/scripts/cenario-A-normal.js \
  --out json=/k6/results/V1_Normal.json

# 3. Parar ambiente
docker-compose down -v
```

#### Automatizado (todos os cenários)
```bash
./run_all_tests.sh
```

**Resultado**: 14 arquivos JSON em `k6/results/`

---

## 📈 ANÁLISE DE RESULTADOS

### Script Principal
**Arquivo**: `analysis/analyze_and_report.py`

**Funcionalidades**:
1. Processamento em streaming (eficiente para arquivos grandes)
2. Cálculo de estatísticas (média, mediana, percentis, CV)
3. Geração de gráficos (PNG)
4. Relatório Markdown

**Execução**:
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar análise
python analysis/analyze_and_report.py
```

**Saída**:
- `analysis_results/plots/*.png` - 4 gráficos
- `analysis_results/markdown/analysis_report.md` - Relatório
- `analysis_results/summary_metrics.csv` - Dados tabulares

---

### Métricas Calculadas

#### Tempo de Resposta
- **Média** (`mean`): Tendência central
- **Mediana** (`median`): Valor típico
- **Desvio Padrão** (`std`): Dispersão
- **Percentis**:
  - P50 (mediana)
  - P75 (terceiro quartil)
  - P90 (90% abaixo deste valor)
  - **P95** (SLA comum)
  - **P99** (casos extremos)

#### Confiabilidade
- **Taxa de Erro** (`error_rate`): % de requisições falhadas
- **Total Requisições** (`total_requests`): Volume processado

#### Variabilidade
- **Coeficiente de Variação** (`CV`): std/mean
  - CV < 0.3: Excelente consistência
  - CV 0.3-0.5: Boa consistência
  - CV > 0.5: Alta variabilidade

---

### Análises Adicionais Necessárias

#### 1. Significância Estatística
**Arquivo**: Criar `analysis/statistical_tests.py`

```python
from scipy import stats
import pandas as pd

def test_significance(v1_data, v2_data):
    # Teste t
    t_stat, p_value = stats.ttest_ind(v1_data, v2_data)
    
    # Mann-Whitney U (não-paramétrico)
    u_stat, p_mw = stats.mannwhitneyu(v1_data, v2_data)
    
    # Cohen's d
    pooled_std = np.sqrt((v1_data.std()**2 + v2_data.std()**2) / 2)
    cohens_d = (v1_data.mean() - v2_data.mean()) / pooled_std
    
    return {
        'p_value_t': p_value,
        'p_value_mw': p_mw,
        'cohens_d': cohens_d,
        'effect': interpret_cohens_d(cohens_d)
    }

def interpret_cohens_d(d):
    if abs(d) < 0.2: return "pequeno"
    if abs(d) < 0.5: return "médio"
    if abs(d) < 0.8: return "grande"
    return "muito grande"
```

#### 2. Análise de Throughput
**Adicionar ao script principal**:
```python
# Calcular RPS (Requests Per Second)
duration_seconds = test_duration  # de metadata
rps_v1 = total_requests_v1 / duration_seconds
rps_v2 = total_requests_v2 / duration_seconds

# Comparar
throughput_diff = ((rps_v2 - rps_v1) / rps_v1) * 100
```

---

## 🔧 GUIAS DE PROCEDIMENTO

### Como Reexecutar Experimentos

#### Passo 1: Preparar Ambiente
```bash
# Limpar resultados anteriores (CUIDADO!)
# rm -rf k6/results/*.json

# Verificar Docker
docker --version
docker-compose --version
```

#### Passo 2: Testar V1
```bash
export PAYMENT_SERVICE_VERSION=v1
docker-compose up -d --build

# Aguardar serviços (~30s)
sleep 30

# Executar cenários (exemplo com 3 básicos)
for cenario in A-normal B-latencia C-falha; do
  docker run --rm -i \
    --network=tcc-performance-circuit-breaker_tcc-network \
    -v $PWD/k6:/k6 \
    grafana/k6:latest run /k6/scripts/cenario-${cenario}.js \
    --out json=/k6/results/V1_${cenario}.json
done

docker-compose down -v
```

#### Passo 3: Testar V2
```bash
export PAYMENT_SERVICE_VERSION=v2
docker-compose up -d --build
sleep 30

for cenario in A-normal B-latencia C-falha; do
  docker run --rm -i \
    --network=tcc-performance-circuit-breaker_tcc-network \
    -v $PWD/k6:/k6 \
    grafana/k6:latest run /k6/scripts/cenario-${cenario}.js \
    --out json=/k6/results/V2_${cenario}.json
done

docker-compose down -v
```

---

### Como Gerar Análises Atualizadas

#### Opção 1: Script Automatizado
```bash
python analysis/analyze_and_report.py
```

#### Opção 2: Com Testes Estatísticos (TODO)
```bash
# Após implementar statistical_tests.py
python analysis/statistical_tests.py
python analysis/analyze_and_report.py --with-stats
```

---

### Como Atualizar Documentação

#### Capítulos do TCC
1. Editar arquivo Markdown em `docs/chapters/`
2. Seguir TODOs listados neste guia
3. Referenciar imagens e dados corretos
4. Manter consistência entre capítulos

#### Diagramas
```bash
cd docs/diagramas

# Editar arquivos .puml
# Gerar PNGs
python generate_diagrams.py

# Imagens vão para docs/images/
```

#### Relatório de Análise
- Executar `analyze_and_report.py`
- Copiar seções relevantes para Capítulo 3
- Ajustar narrativa acadêmica

---

## 🎯 CHECKLIST PARA ESCRITA

### Antes de Começar
- [ ] Ler `docs/ANALISE_INCONGRUENCIAS.md` completamente
- [ ] Verificar que todos os dados estão disponíveis
- [ ] Executar análises atualizadas se necessário
- [ ] Revisar configuração do Circuit Breaker

### Durante a Escrita

#### Capítulo 1
- [ ] Atualizar objetivos para 7 cenários
- [ ] Adicionar referências completas
- [ ] Revisar conexão com Pinheiro et al.

#### Capítulo 2
- [ ] Adicionar seção "Cenários Estendidos"
- [ ] Justificar configuração do CB
- [ ] Incluir nota sobre limitações (Estresse)
- [ ] Atualizar diagramas se necessário

#### Capítulo 3
- [ ] Incluir análise dos 7 cenários
- [ ] Adicionar testes estatísticos
- [ ] Incluir análise de throughput
- [ ] Melhorar gráficos (legendas, qualidade)
- [ ] Discussão de trade-offs

#### Capítulo 4
- [ ] Adicionar seção "Limitações"
- [ ] Expandir trabalhos futuros
- [ ] Resumir contribuições
- [ ] Validar conexão com modelo teórico

### Após Escrever
- [ ] Verificar consistência entre capítulos
- [ ] Validar todas as referências
- [ ] Revisar numeração de figuras/tabelas
- [ ] Spell check
- [ ] Peer review (colegas/orientador)

---

## 📚 REFERÊNCIAS BIBLIOGRÁFICAS

### Já Citadas
1. **Pinheiro, E., Dantas, J., et al.** (2024). Performance Modeling of Microservices with Circuit Breakers using Stochastic Petri Nets.

### Adicionar ao TCC

#### Livros
2. **Nygard, M.** (2018). *Release It!: Design and Deploy Production-Ready Software*. 2nd ed. Pragmatic Bookshelf.
   - Referência clássica sobre Circuit Breaker e padrões de resiliência

3. **Newman, S.** (2021). *Building Microservices: Designing Fine-Grained Systems*. 2nd ed. O'Reilly Media.
   - Arquiteturas de microsserviços e comunicação

4. **Kleppmann, M.** (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
   - Distributed systems, fault tolerance

#### Artigos e Papers
5. **Fowler, M.** (2014). *CircuitBreaker*. martinfowler.com/bliki/CircuitBreaker.html
   - Padrão arquitetural original

6. **Richardson, C.** (2018). *Microservices Patterns*. Manning Publications.
   - Padrões de microsserviços incluindo CB

#### Documentação Técnica
7. **Resilience4j Documentation**. https://resilience4j.readme.io/
   - Biblioteca usada no experimento

8. **k6 Documentation**. https://k6.io/docs/
   - Ferramenta de teste de carga

9. **Spring Cloud Documentation**. https://spring.io/projects/spring-cloud
   - Spring Cloud OpenFeign

---

## 🔗 LINKS ÚTEIS

### Repositório
- GitHub: (adicionar link quando publicar)

### Ferramentas
- Resilience4j: https://resilience4j.readme.io/
- k6: https://k6.io/
- Spring Boot: https://spring.io/projects/spring-boot
- Docker: https://www.docker.com/
- PlantUML: https://plantuml.com/

### Tutoriais
- Circuit Breaker com Resilience4j: https://resilience4j.readme.io/docs/circuitbreaker
- k6 Load Testing: https://k6.io/docs/get-started/running-k6/
- Spring Cloud OpenFeign: https://spring.io/projects/spring-cloud-openfeign

---

## 📞 CONTATOS E SUPORTE

### Autor
- Nome: (adicionar)
- Email: (adicionar)
- LinkedIn: (adicionar)

### Orientador
- Nome: (adicionar)
- Email: (adicionar)

### Instituição
- UFPE - Universidade Federal de Pernambuco
- CIn - Centro de Informática

---

## 📝 HISTÓRICO DE VERSÕES

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 05/11/2025 | Análise Técnica | Versão inicial do guia |

---

**Última atualização**: 05/11/2025  
**Próxima revisão**: Após correção dos TODOs críticos
