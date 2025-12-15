#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE_CMD="docker-compose"
else
  DOCKER_COMPOSE_CMD="docker compose"
fi

PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
DURATION="1h"
STEP="30s"
KEEP_RUNNING="false"
METRICS=()
METRICS_FILE=""
OUTPUT_DIR=""
REPORT_TITLE="Prometheus export"
SERVICES=("prometheus" "grafana")
STARTED_SERVICES=()

usage() {
  cat <<'EOF'
Uso: ./monitoring/scripts/export_prometheus_data.sh [opcoes]

Opcoes principais:
  --duration <janela>     Janela de tempo a exportar (ex: 30m, 2h, 1d). Padrão: 1h
  --step <intervalo>      Intervalo entre pontos (ex: 15s, 1m). Padrão: 30s
  --metric <consulta>     Adiciona uma consulta PromQL (pode ser repetido)
  --metrics-file <caminho>Arquivo com uma consulta PromQL por linha
  --output-dir <caminho>  Diretório destino (default cria timestamp em analysis_results)
  --title <texto>         Título incluído no metadata.json
  --keep-running          Mantém Prometheus/Grafana ativos ao final
  -h, --help              Mostra esta ajuda

Exemplos:
  ./monitoring/scripts/export_prometheus_data.sh \\
      --duration 2h --metric 'rate(http_server_requests_seconds_count[1m])'

  ./monitoring/scripts/export_prometheus_data.sh --metrics-file monitoring/prometheus_queries.txt
EOF
}

trim() {
  printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

parse_duration_to_seconds() {
  local value="$1"
  local rest="$value"
  local total=0
  local matched=0

  while [[ "$rest" =~ ^([0-9]+)([smhdw])(.*)$ ]]; do
    matched=1
    local quantity="${BASH_REMATCH[1]}"
    local unit="${BASH_REMATCH[2]}"
    rest="${BASH_REMATCH[3]}"
    local factor=1
    case "$unit" in
      s) factor=1 ;;
      m) factor=60 ;;
      h) factor=3600 ;;
      d) factor=$((24 * 3600)) ;;
      w) factor=$((7 * 24 * 3600)) ;;
      *) factor=1 ;;
    esac
    total=$((total + quantity * factor))
  done

  if [[ "$matched" -eq 0 || -n "$rest" ]]; then
    echo "Erro: duração inválida '$value'. Use formato como 30m, 2h, 1d." >&2
    exit 1
  fi

  echo "$total"
}

urlencode() {
  python3 -c "import urllib.parse, sys; print(urllib.parse.quote_plus(sys.argv[1]))" "$1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --duration)
      [ $# -ge 2 ] || { echo "Erro: --duration requer valor." >&2; exit 1; }
      DURATION="$2"
      shift 2
      ;;
    --step)
      [ $# -ge 2 ] || { echo "Erro: --step requer valor." >&2; exit 1; }
      STEP="$2"
      shift 2
      ;;
    --metric)
      [ $# -ge 2 ] || { echo "Erro: --metric requer valor." >&2; exit 1; }
      METRICS+=("$2")
      shift 2
      ;;
    --metrics-file)
      [ $# -ge 2 ] || { echo "Erro: --metrics-file requer caminho." >&2; exit 1; }
      METRICS_FILE="$2"
      shift 2
      ;;
    --output-dir)
      [ $# -ge 2 ] || { echo "Erro: --output-dir requer caminho." >&2; exit 1; }
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --title)
      [ $# -ge 2 ] || { echo "Erro: --title requer texto." >&2; exit 1; }
      REPORT_TITLE="$2"
      shift 2
      ;;
    --keep-running)
      KEEP_RUNNING="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Erro: argumento desconhecido '$1'." >&2
      usage
      exit 1
      ;;
  esac
done

if [ -n "$METRICS_FILE" ]; then
  if [ ! -f "$METRICS_FILE" ]; then
    echo "Erro: arquivo de métricas '$METRICS_FILE' não encontrado." >&2
    exit 1
  fi
  while IFS= read -r line || [ -n "$line" ]; do
    line="$(trim "$line")"
    [ -z "$line" ] && continue
    case "$line" in
      \#*) continue ;;
    esac
    METRICS+=("$line")
  done < "$METRICS_FILE"
fi

if [ ${#METRICS[@]} -eq 0 ]; then
  METRICS=(
    'http_server_requests_seconds_count'
    'http_server_requests_seconds_sum'
    'resilience4j_circuitbreaker_calls_total'
    'resilience4j_circuitbreaker_state'
    'jvm_memory_used_bytes'
    'jvm_gc_pause_seconds_count'
    'process_cpu_usage'
    'process_uptime_seconds'
    'container_cpu_usage_seconds_total'
    'container_memory_usage_bytes'
  )
fi

DURATION_SECONDS="$(parse_duration_to_seconds "$DURATION")"
STEP_SECONDS="$(parse_duration_to_seconds "$STEP")"
NOW_TS="$(date -u +"%s")"
START_TS=$((NOW_TS - DURATION_SECONDS))

if [ -z "$OUTPUT_DIR" ]; then
  TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
  OUTPUT_DIR="${PROJECT_ROOT}/analysis_results/prometheus_exports/${TIMESTAMP}"
fi

mkdir -p "$OUTPUT_DIR"

cleanup() {
  if [ "$KEEP_RUNNING" = "false" ]; then
    for svc in "${STARTED_SERVICES[@]}"; do
      ${DOCKER_COMPOSE_CMD} stop "$svc" >/dev/null 2>&1 || true
    done
  fi
}

trap cleanup EXIT

pushd "$PROJECT_ROOT" >/dev/null

for svc in "${SERVICES[@]}"; do
  if [ -n "$(${DOCKER_COMPOSE_CMD} ps -q "$svc")" ]; then
    continue
  fi
  ${DOCKER_COMPOSE_CMD} up -d --no-deps "$svc"
  STARTED_SERVICES+=("$svc")
  if [ "$svc" = "prometheus" ]; then
    echo "Prometheus iniciado usando volume compartilhado prometheus-data."
  elif [ "$svc" = "grafana" ]; then
    echo "Grafana iniciado usando volume compartilhado grafana-data."
  fi
done

popd >/dev/null

if ! curl -sSf "${PROMETHEUS_URL}/-/ready" >/dev/null 2>&1; then
  echo "Aguardando Prometheus ficar pronto em ${PROMETHEUS_URL}..."
  ready="false"
  for attempt in $(seq 1 60); do
    if curl -sSf "${PROMETHEUS_URL}/-/ready" >/dev/null 2>&1; then
      ready="true"
      break
    fi
    sleep 2
  done
  if [ "$ready" != "true" ]; then
    echo "Erro: Prometheus não respondeu em ${PROMETHEUS_URL} após 120 segundos." >&2
    exit 1
  fi
fi

echo "Exportando métricas para ${OUTPUT_DIR}"
for metric in "${METRICS[@]}"; do
  encoded_metric="$(urlencode "$metric")"
  safe_name="$(printf '%s' "$metric" | sed 's/[^A-Za-z0-9_.-]/_/g')"
  target_file="${OUTPUT_DIR}/${safe_name}.json"
  curl -sS "${PROMETHEUS_URL}/api/v1/query_range?query=${encoded_metric}&start=${START_TS}&end=${NOW_TS}&step=${STEP_SECONDS}s" \
    > "$target_file"
  echo "  - ${metric} => ${target_file}"
done

python3 - "${REPORT_TITLE}" "${PROMETHEUS_URL}" "${DURATION}" "${STEP}" "${OUTPUT_DIR}/metadata.json" "${METRICS[@]}" <<'PY'
import datetime
import json
import sys

if len(sys.argv) < 6:
  raise SystemExit("metadata helper requires title, url, duration, step, output path, metrics...")

title, prom_url, duration, step, output_path, *metrics = sys.argv[1:]

payload = {
  "title": title,
  "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
  "prometheus_url": prom_url,
  "duration": duration,
  "step": step,
  "metrics": metrics,
}

with open(output_path, "w", encoding="utf-8") as fh:
  json.dump(payload, fh, indent=2)
  fh.write("\n")
PY

echo
if [ "$KEEP_RUNNING" = "true" ]; then
  echo "Prometheus e Grafana continuarão ativos."
else
  cleanup
  trap - EXIT
  echo "Prometheus e Grafana foram desligados após a exportação."
fi

echo "Arquivos gerados em: ${OUTPUT_DIR}"
echo "Acesse Grafana em http://localhost:3000 (login padrão admin/admin) enquanto o serviço estiver ativo."
