import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from prometheus_api_client import PrometheusConnect
from typing import Dict, List, Any
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
from jinja2 import Template
import warnings
warnings.filterwarnings('ignore')

# Configurações globais
PROMETHEUS_URL = "http://localhost:9090"
RESULTS_DIR = "k6/results"
OUTPUT_DIR = "analysis_results"

# Métricas do Prometheus (PromQL) expandidas
PROMQL_QUERIES = {
    # Métricas de CPU e Memória
    "cpu_usage": 'rate(container_cpu_usage_seconds_total{container_name="servico-pagamento"}[1m]) * 100',
    "memory_usage_mb": 'container_memory_usage_bytes{container_name="servico-pagamento"} / 1024 / 1024',
    
    # Métricas do Tomcat
    "tomcat_threads_busy": 'tomcat_threads_busy{job="servico-pagamento"}',
    "tomcat_threads_current": 'tomcat_threads_current{job="servico-pagamento"}',
    "tomcat_global_request_rate": 'rate(tomcat_global_request_seconds_count{job="servico-pagamento"}[1m])',
    "tomcat_global_error_rate": 'rate(tomcat_global_error_total{job="servico-pagamento"}[1m])',
    
    # Métricas da JVM
    "jvm_threads_live": 'jvm_threads_live{job="servico-pagamento"}',
    "jvm_gc_collection_seconds": 'rate(jvm_gc_collection_seconds_sum{job="servico-pagamento"}[1m])',
    "jvm_memory_used_mb": 'jvm_memory_used_bytes{job="servico-pagamento"} / 1024 / 1024',
    
    # Métricas do Circuit Breaker
    "cb_state": 'resilience4j_circuitbreaker_state{name="adquirente-cb", job="servico-pagamento"}',
    "cb_calls_total": 'rate(resilience4j_circuitbreaker_calls_total{name="adquirente-cb"}[1m])',
    "cb_calls_failed_rate": 'rate(resilience4j_circuitbreaker_calls_total{name="adquirente-cb", kind="failed"}[1m])',
    "cb_calls_not_permitted_rate": 'rate(resilience4j_circuitbreaker_calls_total{name="adquirente-cb", kind="not_permitted"}[1m])',
    "cb_slow_calls_rate": 'rate(resilience4j_circuitbreaker_slow_calls_total{name="adquirente-cb"}[1m])',
    
    # Métricas HTTP
    "http_server_requests_rate": 'rate(http_server_requests_seconds_count{job="servico-pagamento"}[1m])',
    "http_server_errors_rate": 'rate(http_server_requests_seconds_count{job="servico-pagamento",status="5xx"}[1m])',
}

class ExperimentAnalyzer:
    def __init__(self):
        self.prom = PrometheusConnect(url=PROMETHEUS_URL)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(f"{OUTPUT_DIR}/plots", exist_ok=True)
        os.makedirs(f"{OUTPUT_DIR}/csv", exist_ok=True)
        self.all_metrics = {}
        self.k6_results = {}
        
    def load_k6_results(self):
        """Carrega todos os resultados do k6 em um dicionário estruturado"""
        results = {}
        for version in ["V1", "V2"]:
            results[version] = {}
            for scenario in ["Normal", "Latencia", "Falha"]:
                file_path = f"{RESULTS_DIR}/{version}_{scenario}.json"
                if os.path.exists(file_path):
                    metrics = {}
                    with open(file_path, 'r') as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                if data.get("type") == "Metric" and "data" in data:
                                    metric_name = data["data"]["name"]
                                    metrics[metric_name] = {
                                        "type": data["data"]["type"],
                                        "values": []
                                    }
                                elif data.get("metric") in metrics and data.get("type") == "Point":
                                    metrics[data["metric"]]["values"].append(data["data"])
                            except json.JSONDecodeError:
                                continue
                    results[version][scenario] = {"metrics": metrics}
        self.k6_results = results
        return results

    def fetch_prometheus_metrics(self, start_time: str, end_time: str):
        """Busca todas as métricas do Prometheus para o período especificado"""
        metrics = {}
        for metric_name, query in PROMQL_QUERIES.items():
            result = self.prom.custom_query_range(
                query=query,
                start_time=start_time,
                end_time=end_time,
                step='15s'
            )
            metrics[metric_name] = result
        return metrics

    def analyze_response_times(self):
        """Analisa os tempos de resposta dos testes do k6"""
        results = []
        for version in self.k6_results:
            for scenario in self.k6_results[version]:
                data = self.k6_results[version][scenario]
                metrics = data.get('metrics', {})
                
                # Extrair métricas relevantes
                http_req_duration_values = [v.get('value', 0) for v in metrics.get('http_req_duration', {}).get('values', [])]
                http_reqs_values = len([v for v in metrics.get('http_reqs', {}).get('values', []) if v.get('tags', {}).get('status') == '200'])
                http_failed_values = len([v for v in metrics.get('http_reqs', {}).get('values', []) if v.get('tags', {}).get('status') != '200'])
                
                total_requests = http_reqs_values + http_failed_values
                success_rate = (http_reqs_values / total_requests * 100) if total_requests > 0 else 0
                error_rate = (http_failed_values / total_requests * 100) if total_requests > 0 else 0
                
                result = {
                    'version': version,
                    'scenario': scenario,
                    'avg_response_time': np.mean(http_req_duration_values) if http_req_duration_values else 0,
                    'p95_response_time': np.percentile(http_req_duration_values, 95) if http_req_duration_values else 0,
                    'min_response_time': np.min(http_req_duration_values) if http_req_duration_values else 0,
                    'max_response_time': np.max(http_req_duration_values) if http_req_duration_values else 0,
                    'success_rate': success_rate,
                    'error_rate': error_rate
                }
                results.append(result)
        
        # Converter para DataFrame e salvar em CSV
        df = pd.DataFrame(results)
        df.to_csv(f"{OUTPUT_DIR}/csv/response_times_analysis.csv", index=False)
        return df

    def create_comparative_plots(self):
        """Cria gráficos comparativos entre V1 e V2"""
        response_times_df = self.analyze_response_times()
        
        # 1. Gráfico de barras comparativo de tempos de resposta
        plt.figure(figsize=(12, 6))
        x = np.arange(len(response_times_df['scenario'].unique()))
        width = 0.35
        
        v1_data = response_times_df[response_times_df['version'] == 'V1']['avg_response_time']
        v2_data = response_times_df[response_times_df['version'] == 'V2']['avg_response_time']
        
        plt.bar(x - width/2, v1_data, width, label='V1')
        plt.bar(x + width/2, v2_data, width, label='V2')
        
        plt.xlabel('Cenário')
        plt.ylabel('Tempo de Resposta Médio (ms)')
        plt.title('Comparação de Tempos de Resposta: V1 vs V2')
        plt.xticks(x, response_times_df['scenario'].unique())
        plt.legend()
        plt.savefig(f"{OUTPUT_DIR}/plots/response_times_comparison.png")
        plt.close()
        
        # 2. Gráfico de taxa de sucesso
        plt.figure(figsize=(12, 6))
        sns.barplot(data=response_times_df, x='scenario', y='success_rate', hue='version')
        plt.title('Taxa de Sucesso por Cenário')
        plt.savefig(f"{OUTPUT_DIR}/plots/success_rate_comparison.png")
        plt.close()

    def perform_statistical_analysis(self):
        """Realiza análise estatística dos resultados"""
        response_times_df = self.analyze_response_times()
        stats_results = []
        
        for scenario in response_times_df['scenario'].unique():
            v1_data = response_times_df[
                (response_times_df['version'] == 'V1') & 
                (response_times_df['scenario'] == scenario)
            ]['avg_response_time'].values
            
            v2_data = response_times_df[
                (response_times_df['version'] == 'V2') & 
                (response_times_df['scenario'] == scenario)
            ]['avg_response_time'].values
            
            if len(v1_data) > 0 and len(v2_data) > 0:
                # Realizar teste t de Student
                t_stat, p_value = stats.ttest_ind(v1_data, v2_data)
                
                # Calcular o tamanho do efeito (Cohen's d)
                cohens_d = (np.mean(v2_data) - np.mean(v1_data)) / np.sqrt(
                    (np.std(v1_data) ** 2 + np.std(v2_data) ** 2) / 2
                )
                
                stats_results.append({
                    'scenario': scenario,
                    'p_value': p_value,
                    'effect_size': cohens_d,
                    'significant_difference': p_value < 0.05
                })
        
        stats_df = pd.DataFrame(stats_results)
        stats_df.to_csv(f"{OUTPUT_DIR}/csv/statistical_analysis.csv", index=False)
        return stats_df

    def generate_html_report(self):
        """Gera um relatório HTML com todos os resultados"""
        response_times_df = self.analyze_response_times()
        stats_df = self.perform_statistical_analysis()
        
        # Template HTML básico
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Análise de Performance: Circuit Breaker</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f4f4f4; }
                .section { margin: 40px 0; }
                img { max-width: 100%; height: auto; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Relatório de Análise de Performance: Circuit Breaker</h1>
                
                <div class="section">
                    <h2>Resumo dos Tempos de Resposta</h2>
                    {{ response_times_table }}
                </div>
                
                <div class="section">
                    <h2>Análise Estatística</h2>
                    {{ stats_table }}
                </div>
                
                <div class="section">
                    <h2>Gráficos Comparativos</h2>
                    <img src="plots/response_times_comparison.png" alt="Comparação de Tempos de Resposta">
                    <img src="plots/success_rate_comparison.png" alt="Comparação de Taxa de Sucesso">
                </div>
                
                <div class="section">
                    <h2>Conclusões</h2>
                    <p>{{ conclusions }}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Gerar conclusões baseadas nos resultados
        conclusions = []
        for _, row in stats_df.iterrows():
            if row['significant_difference']:
                effect = "positivo" if row['effect_size'] > 0 else "negativo"
                magnitude = abs(row['effect_size'])
                if magnitude < 0.2:
                    effect_size = "pequeno"
                elif magnitude < 0.5:
                    effect_size = "médio"
                else:
                    effect_size = "grande"
                
                conclusions.append(
                    f"No cenário {row['scenario']}, houve uma diferença estatisticamente "
                    f"significativa entre V1 e V2 (p < 0.05), com um efeito {effect_size} {effect}."
                )
        
        # Renderizar o template
        template = Template(template_str)
        html_content = template.render(
            response_times_table=response_times_df.to_html(),
            stats_table=stats_df.to_html(),
            conclusions="<br>".join(conclusions)
        )
        
        # Salvar o relatório
        with open(f"{OUTPUT_DIR}/report.html", 'w') as f:
            f.write(html_content)

def main():
    analyzer = ExperimentAnalyzer()
    
    print("1. Carregando resultados do k6...")
    analyzer.load_k6_results()
    
    print("2. Analisando tempos de resposta...")
    analyzer.analyze_response_times()
    
    print("3. Criando gráficos comparativos...")
    analyzer.create_comparative_plots()
    
    print("4. Realizando análise estatística...")
    analyzer.perform_statistical_analysis()
    
    print("5. Gerando relatório HTML...")
    analyzer.generate_html_report()
    
    print(f"\nAnálise completa! Resultados salvos no diretório: {OUTPUT_DIR}")
    print("- CSV dos resultados: csv/")
    print("- Gráficos: plots/")
    print("- Relatório completo: report.html")

if __name__ == "__main__":
    main()