#!/bin/bash
# =============================================================================
# Script: run_cb_profile_comparison.sh
# Descrição: Executa cenário de teste para cada perfil de Circuit Breaker
# Uso: ./run_cb_profile_comparison.sh [cenario] [--quick]
# =============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
PROFILES=("equilibrado" "conservador" "agressivo")
SCENARIO="${1:-catastrofe}"
QUICK_MODE="${2:-}"
RESULTS_DIR="analysis_results/profile_comparison"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Validar cenário
VALID_SCENARIOS=("catastrofe" "degradacao" "rajadas" "indisponibilidade" "normal")
if [[ ! " ${VALID_SCENARIOS[@]} " =~ " ${SCENARIO} " ]]; then
    echo -e "${RED}❌ Cenário inválido: $SCENARIO${NC}"
    echo "Cenários válidos: ${VALID_SCENARIOS[*]}"
    exit 1
fi

# Mapear cenário para script k6
declare -A SCENARIO_SCRIPTS
SCENARIO_SCRIPTS["catastrofe"]="cenario-falha-catastrofica.js"
SCENARIO_SCRIPTS["degradacao"]="cenario-degradacao-gradual.js"
SCENARIO_SCRIPTS["rajadas"]="cenario-rajadas-intermitentes.js"
SCENARIO_SCRIPTS["indisponibilidade"]="cenario-indisponibilidade-extrema.js"
SCENARIO_SCRIPTS["normal"]="cenario-operacao-normal.js"

K6_SCRIPT="${SCENARIO_SCRIPTS[$SCENARIO]}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       COMPARAÇÃO DE PERFIS DO CIRCUIT BREAKER                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📊 Cenário: ${SCENARIO}${NC}"
echo -e "${YELLOW}📁 Resultados: ${RESULTS_DIR}/${NC}"
echo -e "${YELLOW}⏰ Timestamp: ${TIMESTAMP}${NC}"
echo ""

# Criar diretório de resultados
mkdir -p "$RESULTS_DIR/csv"
mkdir -p "$RESULTS_DIR/json"
mkdir -p "$RESULTS_DIR/plots"

# Função para executar teste com perfil específico
run_profile_test() {
    local profile=$1
    local result_prefix="${RESULTS_DIR}/json/${SCENARIO}_${profile}_${TIMESTAMP}"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}▶ Executando teste com perfil: ${profile}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Parar serviços existentes
    echo -e "${YELLOW}⏹️  Parando serviços...${NC}"
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Rebuild com perfil específico
    echo -e "${YELLOW}🔨 Construindo serviço com perfil ${profile}...${NC}"
    export CB_PROFILE="$profile"
    docker-compose build --no-cache servico-pagamento-v2 2>&1 | tail -5
    
    # Iniciar serviços
    echo -e "${YELLOW}🚀 Iniciando serviços...${NC}"
    docker-compose up -d
    
    # Aguardar serviços ficarem saudáveis
    echo -e "${YELLOW}⏳ Aguardando serviços...${NC}"
    sleep 15
    
    # Verificar health
    for i in {1..10}; do
        if curl -s http://localhost:8082/actuator/health | grep -q "UP"; then
            echo -e "${GREEN}✅ Serviço V2 saudável${NC}"
            break
        fi
        echo "   Tentativa $i/10..."
        sleep 3
    done
    
    # Definir duração do teste
    local duration="13m"
    local vus="100"
    if [[ "$QUICK_MODE" == "--quick" ]]; then
        duration="2m"
        vus="30"
        echo -e "${YELLOW}⚡ Modo rápido ativado: ${duration}, ${vus} VUs${NC}"
    fi
    
    # Executar teste k6
    echo -e "${YELLOW}🧪 Executando teste k6...${NC}"
    docker run --rm -i \
        --network=tcc-performance-circuit-breaker_tcc-network \
        -v "$PWD/k6:/k6" \
        -e "PAYMENT_BASE_URL=http://servico-pagamento-v2:8080" \
        -e "VERSION=V2_${profile}" \
        grafana/k6:latest run \
        --duration="$duration" \
        --vus="$vus" \
        --out json="${result_prefix}.json" \
        --summary-export="${result_prefix}_summary.json" \
        "/k6/scripts/${K6_SCRIPT}" 2>&1 | tail -20
    
    echo -e "${GREEN}✅ Teste com perfil ${profile} concluído${NC}"
    echo ""
}

# Executar teste para cada perfil
for profile in "${PROFILES[@]}"; do
    run_profile_test "$profile"
done

# Parar serviços
echo -e "${YELLOW}⏹️  Parando serviços...${NC}"
docker-compose down

# Gerar análise comparativa
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 Gerando análise comparativa...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Chamar script Python de análise
if [ -f "analysis/scripts/profile_comparison_analyzer.py" ]; then
    python3 analysis/scripts/profile_comparison_analyzer.py \
        --scenario "$SCENARIO" \
        --timestamp "$TIMESTAMP" \
        --output-dir "$RESULTS_DIR"
else
    echo -e "${YELLOW}⚠️  Script de análise não encontrado. Execute manualmente.${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    COMPARAÇÃO CONCLUÍDA!                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📁 Resultados salvos em: ${RESULTS_DIR}/"
echo -e "📊 JSONs: ${RESULTS_DIR}/json/"
echo -e "📈 Plots: ${RESULTS_DIR}/plots/"
echo ""
