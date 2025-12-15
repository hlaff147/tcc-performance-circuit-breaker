# Resumo dos Cenários de Teste

Documento curto com resumo objetivo de cada cenário de teste usado nos experimentos.

---

## cenario-completo.js
- **Objetivo:** Testar comportamento sob carga de estresse (aquecimento → pico → manutenção prolongada → recuperação).
- **O que testa:** resistência e desempenho contínuo do serviço (taxa de falhas, p95 de latência); serve como baseline para comparar versões/estratégias.

## cenario-falha-catastrofica.js
- **Objetivo:** Simular indisponibilidade total da API externa por janela prolongada.
- **O que testa:** abertura rápida do Circuit Breaker, proteção contra timeouts e sobrecarga, mantendo respostas rápidas durante a falha.

## cenario-degradacao-gradual.js
- **Objetivo:** Simular degradação progressiva (aumento de latência e falhas ao longo do tempo).
- **O que testa:** detecção precoce de degradação pelo CB e isolamento antes de cascata total, preservando respostas mais previsíveis.

## cenario-rajadas-intermitentes.js
- **Objetivo:** Simular rajadas intermitentes de falha (períodos de 100% falha alternando com períodos normais).
- **O que testa:** capacidade do CB de abrir/fechar dinamicamente entre rajadas, protegendo durante picos de erro sem sacrificar disponibilidade entre eles.

## cenario-indisponibilidade-extrema.js
- **Objetivo:** Forçar janelas longas de indisponibilidade (≈75% do tempo) para mostrar o ganho máximo do CB.
- **O que testa:** comportamento sob manutenção/prolongada indisponibilidade e como o CB mantém o sistema utilizável apesar da dependência majoritariamente fora do ar.

---

Se quiser, eu adiciono este resumo em `ANALISE_FINAL_TCC.md`, ou exporto como CSV.
