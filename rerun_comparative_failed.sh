#!/bin/bash
# ==============================================================================
# rerun_comparative_failed.sh
# ==============================================================================
# Reexecuta apenas combinações scenario×treatment×run que:
# - não geraram arquivos no EXPERIMENT_DIR (missing), e/ou
# - violaram thresholds (opcional: --include-thresholds)
#
# Mantém o padrão de nomes de arquivos para ficar compatível com o analyzer.
#
# Uso:
#   ./rerun_comparative_failed.sh <EXPERIMENT_DIR> [--include-thresholds] [--wsl|--docker]
#                                 [--scenarios "s1 s2"] [--treatments "v1 v2 v3 v4"]
#                                 [--replications N] [--runs "1 3 5"]
#
# Ex:
#   ./rerun_comparative_failed.sh k6/results/comparative/experiment_20251216_101442
#   ./rerun_comparative_failed.sh k6/results/comparative/experiment_20251216_101442 --include-thresholds
# ==============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Uso: $0 <EXPERIMENT_DIR> [--include-thresholds] [--wsl|--docker] [--scenarios \"s1 s2\"] [--treatments \"v1 v2 v3 v4\"] [--replications N]"
  exit 1
fi

EXPERIMENT_DIR="$1"
shift

# Defaults (podem ser sobrescritos por flags ou auto-detect via experiment.log)
TREATMENTS=("v1" "v2" "v3" "v4")
TREATMENT_NAMES=("BASE" "CB" "RETRY" "CB_RETRY")
SCENARIOS=("indisponibilidade-extrema" "falha-catastrofica")
REPLICATIONS=5
RUNS=()
SEED_BASE=42
WARMUP_TIME=${WARMUP_TIME:-15}
COOLDOWN_TIME=${COOLDOWN_TIME:-5}
INCLUDE_THRESHOLDS=false

# Auto-detectar WSL
USE_LOCAL_K6=false
if grep -qi microsoft /proc/version 2>/dev/null || grep -qi wsl /proc/version 2>/dev/null; then
  USE_LOCAL_K6=true
fi

# Detectar docker-compose vs docker compose
COMPOSE_MODE="docker-compose"
if ! command -v docker-compose >/dev/null 2>&1; then
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_MODE="docker compose"
  else
    echo "❌ docker-compose não encontrado (nem 'docker compose')."
    exit 1
  fi
fi

compose() {
  if [ "$COMPOSE_MODE" = "docker-compose" ]; then
    docker-compose "$@"
  else
    docker compose "$@"
  fi
}

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --include-thresholds|--thresholds)
      INCLUDE_THRESHOLDS=true
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
      IFS=' ' read -r -a SCENARIOS <<< "${2:-}"
      shift 2
      ;;
    --treatments)
      IFS=' ' read -r -a TREATMENTS <<< "${2:-}"
      shift 2
      ;;
    --replications)
      REPLICATIONS="${2:-}"
      shift 2
      ;;
    --runs)
      IFS=' ' read -r -a RUNS <<< "${2:-}"
      shift 2
      ;;
    *)
      echo "Argumento desconhecido: $1"
      exit 1
      ;;
  esac
done

iter_runs() {
  if [ ${#RUNS[@]} -gt 0 ]; then
    printf '%s\n' "${RUNS[@]}"
  else
    seq 1 "$REPLICATIONS"
  fi
}

# Normalizar EXPERIMENT_DIR (aceita relativo)
if [ ! -d "$EXPERIMENT_DIR" ]; then
  echo "❌ EXPERIMENT_DIR não encontrado: $EXPERIMENT_DIR"
  exit 1
fi

# Auto-detect config do experiment.log (se existir) para evitar mismatch
if [ -f "$EXPERIMENT_DIR/experiment.log" ]; then
  detected_replications=$(grep -m1 -E '^  Repetições:' "$EXPERIMENT_DIR/experiment.log" | sed 's/[^0-9]*//g' || true)
  if [ -n "$detected_replications" ]; then
    REPLICATIONS="$detected_replications"
  fi

  detected_scenarios=$(grep -m1 -E '^  Cenários:' "$EXPERIMENT_DIR/experiment.log" | sed -E 's/^  Cenários:[[:space:]]*//')
  if [ -n "$detected_scenarios" ]; then
    IFS=' ' read -r -a SCENARIOS <<< "$detected_scenarios"
  fi

  detected_treatments=$(grep -m1 -E '^  Tratamentos:' "$EXPERIMENT_DIR/experiment.log" | sed -E 's/^  Tratamentos:[[:space:]]*//')
  if [ -n "$detected_treatments" ]; then
    IFS=' ' read -r -a TREATMENTS <<< "$detected_treatments"
  fi
fi

# k6 local obrigatório se USE_LOCAL_K6
if [ "$USE_LOCAL_K6" = true ]; then
  if ! command -v k6 >/dev/null 2>&1; then
    echo "❌ k6 não encontrado no PATH (modo local)."
    exit 1
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
K6_SCRIPTS_DIR="$SCRIPT_DIR/k6/scripts"

# Validar scripts k6
for scenario in "${SCENARIOS[@]}"; do
  if [ ! -f "$K6_SCRIPTS_DIR/cenario-${scenario}.js" ]; then
    echo "❌ Script k6 não encontrado: $K6_SCRIPTS_DIR/cenario-${scenario}.js"
    exit 1
  fi
done

RERUN_LOG="$EXPERIMENT_DIR/rerun.log"
echo "Rerun iniciado em $(date)" >> "$RERUN_LOG"
echo "Config: scenarios='${SCENARIOS[*]}' treatments='${TREATMENTS[*]}' replications=$REPLICATIONS include_thresholds=$INCLUDE_THRESHOLDS" >> "$RERUN_LOG"

wait_for_healthy() {
  local max_attempts=${HEALTH_MAX_ATTEMPTS:-60}
  local attempt=1
  local health_url=${HEALTH_URL:-http://localhost:8080/actuator/health}
  local sleep_seconds=${HEALTH_SLEEP_SECONDS:-2}

  echo -n "  Aguardando serviço ficar saudável (${health_url})"
  while [ $attempt -le $max_attempts ]; do
    if docker inspect -f '{{.State.Status}}' servico-pagamento > /dev/null 2>&1; then
      status=$(docker inspect -f '{{.State.Status}}' servico-pagamento 2>/dev/null || true)
      if [ "$status" != "running" ] && [ "$status" != "healthy" ]; then
        echo ""
        echo "  Container servico-pagamento está '$status'" | tee -a "$RERUN_LOG"
        return 1
      fi
    fi

    if curl -sf "$health_url" > /dev/null 2>&1; then
      echo " OK"
      return 0
    fi
    echo -n "."
    sleep "$sleep_seconds"
    ((attempt++))
  done

  echo ""
  return 1
}

thresholds_ok() {
  local summary_file="$1"
  python3 - "$summary_file" <<'PY'
import json, sys
p=sys.argv[1]
try:
  with open(p,'r',encoding='utf-8') as f:
    d=json.load(f)
except Exception:
  sys.exit(2)
metrics=d.get('metrics',{})
for metric in metrics.values():
  th=metric.get('thresholds')
  if isinstance(th, dict):
    # se algum threshold é False, considera violado
    if any(v is False for v in th.values()):
      sys.exit(1)
sys.exit(0)
PY
}

run_test_local() {
  local treatment="$1"
  local treatment_name="$2"
  local scenario="$3"
  local run="$4"
  local seed="$5"

  local output_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}.json"
  local summary_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}_summary.json"
  local script_path="$K6_SCRIPTS_DIR/cenario-${scenario}.js"

  k6 run \
    --out json="$output_file" \
    --summary-export="$summary_file" \
    --env TREATMENT="$treatment_name" \
    --env VERSION="$treatment" \
    --env RUN="$run" \
    --env SEED="$seed" \
    --env PAYMENT_BASE_URL="http://localhost:8080" \
    "$script_path" >> "$RERUN_LOG" 2>&1
}

run_test_docker() {
  local treatment="$1"
  local treatment_name="$2"
  local scenario="$3"
  local run="$4"
  local seed="$5"

  docker exec k6-tester k6 run \
    --out json=/scripts/results/comparative/$(basename "$EXPERIMENT_DIR")/${scenario}_${treatment}_run${run}.json \
    --summary-export=/scripts/results/comparative/$(basename "$EXPERIMENT_DIR")/${scenario}_${treatment}_run${run}_summary.json \
    --env TREATMENT=$treatment_name \
    --env VERSION=$treatment \
    --env RUN=$run \
    --env SEED=$seed \
    --env PAYMENT_BASE_URL=http://servico-pagamento:8080 \
    /scripts/cenario-${scenario}.js >> "$RERUN_LOG" 2>&1
}

run_test() {
  if [ "$USE_LOCAL_K6" = true ]; then
    run_test_local "$@"
  else
    run_test_docker "$@"
  fi
}

# Preflight: contar o que falta
missing_count=0
threshold_count=0

for scenario in "${SCENARIOS[@]}"; do
  for treatment in "${TREATMENTS[@]}"; do
    while IFS= read -r run; do
      summary_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}_summary.json"
      data_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}.json"

      if [ ! -f "$summary_file" ] || [ ! -f "$data_file" ]; then
        missing_count=$((missing_count + 1))
        continue
      fi

      if [ "$INCLUDE_THRESHOLDS" = true ]; then
        if ! thresholds_ok "$summary_file"; then
          threshold_count=$((threshold_count + 1))
        fi
      fi
    done < <(iter_runs)
  done
done

echo "Faltantes: $missing_count  | Thresholds violados (detectáveis no summary): $threshold_count"

if [ $missing_count -eq 0 ] && { [ "$INCLUDE_THRESHOLDS" = false ] || [ $threshold_count -eq 0 ]; }; then
  echo "Nada para reexecutar.";
  exit 0
fi

# Execução: replica o loop do experimento, mas roda somente os runs marcados
for scenario in "${SCENARIOS[@]}"; do
  echo "============================================================"
  echo "CENÁRIO: $scenario"
  echo "============================================================"

  for i in "${!TREATMENTS[@]}"; do
    treatment="${TREATMENTS[$i]}"
    treatment_name="${TREATMENT_NAMES[$i]:-${TREATMENTS[$i]}}"

    # Ver se há algo a rerodar para esse par scenario×treatment
    needs_any=false
    while IFS= read -r run; do
      summary_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}_summary.json"
      data_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}.json"
      if [ ! -f "$summary_file" ] || [ ! -f "$data_file" ]; then
        needs_any=true
        break
      fi
      if [ "$INCLUDE_THRESHOLDS" = true ]; then
        if ! thresholds_ok "$summary_file"; then
          needs_any=true
          break
        fi
      fi
    done < <(iter_runs)

    if [ "$needs_any" = false ]; then
      echo "- skip ${treatment} (sem rerun necessário)"
      continue
    fi

    echo ""
    echo "▶ Tratamento: $treatment ($treatment_name)"

    compose down --remove-orphans > /dev/null 2>&1 || true

    services="servico-adquirente servico-pagamento"
    if ! PAYMENT_SERVICE_VERSION=$treatment compose up -d --build $services >> "$RERUN_LOG" 2>&1; then
      echo "  ERRO: Falha ao subir/buildar serviços (version=$treatment). Veja: $RERUN_LOG"
      continue
    fi

    if ! wait_for_healthy; then
      echo "  ERRO: serviço não ficou saudável. Veja: $RERUN_LOG"
      compose logs --tail=200 servico-pagamento >> "$RERUN_LOG" 2>&1 || true
      compose down --remove-orphans > /dev/null 2>&1 || true
      continue
    fi

    echo "  Warmup (${WARMUP_TIME}s)..."
    sleep "$WARMUP_TIME"

    while IFS= read -r run; do
      summary_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}_summary.json"
      data_file="$EXPERIMENT_DIR/${scenario}_${treatment}_run${run}.json"

      should_rerun=false
      reason=""

      if [ ! -f "$summary_file" ] || [ ! -f "$data_file" ]; then
        should_rerun=true
        reason="missing"
      elif [ "$INCLUDE_THRESHOLDS" = true ]; then
        if ! thresholds_ok "$summary_file"; then
          should_rerun=true
          reason="threshold"
        fi
      fi

      if [ "$should_rerun" = false ]; then
        continue
      fi

      seed=$((SEED_BASE + run))
      echo "  Run $run/$REPLICATIONS (seed=$seed) [reason=$reason]"

      exit_code=0
      run_test "$treatment" "$treatment_name" "$scenario" "$run" "$seed" || exit_code=$?

      if [ $exit_code -eq 0 ]; then
        echo "   ✓ OK"
      elif [ $exit_code -eq 99 ]; then
        echo "   ⚠ Thresholds ainda violados (exit 99)"
      else
        echo "   ✗ Erro (exit $exit_code)"
      fi

      if [ $run -lt "$REPLICATIONS" ]; then
        sleep "$COOLDOWN_TIME"
      fi
    done < <(iter_runs)

    compose down --remove-orphans > /dev/null 2>&1 || true
  done
done

echo "Rerun finalizado. Log: $RERUN_LOG"
