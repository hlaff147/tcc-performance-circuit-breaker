#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run_all_tests_parallel.sh
# Executa testes k6 para V1, V2 e V3 em PARALELO com ambientes 100% ISOLADOS
# Cada versão tem seu próprio adquirente dedicado - sem interferência
# Economia de tempo: ~60% (de ~30min para ~12min)
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
  
  echo "[${version_upper}] Iniciando teste..." | tee "${log_file}"
  
  # Aguarda o container específico estar pronto via porta do host
  local health_url="http://localhost:${port}/actuator/health"
  echo "[${version_upper}] Aguardando ${health_url}..." | tee -a "${log_file}"
  
  if ! wait_for_http "${health_url}" 90 2; then
    echo "[${version_upper}] ERRO: Container não respondeu!" | tee -a "${log_file}"
    return 1
  fi
  
  echo "[${version_upper}] Container pronto. Aguardando estabilização (15s)..." | tee -a "${log_file}"
  sleep 15
  
  # Executa o k6 apontando para o container específico via nome na rede Docker
  local scenario_file="cenario-completo.js"
  local output_prefix="${K6_RESULTS_HOST_DIR}/${version_upper}_Completo"
  
  echo "[${version_upper}] Executando k6 -> ${container}:8080..." | tee -a "${log_file}"
  
  docker run --rm -i \
    --network="${NETWORK_NAME}" \
    -e "PAYMENT_BASE_URL=http://${container}:8080" \
    -e "VERSION=${version}" \
    -e "PAYMENT_MODE_DISTRIBUTION=normal:0.7,latencia:0.2,falha:0.1" \
    -v "${BASE_K6_SCRIPTS_DIR}:/scripts:ro" \
    -v "${K6_RESULTS_HOST_DIR}:/results" \
    "${K6_IMAGE}" run \
    "/scripts/${scenario_file}" \
    --out "json=/results/${version_upper}_Completo.json" \
    --summary-export "/results/${version_upper}_Completo_summary.json" 2>&1 | tee -a "${log_file}" || true
  
  echo "[${version_upper}] Teste concluído!" | tee -a "${log_file}"
}

cleanup() {
  echo "Encerrando containers..."
  ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true
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

  INCLUDE_V3="${INCLUDE_V3:-true}"

  pushd "${PROJECT_ROOT}" >/dev/null
  trap cleanup EXIT

  echo ""
  echo "╔══════════════════════════════════════════════════════════════════╗"
  echo "║  EXECUÇÃO PARALELA COM AMBIENTES 100% ISOLADOS                   ║"
  echo "║  Cada versão (V1, V2, V3) tem seu próprio adquirente dedicado    ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  
  # 1) Para containers anteriores
  echo "Finalizando containers anteriores..."
  ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" down --remove-orphans >/dev/null 2>&1 || true
  ${DOCKER_COMPOSE_CMD} down --remove-orphans >/dev/null 2>&1 || true

  # 2) Sobe TODOS os containers de uma vez usando o compose paralelo
  echo ""
  echo "Subindo ambientes isolados:"
  echo "  • V1: servico-pagamento-v1 + servico-adquirente-v1"
  echo "  • V2: servico-pagamento-v2 + servico-adquirente-v2"
  if [ "${INCLUDE_V3}" = "true" ]; then
    echo "  • V3: servico-pagamento-v3 + servico-adquirente-v3"
  fi
  echo ""
  
  # Define quais serviços subir
  SERVICES="servico-adquirente-v1 servico-pagamento-v1 servico-adquirente-v2 servico-pagamento-v2"
  if [ "${INCLUDE_V3}" = "true" ]; then
    SERVICES="${SERVICES} servico-adquirente-v3 servico-pagamento-v3"
  fi
  
  ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d --build ${SERVICES}
  
  echo ""
  echo "Aguardando 45 segundos para inicialização dos containers..."
  sleep 45

  # 3) Executa testes em paralelo
  echo ""
  echo "Iniciando testes k6 em paralelo (cada um em seu ambiente isolado)..."
  echo ""
  
  # Array para armazenar PIDs dos processos em background (compatível com Bash 3.x)
  PIDS=()
  
  # Inicia V1
  run_k6_for_version "v1" &
  PIDS+=($!)
  
  # Inicia V2
  run_k6_for_version "v2" &
  PIDS+=($!)
  
  # Inicia V3 (se habilitado)
  if [ "${INCLUDE_V3}" = "true" ]; then
    run_k6_for_version "v3" &
    PIDS+=($!)
  fi

  # Inicia V4 (sempre ativo)
  run_k6_for_version "v4" &
  PIDS+=($!)
  
  # Aguarda todos os processos terminarem
  echo "Aguardando conclusão de todos os testes..."
  echo "(Logs individuais em ${LOG_DIR}/)"
  echo ""
  
  FAILED=0
  for pid in "${PIDS[@]}"; do
    if ! wait "${pid}"; then
      FAILED=$((FAILED + 1))
    fi
  done
  
  echo ""
  echo "╔══════════════════════════════════════════════════════════════════╗"
  if [ ${FAILED} -eq 0 ]; then
    echo "║  ✓ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!                       ║"
  else
    echo "║  ✗ ${FAILED} TESTE(S) FALHARAM                                        ║"
  fi
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Resultados disponíveis em: ${K6_RESULTS_HOST_DIR}"
  echo "Logs de execução em: ${LOG_DIR}"
  
  popd >/dev/null
}

main "$@"
