import subprocess
import datetime
import time
import os
import json
from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
from prometheus_api_client import PrometheusConnect

# --- 1. CONFIGURAÇÃO GLOBAL ---
PROMETHEUS_URL = "http://localhost:9090"
K6_CONTAINER_NAME = "k6-tester"
K6_SCRIPTS_PATH = "/scripts"  # Caminho DENTRO do contêiner k6
K6_RESULTS_PATH_IN_CONTAINER = "/scripts/results"
RESULTS_DIR = "resultados_tcc"  # Diretório local para salvar todos os artefatos

# Matriz de Testes: Executa apenas o cenário completo único
EXPERIMENTS = [
    {"version": "V1 (Baseline)", "output_file": "V1_Completo.json", "k6_script": "cenario-completo.js"},
    {"version": "V2 (Circuit Breaker)", "output_file": "V2_Completo.json", "k6_script": "cenario-completo.js"},
]

# Métricas do Prometheus (PromQL) a serem coletadas
PROMQL_QUERIES = {
    "cpu_usage": 'rate(container_cpu_usage_seconds_total{container_name="servico-pagamento"}[1m]) * 100',
    "memory_usage_mb": 'container_memory_usage_bytes{container_name="servico-pagamento"} / 1024 / 1024',
    "tomcat_threads_busy": 'tomcat_threads_busy{job="servico-pagamento"}',
    "jvm_threads_live": 'jvm_threads_live{job="servico-pagamento"}',
    "cb_state": 'resilience4j_circuitbreaker_state{name="adquirente-cb", job="servico-pagamento"}',  # 1=CLOSED, 0=OPEN, 2=HALF_OPEN
    "cb_calls_failed_rate": 'rate(resilience4j_circuitbreaker_calls_total{name="adquirente-cb", kind="failed"}[1m])',
    "cb_calls_not_permitted_rate": 'rate(resilience4j_circuitbreaker_calls_total{name="adquirente-cb", kind="not_permitted"}[1m])',
}

# --- 2. FUNÇÕES HELPERS ---

def run_docker_command(command: str, capture_output: bool = False, text: bool = True):
    """Executa um comando shell (preferencialmente Docker) de forma robusta."""
    print(f"[CMD] Executando: {command}")
    try:
        return subprocess.run(command, shell=True, check=True, capture_output=capture_output, text=text)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {e}")
        return None

def update_docker_compose(context_path: str) -> None:
    """Atualiza o docker-compose.yml para apontar para o build context correto (V1 ou V2)."""
    print(f"Atualizando docker-compose.yml para usar o contexto: {context_path}")
    try:
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()

        import re

        pattern = r"(services:\s+servico-pagamento:\s+build:\s+context:\s+).*"
        replacement = r"\\g<1>" + context_path

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)

        with open("docker-compose.yml", "w", encoding="utf-8") as f:
            f.write(new_content)

    except FileNotFoundError:
        print("ERRO: 'docker-compose.yml' não encontrado.")
        raise
    except Exception as e:
        print(f"ERRO ao atualizar docker-compose.yml: {e}")
        raise

def plot_metric(metric_data: List[Dict[str, Any]], metric_name: str, output_dir: str, test_name: str) -> None:
    """Converte dados do Prometheus em um gráfico PNG usando Matplotlib."""
    try:
        if not metric_data or not metric_data[0].get("values"):
            print(f"  [Plot] Sem dados para a métrica: {metric_name}")
            return

        data = metric_data[0]["values"]
        df = pd.DataFrame(data, columns=["timestamp", "value"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["value"] = pd.to_numeric(df["value"])

        plt.figure(figsize=(12, 6))
        plt.plot(df["timestamp"], df["value"], label=metric_name)
        plt.xlabel("Tempo")
        plt.ylabel("Valor")
        plt.title(f"{test_name}\n{metric_name}")
        plt.legend()
        plt.grid(True)

        filename = os.path.join(output_dir, f"{test_name}_{metric_name}.png")
        plt.savefig(filename)
        plt.close()
        print(f"  [Plot] Gráfico salvo: {filename}")

    except Exception as e:
        print(f"  [Plot] Erro ao plotar {metric_name}: {e}")

def fetch_prometheus_data(prom_client: PrometheusConnect, start_time: datetime.datetime, end_time: datetime.datetime, output_dir: str, test_name: str) -> None:
    """Busca todas as métricas do Prometheus para o intervalo de tempo do teste e as plota."""
    print(f"  [Prometheus] Coletando métricas de {start_time} a {end_time}")
    for key, query in PROMQL_QUERIES.items():
        try:
            metric_data = prom_client.custom_query_range(
                query=query,
                start_time=start_time,
                end_time=end_time,
                step="5s",
            )
            plot_metric(metric_data, key, output_dir, test_name)
        except Exception as e:
            print(f"  [Prometheus] Erro ao buscar métrica {key}: {e}")

def _extract_trend_stats(metric_payload: Dict[str, Any], prefix: str) -> Dict[str, float]:
    """Gera um dicionário achatado com estatísticas relevantes para métricas do tipo Trend."""
    stats = {}
    if not metric_payload:
        return stats

    mappings = {
        "avg": "avg",
        "min": "min",
        "max": "max",
        "med": "med",
        "p(90)": "p90",
        "p(95)": "p95",
        "p(99)": "p99",
    }

    for key, suffix in mappings.items():
        value = metric_payload.get(key)
        if value is not None:
            stats[f"{prefix}_{suffix}_ms"] = float(value)
    return stats

def run_k6_test(script_name: str, output_file: str) -> None:
    """Executa um teste k6 dentro do contêiner k6."""
    k6_command = (
        f"docker exec {K6_CONTAINER_NAME} k6 run "
        f"{K6_SCRIPTS_PATH}/{script_name} "
        f"--out json={K6_RESULTS_PATH_IN_CONTAINER}/{output_file}"
    )
    print(f"  [k6] Executando: {k6_command}")
    run_docker_command(k6_command)

def parse_k6_summary(json_file_path: str) -> Dict[str, Any]:
    """
    Analisa o arquivo JSON de saída do k6 e extrai um dicionário detalhado de métricas.
    Esta função foi aprimorada para extrair métricas-chave, incluindo todas as trends customizadas
    (p95, p99, média, etc.). O formato esperado é o JSON exportado via --summary-export.
    """
    print(f"  [k6] Analisando arquivo de resultado: {json_file_path}")
    if not os.path.exists(json_file_path):
        print(f"  [k6] ERRO: Arquivo JSON não encontrado: {json_file_path}")
        return {}

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("  [k6] ERRO: Arquivo não está em formato JSON consolidado. Verifique se o teste usou --summary-export.")
        return {}

    metrics = data.get("metrics", {})

    def get_metric_field(metric_name: str, field: str, default: float = 0.0) -> float:
        metric_data = metrics.get(metric_name, {})
        return float(metric_data.get(field, default)) if metric_data else default

    summary: Dict[str, Any] = {}

    # Métricas gerais
    summary["vazao_req_s"] = get_metric_field("http_reqs", "rate")
    summary["falha_rate_%"] = get_metric_field("http_req_failed", "rate") * 100
    summary["checks_rate_%"] = get_metric_field("checks", "rate") * 100
    summary["reqs_total"] = get_metric_field("http_reqs", "count")
    summary["duration_teste_ms"] = get_metric_field("iterations", "duration")

    # Tendências principais
    trend_mappings = {
        "http_req_duration": "req_duration",
        "http_req_waiting": "req_waiting",
        "http_req_blocked": "req_blocked",
        "http_req_connecting": "req_connecting",
        "http_req_tls_handshaking": "req_tls_handshaking",
        "http_req_sending": "req_sending",
        "http_req_receiving": "req_receiving",
        "ttfb": "ttfb",
        "waiting_time": "waiting_time",
        "iteration_duration": "iteration_duration",
    }

    for metric_name, prefix in trend_mappings.items():
        metric_payload = metrics.get(metric_name)
        if metric_payload:
            summary.update(_extract_trend_stats(metric_payload, prefix))

    return summary

# --- 3. FUNÇÃO PRINCIPAL (ORQUESTRADOR) ---

def main() -> None:
    """Orquestra todo o experimento: build, execução, coleta e análise."""

    print("--- INICIANDO EXPERIMENTO DE BENCHMARK E ANÁLISE ---")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    try:
        prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)
        print(f"[Setup] Conectado ao Prometheus em {PROMETHEUS_URL}")
    except Exception as e:
        print(f"ERRO: Não foi possível conectar ao Prometheus em {PROMETHEUS_URL}. Verifique se ele está rodando.")
        print(e)
        return

    all_results_data: List[Dict[str, Any]] = []

    for exp in EXPERIMENTS:
        version = exp["version"]
        k6_script = exp["k6_script"]
        output_file = exp["output_file"]

        # Define o caminho de contexto com base na versão
        context_path = "./services/payment-service-v2" if "V2" in version else "./services/payment-service-v1"

        test_name = f"{version.replace(' ', '_')}_Completo"
        test_output_dir = os.path.join(RESULTS_DIR, test_name)
        os.makedirs(test_output_dir, exist_ok=True)

        print(f"\n--- EXECUTANDO TESTE: {test_name} ---")

        try:
            print("[Setup] Parando e limpando ambiente docker...")
            run_docker_command("docker-compose down -v --remove-orphans")

            update_docker_compose(context_path)

            print(f"[Setup] Subindo ambiente para {version}...")
            run_docker_command(
                "docker-compose up -d --build payment-service acquirer-service prometheus cadvisor grafana k6"
            )

            print("[Setup] Aguardando 30s para a inicialização dos serviços...")
            time.sleep(30)

            start_time = datetime.datetime.now()
            print(f"[k6] Início do teste k6: {start_time}")

            run_k6_test(k6_script, output_file)

            end_time = datetime.datetime.now()
            print(f"[k6] Fim do teste k6: {end_time}")

            fetch_prometheus_data(
                prom,
                start_time,
                end_time + datetime.timedelta(seconds=15),
                test_output_dir,
                test_name,
            )

            k6_json_output_path_local = os.path.join(test_output_dir, output_file)
            run_docker_command(
                f"docker cp {K6_CONTAINER_NAME}:{K6_RESULTS_PATH_IN_CONTAINER}/{output_file} {k6_json_output_path_local}"
            )

            summary_data = parse_k6_summary(k6_json_output_path_local)

            summary_data["versao"] = version
            summary_data["cenario"] = "Completo"
            all_results_data.append(summary_data)

            print(
                f"--- TESTE {test_name} CONCLUÍDO. Gráficos e resultados salvos em: {test_output_dir} ---"
            )

        except Exception as e:
            print(f"ERRO: Teste {test_name} falhou catastroficamente: {e}")
            continue

    print("\n--- EXPERIMENTO COMPLETO ---")

    if all_results_data:
        summary_df = pd.DataFrame(all_results_data)
        summary_df = summary_df.set_index(["versao", "cenario"])

        csv_filename = os.path.join(RESULTS_DIR, "resumo_comparativo_final.csv")
        summary_df.to_csv(csv_filename)

        print(f"Tabela de resumo comparativo salva em: {csv_filename}")
        print("\nResumo dos Resultados:")
        print(summary_df.to_markdown())

    print("Limpando ambiente docker final...")
    run_docker_command("docker-compose down -v --remove-orphans")

    print("--- AUTOMAÇÃO CONCLUÍDA ---")


if __name__ == "__main__":
    main()
