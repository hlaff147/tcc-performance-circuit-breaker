#!/bin/bash

###############################################################################
# Script de Automação de Experimentos - TCC Circuit Breaker
#
# Este script automatiza a execução dos experimentos comparando V1 e V2
# do serviço de pagamento sob diferentes cenários de carga.
#
# Uso:
#   ./run-experiments.sh [cenario] [versao]
#   ./run-experiments.sh all          # Executa todos os cenários para V1 e V2
#   ./run-experiments.sh catastrofe v2  # Executa cenário específico
#
# Cenários disponíveis:
#   - completo
#   - catastrofe (falha-catastrofica)
#   - degradacao (degradacao-gradual)
#   - rajadas (rajadas-intermitentes)
#   - extrema (indisponibilidade-extrema)
#   - all (todos os cenários)
#
# Versões:
#   - v1 (Baseline sem Circuit Breaker)
#   - v2 (Com Circuit Breaker + Fallback)
#   - all (ambas as versões)
###############################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_SCRIPTS_DIR="${SCRIPT_DIR}/k6/scripts"
RESULTS_DIR="${SCRIPT_DIR}/k6/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Configurações
DOCKER_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
HEALTHCHECK_TIMEOUT=120  # segundos
COOLDOWN_BETWEEN_TESTS=30  # segundos

# Mapeamento de cenários para scripts
declare -A SCENARIO_SCRIPTS=(
    ["completo"]="cenario-completo.js"
    ["catastrofe"]="cenario-falha-catastrofica.js"
    ["degradacao"]="cenario-degradacao-gradual.js"
    ["rajadas"]="cenario-rajadas-intermitentes.js"
    ["extrema"]="cenario-indisponibilidade-extrema.js"
)

# Funções de utilidade
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC} $1"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Verifica pré-requisitos
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker não encontrado. Por favor, instale o Docker."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose não encontrado."
        exit 1
    fi
    
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Arquivo docker-compose.yml não encontrado em $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # Cria diretório de resultados se não existir
    mkdir -p "$RESULTS_DIR"
    mkdir -p "${RESULTS_DIR}/scenarios"
    
    log_success "Pré-requisitos verificados!"
}

# Inicia os serviços Docker para uma versão específica
start_services() {
    local version=$1
    
    log_info "Iniciando serviços para versão ${version}..."
    
    # Para qualquer container existente
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    # Exporta variável de versão e inicia
    export PAYMENT_SERVICE_VERSION="$version"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
    
    log_info "Aguardando healthcheck dos serviços..."
    wait_for_healthcheck
    
    log_success "Serviços iniciados e saudáveis!"
}

# Aguarda healthcheck dos serviços
wait_for_healthcheck() {
    local elapsed=0
    local interval=5
    
    while [ $elapsed -lt $HEALTHCHECK_TIMEOUT ]; do
        # Verifica se o serviço de pagamento está saudável
        if curl -sf http://localhost:8080/actuator/health > /dev/null 2>&1; then
            # Verifica se o serviço adquirente está saudável
            if curl -sf http://localhost:8081/actuator/health > /dev/null 2>&1; then
                return 0
            fi
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    
    echo ""
    log_error "Timeout aguardando serviços ficarem saudáveis"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
    exit 1
}

# Para os serviços Docker
stop_services() {
    log_info "Parando serviços..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
    log_success "Serviços parados!"
}

# Executa um cenário de teste
run_scenario() {
    local scenario=$1
    local version=$2
    local script_file="${SCENARIO_SCRIPTS[$scenario]}"
    
    if [ -z "$script_file" ]; then
        log_error "Cenário desconhecido: $scenario"
        log_info "Cenários disponíveis: ${!SCENARIO_SCRIPTS[*]}"
        exit 1
    fi
    
    local script_path="${K6_SCRIPTS_DIR}/${script_file}"
    
    if [ ! -f "$script_path" ]; then
        log_error "Script não encontrado: $script_path"
        exit 1
    fi
    
    local result_file="${RESULTS_DIR}/scenarios/${version}_${scenario}_${TIMESTAMP}"
    
    log_header "Executando: ${scenario} (${version})"
    log_info "Script: $script_file"
    log_info "Resultados: ${result_file}.json"
    
    # Executa k6 via Docker
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T k6-tester \
        k6 run \
        --out json=/scripts/results/scenarios/${version}_${scenario}_${TIMESTAMP}.json \
        --summary-export=/scripts/results/scenarios/${version}_${scenario}_${TIMESTAMP}_summary.json \
        -e VERSION="${version}" \
        -e PAYMENT_BASE_URL="http://servico-pagamento:8080" \
        "/scripts/${script_file}"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Cenário ${scenario} (${version}) concluído com sucesso!"
    else
        log_warn "Cenário ${scenario} (${version}) concluído com thresholds violados (exit code: $exit_code)"
    fi
    
    return $exit_code
}

# Executa todos os cenários para uma versão
run_all_scenarios() {
    local version=$1
    local failed=0
    
    log_header "Executando TODOS os cenários para ${version}"
    
    start_services "$version"
    
    for scenario in "${!SCENARIO_SCRIPTS[@]}"; do
        run_scenario "$scenario" "$version" || ((failed++))
        
        log_info "Cooldown de ${COOLDOWN_BETWEEN_TESTS}s entre cenários..."
        sleep $COOLDOWN_BETWEEN_TESTS
    done
    
    stop_services
    
    if [ $failed -gt 0 ]; then
        log_warn "Total de cenários com falhas: $failed"
    else
        log_success "Todos os cenários executados com sucesso!"
    fi
    
    return $failed
}

# Executa experimento completo (V1 + V2)
run_full_experiment() {
    log_header "EXPERIMENTO COMPLETO - V1 vs V2"
    log_info "Timestamp: $TIMESTAMP"
    log_info "Resultados serão salvos em: $RESULTS_DIR"
    
    local total_failed=0
    
    # Executa V1 (Baseline)
    run_all_scenarios "v1" || ((total_failed++))
    
    log_info "Pausa de 60s entre versões para garantir limpeza de estado..."
    sleep 60
    
    # Executa V2 (Circuit Breaker)
    run_all_scenarios "v2" || ((total_failed++))
    
    # Gera relatório
    generate_summary_report
    
    log_header "EXPERIMENTO CONCLUÍDO"
    log_info "Resultados em: $RESULTS_DIR"
    log_info "Para análise, execute: python analysis/scripts/analyzer.py"
    
    return $total_failed
}

# Gera relatório de resumo
generate_summary_report() {
    local report_file="${RESULTS_DIR}/experiment_${TIMESTAMP}.md"
    
    cat > "$report_file" << EOF
# Relatório de Experimento - Circuit Breaker TCC

**Data:** $(date '+%Y-%m-%d %H:%M:%S')
**Timestamp:** $TIMESTAMP

## Cenários Executados

| Cenário | V1 (Baseline) | V2 (Circuit Breaker) |
|---------|---------------|----------------------|
EOF

    for scenario in "${!SCENARIO_SCRIPTS[@]}"; do
        local v1_file="${RESULTS_DIR}/scenarios/v1_${scenario}_${TIMESTAMP}_summary.json"
        local v2_file="${RESULTS_DIR}/scenarios/v2_${scenario}_${TIMESTAMP}_summary.json"
        
        local v1_status="❌ Não executado"
        local v2_status="❌ Não executado"
        
        [ -f "$v1_file" ] && v1_status="✅ Concluído"
        [ -f "$v2_file" ] && v2_status="✅ Concluído"
        
        echo "| $scenario | $v1_status | $v2_status |" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

## Arquivos Gerados

\`\`\`
$(ls -la "${RESULTS_DIR}/scenarios/"*"${TIMESTAMP}"* 2>/dev/null || echo "Nenhum arquivo encontrado")
\`\`\`

## Próximos Passos

1. Executar análise estatística: \`python analysis/scripts/analyzer.py\`
2. Gerar gráficos: \`python analysis/scripts/generate_final_charts.py\`
3. Revisar resultados em \`analysis_results/\`
EOF

    log_success "Relatório gerado: $report_file"
}

# Exibe ajuda
show_help() {
    cat << EOF
Uso: $0 [cenario] [versao]

Cenários disponíveis:
  completo    - Teste de estresse progressivo
  catastrofe  - Falha catastrófica (100% indisponibilidade)
  degradacao  - Degradação gradual
  rajadas     - Rajadas intermitentes
  extrema     - Indisponibilidade extrema (75% off)
  all         - Todos os cenários

Versões:
  v1   - Baseline (sem Circuit Breaker)
  v2   - Com Circuit Breaker + Fallback
  all  - Ambas as versões

Exemplos:
  $0 all               # Executa TODOS os cenários para V1 e V2
  $0 catastrofe v2     # Executa apenas cenário catástrofe para V2
  $0 completo all      # Executa cenário completo para V1 e V2
EOF
}

# Main
main() {
    local scenario="${1:-all}"
    local version="${2:-all}"
    
    if [ "$scenario" == "help" ] || [ "$scenario" == "--help" ] || [ "$scenario" == "-h" ]; then
        show_help
        exit 0
    fi
    
    check_prerequisites
    
    if [ "$scenario" == "all" ] && [ "$version" == "all" ]; then
        run_full_experiment
    elif [ "$scenario" == "all" ]; then
        run_all_scenarios "$version"
    elif [ "$version" == "all" ]; then
        start_services "v1"
        run_scenario "$scenario" "v1"
        stop_services
        
        sleep 30
        
        start_services "v2"
        run_scenario "$scenario" "v2"
        stop_services
    else
        start_services "$version"
        run_scenario "$scenario" "$version"
        stop_services
    fi
}

main "$@"
