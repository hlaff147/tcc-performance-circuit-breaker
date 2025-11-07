# 📚 Documentação do TCC - Circuit Breaker

Esta pasta contém toda a documentação necessária para escrever o TCC.

---

## 🚀 COMECE AQUI

### Primeiro Passo
Leia os documentos nesta ordem:

1. **[📊 Sumário Executivo](SUMARIO_EXECUTIVO.md)** ← **COMECE AQUI!**
   - Visão geral de tudo que foi analisado
   - Resumo dos problemas e soluções
   - ~10 minutos de leitura

2. **[⚡ Ações Prioritárias](ACOES_PRIORITARIAS.md)** ← **DEPOIS LEIA ISTO!**
   - O que fazer AGORA
   - Passo a passo com código pronto
   - Cronograma sugerido

3. **[📑 Índice Mestre](INDICE_MESTRE.md)**
   - Use como referência
   - Marque nos favoritos
   - Todos os links do projeto

4. **[📋 Relatório de Incongruências](ANALISE_INCONGRUENCIAS.md)**
   - Problemas detalhados
   - Análise técnica completa
   - Consulte quando tiver dúvidas

5. **[📚 Guia de Organização](GUIA_ORGANIZACAO_TCC.md)**
   - Estrutura completa
   - Checklists
   - Procedimentos

---

## 📖 Capítulos do TCC

Os capítulos estão em [`chapters/`](chapters/):

| Capítulo | Arquivo | Status | TODOs |
|----------|---------|--------|-------|
| 1. Introdução | [01-introducao-e-justificativa.md](chapters/01-introducao-e-justificativa.md) | ⚠️ Atualizar | 2 TODOs |
| 2. Metodologia | [02-metodologia-e-design-experimento.md](chapters/02-metodologia-e-design-experimento.md) | 🔴 Urgente | 3 TODOs críticos |
| 3. Resultados | [03-resultados-e-discussao.md](chapters/03-resultados-e-discussao.md) | 🔴 Expandir | 4 TODOs críticos |
| 4. Conclusão | [04-conclusao.md](chapters/04-conclusao.md) | ⚠️ Adicionar | 3 TODOs |

---

## 🎨 Diagramas e Imagens

### Diagramas PlantUML (Fontes)
Localização: [`diagramas/puml/`](diagramas/puml/)

- `arquitetura_geral.puml`
- `componentes_internos.puml`
- `sequencia_falha_v1.puml`
- `sequencia_resiliencia_v2.puml`
- `stack_monitoramento.puml`

**Gerar imagens**:
```bash
cd diagramas
python generate_diagrams.py
```

### Imagens PNG (Prontas para Uso)
Localização: [`images/`](images/)

Use nos capítulos com:
```markdown
![Descrição](../images/nome_arquivo.png)
```

---

## 🔍 Problemas Identificados

### 🔴 Críticos (6 problemas)
1. Discrepância 3 vs 7 cenários
2. Taxas de erro 100% em V1 (validado, mas precisa explicação)
3. Cenário Estresse não processado
4. Falta significância estatística
5. Overhead CB não discutido
6. Configuração CB não justificada

### ⚠️ Moderados (4 problemas)
7. Falta análise de throughput
8. Inconsistência no número de requisições
9. Gráficos sem legendas adequadas
10. Falta conexão com literatura

**Detalhes**: Ver [ANALISE_INCONGRUENCIAS.md](ANALISE_INCONGRUENCIAS.md)

---

## ✅ Checklist Rápido

### Esta Semana
- [ ] Atualizar Cap. 1 (objetivos)
- [ ] Atualizar Cap. 2 (cenários + config CB)
- [ ] Documentar taxas de erro no Cap. 3
- [ ] Decidir sobre Estresse

### Próximas 2 Semanas
- [ ] Implementar testes estatísticos
- [ ] Expandir Cap. 3 (7 cenários)
- [ ] Adicionar trade-offs
- [ ] Atualizar Cap. 4

---

## 📊 Dados Disponíveis

### Resultados Processados
- **Relatório**: `../analysis_results/markdown/analysis_report.md`
- **CSV**: `../analysis_results/summary_metrics.csv`
- **Gráficos**: `../analysis_results/plots/*.png`

### Dados Brutos
- **k6 JSON**: `../k6/results/*.json` (14 arquivos, ~14.7 GB)

---

## 🆘 Ajuda

### Se estiver perdido
1. Volte ao [Sumário Executivo](SUMARIO_EXECUTIVO.md)
2. Consulte o [Índice Mestre](INDICE_MESTRE.md)
3. Siga as [Ações Prioritárias](ACOES_PRIORITARIAS.md)

### Se tiver dúvidas técnicas
- Consulte [GUIA_ORGANIZACAO_TCC.md](GUIA_ORGANIZACAO_TCC.md)
- Seção específica sobre código, testes, análises

### Se quiser entender os problemas
- Leia [ANALISE_INCONGRUENCIAS.md](ANALISE_INCONGRUENCIAS.md)
- Lista completa com severidade e soluções

---

## 📁 Estrutura desta Pasta

```
docs/
├── README.md                          ← Você está aqui
├── SUMARIO_EXECUTIVO.md              ← LEIA PRIMEIRO
├── ACOES_PRIORITARIAS.md             ← DEPOIS ISTO
├── INDICE_MESTRE.md                  ← Referência
├── ANALISE_INCONGRUENCIAS.md         ← Problemas detalhados
├── GUIA_ORGANIZACAO_TCC.md           ← Guia completo
│
├── chapters/                          ← Capítulos do TCC
│   ├── 01-introducao-e-justificativa.md
│   ├── 02-metodologia-e-design-experimento.md
│   ├── 03-resultados-e-discussao.md
│   └── 04-conclusao.md
│
├── diagramas/                         ← Diagramas PlantUML
│   ├── generate_diagrams.py
│   └── puml/
│       └── *.puml
│
└── images/                            ← Imagens PNG
    └── *.png
```

---

## 🎯 Objetivo Final

Ter um TCC com:
- ✅ Documentação completa e coerente
- ✅ Análise estatística rigorosa
- ✅ Todos os 7 cenários documentados
- ✅ Justificativas técnicas sólidas
- ✅ Conexão com literatura (Pinheiro et al.)
- ✅ Discussão balanceada de trade-offs

---

**Você tem tudo que precisa. Agora é só seguir o plano!** 🚀

---

**Última atualização**: 05/11/2025
