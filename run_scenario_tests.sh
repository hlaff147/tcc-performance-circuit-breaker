#!/bin/bash

###############################################################################
# Script para executar os cenários de teste que demonstram as vantagens
# do Circuit Breaker em situações críticas.
#
# Uso:
#   ./run_scenario_tests.sh [all|catastrofe|degradacao|rajadas|indisponibilidade]
#
# Cada cenário roda para V1 e V2, salvando resultados separados.
###############################################################################

set -e

SCENARIO=${1:-all}
RESULTS_DIR="k6/results/scenarios"
SCRIPTS_DIR="k6/scripts"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cria diretório de resultados
mkdir -p "$RESULTS_DIR"

# Verifica se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker não está rodando. Inicie o Docker primeiro.${NC}"
    exit 1
fi

# Garante que k6-tester está rodando
echo -e "${BLUE}🔧 Preparando ambiente...${NC}"
docker-compose up -d k6-tester servico-adquirente
sleep 5

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

run_scenario() {
    local scenario_name=$1
    local script_file=$2
    local description=$3
    
    print_header "$description"
    
    echo -e "${YELLOW}📊 Executando cenário: $scenario_name${NC}\n"
    
    # V1 - Sem Circuit Breaker
    echo -e "${GREEN}🔄 Rodando V1 (baseline - sem CB)...${NC}"
    
    # Rebuild do serviço de pagamento V1
    PAYMENT_SERVICE_VERSION=v1 docker-compose up -d --build servico-pagamento
    echo "Aguardando serviço V1 inicializar..."
    sleep 15
    
    # Garante que k6-tester está rodando
    docker-compose up -d k6-tester
    sleep 2
    
    # Executa k6 (|| true ignora falhas de threshold)
    docker-compose exec -T k6-tester k6 run \
        --out json="/scripts/results/scenarios/${scenario_name}_V1.json" \
        --summary-export="/scripts/results/scenarios/${scenario_name}_V1_summary.json" \
        -e PAYMENT_BASE_URL=http://servico-pagamento:8080 \
        "/scripts/$script_file" || echo "⚠️  Threshold falhou mas dados foram coletados"
    
    echo -e "\n${GREEN}✅ V1 concluído${NC}\n"
    sleep 10  # Pausa entre testes
    
    # V2 - Com Circuit Breaker
    echo -e "${GREEN}🔄 Rodando V2 (com Circuit Breaker)...${NC}"
    
    # Rebuild do serviço de pagamento V2
    PAYMENT_SERVICE_VERSION=v2 docker-compose up -d --build servico-pagamento
    echo "Aguardando serviço V2 inicializar..."
    sleep 15
    
    # Garante que k6-tester está rodando
    docker-compose up -d k6-tester
    sleep 2
    
    # Executa k6 (|| true ignora falhas de threshold)
    docker-compose exec -T k6-tester k6 run \
        --out json="/scripts/results/scenarios/${scenario_name}_V2.json" \
        --summary-export="/scripts/results/scenarios/${scenario_name}_V2_summary.json" \
        -e PAYMENT_BASE_URL=http://servico-pagamento:8080 \
        "/scripts/$script_file" || echo "⚠️  Threshold falhou mas dados foram coletados"
    
    echo -e "\n${GREEN}✅ V2 concluído${NC}\n"
    
    echo -e "${GREEN}✨ Cenário $scenario_name finalizado!${NC}\n"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

run_catastrofe() {
    run_scenario \
        "catastrofe" \
        "cenario-falha-catastrofica.js" \
        "Cenário 1: FALHA CATASTRÓFICA (API completamente fora)"
}

run_degradacao() {
    run_scenario \
        "degradacao" \
        "cenario-degradacao-gradual.js" \
        "Cenário 2: DEGRADAÇÃO GRADUAL (Lentidão progressiva)"
}

run_rajadas() {
    run_scenario \
        "rajadas" \
        "cenario-rajadas-intermitentes.js" \
        "Cenário 3: RAJADAS INTERMITENTES (Falhas em ondas)"
}

run_indisponibilidade() {
    run_scenario \
        "indisponibilidade" \
        "cenario-indisponibilidade-extrema.js" \
        "Cenário 4: INDISPONIBILIDADE EXTREMA (75% OFF)"
}

# Main
echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   TESTES DE CENÁRIOS CRÍTICOS - CIRCUIT BREAKER                ║
║                                                                ║
║   Demonstra as vantagens do CB em situações onde ele          ║
║   realmente faz diferença significativa.                       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

case $SCENARIO in
    catastrofe)
        run_catastrofe
        ;;
    degradacao)
        run_degradacao
        ;;
    rajadas)
        run_rajadas
        ;;
    indisponibilidade)
        run_indisponibilidade
        ;;
    all)
        echo -e "${YELLOW}🚀 Executando TODOS os cenários...${NC}\n"
        run_catastrofe
        echo -e "\n⏸️  Pausa de 30s antes do próximo cenário...\n"
        sleep 30
        run_degradacao
        echo -e "\n⏸️  Pausa de 30s antes do próximo cenário...\n"
        sleep 30
        run_rajadas
        echo -e "\n⏸️  Pausa de 30s antes do próximo cenário...\n"
        sleep 30
        run_indisponibilidade
        ;;
    *)
        echo -e "${RED}❌ Cenário inválido: $SCENARIO${NC}"
        echo "Uso: $0 [all|catastrofe|degradacao|rajadas]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!                ${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}📁 Resultados salvos em: $RESULTS_DIR/${NC}"
echo -e "${YELLOW}📊 Execute o analisador para ver as comparações detalhadas${NC}\n"
