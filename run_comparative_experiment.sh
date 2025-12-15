#!/bin/bash
# ==============================================================================
# run_comparative_experiment.sh
# ==============================================================================
# Script para executar experimento comparativo completo:
# - 4 tratamentos: V1 (BASE), V2 (CB), V3 (RETRY), V4 (CB+RETRY)
# - N repetições por tratamento × cenário
# - Coleta de métricas com identificação por tratamento
#
# Uso:
#   ./run_comparative_experiment.sh [--pilot] [--scenarios "cenario1 cenario2"]
#
# Exemplos:
#   ./run_comparative_experiment.sh                    # Experimento completo (5 runs)
#   ./run_comparative_experiment.sh --pilot            # Teste rápido (1 run cada)
#   ./run_comparative_experiment.sh --scenarios "indisponibilidade catastrofe"
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

# Parse argumentos
PILOT_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --pilot)
            PILOT_MODE=true
            REPLICATIONS=1
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
            exit 1
            ;;
    esac
done

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
echo ""

# Criar diretório de resultados
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPERIMENT_DIR="$RESULTS_DIR/experiment_$TIMESTAMP"
mkdir -p "$EXPERIMENT_DIR"

# Log do experimento
LOG_FILE="$EXPERIMENT_DIR/experiment.log"
echo "Experimento iniciado em $(date)" > "$LOG_FILE"
echo "Configuração:" >> "$LOG_FILE"
echo "  Tratamentos: ${TREATMENTS[*]}" >> "$LOG_FILE"
echo "  Cenários: ${SCENARIOS[*]}" >> "$LOG_FILE"
echo "  Repetições: $REPLICATIONS" >> "$LOG_FILE"
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

# Função para executar um teste
run_test() {
    local treatment=$1
    local treatment_name=$2
    local scenario=$3
    local run=$4
    local seed=$5
    
    local output_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}.json"
    local summary_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}_summary.json"
    
    echo -e "  ${YELLOW}Executando k6...${NC}"
    
    docker exec k6-tester k6 run \
        --out json=/scripts/results/comparative/experiment_$TIMESTAMP/${scenario}_${treatment}_run${run}.json \
        --summary-export=/scripts/results/comparative/experiment_$TIMESTAMP/${scenario}_${treatment}_run${run}_summary.json \
        --env TREATMENT=$treatment_name \
        --env RUN=$run \
        --env SEED=$seed \
        /scripts/cenario-${scenario}.js 2>&1 | tee -a "$LOG_FILE"
    
    return $?
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
        PAYMENT_SERVICE_VERSION=$treatment docker-compose up -d --build 2>&1 | tee -a "$LOG_FILE"
        
        # Aguardar serviço ficar saudável
        if ! wait_for_healthy; then
            echo -e "${RED}ERRO: Serviço não iniciou corretamente${NC}" | tee -a "$LOG_FILE"
            docker-compose logs servico-pagamento >> "$LOG_FILE"
            continue
        fi
        
        # Warmup
        echo "  Aguardando warmup (${WARMUP_TIME}s)..."
        sleep $WARMUP_TIME
        
        # Executar N repetições
        for run in $(seq 1 $REPLICATIONS); do
            ((current_run++))
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
