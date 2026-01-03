# Resultados Estatísticos - TCC Circuit Breaker

## Resumo dos Testes

### Comparações Pairwise

| Cenário | Teste | Comparação | p-value | Cohen's d | Efeito | Significativo |
|---------|-------|------------|---------|-----------|--------|---------------|
| catastrofe | Mann-Whitney U | V1 vs V2 | 0.0000 | 0.022 | negligível | ✅ Sim |
| catastrofe | Mann-Whitney U | V1 vs V3 | 0.0000 | -0.312 | pequeno | ✅ Sim |
| catastrofe | Mann-Whitney U | V1 vs V4 | 0.0000 | 0.024 | negligível | ✅ Sim |
| catastrofe | Mann-Whitney U | V2 vs V3 | 0.0000 | -0.331 | pequeno | ✅ Sim |
| catastrofe | Mann-Whitney U | V2 vs V4 | 0.0015 | 0.002 | negligível | ✅ Sim |
| catastrofe | Mann-Whitney U | V3 vs V4 | 0.0000 | 0.333 | pequeno | ✅ Sim |
| Completo | Mann-Whitney U | V1 vs V2 | 0.0000 | 0.256 | pequeno | ✅ Sim |
| Completo | Mann-Whitney U | V1 vs V3 | 0.0000 | -0.146 | negligível | ✅ Sim |
| Completo | Mann-Whitney U | V1 vs V4 | 0.0000 | 0.244 | pequeno | ✅ Sim |
| Completo | Mann-Whitney U | V2 vs V3 | 0.0000 | -0.364 | pequeno | ✅ Sim |
| Completo | Mann-Whitney U | V2 vs V4 | 0.0010 | -0.015 | negligível | ✅ Sim |
| Completo | Mann-Whitney U | V3 vs V4 | 0.0000 | 0.354 | pequeno | ✅ Sim |
| degradacao | Mann-Whitney U | V1 vs V2 | 0.0000 | 0.224 | pequeno | ✅ Sim |
| degradacao | Mann-Whitney U | V1 vs V3 | 0.0000 | -0.106 | negligível | ✅ Sim |
| degradacao | Mann-Whitney U | V1 vs V4 | 0.0000 | 0.238 | pequeno | ✅ Sim |
| degradacao | Mann-Whitney U | V2 vs V3 | 0.0000 | -0.334 | pequeno | ✅ Sim |
| degradacao | Mann-Whitney U | V2 vs V4 | 0.3056 | 0.015 | negligível | ❌ Não |
| degradacao | Mann-Whitney U | V3 vs V4 | 0.0000 | 0.347 | pequeno | ✅ Sim |
| indisponibilidade | Mann-Whitney U | V1 vs V2 | 0.0000 | 0.113 | negligível | ✅ Sim |
| indisponibilidade | Mann-Whitney U | V1 vs V3 | 0.0000 | -0.498 | pequeno | ✅ Sim |
| indisponibilidade | Mann-Whitney U | V1 vs V4 | 0.0000 | 0.115 | negligível | ✅ Sim |
| indisponibilidade | Mann-Whitney U | V2 vs V3 | 0.0000 | -0.586 | médio | ✅ Sim |
| indisponibilidade | Mann-Whitney U | V2 vs V4 | 0.0589 | 0.002 | negligível | ❌ Não |
| indisponibilidade | Mann-Whitney U | V3 vs V4 | 0.0000 | 0.588 | médio | ✅ Sim |
| rajadas | Mann-Whitney U | V1 vs V2 | 0.0000 | 0.010 | negligível | ✅ Sim |
| rajadas | Mann-Whitney U | V1 vs V3 | 0.0000 | -0.164 | negligível | ✅ Sim |
| rajadas | Mann-Whitney U | V1 vs V4 | 0.0000 | 0.012 | negligível | ✅ Sim |
| rajadas | Mann-Whitney U | V2 vs V3 | 0.0000 | -0.173 | negligível | ✅ Sim |
| rajadas | Mann-Whitney U | V2 vs V4 | 0.7759 | 0.002 | negligível | ❌ Não |
| rajadas | Mann-Whitney U | V3 vs V4 | 0.0000 | 0.175 | negligível | ✅ Sim |
| normal | Mann-Whitney U | V1 vs V2 | 0.7226 | 0.001 | negligível | ❌ Não |
| normal | Mann-Whitney U | V1 vs V3 | 0.4562 | -0.001 | negligível | ❌ Não |
| normal | Mann-Whitney U | V1 vs V4 | 0.6787 | 0.001 | negligível | ❌ Não |
| normal | Mann-Whitney U | V2 vs V3 | 0.2695 | -0.002 | negligível | ❌ Não |
| normal | Mann-Whitney U | V2 vs V4 | 0.9531 | 0.000 | negligível | ❌ Não |
| normal | Mann-Whitney U | V3 vs V4 | 0.2440 | 0.003 | negligível | ❌ Não |

### ANOVA (Múltiplos Grupos)

| Cenário | Grupos | F | p-value | η² | Significativo |
|---------|--------|---|---------|-----|---------------|
| catastrofe | V1, V2, V3, V4 | 17276.10 | 0.0000 | 0.025 | ✅ Sim |
| Completo | V1, V2, V3, V4 | 18797.35 | 0.0000 | 0.027 | ✅ Sim |
| degradacao | V1, V2, V3, V4 | 15258.49 | 0.0000 | 0.022 | ✅ Sim |
| indisponibilidade | V1, V2, V3, V4 | 62722.12 | 0.0000 | 0.086 | ✅ Sim |
| rajadas | V1, V2, V3, V4 | 4248.24 | 0.0000 | 0.006 | ✅ Sim |
| normal | V1, V2, V3, V4 | 0.52 | 0.6660 | 0.000 | ❌ Não |