import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
from scipy import stats
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Import do loader otimizado
try:
    from fast_loader import FastK6Loader, fast_bootstrap_ci, fast_cliffs_delta
    USE_FAST_LOADER = True
except ImportError:
    USE_FAST_LOADER = False
    print("⚠️  fast_loader não encontrado. Usando carregamento padrão.")

# --- Configurações ---
RESULTS_DIR = "k6/results"
OUTPUT_DIR = "analysis_results"
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")
LATEX_DIR = os.path.join(OUTPUT_DIR, "latex")
MARKDOWN_DIR = os.path.join(OUTPUT_DIR, "markdown")

# --- Cores e Estilos para Gráficos ---
PALETTE = {"V1": "#d62728", "V2": "#2ca02c", "V3": "#1f77b4", "V4": "#ff7f0e"}
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
        self.latex_dir = os.path.join(output_dir, "latex")
        self.markdown_dir = os.path.join(output_dir, "markdown")
        self.data = {}
        self.response_times = {}  # Para análise estatística

        # Cria diretórios de saída se não existirem
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.latex_dir, exist_ok=True)
        os.makedirs(self.markdown_dir, exist_ok=True)

    def load_data(self, max_sample_size=500000, versions=None):
        """
        Carrega os dados dos arquivos de resultado do k6 (JSON) de forma eficiente.
        
        Args:
            max_sample_size: Número máximo de pontos a carregar por versão (default: 500k)
            versions: Lista de versões a carregar (default: V1, V2, V3, V4)
        """
        versions = versions or ["V1", "V2", "V3", "V4"]
        import gc
        
        start_time = time.time()
        print("\n" + "="*60)
        print("  CARREGAMENTO DE DADOS")
        print("="*60)
        
        if USE_FAST_LOADER:
            print("🚀 Usando FastK6Loader (otimizado)")
            loader = FastK6Loader(
                results_dir=self.results_dir,
                use_cache=True
            )
            self.data = loader.load_all_versions(
                max_sample_size=max_sample_size,
                versions=versions
            )
        else:
            print("⚠️  Usando carregamento padrão (mais lento)")
            self._load_data_legacy(max_sample_size, versions)
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  Tempo de carregamento: {elapsed:.2f}s")
        print("="*60 + "\n")
        
        gc.collect()
    
    def _load_data_legacy(self, max_sample_size=500000, versions=None):
        """
        Carregamento legado para fallback quando FastK6Loader não está disponível.
        """
        versions = versions or ["V1", "V2", "V3", "V4"]
        import random
        
        print("Carregando dados dos resultados do k6 (modo legado)...")
        for version in versions:
            file_path = os.path.join(self.results_dir, f"{version}_Completo.json")
            if os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  {version}: arquivo tem {file_size_mb:.1f} MB")
                
                use_sampling = file_size_mb > 100
                
                if use_sampling:
                    print(f"  {version}: usando amostragem (máx. {max_sample_size:,} pontos)...")
                    all_points = []
                    line_count = 0
                    
                    with open(file_path, 'r') as f:
                        for line in f:
                            if '"type":"Point"' in line:
                                line_count += 1
                                try:
                                    m = json.loads(line)
                                    point_data = m['data']
                                    point_data['metric'] = m['metric']
                                    
                                    if len(all_points) < max_sample_size:
                                        all_points.append(point_data)
                                    else:
                                        j = random.randint(0, line_count - 1)
                                        if j < max_sample_size:
                                            all_points[j] = point_data
                                except json.JSONDecodeError:
                                    continue
                    
                    print(f"  {version}: processadas {line_count:,} linhas, amostradas {len(all_points):,}")
                else:
                    all_points = []
                    with open(file_path, 'r') as f:
                        for line in f:
                            if '"type":"Point"' in line:
                                try:
                                    m = json.loads(line)
                                    point_data = m['data']
                                    point_data['metric'] = m['metric']
                                    all_points.append(point_data)
                                except json.JSONDecodeError:
                                    continue
                
                if all_points:
                    self.data[version] = pd.DataFrame(all_points)
                    print(f"Dados de {version} carregados com sucesso ({len(all_points):,} pontos).")
                else:
                    print(f"Aviso: Nenhum ponto de métrica encontrado para {version}")
            else:
                print(f"Aviso: Arquivo de resultado para {version} não encontrado")

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
        colors = [PALETTE.get(v, '#333333') for v in self.summary_df['Version'].tolist()]
        self.summary_df.plot(
            kind='bar',
            x='Version',
            y=['Avg Response Time (ms)', 'P95 Response Time (ms)'],
            color=colors,
            title="Tempo de Resposta: Comparacao de Versoes"
        )
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
                <h1>Relatório de Análise de Performance: V1, V2, V3 e V4</h1>
                
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

    def plot_timeline(self, window_size='5s'):
        """
        Gera gráficos de série temporal para análise do comportamento ao longo do teste.
        Permite identificar padrões de degradação, recuperação e transições do CB.
        
        Args:
            window_size: Janela de agregação para suavização (ex: '5s', '10s', '30s')
        """
        print(f"Gerando análise de séries temporais (janela: {window_size})...")
        
        for version, df in self.data.items():
            if 'time' not in df.columns:
                print(f"Aviso: Coluna 'time' não encontrada para {version}. Pulando série temporal.")
                continue
            
            # Converte timestamp para datetime
            df_timeline = df.copy()
            df_timeline['timestamp'] = pd.to_datetime(df_timeline['time'])
            df_timeline = df_timeline.set_index('timestamp')
            
            # Filtra apenas métricas de duração de requisição
            req_duration = df_timeline[df_timeline['metric'] == 'http_req_duration']
            
            if req_duration.empty:
                print(f"Aviso: Nenhuma métrica de duração encontrada para {version}.")
                continue
            
            # Armazena para análise estatística
            self.response_times[version] = req_duration['value'].values
            
            # Agrega por janela de tempo
            resampled = req_duration['value'].resample(window_size).agg(['mean', 'median', 'std', 'count'])
            resampled.columns = ['Média', 'Mediana', 'Desvio Padrão', 'Contagem']
            
            # Calcula percentis móveis
            resampled['P95'] = req_duration['value'].resample(window_size).quantile(0.95)
            resampled['P99'] = req_duration['value'].resample(window_size).quantile(0.99)
            
            # Plot 1: Tempo de resposta ao longo do tempo
            fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
            
            # Subplot 1: Média e Percentis
            ax1 = axes[0]
            ax1.plot(resampled.index, resampled['Média'], label='Média', color=PALETTE[version], linewidth=2)
            ax1.fill_between(resampled.index, 
                            resampled['Média'] - resampled['Desvio Padrão'],
                            resampled['Média'] + resampled['Desvio Padrão'],
                            alpha=0.3, color=PALETTE[version], label='±1 Desvio Padrão')
            ax1.plot(resampled.index, resampled['P95'], '--', label='P95', color='orange', linewidth=1.5)
            ax1.plot(resampled.index, resampled['P99'], ':', label='P99', color='red', linewidth=1.5)
            ax1.set_ylabel('Tempo de Resposta (ms)')
            ax1.set_title(f'{version} - Tempo de Resposta ao Longo do Teste')
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3)
            
            # Subplot 2: Throughput (requisições por janela)
            ax2 = axes[1]
            ax2.bar(resampled.index, resampled['Contagem'], width=pd.Timedelta(window_size)*0.8,
                   color=PALETTE[version], alpha=0.7, label='Requisições')
            ax2.set_ylabel('Requisições por Janela')
            ax2.set_title(f'{version} - Throughput')
            ax2.grid(True, alpha=0.3)
            
            # Subplot 3: Taxa de Sucesso por janela (se disponível)
            ax3 = axes[2]
            http_reqs = df_timeline[df_timeline['metric'] == 'http_reqs'].copy()
            if not http_reqs.empty and 'tags' in http_reqs.columns:
                http_reqs['status'] = http_reqs['tags'].apply(
                    lambda x: str(x.get('status')) if isinstance(x, dict) and x.get('status') else None
                )
                success_rate = http_reqs.groupby([pd.Grouper(freq=window_size), 'status'])['value'].sum().unstack(fill_value=0)
                
                if '200' in success_rate.columns:
                    total_per_window = success_rate.sum(axis=1)
                    success_pct = (success_rate.get('200', 0) / total_per_window * 100).fillna(0)
                    ax3.plot(success_pct.index, success_pct.values, color=PALETTE[version], linewidth=2)
                    ax3.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='SLA 95%')
                    ax3.axhline(y=99, color='blue', linestyle=':', alpha=0.5, label='SLA 99%')
                    ax3.fill_between(success_pct.index, success_pct.values, alpha=0.3, color=PALETTE[version])
            
            ax3.set_ylabel('Taxa de Sucesso (%)')
            ax3.set_xlabel('Tempo')
            ax3.set_title(f'{version} - Taxa de Sucesso')
            ax3.set_ylim(0, 105)
            ax3.legend(loc='lower right')
            ax3.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.plots_dir, f"timeline_{version}.png"), dpi=150)
            plt.close()
            
            # Salva dados da série temporal
            resampled.to_csv(os.path.join(self.csv_dir, f"timeline_{version}.csv"))
        
        # Gera plot comparativo V1 vs V2
        self._plot_comparative_timeline(window_size)
        
        print("Análise de séries temporais concluída.")

    def _plot_comparative_timeline(self, window_size='5s'):
        """
        Gera gráfico comparativo de V1 vs V2 ao longo do tempo.
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        for version, df in self.data.items():
            if 'time' not in df.columns:
                continue
            
            df_timeline = df.copy()
            df_timeline['timestamp'] = pd.to_datetime(df_timeline['time'])
            df_timeline = df_timeline.set_index('timestamp')
            
            req_duration = df_timeline[df_timeline['metric'] == 'http_req_duration']
            if req_duration.empty:
                continue
            
            resampled = req_duration['value'].resample(window_size).agg(['mean', 'median'])
            
            # Plot média
            axes[0].plot(resampled.index, resampled['mean'], label=f'{version} - Média', 
                        color=PALETTE[version], linewidth=2)
            axes[1].plot(resampled.index, resampled['median'], label=f'{version} - Mediana', 
                        color=PALETTE[version], linewidth=2)
        
        axes[0].set_ylabel('Tempo Médio (ms)')
        axes[0].set_title('Comparação V1 vs V2 - Tempo de Resposta Médio')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        axes[1].set_ylabel('Tempo Mediano (ms)')
        axes[1].set_xlabel('Tempo')
        axes[1].set_title('Comparação V1 vs V2 - Tempo de Resposta Mediano')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "timeline_comparison.png"), dpi=150)
        plt.close()

    def statistical_analysis(self):
        """
        Realiza análise estatística robusta incluindo:
        - Teste de Mann-Whitney U (diferença significativa entre V1 e V2)
        - Teste de Kolmogorov-Smirnov (diferença nas distribuições)
        - Effect Size (Cliff's Delta)
        - Intervalos de confiança bootstrap
        """
        print("Realizando análise estatística robusta...")
        
        # Garante que temos os dados de tempo de resposta
        if not self.response_times:
            for version, df in self.data.items():
                if 'time' in df.columns:
                    req_duration = df[df['metric'] == 'http_req_duration']
                    self.response_times[version] = req_duration['value'].values
        
        if 'V1' not in self.response_times or 'V2' not in self.response_times:
            print("Aviso: Dados insuficientes para análise estatística comparativa.")
            return
        
        v1_times = self.response_times['V1']
        v2_times = self.response_times['V2']
        
        # Teste de Mann-Whitney U (não paramétrico)
        statistic_mw, p_value_mw = stats.mannwhitneyu(v1_times, v2_times, alternative='two-sided')
        
        # Teste de Kolmogorov-Smirnov
        statistic_ks, p_value_ks = stats.ks_2samp(v1_times, v2_times)
        
        # Effect Size: Cliff's Delta
        cliffs_delta = self._cliffs_delta(v1_times, v2_times)
        
        # Bootstrap para intervalo de confiança da diferença de médias
        ci_low, ci_high = self._bootstrap_ci(v1_times, v2_times, n_bootstrap=10000)
        
        # Estatísticas descritivas
        stats_results = {
            'Métrica': [
                'N (V1)', 'N (V2)',
                'Média (V1)', 'Média (V2)',
                'Mediana (V1)', 'Mediana (V2)',
                'Desvio Padrão (V1)', 'Desvio Padrão (V2)',
                'P95 (V1)', 'P95 (V2)',
                'P99 (V1)', 'P99 (V2)',
                'Mann-Whitney U', 'p-valor (MW)',
                'Kolmogorov-Smirnov', 'p-valor (KS)',
                "Cliff's Delta", 'Interpretação Effect Size',
                'IC 95% Diferença (baixo)', 'IC 95% Diferença (alto)',
                'Diferença Significativa (α=0.05)'
            ],
            'Valor': [
                len(v1_times), len(v2_times),
                f'{np.mean(v1_times):.2f} ms', f'{np.mean(v2_times):.2f} ms',
                f'{np.median(v1_times):.2f} ms', f'{np.median(v2_times):.2f} ms',
                f'{np.std(v1_times):.2f} ms', f'{np.std(v2_times):.2f} ms',
                f'{np.percentile(v1_times, 95):.2f} ms', f'{np.percentile(v2_times, 95):.2f} ms',
                f'{np.percentile(v1_times, 99):.2f} ms', f'{np.percentile(v2_times, 99):.2f} ms',
                f'{statistic_mw:.2f}', f'{p_value_mw:.2e}',
                f'{statistic_ks:.4f}', f'{p_value_ks:.2e}',
                f'{cliffs_delta:.4f}', self._interpret_cliffs_delta(cliffs_delta),
                f'{ci_low:.2f} ms', f'{ci_high:.2f} ms',
                'Sim' if p_value_mw < 0.05 else 'Não'
            ]
        }
        
        self.stats_df = pd.DataFrame(stats_results)
        self.stats_df.to_csv(os.path.join(self.csv_dir, "statistical_analysis.csv"), index=False)
        
        # Gera visualização das distribuições
        self._plot_distributions(self.response_times)
        
        print(f"\n=== Resultados da Análise Estatística ===")
        print(f"Mann-Whitney U (V1 vs V2): {statistic_mw:.2f}, p-valor: {p_value_mw:.2e}")
        print(f"Cliff's Delta (V1 vs V2): {cliffs_delta:.4f} ({self._interpret_cliffs_delta(cliffs_delta)})")
        print(f"IC 95% da diferença de médias (V1 vs V2): [{ci_low:.2f}, {ci_high:.2f}] ms")
        print(f"Diferença estatisticamente significativa (V1 vs V2): {'Sim' if p_value_mw < 0.05 else 'Não'}")
        
        return self.stats_df

    def _cliffs_delta(self, x, y):
        """
        Calcula Cliff's Delta - medida de effect size não paramétrica.
        Usa versão vetorizada quando FastK6Loader está disponível.
        
        Valores: [-1, 1], onde:
        - |d| < 0.147: negligível
        - |d| < 0.33: pequeno
        - |d| < 0.474: médio
        - |d| >= 0.474: grande
        """
        if USE_FAST_LOADER:
            return fast_cliffs_delta(x, y)
        
        # Fallback para implementação legada
        n_x, n_y = len(x), len(y)
        more = np.sum([np.sum(xi > y) for xi in x])
        less = np.sum([np.sum(xi < y) for xi in x])
        return (more - less) / (n_x * n_y)

    def _interpret_cliffs_delta(self, d):
        """Interpreta o valor de Cliff's Delta."""
        abs_d = abs(d)
        if abs_d < 0.147:
            return "Negligível"
        elif abs_d < 0.33:
            return "Pequeno"
        elif abs_d < 0.474:
            return "Médio"
        else:
            return "Grande"

    def _bootstrap_ci(self, x, y, n_bootstrap=10000, ci=0.95):
        """
        Calcula intervalo de confiança bootstrap para a diferença de médias.
        Usa versão vetorizada quando FastK6Loader está disponível (~10x mais rápido).
        """
        if USE_FAST_LOADER:
            return fast_bootstrap_ci(x, y, n_bootstrap=n_bootstrap, ci=ci)
        
        # Fallback para implementação legada
        np.random.seed(42)
        diff_means = []
        for _ in range(n_bootstrap):
            x_sample = np.random.choice(x, size=len(x), replace=True)
            y_sample = np.random.choice(y, size=len(y), replace=True)
            diff_means.append(np.mean(x_sample) - np.mean(y_sample))
        
        alpha = 1 - ci
        lower = np.percentile(diff_means, alpha / 2 * 100)
        upper = np.percentile(diff_means, (1 - alpha / 2) * 100)
        return lower, upper

    def _plot_distributions(self, times_dict):
        """
        Gera visualizações das distribuições de tempo de resposta para todas as versões.
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        versions = sorted(times_dict.keys())
        
        # Histograma comparativo
        ax1 = axes[0, 0]
        for version in versions:
            ax1.hist(times_dict[version], bins=50, alpha=0.5, label=version, 
                    color=PALETTE.get(version, '#333'), density=True)
        ax1.set_xlabel('Tempo de Resposta (ms)')
        ax1.set_ylabel('Densidade')
        ax1.set_title('Distribuição de Tempos de Resposta')
        ax1.legend()
        
        # Box plot
        ax2 = axes[0, 1]
        data_bp = [times_dict[v] for v in versions]
        bp = ax2.boxplot(data_bp, labels=versions, patch_artist=True)
        for i, version in enumerate(versions):
            bp['boxes'][i].set_facecolor(PALETTE.get(version, '#333'))
            bp['boxes'][i].set_alpha(0.7)
        ax2.set_ylabel('Tempo de Resposta (ms)')
        ax2.set_title('Box Plot Comparativo')
        
        # Violin plot
        ax3 = axes[1, 0]
        positions = np.arange(1, len(versions) + 1)
        parts = ax3.violinplot(data_bp, positions=positions, showmeans=True, showmedians=True)
        for i, (version, pc) in enumerate(zip(versions, parts['bodies'])):
            pc.set_facecolor(PALETTE.get(version, '#333'))
            pc.set_alpha(0.7)
        ax3.set_xticks(positions)
        ax3.set_xticklabels(versions)
        ax3.set_ylabel('Tempo de Resposta (ms)')
        ax3.set_title('Violin Plot - Distribuição Completa')
        
        # ECDF
        ax4 = axes[1, 1]
        for version in versions:
            sorted_times = np.sort(times_dict[version])
            ax4.plot(sorted_times, np.arange(1, len(sorted_times)+1) / len(sorted_times), 
                    label=version, color=PALETTE.get(version, '#333'), linewidth=2)
        ax4.set_xlabel('Tempo de Resposta (ms)')
        ax4.set_ylabel('Proporção Cumulativa')
        ax4.set_title('ECDF - Distribuição Cumulativa Empírica')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "distributions.png"), dpi=150)
        plt.close()

    def export_latex(self):
        """
        Exporta tabelas e resultados para formato LaTeX para inclusão direta no TCC.
        """
        print("Exportando resultados para LaTeX...")
        
        # Tabela de resumo principal
        if hasattr(self, 'summary_df'):
            latex_summary = self.summary_df.to_latex(
                index=False,
                caption="Resumo das Métricas de Performance: V1 vs V2",
                label="tab:metricas-performance",
                column_format='l' + 'r' * (len(self.summary_df.columns) - 1),
                float_format="%.2f",
                escape=True
            )
            
            with open(os.path.join(self.latex_dir, "tabela_resumo.tex"), 'w') as f:
                f.write(latex_summary)
        
        # Tabela de análise estatística
        if hasattr(self, 'stats_df'):
            latex_stats = self.stats_df.to_latex(
                index=False,
                caption="Análise Estatística Comparativa entre V1 e V2",
                label="tab:analise-estatistica",
                column_format='lr',
                escape=True
            )
            
            with open(os.path.join(self.latex_dir, "tabela_estatistica.tex"), 'w') as f:
                f.write(latex_stats)
        
        # Gera arquivo .tex com figuras
        figures_tex = r"""
% Figuras geradas automaticamente pelo analyzer.py
% Inclua este arquivo no seu documento LaTeX com \input{figuras_analise.tex}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{analysis_results/plots/response_times.png}
    \caption{Comparação de Tempo de Resposta entre V1 (sem Circuit Breaker) e V2 (com Circuit Breaker).}
    \label{fig:response-times}
\end{figure}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{analysis_results/plots/success_failure_rate.png}
    \caption{Composição das Respostas: Taxa de Sucesso, Fallback e Falha para cada versão.}
    \label{fig:success-failure-rate}
\end{figure}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{analysis_results/plots/timeline_comparison.png}
    \caption{Evolução temporal do tempo de resposta durante o teste de carga.}
    \label{fig:timeline-comparison}
\end{figure}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{analysis_results/plots/distributions.png}
    \caption{Distribuições estatísticas dos tempos de resposta: (a) Histograma, (b) Box Plot, (c) Violin Plot, (d) ECDF.}
    \label{fig:distributions}
\end{figure}
"""
        with open(os.path.join(self.latex_dir, "figuras_analise.tex"), 'w') as f:
            f.write(figures_tex)
        
        # Gera resumo em Markdown também
        self._export_markdown()
        
        print(f"Arquivos LaTeX exportados para: {self.latex_dir}")

    def _export_markdown(self):
        """
        Exporta resultados para Markdown para documentação.
        """
        md_content = f"""# Análise de Performance: V1 vs V2

Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumo das Métricas

"""
        if hasattr(self, 'summary_df'):
            md_content += self.summary_df.to_markdown(index=False)
            md_content += "\n\n"
        
        md_content += "## Análise Estatística\n\n"
        
        if hasattr(self, 'stats_df'):
            md_content += self.stats_df.to_markdown(index=False)
            md_content += "\n\n"
        
        md_content += """## Gráficos Gerados

- `plots/response_times.png`: Tempo de resposta médio e P95
- `plots/success_failure_rate.png`: Composição das respostas
- `plots/timeline_V1.png` / `timeline_V2.png`: Séries temporais por versão
- `plots/timeline_comparison.png`: Comparação temporal V1 vs V2
- `plots/distributions.png`: Análise de distribuições

## Interpretação

### Significância Estatística
- **Mann-Whitney U Test**: Teste não paramétrico para comparar as distribuições
- **Cliff's Delta**: Medida de effect size (magnitude da diferença)
- **Bootstrap CI**: Intervalo de confiança para a diferença de médias

### Thresholds de Cliff's Delta
| Valor |d| | Interpretação |
|---------|---------------|
| < 0.147 | Negligível    |
| < 0.33  | Pequeno       |
| < 0.474 | Médio         |
| ≥ 0.474 | Grande        |
"""
        
        with open(os.path.join(self.markdown_dir, "analise_resultados.md"), 'w') as f:
            f.write(md_content)

    def run_analysis(self, include_timeline=True, include_stats=True, export_latex=True):
        """
        Executa o pipeline completo de análise.
        
        Args:
            include_timeline: Se True, gera análise de séries temporais
            include_stats: Se True, realiza análise estatística robusta
            export_latex: Se True, exporta resultados para LaTeX
        """
        self.load_data()
        if not self.data:
            print("Nenhum dado foi carregado. Abortando a análise.")
            return
        self.process_data()
        self.generate_plots()
        
        if include_timeline:
            self.plot_timeline(window_size='5s')
        
        if include_stats:
            self.statistical_analysis()
        
        self.generate_html_report()
        
        if export_latex:
            self.export_latex()
        
        print("\nAnálise concluída com sucesso!")

if __name__ == "__main__":
    analyzer = K6Analyzer(results_dir=RESULTS_DIR, output_dir=OUTPUT_DIR)
    analyzer.run_analysis()
