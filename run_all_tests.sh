#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE_CMD="docker-compose"
else
  DOCKER_COMPOSE_CMD="docker compose"
fi

DEFAULT_NETWORK_PREFIX="${COMPOSE_PROJECT_NAME:-tcc-performance-circuit-breaker}"
NETWORK_NAME="${COMPOSE_NETWORK_NAME:-${DEFAULT_NETWORK_PREFIX}_tcc-network}"
K6_IMAGE="${K6_IMAGE:-grafana/k6:latest}"

if [ -d "${PROJECT_ROOT}/k6-scripts" ]; then
  K6_SCRIPTS_HOST_DIR="${PROJECT_ROOT}/k6-scripts"
else
  K6_SCRIPTS_HOST_DIR="${PROJECT_ROOT}/k6/scripts"
fi

if [ -d "${PROJECT_ROOT}/k6-results" ]; then
  K6_RESULTS_HOST_DIR="${PROJECT_ROOT}/k6-results"
else
  K6_RESULTS_HOST_DIR="${PROJECT_ROOT}/k6/results"
fi

mkdir -p "${K6_RESULTS_HOST_DIR}"

SCENARIOS=(
  "Normal:cenario-A-normal.js"
  "Latencia:cenario-B-latencia.js"
  "Falha:cenario-C-falha.js"
  "Estresse:cenario-D-estresse-crescente.js"
  "Recuperacao:cenario-E-recuperacao.js"
  "FalhasIntermitentes:cenario-F-falhas-intermitentes.js"
  #"AltaConcorrencia:cenario-G-alta-concorrencia.js"
)

wait_for_http() {
  local url="$1"
  local retries="${2:-45}"  # Aumentado de 30 para 45 tentativas
  local delay="${3:-3}"    # Aumentado de 2 para 3 segundos de delay

  for attempt in $(seq 1 "${retries}"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${delay}"
  done

  return 1
}

run_k6_scenarios() {
  local version_key="$1"
  local version_label="$(echo ${version_key} | tr '[:lower:]' '[:upper:]')"

  echo "=============================="
  echo "Iniciando rodada para ${version_label}"
  echo "=============================="

  export PAYMENT_SERVICE_VERSION="${version_key}"

  echo "Finalizando containers anteriores (se existirem)..."
  ${DOCKER_COMPOSE_CMD} down --remove-orphans >/dev/null 2>&1 || true

  echo "Subindo ambiente docker-compose para ${version_label}..."
  ${DOCKER_COMPOSE_CMD} up -d --build

  echo "Aguardando serviços responderem..."
  # Espera inicial para garantir que os containers estejam prontos
  echo "Aguardando 30 segundos para inicialização inicial dos containers..."
  sleep 30
  
  if wait_for_http "http://localhost:8080/actuator/health" 60 3; then
    echo "servico-pagamento respondeu no endpoint /actuator/health."
    # Espera adicional após confirmação para garantir estabilidade
    echo "Aguardando mais 15 segundos para estabilização completa..."
    sleep 15
  else
    echo "Aviso: não foi possível confirmar o /actuator/health. Prosseguindo após espera adicional."
    sleep 30  # Aumentado de 15 para 30 segundos
  fi

  for scenario in "${SCENARIOS[@]}"; do
    IFS=":" read -r scenario_label scenario_file <<<"${scenario}"
    output_file="${K6_RESULTS_HOST_DIR}/${version_label}_${scenario_label}.json"

    echo "Executando cenário ${scenario_label} (${scenario_file}) para ${version_label}..."
    # Executa o k6 e ignora o código de saída para continuar mesmo se o teste falhar
    docker run --rm -i \
      --network="${NETWORK_NAME}" \
      -v "${K6_SCRIPTS_HOST_DIR}:/scripts" \
      -v "${K6_RESULTS_HOST_DIR}:/scripts/results" \
      "${K6_IMAGE}" run \
      "/scripts/${scenario_file}" \
      --out "json=/scripts/results/${version_label}_${scenario_label}.json" || true

    echo "Resultado salvo em ${output_file}"
    
    # Aguarda 45 segundos entre cada cenário para garantir que o sistema volte ao estado inicial
    echo "Aguardando 45 segundos entre cenários para recuperação completa..."
    sleep 45
  done

  echo "Encerrando containers da rodada ${version_label}..."
  ${DOCKER_COMPOSE_CMD} down --remove-orphans >/dev/null 2>&1 || true

  unset PAYMENT_SERVICE_VERSION
}

main() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Erro: docker não encontrado no PATH." >&2
    exit 1
  fi

  pushd "${PROJECT_ROOT}" >/dev/null
  trap '${DOCKER_COMPOSE_CMD} down --remove-orphans >/dev/null 2>&1 || true' EXIT

  for version in v1 v2; do
    run_k6_scenarios "${version}"
  done

  echo "Execução concluída. Resultados disponíveis em ${K6_RESULTS_HOST_DIR}."
  popd >/dev/null
}

main "$@"
