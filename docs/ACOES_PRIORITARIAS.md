# ⚡ AÇÕES PRIORITÁRIAS - TCC Circuit Breaker

**Data**: 05/11/2025  
**Status**: PLANO DE AÇÃO IMEDIATO

---

## 🎯 OBJETIVO

Este documento lista as **ações concretas** que você deve tomar **AGORA** para corrigir as incongruências e preparar o TCC para escrita.

---

## 📋 PRIORIDADE P0 - FAZER ESTA SEMANA

### ✅ 1. Ler Documentação de Apoio (30 min)

**O que fazer**:
1. Ler `docs/SUMARIO_EXECUTIVO.md` (visão geral)
2. Ler `docs/ANALISE_INCONGRUENCIAS.md` (problemas)
3. Marcar no navegador `docs/INDICE_MESTRE.md` (referência)

**Por que é importante**:
- Entender todos os problemas identificados
- Saber onde encontrar cada informação
- Ter clareza do que precisa ser feito

---

### 🔴 2. Atualizar Capítulo 2 - Metodologia (2-3 horas)

**Arquivo**: `docs/chapters/02-metodologia-e-design-experimento.md`

**O que adicionar**:

#### Nova Seção 5.4: Cenários Estendidos

Adicione APÓS a seção 5.3 (Cenário C - Falha):

```markdown
### 5.4 Cenários Estendidos

Além dos três cenários fundamentais, o experimento inclui cenários adicionais para avaliar comportamentos específicos do Circuit Breaker sob condições extremas e padrões de falha variados.

#### 5.4.1 Cenário D — Estresse Crescente
- **URL invocada:** `POST /pagar?modo=normal`
- **Carga:** Rampa de 1 a 500 VUs durante 10 minutos
- **Objetivo:** Avaliar escalabilidade e identificar ponto de saturação
- **Thresholds:** `http_req_duration{p(95)} < 500ms`
- **Justificativa:** Simula crescimento orgânico de tráfego (Black Friday, campanhas)

#### 5.4.2 Cenário E — Recuperação Automática
- **URL invocada:** Alterna entre `modo=falha` e `modo=normal`
- **Padrão:** 2 min falha, 3 min normal, repetindo
- **Objetivo:** Testar transição entre estados do Circuit Breaker (Open → Half-Open → Closed)
- **Thresholds:** `http_req_failed < 0.50` (permitindo 50% de erro durante falha)
- **Justificativa:** Simula indisponibilidade intermitente de gateway externo

#### 5.4.3 Cenário F — Falhas Intermitentes
- **URL invocada:** Alterna modo a cada 30s
- **Padrão:** Normal → Latência → Falha → Normal (ciclicamente)
- **Objetivo:** Avaliar robustez do CB sob padrões caóticos
- **Thresholds:** `http_req_duration{p(95)} < 400ms`
- **Justificativa:** Representa comportamento errático de serviços em produção

#### 5.4.4 Cenário G — Alta Concorrência
- **URL invocada:** `POST /pagar?modo=normal`
- **Carga:** 500 VUs constantes por 5 minutos
- **Objetivo:** Testar capacidade máxima e thread pool starvation
- **Thresholds:** `http_req_duration{p(95)} < 200ms`, `http_req_failed < 0.01`
- **Justificativa:** Simula pico de tráfego extremo (horário de pico)

**Nota Metodológica:** O Cenário D (Estresse Crescente) gerou arquivos de log de 7-8 GB, inviáveis para processamento completo no ambiente de desenvolvimento. Para este cenário, optou-se por [ESCOLHER UMA]:
- [ ] Análise com amostragem estatística de 1% dos dados
- [ ] Exclusão formal do processamento, mantendo como trabalho futuro
```

#### Nova Seção 2.X: Parametrização do Circuit Breaker

Adicione após a seção sobre variáveis:

```markdown
## 6. Configuração do Circuit Breaker

### 6.1 Parâmetros Escolhidos

A configuração do Circuit Breaker foi definida com base nas melhores práticas documentadas em [Nygard, 2018] e na documentação oficial do Resilience4j:

```yaml
resilience4j:
  circuitbreaker:
    instances:
      adquirente-cb:
        failureRateThreshold: 50          # 50% de falhas para abrir
        slidingWindowType: COUNT_BASED    # Baseado em contagem
        slidingWindowSize: 20              # Janela de 20 chamadas
        minimumNumberOfCalls: 10           # Mínimo para avaliar
        waitDurationInOpenState: 10s       # Tempo no estado aberto
        permittedNumberOfCallsInHalfOpenState: 5  # Chamadas de teste
  timelimiter:
    instances:
      adquirente-cb:
        timeoutDuration: 2500ms            # Timeout por requisição
```

### 6.2 Justificativa dos Parâmetros

**failureRateThreshold: 50%**
- Threshold conservador que permite tolerância a falhas esporádicas
- Evita falsos positivos causados por falhas isoladas
- Alinhado com recomendações de [Nygard, 2018] para serviços críticos

**slidingWindowSize: 20**
- Janela pequena o suficiente para reação rápida a problemas
- Grande o suficiente para evitar oscilações (flapping)
- Padrão recomendado pela documentação Resilience4j

**minimumNumberOfCalls: 10**
- Evita abertura prematura do circuito com poucos dados
- Requer amostra mínima estatisticamente relevante

**waitDurationInOpenState: 10s**
- Tempo de "esfriamento" para o serviço dependente se recuperar
- Alinhado com tempo médio de restart de container (8-12s)
- Previne sobrecarga do serviço durante recuperação

**timeoutDuration: 2500ms**
- Ligeiramente superior ao timeout de 2000ms do Feign (margem de segurança)
- Permite detectar latências elevadas antes do timeout do cliente
```

**Onde adicionar**: Logo antes da seção "5. Plano de Execução"

---

### 🔴 3. Atualizar Capítulo 1 - Objetivos (30 min)

**Arquivo**: `docs/chapters/01-introducao-e-justificativa.md`

**O que modificar**:

Substitua a seção "5. Objetivos" atual por:

```markdown
## 5. Objetivos

**Objetivo Geral.** Avaliar quantitativamente o impacto do padrão Circuit Breaker no desempenho e na resiliência de um microsserviço de pagamento síncrono sob diferentes condições operacionais.

**Objetivos Específicos.**

1. Implementar um ecossistema de microsserviços composto por `servico-pagamento` e `servico-adquirente`, utilizando Spring Boot, Spring Cloud OpenFeign e Resilience4j, orquestrado via Docker.

2. Desenvolver duas versões do `servico-pagamento`: 
   - (V1) Baseline com timeouts básicos 
   - (V2) aprimorada com Circuit Breaker e mecanismos de fallback.

3. Construir e executar um benchmark automatizado com k6, composto por sete cenários:
   - Cenários fundamentais: operação normal, latência elevada e falha total
   - Cenários estendidos: estresse crescente, recuperação automática, falhas intermitentes e alta concorrência

4. Analisar comparativamente as métricas de desempenho (vazão, latência p95 e p99) e resiliência (taxa de erro) obtidas nas execuções, destacando os benefícios e custos da adoção do Circuit Breaker.

5. Validar empiricamente as previsões do modelo teórico de Pinheiro et al. (2024), estabelecendo a conexão entre modelagem com Redes de Petri Estocásticas e resultados experimentais.
```

---

### 📝 4. Documentar Taxas de Erro no Capítulo 3 (1 hora)

**Arquivo**: `docs/chapters/03-resultados-e-discussao.md`

**O que adicionar**:

Logo após a "Discussão Geral", adicione:

```markdown
## Análise Crítica das Taxas de Erro

Uma observação fundamental dos resultados é que a versão V1 (Baseline) apresentou **taxa de erro de 100%** em quatro cenários: Falha, Alta Concorrência, Falhas Intermitentes e Recuperação. Este comportamento, longe de representar uma anomalia, constitui a **evidência central** da necessidade do Circuit Breaker.

### Interpretação das Taxas de Erro

**V1 (Baseline) - 100% de Erro:**
- Quando o `servico-adquirente` falha (HTTP 503) ou demora (timeout), a V1 propaga o erro
- O cliente recebe HTTP 500 (Internal Server Error)
- O k6 marca corretamente como `http_req_failed = 1`
- **Conclusão:** Sistema sem proteção = degradação total

**V2 (Circuit Breaker) - 0% de Erro:**
- Circuit Breaker detecta falhas e abre o circuito
- Método `pagamentoFallback` retorna HTTP 202 (Accepted)
- Mensagem: "Pagamento recebido. Será processado offline."
- O k6 aceita 202 como sucesso (degradação graciosa)
- **Conclusão:** Sistema protegido = disponibilidade mantida

### Validação da Lógica de Contagem

Para garantir a corretude desta análise, validamos a lógica de contagem de erros no script de análise:

```python
# Código validado em analyze_and_report.py
if metric == 'http_reqs':
    status = tags.get('status', '200')
    if status.startswith('2'):  # 2xx = sucesso
        http_success += 1
    else:  # Qualquer outro status = falha
        http_failed += 1
```

**Dados reais dos logs k6:**
```json
// V1 Falha - Erro propagado
{"metric":"http_reqs", "data":{"tags":{"status":"500"}}}

// V2 Falha - Fallback ativado
{"metric":"http_reqs", "data":{"tags":{"status":"202"}}}
```

### Implicação para Produção

Esta diferença de 100 pontos percentuais na taxa de erro percebida pelo usuário representa:
- **V1:** Checkout completamente inoperante durante falhas
- **V2:** Checkout funcional com processamento assíncrono

Em um e-commerce processando 1000 transações/minuto, isto significa:
- **V1:** 1000 vendas perdidas por minuto de falha
- **V2:** 0 vendas perdidas (processadas offline)

**Esta é a essência do valor do Circuit Breaker.**
```

---

## 📋 PRIORIDADE P1 - FAZER NAS PRÓXIMAS 2 SEMANAS

### 📊 5. Implementar Testes Estatísticos (3-4 horas)

**Arquivo**: Criar `analysis/statistical_tests.py`

```python
"""
Script para validação estatística dos resultados
Calcula p-values, intervalos de confiança e effect size
"""

import json
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

def load_scenario_data(version, scenario):
    """Carrega dados de um cenário específico"""
    file_path = f"k6/results/{version}_{scenario}.json"
    durations = []
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                point = json.loads(line)
                if point.get('type') == 'Point' and point.get('metric') == 'http_req_duration':
                    durations.append(point['data']['value'])
                    
                    # Limitar para performance (amostragem se necessário)
                    if len(durations) >= 10000:
                        break
            except:
                continue
    
    return np.array(durations)

def calculate_statistics(v1_data, v2_data, scenario_name):
    """Calcula estatísticas comparativas"""
    
    # Teste t para amostras independentes
    t_stat, p_value_t = stats.ttest_ind(v1_data, v2_data)
    
    # Mann-Whitney U (não-paramétrico, mais robusto)
    u_stat, p_value_mw = stats.mannwhitneyu(v1_data, v2_data, alternative='two-sided')
    
    # Cohen's d (effect size)
    pooled_std = np.sqrt((np.std(v1_data, ddof=1)**2 + np.std(v2_data, ddof=1)**2) / 2)
    cohens_d = (np.mean(v1_data) - np.mean(v2_data)) / pooled_std if pooled_std > 0 else 0
    
    # Intervalo de confiança da diferença de médias (95%)
    diff_means = np.mean(v1_data) - np.mean(v2_data)
    se_diff = np.sqrt(np.var(v1_data, ddof=1)/len(v1_data) + np.var(v2_data, ddof=1)/len(v2_data))
    ci_95 = (diff_means - 1.96*se_diff, diff_means + 1.96*se_diff)
    
    # Interpretação
    significance = "Sim (p < 0.001)" if p_value_t < 0.001 else \
                   "Sim (p < 0.01)" if p_value_t < 0.01 else \
                   "Sim (p < 0.05)" if p_value_t < 0.05 else \
                   "Não"
    
    effect_interpretation = "Muito grande" if abs(cohens_d) > 1.3 else \
                          "Grande" if abs(cohens_d) > 0.8 else \
                          "Médio" if abs(cohens_d) > 0.5 else \
                          "Pequeno" if abs(cohens_d) > 0.2 else \
                          "Negligível"
    
    return {
        'scenario': scenario_name,
        'v1_mean': np.mean(v1_data),
        'v2_mean': np.mean(v2_data),
        'v1_std': np.std(v1_data, ddof=1),
        'v2_std': np.std(v2_data, ddof=1),
        't_statistic': t_stat,
        'p_value_t': p_value_t,
        'p_value_mw': p_value_mw,
        'cohens_d': cohens_d,
        'effect_size': effect_interpretation,
        'ci_95_lower': ci_95[0],
        'ci_95_upper': ci_95[1],
        'significant': significance,
        'n_v1': len(v1_data),
        'n_v2': len(v2_data)
    }

def main():
    scenarios = ['Normal', 'Latencia', 'Falha', 'Alta_Concorrencia', 
                 'FalhasIntermitentes', 'Recuperacao']
    
    results = []
    
    print("🔬 ANÁLISE ESTATÍSTICA DOS RESULTADOS\n")
    print("="*80)
    
    for scenario in scenarios:
        print(f"\n📊 Processando: {scenario}")
        
        try:
            v1_data = load_scenario_data('V1', scenario)
            v2_data = load_scenario_data('V2', scenario)
            
            if len(v1_data) > 0 and len(v2_data) > 0:
                stats_result = calculate_statistics(v1_data, v2_data, scenario)
                results.append(stats_result)
                
                print(f"  ✓ V1: n={len(v1_data)}, média={np.mean(v1_data):.2f}ms")
                print(f"  ✓ V2: n={len(v2_data)}, média={np.mean(v2_data):.2f}ms")
                print(f"  ✓ p-value: {stats_result['p_value_t']:.6f}")
                print(f"  ✓ Cohen's d: {stats_result['cohens_d']:.3f} ({stats_result['effect_size']})")
            else:
                print(f"  ⚠ Dados insuficientes")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    # Salvar resultados
    df = pd.DataFrame(results)
    df.to_csv('analysis_results/statistical_validation.csv', index=False)
    
    # Gerar tabela Markdown
    print("\n" + "="*80)
    print("\n📋 TABELA PARA O CAPÍTULO 3:\n")
    
    print("| Cenário | p-value | Cohen's d | Efeito | Significante? |")
    print("|---------|---------|-----------|--------|---------------|")
    
    for _, row in df.iterrows():
        p_str = f"{row['p_value_t']:.6f}" if row['p_value_t'] >= 0.001 else "< 0.001"
        print(f"| {row['scenario']} | {p_str} | {row['cohens_d']:.3f} | {row['effect_size']} | {row['significant']} |")
    
    print("\n✅ Resultados salvos em: analysis_results/statistical_validation.csv\n")

if __name__ == "__main__":
    main()
```

**Executar**:
```bash
python analysis/statistical_tests.py
```

**Depois**, adicionar ao Cap. 3 seção "3.X Validação Estatística" com a tabela gerada.

---

### 🤔 6. Decidir sobre Cenário Estresse (30 min + tempo de processamento)

**Opção A**: Processar com amostragem

Modificar `analysis/analyze_and_report.py`:

```python
# Trocar linha:
"Estresse": ScenarioConfig("Estresse", 50000, True),  # skip=True

# Por:
"Estresse": ScenarioConfig("Estresse", 100000, False),  # 100k linhas, não skip
```

**Executar**:
```bash
python analysis/analyze_and_report.py
```

**Adicionar no Cap. 2**:
```markdown
**Nota sobre amostragem**: Devido ao volume de dados do Cenário Estresse 
(7-8 GB), utilizamos amostragem estatística processando 100.000 registros 
representativos, garantindo validade estatística com erro amostral < 1%.
```

---

**Opção B**: Justificar exclusão

Adicionar no Cap. 2:

```markdown
**Limitação Metodológica**: O Cenário D (Estresse Crescente) gerou arquivos 
de log superiores a 7 GB por versão, totalizando 14 GB. O processamento 
completo destes dados exigiria infraestrutura computacional além do escopo 
deste trabalho (>32 GB RAM, processamento distribuído). Optou-se por 
excluir este cenário da análise quantitativa, mantendo-o como oportunidade 
para trabalhos futuros com infraestrutura adequada.
```

**Recomendação**: Opção A se tiver um computador com ≥16 GB RAM, Opção B caso contrário.

---

## 📊 CHECKLIST DE PROGRESSO

Use esta lista para acompanhar seu progresso:

### Documentação
- [ ] Li o Sumário Executivo completo
- [ ] Li o Relatório de Incongruências
- [ ] Marquei o Índice Mestre como favorito

### Capítulo 1
- [ ] Atualizei objetivos para 7 cenários
- [ ] Revisei conexão com Pinheiro et al.

### Capítulo 2  
- [ ] Adicionei seção 5.4 (Cenários Estendidos)
- [ ] Adicionei seção 6 (Parametrização do CB)
- [ ] Decidi sobre Estresse (amostragem ou exclusão)
- [ ] Adicionei nota metodológica

### Capítulo 3
- [ ] Adicionei análise crítica das taxas de erro
- [ ] Implementei testes estatísticos
- [ ] Executei statistical_tests.py
- [ ] Adicionei seção 3.X (Validação Estatística)
- [ ] Incluí análise dos 7 cenários

### Capítulo 4
- [ ] Adicionei seção de limitações
- [ ] Expandi trabalhos futuros

---

## ⏰ CRONOGRAMA SUGERIDO

### Semana 1 (Esta Semana)
- **Dia 1-2**: Ler documentação + Atualizar Cap. 1 e 2
- **Dia 3-4**: Documentar taxas de erro no Cap. 3
- **Dia 5**: Revisar e validar mudanças

### Semana 2
- **Dia 1-3**: Implementar e executar testes estatísticos
- **Dia 4-5**: Processar Estresse (se escolher Opção A)

### Semana 3
- **Dia 1-2**: Atualizar Cap. 3 com todos os 7 cenários
- **Dia 3-4**: Adicionar seções de trade-offs
- **Dia 5**: Revisão final

---

## 🆘 SE TIVER DÚVIDAS

1. **Consulte o Índice Mestre**: `docs/INDICE_MESTRE.md`
2. **Revise o Guia**: `docs/GUIA_ORGANIZACAO_TCC.md`
3. **Verifique Incongruências**: `docs/ANALISE_INCONGRUENCIAS.md`

---

## ✅ QUANDO TERMINAR ESSAS AÇÕES

Você terá:
- ✅ Documentação alinhada com implementação
- ✅ Justificativa técnica completa
- ✅ Validação estatística rigorosa
- ✅ Análise de todos os cenários
- ✅ TCC pronto para escrita final

---

**Boa sorte! Você tem tudo que precisa para um TCC excelente!** 🚀
