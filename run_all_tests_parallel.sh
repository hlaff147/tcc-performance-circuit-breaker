#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run_all_tests_parallel.sh
# Executa testes k6 para V1, V2, V3 e V4 em PARALELO com ambientes 100% ISOLADOS
# Cada versão tem seu próprio adquirente dedicado - sem interferência
# Economia de tempo: ~75% (de ~40min para ~12min)
# =============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE_CMD="docker-compose"
else
  DOCKER_COMPOSE_CMD="docker compose"
fi

# Usa o docker-compose-parallel.yml que tem ambientes isolados
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose-parallel.yml"

NETWORK_NAME="${COMPOSE_NETWORK_NAME:-tcc-performance-circuit-breaker_tcc-network}"
K6_IMAGE="${K6_IMAGE:-grafana/k6:latest}"

BASE_K6_SCRIPTS_DIR="${PROJECT_ROOT}/k6/scripts"

if [ -d "${PROJECT_ROOT}/k6-results" ]; then
  K6_RESULTS_HOST_DIR="${PROJECT_ROOT}/k6-results"
else
  K6_RESULTS_HOST_DIR="${PROJECT_ROOT}/k6/results"
fi

mkdir -p "${K6_RESULTS_HOST_DIR}"
chmod -R 777 "${K6_RESULTS_HOST_DIR}"

# Diretório para logs de cada versão
LOG_DIR="${PROJECT_ROOT}/.parallel_logs"
mkdir -p "${LOG_DIR}"

# Funções de mapeamento (compatível com Bash 3.x do macOS)
get_container_for_version() {
  case "$1" in
    v1) echo "servico-pagamento-v1" ;;
    v2) echo "servico-pagamento-v2" ;;
    v3) echo "servico-pagamento-v3" ;;
    v4) echo "servico-pagamento-v4" ;;
  esac
}

get_port_for_version() {
  case "$1" in
    v1) echo "8080" ;;
    v2) echo "8082" ;;
    v3) echo "8083" ;;
    v4) echo "8084" ;;
  esac
}

wait_for_http() {
  local url="$1"
  local retries="${2:-60}"
  local delay="${3:-3}"

  for attempt in $(seq 1 "${retries}"); do
    local status
    status="$(curl -sS -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo 000)"

    if [ "${status}" != "000" ]; then
      if [ "${status}" -ge 200 ] && [ "${status}" -lt 500 ]; then
        return 0
      fi
    fi

    sleep "${delay}"
  done

  return 1
}

run_k6_for_version() {
  local version="$1"
  local container="$(get_container_for_version "$version")"
  local port="$(get_port_for_version "$version")"
  local version_upper="$(echo ${version} | tr '[:lower:]' '[:upper:]')"
  local log_file="${LOG_DIR}/${version}.log"
  
  # Argumentos extras para o k6
  local k6_scenario_file="${2:-cenario-completo.js}"
  local k6_scenario_label="${3:-Completo}"
  
  echo "[${version_upper}] Iniciando teste (${k6_scenario_label})..." | tee -a "${log_file}"
  
  # Aguarda o container específico estar pronto via porta do host
  local health_url="http://localhost:${port}/actuator/health"
  echo "[${version_upper}] Aguardando ${health_url}..." | tee -a "${log_file}"
  
  if ! wait_for_http "${health_url}" 90 2; then
    echo "[${version_upper}] ERRO: Container não respondeu!" | tee -a "${log_file}"
    return 1
  fi
  
  echo "[${version_upper}] Container pronto. Aguardando estabilização (10s)..." | tee -a "${log_file}"
  sleep 10
  
  # Determina o diretório de saída (scenarios/ se não for o completo)
  local output_dir="${K6_RESULTS_HOST_DIR}"
  local container_output_path="/results"
  local json_name="${k6_scenario_label}_${version_upper}.json"
  local summary_name="${k6_scenario_label}_${version_upper}_summary.json"

  if [ "${k6_scenario_label}" != "Completo" ]; then
    output_dir="${K6_RESULTS_HOST_DIR}/scenarios"
    container_output_path="/results/scenarios"
    mkdir -p "${output_dir}"
    chmod 777 "${output_dir}"
  else
    # Convenção do analyzer.py: V1_Completo.json
    json_name="${version_upper}_Completo.json"
    summary_name="${version_upper}_Completo_summary.json"
  fi

  echo "[${version_upper}] Executando k6 (${k6_scenario_label}) -> ${container}:8080..." | tee -a "${log_file}"
  
  docker run --rm -i \
    --network="${NETWORK_NAME}" \
    -e "PAYMENT_BASE_URL=http://${container}:8080" \
    -e "VERSION=${version}" \
    -e "PAYMENT_MODE_DISTRIBUTION=normal:0.7,latencia:0.2,falha:0.1" \
    -v "${BASE_K6_SCRIPTS_DIR}:/scripts:ro" \
    -v "${K6_RESULTS_HOST_DIR}:/results" \
    "${K6_IMAGE}" run \
    "/scripts/${k6_scenario_file}" \
    --out "json=${container_output_path}/${json_name}" \
    --summary-export "${container_output_path}/${summary_name}" 2>&1 | tee -a "${log_file}" || true
  
  echo "[${version_upper}] Teste (${k6_scenario_label}) concluído!" | tee -a "${log_file}"
}

cleanup() {
  echo "Encerrando containers..."
  ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true
}

run_scenario_wave() {
  local scenario_file="$1"
  local scenario_label="$2"
  local PW_PIDS=()

  echo "----------------------------------------------------------------------"
  echo ">>> Onda Paralela: ${scenario_label}"
  echo "----------------------------------------------------------------------"

  # Inicia V1
  run_k6_for_version "v1" "${scenario_file}" "${scenario_label}" &
  PW_PIDS+=($!)
  
  # Inicia V2
  run_k6_for_version "v2" "${scenario_file}" "${scenario_label}" &
  PW_PIDS+=($!)
  
  # Inicia V3 (se habilitado)
  if [ "${INCLUDE_V3}" = "true" ]; then
    run_k6_for_version "v3" "${scenario_file}" "${scenario_label}" &
    PW_PIDS+=($!)
  fi

  # Inicia V4 (sempre ativo)
  run_k6_for_version "v4" "${scenario_file}" "${scenario_label}" &
  PW_PIDS+=($!)
  
  local FAILED_WAVE=0
  for pid in "${PW_PIDS[@]}"; do
    if ! wait "${pid}"; then
      FAILED_WAVE=$((FAILED_WAVE + 1))
    fi
  done
  return ${FAILED_WAVE}
}

main() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Erro: docker não encontrado no PATH." >&2
    exit 1
  fi

  if [ ! -f "${COMPOSE_FILE}" ]; then
    echo "Erro: ${COMPOSE_FILE} não encontrado." >&2
    exit 1
  fi

  local TARGET_SCENARIOS="${1:-Completo}"
  INCLUDE_V3="${INCLUDE_V3:-true}"

  pushd "${PROJECT_ROOT}" >/dev/null
  trap cleanup EXIT

  echo ""
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║  EXECUÇÃO PARALELA (V1-V4) - AMBIENTES ISOLADOS                  ║"
  echo "║  Cenários solicitados: ${TARGET_SCENARIOS}                         ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  
  # 1) Para e limpa containers anteriores
  echo "Limpando ambiente..."
  ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true

  # 2) Sobe TODOS os containers
  echo "Subindo serviços..."
  SERVICES="servico-adquirente-v1 servico-pagamento-v1 servico-adquirente-v2 servico-pagamento-v2 servico-adquirente-v4 servico-pagamento-v4"
  if [ "${INCLUDE_V3}" = "true" ]; then
    SERVICES="${SERVICES} servico-adquirente-v3 servico-pagamento-v3"
  fi
  ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d --build ${SERVICES}
  
  echo "Aguardando 45s para inicialização..."
  sleep 45

  # 3) Determina quais ondas executar
  TOTAL_FAILED=0
  
  # Se for "all", executa a lista completa
  if [ "${TARGET_SCENARIOS}" = "all" ]; then
    # Onda 1: Completo
    run_scenario_wave "cenario-completo.js" "Completo" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    
    # Onda 2: Catástrofe
    run_scenario_wave "cenario-falha-catastrofica.js" "catastrofe" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    
    # Onda 3: Degradação
    run_scenario_wave "cenario-degradacao-gradual.js" "degradacao" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    
    # Onda 4: Rajadas
    run_scenario_wave "cenario-rajadas-intermitentes.js" "rajadas" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    
    # Onda 5: Indisponibilidade
    run_scenario_wave "cenario-indisponibilidade-extrema.js" "indisponibilidade" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    
    # Onda 6: Normal
    run_scenario_wave "cenario-operacao-normal.js" "normal" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
  else
    # Executa apenas o cenário passado (ex: Completo)
    if [ "${TARGET_SCENARIOS}" = "Completo" ]; then
        run_scenario_wave "cenario-completo.js" "Completo" || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    else
        # Se for um cenário específico passado do run_everything
        # Ex: "catastrofe" mapping to cenario-falha-catastrofica.js
        case "${TARGET_SCENARIOS}" in
            catastrofe) run_scenario_wave "cenario-falha-catastrofica.js" "catastrofe" ;;
            degradacao) run_scenario_wave "cenario-degradacao-gradual.js" "degradacao" ;;
            rajadas) run_scenario_wave "cenario-rajadas-intermitentes.js" "rajadas" ;;
            indisponibilidade) run_scenario_wave "cenario-indisponibilidade-extrema.js" "indisponibilidade" ;;
            normal) run_scenario_wave "cenario-operacao-normal.js" "normal" ;;
            *) echo "⚠️  Cenário desconhecido: ${TARGET_SCENARIOS}"; exit 1 ;;
        esac || TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
  fi
  
  echo ""
  echo "╔══════════════════════════════════════════════════════════════════╗"
  if [ ${TOTAL_FAILED} -eq 0 ]; then
    echo "║  ✓ TODOS OS CENÁRIOS CONCLUÍDOS COM SUCESSO!                     ║"
  else
    echo "║  ✗ ${TOTAL_FAILED} CENÁRIO(S) TIVERAM FALHAS                              ║"
  fi
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Logs: ${LOG_DIR}/"
  
  popd >/dev/null
}

main "$@"
