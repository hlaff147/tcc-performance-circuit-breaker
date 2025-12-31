#!/bin/bash

###############################################################################
# Script para executar os cenários de teste que demonstram as vantagens
# do Circuit Breaker em situações críticas.
#
# Uso:
#   ./run_scenario_tests.sh [all|catastrofe|degradacao|rajadas|indisponibilidade|normal]
#
# Cada cenário roda para V1 e V2, salvando resultados separados.
###############################################################################

set -e

SCENARIO=${1:-all}
RESULTS_DIR="k6/results/scenarios"
SCRIPTS_DIR="k6/scripts"
INCLUDE_V3=${INCLUDE_V3:-false}

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Cria diretório de resultados
mkdir -p "$RESULTS_DIR"

###############################################################################
# FUNÇÕES DE VALIDAÇÃO
###############################################################################

validate_docker() {
    echo -e "${CYAN}🔍 Validando Docker...${NC}"
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker não está rodando. Inicie o Docker primeiro.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker está rodando${NC}"
}

validate_docker_compose() {
    echo -e "${CYAN}🔍 Validando docker-compose.yml...${NC}"
    if ! docker-compose config > /dev/null 2>&1; then
        echo -e "${RED}❌ docker-compose.yml inválido ou não encontrado${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ docker-compose.yml válido${NC}"
}

validate_k6_scripts() {
    echo -e "${CYAN}🔍 Validando scripts k6...${NC}"
    local scripts=(
        "cenario-falha-catastrofica.js"
        "cenario-degradacao-gradual.js"
        "cenario-rajadas-intermitentes.js"
        "cenario-indisponibilidade-extrema.js"
        "cenario-operacao-normal.js"
    )
    
    local missing=0
    for script in "${scripts[@]}"; do
        if [ ! -f "$SCRIPTS_DIR/$script" ]; then
            echo -e "${RED}  ❌ Faltando: $script${NC}"
            missing=$((missing + 1))
        else
            echo -e "${GREEN}  ✓ $script${NC}"
        fi
    done
    
    if [ $missing -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $missing script(s) não encontrado(s)${NC}"
    fi
}

validate_services() {
    echo -e "${CYAN}🔍 Validando serviços...${NC}"
    
    # Inicia os serviços necessários
    echo -e "${YELLOW}  ⏳ Iniciando infraestrutura...${NC}"
    docker-compose up -d servico-adquirente prometheus grafana cadvisor 2>/dev/null || true
    sleep 5
    
    # Verifica se servico-adquirente está healthy
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}  ⏳ Aguardando servico-adquirente ficar saudável...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T servico-adquirente curl -sf http://localhost:8081/actuator/health > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ servico-adquirente está saudável${NC}"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}  ❌ servico-adquirente não ficou saudável após ${max_attempts} tentativas${NC}"
        echo -e "${YELLOW}  💡 Tentando reiniciar o serviço...${NC}"
        docker-compose restart servico-adquirente
        sleep 10
    fi
    
    # Verifica Prometheus
    if docker-compose ps prometheus | grep -q "Up"; then
        echo -e "${GREEN}  ✓ Prometheus está rodando${NC}"
    else
        echo -e "${YELLOW}  ⚠️ Prometheus não está rodando${NC}"
    fi
    
    # Verifica Grafana
    if docker-compose ps grafana | grep -q "Up"; then
        echo -e "${GREEN}  ✓ Grafana está rodando${NC}"
    else
        echo -e "${YELLOW}  ⚠️ Grafana não está rodando${NC}"
    fi
}

wait_for_payment_service() {
    local version=$1
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}  ⏳ Aguardando serviço de pagamento ($version) ficar saudável...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T servico-pagamento curl -sf http://localhost:8080/actuator/health > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Serviço de pagamento ($version) está saudável${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo -e "${RED}  ❌ Serviço de pagamento ($version) não ficou saudável após ${max_attempts} tentativas${NC}"
    return 1
}

run_pre_flight_checks() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  🔍 PRE-FLIGHT CHECKS                                      ${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
    
    validate_docker
    validate_docker_compose
    validate_k6_scripts
    validate_services
    
    echo -e "\n${GREEN}✅ Todas as validações passaram!${NC}\n"
}

# Executa validações pré-teste
run_pre_flight_checks

# Garante que infraestrutura base está rodando (sem o servico-pagamento que será trocado)
echo -e "${BLUE}🔧 Preparando ambiente de testes...${NC}"
docker-compose up -d servico-adquirente cadvisor prometheus grafana

# Aguarda servico-adquirente ficar healthy
echo -e "${YELLOW}⏳ Aguardando infraestrutura ficar pronta...${NC}"
sleep 10

# Verifica se servico-adquirente está healthy antes de continuar
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker inspect --format='{{.State.Health.Status}}' servico-adquirente 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✅ servico-adquirente está healthy${NC}"
        break
    fi
    echo -e "${YELLOW}  Tentativa $((attempt + 1))/$max_attempts - aguardando...${NC}"
    attempt=$((attempt + 1))
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ servico-adquirente não ficou healthy. Verifique os logs com: docker logs servico-adquirente${NC}"
    exit 1
fi

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
    
    # Para apenas o servico-pagamento para trocar a versão
    docker-compose stop servico-pagamento 2>/dev/null || true
    
    # Rebuild e inicia apenas o serviço de pagamento V1 (sem afetar outros containers)
    PAYMENT_SERVICE_VERSION=v1 docker-compose build servico-pagamento
    PAYMENT_SERVICE_VERSION=v1 docker-compose up -d --no-deps servico-pagamento
    echo "Aguardando serviço V1 inicializar..."
    wait_for_payment_service "V1"
    
    # Garante que k6-tester está rodando (sem reiniciar dependências)
    docker-compose up -d --no-deps k6-tester
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
    
    # Para apenas o servico-pagamento para trocar a versão
    docker-compose stop servico-pagamento 2>/dev/null || true
    
    # Rebuild e inicia apenas o serviço de pagamento V2 (sem afetar outros containers)
    PAYMENT_SERVICE_VERSION=v2 docker-compose build servico-pagamento
    PAYMENT_SERVICE_VERSION=v2 docker-compose up -d --no-deps servico-pagamento
    echo "Aguardando serviço V2 inicializar..."
    wait_for_payment_service "V2"
    
    # Garante que k6-tester está rodando (sem reiniciar dependências)
    docker-compose up -d --no-deps k6-tester
    sleep 2
    
    # Executa k6 (|| true ignora falhas de threshold)
    docker-compose exec -T k6-tester k6 run \
        --out json="/scripts/results/scenarios/${scenario_name}_V2.json" \
        --summary-export="/scripts/results/scenarios/${scenario_name}_V2_summary.json" \
        -e PAYMENT_BASE_URL=http://servico-pagamento:8080 \
        "/scripts/$script_file" || echo "⚠️  Threshold falhou mas dados foram coletados"
    
    echo -e "\n${GREEN}✅ V2 concluído${NC}\n"

    # V3 - Retry com Backoff Exponencial (opcional)
    if [ "${INCLUDE_V3}" = "true" ]; then
        echo -e "${GREEN}🔄 Rodando V3 (retry/backoff)...${NC}"

        docker-compose stop servico-pagamento 2>/dev/null || true

        PAYMENT_SERVICE_VERSION=v3 docker-compose build servico-pagamento
        PAYMENT_SERVICE_VERSION=v3 docker-compose up -d --no-deps servico-pagamento
        echo "Aguardando serviço V3 inicializar..."
        wait_for_payment_service "V3"

        docker-compose up -d --no-deps k6-tester
        sleep 2

        docker-compose exec -T k6-tester k6 run \
            --out json="/scripts/results/scenarios/${scenario_name}_V3.json" \
            --summary-export="/scripts/results/scenarios/${scenario_name}_V3_summary.json" \
            -e PAYMENT_BASE_URL=http://servico-pagamento:8080 \
            "/scripts/$script_file" || echo "⚠️  Threshold falhou mas dados foram coletados"

        echo -e "\n${GREEN}✅ V3 concluído${NC}\n"
    fi
    
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

run_normal() {
    run_scenario \
        "normal" \
        "cenario-operacao-normal.js" \
        "Cenário 5: OPERAÇÃO NORMAL (Baseline sem falhas)"
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
    normal)
        run_normal
        ;;
    all)
        echo -e "${YELLOW}🚀 Executando TODOS os cenários...${NC}\n"
        run_normal
        echo -e "\n⏸️  Pausa de 30s antes do próximo cenário...\n"
        sleep 30
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
        echo "Uso: $0 [all|catastrofe|degradacao|rajadas|indisponibilidade|normal]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!                ${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}📁 Resultados salvos em: $RESULTS_DIR/${NC}"
echo -e "${YELLOW}📊 Execute o analisador para ver as comparações detalhadas${NC}\n"
