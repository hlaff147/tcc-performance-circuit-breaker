#!/bin/bash

# Script para reexecutar o cenário completo com métricas corretas
# Autor: TCC Performance Circuit Breaker
# Data: 2025-11-07

set -e  # Exit on error

echo "=========================================="
echo "REEXECUTANDO CENÁRIO COMPLETO"
echo "com métricas CORRETAS do Circuit Breaker"
echo "=========================================="
echo ""

# Diretório base
BASE_DIR="/Users/hlaff/tcc-performance-circuit-breaker"
cd "$BASE_DIR"

# Verificar se docker-compose está rodando
echo "📋 Verificando se os serviços estão rodando..."
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Serviços não estão rodando. Iniciando..."
    docker-compose up -d
    echo "⏳ Aguardando serviços iniciarem (30 segundos)..."
    sleep 30
fi

echo "✅ Serviços estão rodando"
echo ""

# Fazer backup dos resultados antigos
echo "📦 Fazendo backup dos resultados antigos..."
BACKUP_DIR="k6/results/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f "k6/results/V1_Completo.json" ]; then
    mv k6/results/V1_Completo.json "$BACKUP_DIR/"
fi
if [ -f "k6/results/V2_Completo.json" ]; then
    mv k6/results/V2_Completo.json "$BACKUP_DIR/"
fi
echo "✅ Backup criado em $BACKUP_DIR"
echo ""

# Executar V1 (Baseline - Sem Circuit Breaker)
echo "=========================================="
echo "🔴 EXECUTANDO V1 (Baseline - Sem CB)"
echo "=========================================="
echo "Duração: ~12 minutos"
echo ""

docker exec k6 run /scripts/cenario-completo.js \
  --out json=/results/V1_Completo.json

echo ""
echo "✅ V1 executado com sucesso!"
echo ""

# Aguardar um pouco entre os testes
echo "⏳ Aguardando 10 segundos antes de executar V2..."
sleep 10
echo ""

# Executar V2 (Com Circuit Breaker)
echo "=========================================="
echo "🟢 EXECUTANDO V2 (Com Circuit Breaker)"
echo "=========================================="
echo "Duração: ~12 minutos"
echo ""

# Modificar a URL base para V2
sed 's|servico-pagamento:8080|servico-pagamento-v2:8080|g' \
  k6/scripts/cenario-completo.js > /tmp/cenario-completo-v2.js

docker exec -i k6 run - < /tmp/cenario-completo-v2.js \
  --out json=/results/V2_Completo.json

echo ""
echo "✅ V2 executado com sucesso!"
echo ""

# Restaurar arquivo original
git checkout k6/scripts/cenario-completo.js 2>/dev/null || true

# Executar análise
echo "=========================================="
echo "📊 EXECUTANDO ANÁLISE"
echo "=========================================="
echo ""

python3 analysis/scripts/extract_cb_metrics.py \
  k6/results/V1_Completo.json \
  k6/results/V2_Completo.json

echo ""
echo "=========================================="
echo "✅ EXECUÇÃO COMPLETA!"
echo "=========================================="
echo ""
echo "Arquivos gerados:"
echo "  • k6/results/V1_Completo.json"
echo "  • k6/results/V2_Completo.json"
echo ""
echo "Backup anterior em:"
echo "  • $BACKUP_DIR"
echo ""
echo "Próximos passos:"
echo "  1. Executar análise completa: python3 analysis/scripts/analyze_high_concurrency.py"
echo "  2. Gerar relatórios: python3 analysis/analyze_and_report.py"
echo ""
