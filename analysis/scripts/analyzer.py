import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import warnings

warnings.filterwarnings('ignore')

# --- Configurações ---
RESULTS_DIR = "k6/results"
OUTPUT_DIR = "analysis_results"
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")

# --- Cores e Estilos para Gráficos ---
PALETTE = {"V1": "#d62728", "V2": "#2ca02c"}
sns.set_style("whitegrid")

class K6Analyzer:
    """
    Analisa os resultados de testes de carga do k6, gera gráficos e um relatório HTML.
    """
    def __init__(self, results_dir, output_dir):
        self.results_dir = results_dir
        self.output_dir = output_dir
        self.plots_dir = os.path.join(output_dir, "plots")
        self.csv_dir = os.path.join(output_dir, "csv")
        self.data = {}

        # Cria diretórios de saída se não existirem
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)

    def load_data(self):
        """
        Carrega os dados dos arquivos de resultado do k6 (JSON).
        """
        print("Carregando dados dos resultados do k6...")
        for version in ["V1", "V2"]:
            file_path = os.path.join(self.results_dir, f"{version}_Completo.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    # Processa cada linha do JSONL, combinando 'data' e 'metric'
                    all_points = []
                    for line in f:
                        if '"type":"Point"' in line:
                            m = json.loads(line)
                            point_data = m['data']
                            point_data['metric'] = m['metric']
                            all_points.append(point_data)
                
                if all_points:
                    self.data[version] = pd.DataFrame(all_points)
                    print(f"Dados de {version} carregados com sucesso.")
                else:
                    print(f"Aviso: Nenhum ponto de métrica encontrado para {version} em {file_path}")
            else:
                print(f"Aviso: Arquivo de resultado para {version} não encontrado em {file_path}")

    def process_data(self):
        """
        Processa os dados brutos para extrair e calcular métricas chave,
        diferenciando sucesso, fallback e falha.
        
        V1: Não tem Circuit Breaker
            - 200: Sucesso
            - 5xx: Falhas diretas da API
        
        V2: Com Circuit Breaker
            - 200: Sucesso
            - 500: Falha da API (aciona fallback, conta para abrir CB)
            - 503: Circuit Breaker aberto
            - 202: Contingência (não usado neste cenário)
        """
        print("Processando e agregando dados...")
        processed_data = []
        for version, df in self.data.items():
            if 'tags' not in df.columns:
                print(f"Aviso: Coluna 'tags' não encontrada para a versão {version}. Pulando.")
                continue

            # Normaliza o status para string para evitar comparações problemáticas
            df['status'] = df['tags'].apply(lambda x: str(x.get('status')) if isinstance(x, dict) and x.get('status') is not None else None)

            req_duration_df = df[df['metric'] == 'http_req_duration']
            http_reqs_df = df[df['metric'] == 'http_reqs']
            
            # Contagem por código de status
            success_count = http_reqs_df[http_reqs_df['status'] == '200']['value'].sum()
            fallback_count = http_reqs_df[http_reqs_df['status'] == '202']['value'].sum()
            cb_open_count = http_reqs_df[http_reqs_df['status'] == '503']['value'].sum()
            
            # Falhas da API (status 500)
            # V1: Todas as falhas 5xx são falhas diretas (não tem CB)
            # V2: Status 500 = falha que aciona fallback e conta para abrir CB
            #     Status 503 = CB já está aberto (contabilizado separadamente)
            failure_count = http_reqs_df[http_reqs_df['status'] == '500']['value'].sum()

            # Total real de requisições registrado pelo http_reqs (evita omitir códigos inesperados)
            total_requests = http_reqs_df['value'].sum()
            
            # Debug: mostrar contagens brutas
            print(f"\n{version} - Contagens brutas:")
            print(f"  Status 200 (Sucesso): {success_count}")
            print(f"  Status 500 (Falha API): {failure_count}")
            print(f"  Status 503 (CB Aberto): {cb_open_count}")
            print(f"  Status 202 (Contingência): {fallback_count}")
            print(f"  Total: {total_requests}")

            summary = {
                "Version": version,
                "Total Requests": total_requests,
                "Avg Response Time (ms)": req_duration_df['value'].mean(),
                "P95 Response Time (ms)": req_duration_df['value'].quantile(0.95),
                "Success Rate (%)": (success_count / total_requests) * 100 if total_requests > 0 else 0,
                "Fallback Rate (%)": (fallback_count / total_requests) * 100 if total_requests > 0 else 0,
                "Circuit Breaker Open Rate (%)": (cb_open_count / total_requests) * 100 if total_requests > 0 else 0,
                "API Failure Rate (%)": (failure_count / total_requests) * 100 if total_requests > 0 else 0,
            }
            processed_data.append(summary)
            
        self.summary_df = pd.DataFrame(processed_data)
        self.summary_df.to_csv(os.path.join(self.csv_dir, "summary_analysis.csv"), index=False)
        print("Dados processados e salvos em CSV.")
        print(f"\nResumo das contagens:")
        for idx, row in self.summary_df.iterrows():
            print(f"\n{row['Version']}:")
            print(f"  - Total: {row['Total Requests']:.0f}")
            print(f"  - Sucesso (200): {row['Success Rate (%)']:.2f}%")
            print(f"  - Falhas API (500): {row['API Failure Rate (%)']:.2f}%")
            print(f"  - CB Aberto (503): {row['Circuit Breaker Open Rate (%)']:.2f}%")
            print(f"  - Contingência (202): {row['Fallback Rate (%)']:.2f}%")

    def generate_plots(self):
        """
        Gera gráficos comparativos a partir dos dados processados.
        """
        print("Gerando gráficos comparativos...")

        # Gráfico 1: Tempo de Resposta (Médio e P95)
        plt.figure(figsize=(12, 7))
        self.summary_df.plot(kind='bar', x='Version', y=['Avg Response Time (ms)', 'P95 Response Time (ms)'],
                               color=[PALETTE['V1'], PALETTE['V2']],
                               title="Tempo de Resposta: V1 vs V2")
        plt.ylabel("Tempo (ms)")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "response_times.png"))
        plt.close()

        # Gráfico 2: Taxa de Sucesso vs Falha vs Fallback
        plt.figure(figsize=(12, 7))
        plot_df = self.summary_df.set_index('Version')[['Success Rate (%)', 'Fallback Rate (%)', 'Circuit Breaker Open Rate (%)', 'API Failure Rate (%)']]
        plot_df.plot(
            kind='bar', 
            stacked=True, 
            color={
                "Success Rate (%)": "#2ca02c", 
                "Fallback Rate (%)": "#ff7f0e", 
                "Circuit Breaker Open Rate (%)": "#f0f000", # Amarelo para CB Aberto
                "API Failure Rate (%)": "#d62728"
            },
            title="Composição das Respostas: Sucesso, Fallback e Falha"
        )
        plt.ylabel("Percentual (%)")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "success_failure_rate.png"))
        plt.close()
        
        print("Gráficos gerados com sucesso.")

    def generate_html_report(self):
        """
        Gera um relatório HTML consolidado com os resultados e gráficos.
        """
        print("Gerando relatório HTML...")
        template_str = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Análise de Performance</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f9f9f9; color: #333; }
                .container { max-width: 1200px; margin: 0 auto; background-color: #fff; padding: 30px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
                h1, h2 { color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }
                table { border-collapse: collapse; width: 100%; margin: 25px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #007bff; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .section { margin: 40px 0; }
                img { max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Relatório de Análise de Performance: V1 vs V2</h1>
                
                <div class="section">
                    <h2>Resumo das Métricas</h2>
                    <p>Esta tabela resume as principais métricas de performance para cada versão do serviço.</p>
                    {{ summary_table }}
                </div>
                
                <div class="section">
                    <h2>Gráficos Comparativos</h2>
                    <h3>Tempo de Resposta (Médio e P95)</h3>
                    <img src="plots/response_times.png" alt="Gráfico de Tempo de Resposta">
                    
                    <h3>Composição das Respostas: Sucesso, Fallback e Falha</h3>
                    <img src="plots/success_failure_rate.png" alt="Gráfico de Composição das Respostas">
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        html_content = template.render(
            summary_table=self.summary_df.to_html(index=False, classes='table table-striped')
        )
        
        report_path = os.path.join(self.output_dir, "analysis_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Relatório HTML gerado em: {report_path}")

    def run_analysis(self):
        """
        Executa o pipeline completo de análise.
        """
        self.load_data()
        if not self.data:
            print("Nenhum dado foi carregado. Abortando a análise.")
            return
        self.process_data()
        self.generate_plots()
        self.generate_html_report()
        print("\nAnálise concluída com sucesso!")

if __name__ == "__main__":
    analyzer = K6Analyzer(results_dir=RESULTS_DIR, output_dir=OUTPUT_DIR)
    analyzer.run_analysis()
