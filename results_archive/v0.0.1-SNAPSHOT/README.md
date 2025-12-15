# Resultados - Versão 0.0.1-SNAPSHOT

**Data do arquivamento:** 2024-12-06
**Descrição:** Versão inicial do experimento - Implementação básica V1/V2 sem refatoração

## 📋 Resumo da Versão

Esta é a versão inicial do experimento de TCC, contendo:

- **Payment Service V1 (Baseline):** Implementação simples com timeout
- **Payment Service V2 (Resilient):** Implementação com Circuit Breaker básico
- **Cenários testados:** Catástrofe, Degradação, Rajadas, Indisponibilidade Extrema

## 📊 Resultados Principais

### Cenário: Indisponibilidade Extrema (75% OFF)
| Métrica | V1 | V2 |
|---------|----|----|
| Disponibilidade | 10.1% | 97.1% |
| Fallback | N/A | 92.8% |
| Tempo médio | 156ms | 40ms |

### Cenário: Falha Catastrófica
| Métrica | V1 | V2 |
|---------|----|----|
| Disponibilidade | 90.0% | 94.5% |
| Redução de falhas | - | 44.8% |

## 📂 Conteúdo

- `results/` - Resultados brutos do K6 (JSON)
- `analysis_results/` - Gráficos, CSVs e relatórios HTML

## 🔄 Como Reproduzir

```bash
# Checkout da versão
git checkout v0.0.1-SNAPSHOT  # Se houver tag

# Ou restaurar arquivos desta versão
cp -r results_archive/v0.0.1-SNAPSHOT/results/* k6/results/
cp -r results_archive/v0.0.1-SNAPSHOT/analysis_results/* analysis_results/
```

## ⚠️ Notas

- Esta versão não possui testes unitários
- O Controller continha lógica de negócio (violação SRP)
- Métricas K6 não eram padronizadas entre cenários
