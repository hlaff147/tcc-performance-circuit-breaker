# ⚡ Solução Rápida - Exit Code 99

## 🎯 O Que Aconteceu

Exit code 99 = **Threshold falhou** mas **dados foram coletados com sucesso!**

Você viu:
```
✗ 'p(95)<1000' p(95)=3s
level=error msg="thresholds on metrics have been crossed"
```

**Isto é ESPERADO e NORMAL** no cenário catastrófico! P95 de 3 segundos é exatamente o que queremos medir.

## ✅ Correção Aplicada

Scripts agora **ignoram falhas de threshold** e continuam:
- ✅ `run_scenario_tests.sh` atualizado
- ✅ `run_and_analyze.sh` vai funcionar completo

## 🚀 Execute Agora

**Opção A: Continuar de onde parou (mais rápido)**
```bash
# Você já tem V1, só falta V2
PAYMENT_SERVICE_VERSION=v2 docker-compose up -d --build servico-pagamento && sleep 15
docker-compose up -d k6-tester && sleep 2
docker-compose exec -T k6-tester k6 run \
  --out json="/scripts/results/scenarios/catastrofe_V2.json" \
  --summary-export="/scripts/results/scenarios/catastrofe_V2_summary.json" \
  -e PAYMENT_BASE_URL=http://servico-pagamento:8080 \
  /scripts/cenario-falha-catastrofica.js || true

python3 analysis/scripts/scenario_analyzer.py catastrofe
open analysis_results/scenarios/catastrofe_report.html
```

**Opção B: Rodar tudo com script corrigido**
```bash
docker-compose down
./run_and_analyze.sh catastrofe
```

**Opção C: Rodar todos os cenários**
```bash
docker-compose down
./run_and_analyze.sh all
```

## 📊 Resultados Ficam Em

```
analysis_results/scenarios/
├── catastrofe_report.html              ← ABRA ESTE
├── csv/consolidated_benefits.csv       ← USE NO TCC
└── plots/catastrofe/*.png              ← GRÁFICOS
```

---

**TL;DR:** Exit 99 é OK! Script corrigido. Execute `./run_and_analyze.sh catastrofe` novamente.
