#!/bin/bash
# ==============================================================================
# run_comparative_experiment.sh - Versão WSL/Local
# ==============================================================================
# Script para executar experimento comparativo completo:
# - 4 tratamentos: V1 (BASE), V2 (CB), V3 (RETRY), V4 (CB+RETRY)
# - N repetições por tratamento × cenário
# - Compatível com WSL usando k6 local (não Docker)
#
# Uso:
#   ./run_comparative_experiment.sh [--pilot] [--wsl] [--scenarios "cenario1 cenario2"]
#
# Exemplos:
#   ./run_comparative_experiment.sh                    # Auto-detecta plataforma
#   ./run_comparative_experiment.sh --pilot            # Teste rápido (1 run cada)
#   ./run_comparative_experiment.sh --wsl              # Força modo WSL (k6 local)
#   ./run_comparative_experiment.sh --docker           # Força modo Docker (k6 container)
# ==============================================================================

set -e

# Configuração padrão
TREATMENTS=("v1" "v2" "v3" "v4")
TREATMENT_NAMES=("BASE" "CB" "RETRY" "CB_RETRY")
SCENARIOS=("indisponibilidade-extrema" "falha-catastrofica")
REPLICATIONS=5
SEED_BASE=42
RESULTS_DIR="k6/results/comparative"
WARMUP_TIME=15  # segundos para warmup do serviço
COOLDOWN_TIME=5 # segundos entre runs

# Auto-detectar WSL
USE_LOCAL_K6=false
if grep -qi microsoft /proc/version 2>/dev/null || grep -qi wsl /proc/version 2>/dev/null; then
    USE_LOCAL_K6=true
    echo "🐧 WSL detectado - usando k6 local"
fi

# Parse argumentos
PILOT_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --pilot)
            PILOT_MODE=true
            REPLICATIONS=1
            shift
            ;;
        --wsl|--local)
            USE_LOCAL_K6=true
            shift
            ;;
        --docker)
            USE_LOCAL_K6=false
            shift
            ;;
        --scenarios)
            IFS=' ' read -r -a SCENARIOS <<< "$2"
            shift 2
            ;;
        --replications)
            REPLICATIONS=$2
            shift 2
            ;;
        *)
            echo "Argumento desconhecido: $1"
            echo "Uso: $0 [--pilot] [--wsl|--docker] [--scenarios \"s1 s2\"] [--replications N]"
            exit 1
            ;;
    esac
done

# Verificar k6 local se necessário
if [ "$USE_LOCAL_K6" = true ]; then
    if ! command -v k6 &> /dev/null; then
        echo "❌ k6 não encontrado. Instale com:"
        echo "   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69"
        echo "   echo 'deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main' | sudo tee /etc/apt/sources.list.d/k6.list"
        echo "   sudo apt-get update && sudo apt-get install k6"
        exit 1
    fi
    echo "✅ k6 local: $(k6 version | head -1)"
fi

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   EXPERIMENTO COMPARATIVO CB vs RETRY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Tratamentos: ${GREEN}${TREATMENTS[*]}${NC}"
echo -e "Cenários: ${GREEN}${SCENARIOS[*]}${NC}"
echo -e "Repetições por tratamento×cenário: ${GREEN}${REPLICATIONS}${NC}"
echo -e "Modo piloto: ${YELLOW}${PILOT_MODE}${NC}"
echo -e "Usar k6 local: ${YELLOW}${USE_LOCAL_K6}${NC}"
echo ""

# Criar diretório de resultados
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPERIMENT_DIR="$RESULTS_DIR/experiment_$TIMESTAMP"
mkdir -p "$EXPERIMENT_DIR"

# Caminho absoluto para o diretório de scripts k6
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
K6_SCRIPTS_DIR="$SCRIPT_DIR/k6/scripts"

# Log do experimento
LOG_FILE="$EXPERIMENT_DIR/experiment.log"
echo "Experimento iniciado em $(date)" > "$LOG_FILE"
echo "Configuração:" >> "$LOG_FILE"
echo "  Tratamentos: ${TREATMENTS[*]}" >> "$LOG_FILE"
echo "  Cenários: ${SCENARIOS[*]}" >> "$LOG_FILE"
echo "  Repetições: $REPLICATIONS" >> "$LOG_FILE"
echo "  Modo k6: $(if [ "$USE_LOCAL_K6" = true ]; then echo 'local'; else echo 'docker'; fi)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Função para verificar se serviço está saudável
wait_for_healthy() {
    local max_attempts=30
    local attempt=1
    
    echo -n "  Aguardando serviço ficar saudável"
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:8080/actuator/health > /dev/null 2>&1; then
            echo -e " ${GREEN}OK${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e " ${RED}FALHOU${NC}"
    return 1
}

# Função para executar um teste com k6 LOCAL
run_test_local() {
    local treatment=$1
    local treatment_name=$2
    local scenario=$3
    local run=$4
    local seed=$5
    
    local output_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}.json"
    local summary_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}_summary.json"
    local script_path="$K6_SCRIPTS_DIR/cenario-${scenario}.js"
    
    echo -e "  ${YELLOW}Executando k6 (local)...${NC}"
    
    # Rodar k6 local - redirecionar logs em vez de usar tee (evita travamento WSL)
    k6 run \
        --out json="$output_file" \
        --summary-export="$summary_file" \
        --env TREATMENT="$treatment_name" \
        --env RUN="$run" \
        --env SEED="$seed" \
        --env BASE_URL="http://localhost:8080" \
        "$script_path" >> "$LOG_FILE" 2>&1
    
    local exit_code=$?
    
    # Mostrar resumo
    if [ -f "$summary_file" ]; then
        echo -e "  ${GREEN}Resumo salvo em: $summary_file${NC}"
    fi
    
    return $exit_code
}

# Função para executar um teste com k6 DOCKER
run_test_docker() {
    local treatment=$1
    local treatment_name=$2
    local scenario=$3
    local run=$4
    local seed=$5
    
    echo -e "  ${YELLOW}Executando k6 (docker)...${NC}"
    
    docker exec k6-tester k6 run \
        --out json=/scripts/results/comparative/experiment_$TIMESTAMP/${scenario}_${treatment}_run${run}.json \
        --summary-export=/scripts/results/comparative/experiment_$TIMESTAMP/${scenario}_${treatment}_run${run}_summary.json \
        --env TREATMENT=$treatment_name \
        --env RUN=$run \
        --env SEED=$seed \
        /scripts/cenario-${scenario}.js >> "$LOG_FILE" 2>&1
    
    return $?
}

# Função wrapper para rodar teste
run_test() {
    if [ "$USE_LOCAL_K6" = true ]; then
        run_test_local "$@"
    else
        run_test_docker "$@"
    fi
}

# Serviços a subir (sem k6 se usando local)
get_services() {
    if [ "$USE_LOCAL_K6" = true ]; then
        echo "servico-adquirente servico-pagamento"
    else
        echo ""  # docker-compose up -d sobe todos
    fi
}

# Contador de progresso
total_runs=$((${#SCENARIOS[@]} * ${#TREATMENTS[@]} * REPLICATIONS))
current_run=0

echo -e "${BLUE}Total de runs: $total_runs${NC}"
echo ""

# Loop principal do experimento
for scenario in "${SCENARIOS[@]}"; do
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}CENÁRIO: $scenario${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    for i in "${!TREATMENTS[@]}"; do
        treatment="${TREATMENTS[$i]}"
        treatment_name="${TREATMENT_NAMES[$i]}"
        
        echo ""
        echo -e "${GREEN}▶ Tratamento: $treatment ($treatment_name)${NC}"
        echo "  Iniciando ambiente..."
        
        # Parar containers anteriores
        docker-compose down --remove-orphans > /dev/null 2>&1 || true
        
        # Iniciar com o tratamento correto
        echo "  Construindo e iniciando serviços (version=$treatment)..."
        services=$(get_services)
        if [ -n "$services" ]; then
            PAYMENT_SERVICE_VERSION=$treatment docker-compose up -d --build $services >> "$LOG_FILE" 2>&1
        else
            PAYMENT_SERVICE_VERSION=$treatment docker-compose up -d --build >> "$LOG_FILE" 2>&1
        fi
        
        # Aguardar serviço ficar saudável
        if ! wait_for_healthy; then
            echo -e "${RED}ERRO: Serviço não iniciou corretamente${NC}"
            echo "  Ver logs: docker-compose logs servico-pagamento"
            docker-compose logs servico-pagamento >> "$LOG_FILE" 2>&1
            continue
        fi
        
        # Warmup
        echo "  Aguardando warmup (${WARMUP_TIME}s)..."
        sleep $WARMUP_TIME
        
        # Executar N repetições
        for run in $(seq 1 $REPLICATIONS); do
            ((current_run++)) || true
            seed=$((SEED_BASE + run))
            
            echo ""
            echo -e "  ${YELLOW}Run $run/$REPLICATIONS (seed=$seed) [$current_run/$total_runs]${NC}"
            
            if run_test "$treatment" "$treatment_name" "$scenario" "$run" "$seed"; then
                echo -e "  ${GREEN}✓ Concluído${NC}"
            else
                echo -e "  ${RED}✗ Falhou${NC}"
            fi
            
            # Cooldown entre runs
            if [ $run -lt $REPLICATIONS ]; then
                echo "  Cooldown (${COOLDOWN_TIME}s)..."
                sleep $COOLDOWN_TIME
            fi
        done
        
        echo "  Parando containers..."
        docker-compose down > /dev/null 2>&1
    done
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}EXPERIMENTO CONCLUÍDO${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Resultados salvos em: ${GREEN}$EXPERIMENT_DIR${NC}"
echo ""
echo "Próximos passos:"
echo "  1. Analisar resultados: python3 analysis/scripts/comparative_analyzer.py $EXPERIMENT_DIR"
echo "  2. Gerar relatório: python3 analysis/scripts/generate_comparative_report.py $EXPERIMENT_DIR"
echo ""

echo "Experimento finalizado em $(date)" >> "$LOG_FILE"
