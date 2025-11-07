# 📚 ÍNDICE MESTRE DO TCC - CIRCUIT BREAKER

**Projeto**: Análise de Desempenho e Resiliência em Microsserviços com Circuit Breaker  
**Última Atualização**: 05/11/2025

---

## 🎯 INÍCIO RÁPIDO

### Para Revisar a Documentação
1. Leia o **[Relatório de Incongruências](ANALISE_INCONGRUENCIAS.md)** primeiro
2. Consulte o **[Guia de Organização](GUIA_ORGANIZACAO_TCC.md)** para navegação
3. Use este índice para acesso rápido aos documentos

### Para Escrever o TCC
1. Siga a ordem dos capítulos listados abaixo
2. Consulte os TODOs em cada documento
3. Valide com o checklist do Guia de Organização

---

## 📖 DOCUMENTAÇÃO DO TCC

### Documentos de Apoio (LEIA PRIMEIRO)
| Documento | Localização | Propósito |
|-----------|-------------|-----------|
| **Relatório de Incongruências** | [`docs/ANALISE_INCONGRUENCIAS.md`](ANALISE_INCONGRUENCIAS.md) | Lista todos os problemas identificados, severidade e recomendações |
| **Guia de Organização** | [`docs/GUIA_ORGANIZACAO_TCC.md`](GUIA_ORGANIZACAO_TCC.md) | Navegação completa, estrutura, checklists e procedimentos |
| Este Índice | [`docs/INDICE_MESTRE.md`](INDICE_MESTRE.md) | Acesso rápido a todos os documentos |

---

### Capítulos do TCC

#### Capítulo 1: Introdução e Justificativa
- **Arquivo**: [`chapters/01-introducao-e-justificativa.md`](chapters/01-introducao-e-justificativa.md)
- **Status**: ⚠️ Requer atualização
- **TODOs Críticos**:
  - [ ] Atualizar objetivos para incluir 7 cenários (não apenas 3)
  - [ ] Adicionar objetivo sobre análise de alta concorrência

#### Capítulo 2: Metodologia e Design do Experimento
- **Arquivo**: [`chapters/02-metodologia-e-design-experimento.md`](chapters/02-metodologia-e-design-experimento.md)
- **Status**: 🔴 Requer atualização urgente
- **TODOs Críticos**:
  - [ ] **ADICIONAR** Seção 5.4: "Cenários Estendidos" (7 cenários, não 3)
  - [ ] **ADICIONAR** Seção 2.X: "Parametrização do Circuit Breaker"
  - [ ] Justificar configuração do CB (threshold, window size, etc.)

#### Capítulo 3: Resultados e Discussão
- **Arquivo**: [`chapters/03-resultados-e-discussao.md`](chapters/03-resultados-e-discussao.md)
- **Status**: 🔴 Requer expansão significativa
- **TODOs Críticos**:
  - [ ] **EXPANDIR** para 7 cenários (usar dados de `analysis_results/`)
  - [ ] **ADICIONAR** Seção 3.X: "Validação Estatística" (testes t, p-values)
  - [ ] **ADICIONAR** Seção 3.Y: "Análise de Throughput"
  - [ ] Incluir análise de trade-offs do CB

#### Capítulo 4: Conclusão
- **Arquivo**: [`chapters/04-conclusao.md`](chapters/04-conclusao.md)
- **Status**: ⚠️ Requer adições
- **TODOs**:
  - [ ] **ADICIONAR** Seção: "Limitações do Estudo"
  - [ ] **EXPANDIR** "Trabalhos Futuros"
  - [ ] **ADICIONAR** "Contribuições"

---

## 📊 DADOS E RESULTADOS

### Dados Brutos (k6)
**Localização**: `k6/results/`

| Cenário | V1 | V2 | Status | Tamanho |
|---------|----|----|--------|---------|
| Normal | ✅ | ✅ | Processado | ~11 MB cada |
| Latência | ✅ | ✅ | Processado | ~3 MB cada |
| Falha | ✅ | ✅ | Processado | ~11 MB cada |
| Alta Concorrência | ✅ | ✅ | Processado | ~230 MB cada |
| Falhas Intermitentes | ✅ | ✅ | Processado | ~315 MB cada |
| Recuperação | ✅ | ✅ | Processado | ~205 MB cada |
| Estresse | ✅ | ✅ | ⚠️ **PENDENTE** | ~7 GB cada |

**Total**: 14 arquivos, ~14.7 GB

---

### Resultados Processados
**Localização**: `analysis_results/`

| Tipo | Arquivo | Uso |
|------|---------|-----|
| **Relatório Principal** | `markdown/analysis_report.md` | Base para Capítulo 3 |
| **Métricas CSV** | `summary_metrics.csv` | Dados tabulares, análises adicionais |
| **Gráficos** | `plots/response_times.png` | Tempos médio e P95 |
| | `plots/error_rates.png` | Taxas de erro comparativas |
| | `plots/distribution_boxplot.png` | Distribuição dos tempos |
| | `plots/statistical_variability.png` | Coeficiente de Variação |

---

### Análises Específicas
**Localização**: `analysis/reports/`

| Relatório | Arquivo | Foco |
|-----------|---------|------|
| Alta Concorrência | `high_concurrency_analysis.md` | Análise detalhada de 500 VUs |
| CSV Stats | `csv/response_times_analysis.csv` | Dados para gráficos |
| | `csv/statistical_analysis.csv` | Estatísticas adicionais |

---

## 🎨 DIAGRAMAS E IMAGENS

### Diagramas PlantUML (Fontes)
**Localização**: `diagramas/puml/`

| Diagrama | Arquivo | Usado em |
|----------|---------|----------|
| Arquitetura Geral | `arquitetura_geral.puml` | Cap. 2 - Visão geral |
| Componentes Internos | `componentes_internos.puml` | Cap. 2 - Detalhamento |
| Sequência Falha V1 | `sequencia_falha_v1.puml` | Cap. 1, 3 - Problema |
| Sequência CB V2 | `sequencia_resiliencia_v2.puml` | Cap. 1, 3 - Solução |
| Stack Monitoramento | `stack_monitoramento.puml` | Cap. 2 - Observabilidade |

**Como gerar**: `python diagramas/generate_diagrams.py`

---

### Imagens PNG (Geradas)
**Localização**: `images/`

Todas as imagens estão prontas para uso nos capítulos:
```markdown
![Arquitetura Geral](../images/arquitetura_geral.png)
```

---

## 💻 CÓDIGO-FONTE

### Serviços Java/Spring Boot
**Localização**: `../services/`

| Serviço | Diretório | Características |
|---------|-----------|-----------------|
| **Payment V1** (Baseline) | `payment-service-v1/` | Spring Boot + Feign, timeout 2s |
| **Payment V2** (CB) | `payment-service-v2/` | + Resilience4j Circuit Breaker |
| **Acquirer** (Simulador) | `acquirer-service/` | Modos: normal/latencia/falha |

**Arquivos Chave**:
- `payment-service-v2/src/main/resources/application.yml` - Configuração CB
- `payment-service-v2/.../PagamentoController.java` - @CircuitBreaker
- `acquirer-service/.../AdquirenteController.java` - Simulador

---

### Scripts de Teste k6
**Localização**: `../k6/scripts/`

| Script | Cenário | Documentado? |
|--------|---------|--------------|
| `cenario-A-normal.js` | Normal | ✅ Cap. 2 |
| `cenario-B-latencia.js` | Latência | ✅ Cap. 2 |
| `cenario-C-falha.js` | Falha | ✅ Cap. 2 |
| `cenario-G-alta-concorrencia.js` | Alta Concorrência | ⚠️ **TODO** |
| `cenario-F-falhas-intermitentes.js` | Falhas Intermitentes | ⚠️ **TODO** |
| `cenario-E-recuperacao.js` | Recuperação | ⚠️ **TODO** |
| `cenario-D-estresse-crescente.js` | Estresse | ⚠️ **TODO** |

---

### Scripts de Análise Python
**Localização**: `../analysis/`

| Script | Funcionalidade |
|--------|----------------|
| `analyze_and_report.py` | Processamento principal, gera relatório e gráficos |
| `scripts/analyze_high_concurrency.py` | Análise específica Alta Concorrência |
| `scripts/analyze_results.py` | Análises adicionais |

---

## 🔍 PROBLEMAS IDENTIFICADOS

### 🔴 Críticos (Resolver Urgentemente)
1. **Discrepância Documentação vs Implementação**
   - Capítulos 1-2 mencionam 3 cenários, mas há 7 implementados
   - **Ação**: Atualizar Cap. 2 seção 5.4 com cenários estendidos

2. **Taxas de Erro de 100% em V1**
   - Cenários Falha/Alta_Concorrencia/Intermitentes/Recuperacao
   - **Validado**: É correto! V1 falha sem CB, V2 retorna 202
   - **Ação**: Explicar no Cap. 3 que isso PROVA necessidade do CB

3. **Falta de Significância Estatística**
   - Relatório não tem p-values, intervalos de confiança
   - **Ação**: Adicionar testes estatísticos ao Cap. 3

4. **Cenário Estresse Não Analisado**
   - 14 GB de dados não processados
   - **Ação**: Decidir (processar com amostragem OU justificar exclusão)

---

### ⚠️ Moderados (Atenção Necessária)
5. **Overhead do CB Não Discutido**
   - V2 às vezes tem CV maior que V1
   - **Ação**: Seção de trade-offs no Cap. 3/4

6. **Configuração CB Não Justificada**
   - Por que threshold 50%? Por que window 20?
   - **Ação**: Adicionar justificativa no Cap. 2

7. **Falta Conexão com Literatura**
   - Pinheiro et al. citado mas não comparado
   - **Ação**: Comparar resultados com modelo SPN

---

## ✅ PONTOS FORTES

1. ✅ **Código Bem Estruturado**: V1 e V2 separados, fácil comparar
2. ✅ **Dados Completos**: 14 arquivos JSON, todos os cenários
3. ✅ **Análise Corrigida**: Script Python usa status HTTP corretamente
4. ✅ **Métricas Avançadas**: Percentis, CV, distribuições
5. ✅ **Implementação Correta**: Resilience4j com fallback adequado
6. ✅ **Validação k6**: Checks aceitam 200 OR 202
7. ✅ **Documentação Estruturada**: Capítulos em Markdown
8. ✅ **Reprodutível**: Docker + scripts automatizados

---

## 📋 CHECKLISTS

### Checklist Geral de Escrita
- [ ] Ler `ANALISE_INCONGRUENCIAS.md` completo
- [ ] Seguir estrutura do `GUIA_ORGANIZACAO_TCC.md`
- [ ] Atualizar todos os TODOs dos capítulos
- [ ] Validar consistência entre capítulos
- [ ] Adicionar testes estatísticos
- [ ] Incluir todos os 7 cenários
- [ ] Justificar configuração do CB
- [ ] Discutir trade-offs
- [ ] Conectar com Pinheiro et al.
- [ ] Revisar referências bibliográficas

---

### Checklist por Capítulo

#### Capítulo 1
- [x] Contextualização
- [x] Problema definido
- [x] Solução proposta
- [x] Conexão com literatura
- [ ] **TODO**: Atualizar objetivos (7 cenários)

#### Capítulo 2
- [x] Metodologia
- [x] Stack tecnológico
- [x] Arquitetura
- [x] 3 cenários básicos
- [ ] **TODO**: Cenários estendidos
- [ ] **TODO**: Justificar config CB

#### Capítulo 3
- [x] Tabelas básicas (3 cenários)
- [ ] **TODO**: Expandir para 7 cenários
- [ ] **TODO**: Testes estatísticos
- [ ] **TODO**: Análise throughput
- [ ] **TODO**: Trade-offs

#### Capítulo 4
- [x] Síntese
- [x] Conexão teórica
- [ ] **TODO**: Limitações
- [ ] **TODO**: Trabalhos futuros expandidos

---

## 🎯 PRIORIZAÇÃO DE TAREFAS

### Semana 1 (Urgente)
1. **P0**: Atualizar Cap. 2 - Cenários Estendidos
2. **P0**: Validar taxas de erro (já OK, mas documentar)
3. **P1**: Adicionar testes estatísticos

### Semana 2 (Importante)
4. **P2**: Decisão sobre Estresse
5. **P2**: Seção trade-offs do CB
6. **P3**: Justificar config CB
7. **P3**: Conectar com Pinheiro et al.

### Semana 3 (Se Houver Tempo)
8. **P4**: Análise throughput
9. **P4**: Investigar diferença requisições
10. **P5**: Melhorar gráficos

---

## 📚 REFERÊNCIAS RÁPIDAS

### Documentação Técnica
- [Resilience4j Circuit Breaker](https://resilience4j.readme.io/docs/circuitbreaker)
- [k6 Load Testing](https://k6.io/docs/)
- [Spring Cloud OpenFeign](https://spring.io/projects/spring-cloud-openfeign)

### Literatura Acadêmica
- Pinheiro et al. (2024) - SPNs e CB
- Nygard (2018) - Release It!
- Newman (2021) - Building Microservices
- Fowler (2014) - CircuitBreaker pattern

---

## 🔗 NAVEGAÇÃO RÁPIDA

### Por Tipo de Conteúdo

#### 📖 Leitura/Escrita
- [Cap. 1 - Introdução](chapters/01-introducao-e-justificativa.md)
- [Cap. 2 - Metodologia](chapters/02-metodologia-e-design-experimento.md)
- [Cap. 3 - Resultados](chapters/03-resultados-e-discussao.md)
- [Cap. 4 - Conclusão](chapters/04-conclusao.md)

#### 📊 Análise
- [Relatório Principal](../analysis_results/markdown/analysis_report.md)
- [Análise Alta Concorrência](../analysis/reports/high_concurrency_analysis.md)
- [Métricas CSV](../analysis_results/summary_metrics.csv)

#### 🖼️ Imagens
- [Gráficos](../analysis_results/plots/)
- [Diagramas](images/)

#### 💻 Código
- [Payment V1](../services/payment-service-v1/)
- [Payment V2](../services/payment-service-v2/)
- [Scripts k6](../k6/scripts/)
- [Script Análise](../analysis/analyze_and_report.py)

---

## 📞 INFORMAÇÕES DO PROJETO

### Instituição
- **Universidade**: UFPE - Universidade Federal de Pernambuco
- **Centro**: CIn - Centro de Informática
- **Curso**: (Adicionar)

### Contatos
- **Autor**: (Adicionar)
- **Orientador**: (Adicionar)

---

## 📝 CONTROLE DE VERSÃO

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | 05/11/2025 | Versão inicial do índice mestre |

---

**Última Atualização**: 05/11/2025  
**Próxima Revisão**: Após correção dos TODOs P0 e P1
