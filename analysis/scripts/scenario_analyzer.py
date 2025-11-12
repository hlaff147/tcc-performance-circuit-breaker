#!/usr/bin/env python3
"""
Analisador específico para os cenários críticos que demonstram
as vantagens do Circuit Breaker.

Gera relatórios comparativos detalhados mostrando:
1. Tempo de resposta durante falhas (V1 vs V2)
2. Taxa de proteção do CB (% de requests que evitaram timeout)
3. Análise por fase do teste
4. Cálculo do ganho real do Circuit Breaker
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import numpy as np
import warnings

warnings.filterwarnings('ignore')

RESULTS_DIR = "k6/results/scenarios"
OUTPUT_DIR = "analysis_results/scenarios"
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")

PALETTE = {"V1": "#d62728", "V2": "#2ca02c"}
sns.set_style("whitegrid")

class ScenarioAnalyzer:
    """Analisa cenários críticos comparando V1 vs V2"""
    
    def __init__(self, scenario_name, results_dir, output_dir):
        self.scenario_name = scenario_name
        self.results_dir = results_dir
        self.output_dir = output_dir
        self.plots_dir = os.path.join(output_dir, "plots", scenario_name)
        self.csv_dir = os.path.join(output_dir, "csv")
        
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
        
        self.data = {}
        
    def load_data(self):
        """Carrega dados do cenário"""
        print(f"\n📂 Carregando dados do cenário: {self.scenario_name}")
        
        for version in ["V1", "V2"]:
            file_path = os.path.join(self.results_dir, f"{self.scenario_name}_{version}.json")
            
            if os.path.exists(file_path):
                all_points = []
                with open(file_path, 'r') as f:
                    for line in f:
                        if '"type":"Point"' in line:
                            m = json.loads(line)
                            point_data = m['data']
                            point_data['metric'] = m['metric']
                            all_points.append(point_data)
                
                if all_points:
                    self.data[version] = pd.DataFrame(all_points)
                    print(f"  ✅ {version}: {len(all_points)} pontos carregados")
                else:
                    print(f"  ⚠️  {version}: Nenhum ponto encontrado")
            else:
                print(f"  ❌ {version}: Arquivo não encontrado")
    
    def analyze_response_times(self):
        """Analisa tempos de resposta com foco em períodos de falha"""
        print(f"\n📊 Analisando tempos de resposta...")
        
        results = []
        
        for version, df in self.data.items():
            req_duration = df[df['metric'] == 'http_req_duration']['value']
            
            if len(req_duration) == 0:
                continue
            
            # Estatísticas gerais
            avg_response = req_duration.mean()
            p50_response = req_duration.quantile(0.50)
            p95_response = req_duration.quantile(0.95)
            p99_response = req_duration.quantile(0.99)
            max_response = req_duration.max()
            
            # Conta requisições rápidas (< 500ms) e lentas (> 2000ms)
            fast_requests = (req_duration < 500).sum()
            slow_requests = (req_duration > 2000).sum()
            total = len(req_duration)
            
            results.append({
                'Version': version,
                'Avg Response (ms)': avg_response,
                'P50 (ms)': p50_response,
                'P95 (ms)': p95_response,
                'P99 (ms)': p99_response,
                'Max (ms)': max_response,
                'Fast Requests (%)': (fast_requests / total) * 100,
                'Slow Requests (%)': (slow_requests / total) * 100,
            })
        
        self.response_df = pd.DataFrame(results)
        return self.response_df
    
    def analyze_status_codes(self):
        """Analisa distribuição de códigos de status"""
        print(f"\n🔍 Analisando códigos de status...")
        
        results = []
        
        for version, df in self.data.items():
            df['status'] = df['tags'].apply(
                lambda x: str(x.get('status')) if isinstance(x, dict) and x.get('status') is not None else None
            )
            
            http_reqs = df[df['metric'] == 'http_reqs']
            
            success = http_reqs[http_reqs['status'] == '200']['value'].sum()
            api_fail = http_reqs[http_reqs['status'] == '500']['value'].sum()
            cb_open = http_reqs[http_reqs['status'] == '503']['value'].sum()
            fallback = http_reqs[http_reqs['status'] == '202']['value'].sum()
            total = http_reqs['value'].sum()
            
            # Sucesso total = 200 + 202 (fallback também é considerado aceito)
            total_success = success + fallback
            
            results.append({
                'Version': version,
                'Total Requests': total,
                'Success (200)': success,
                'API Failure (500)': api_fail,
                'CB Open (503)': cb_open,
                'Fallback (202)': fallback,
                'Success Rate (%)': (success / total) * 100 if total > 0 else 0,
                'Total Success Rate (%)': (total_success / total) * 100 if total > 0 else 0,
                'API Failure Rate (%)': (api_fail / total) * 100 if total > 0 else 0,
                'CB Protection Rate (%)': (cb_open / total) * 100 if total > 0 else 0,
                'Fallback Rate (%)': (fallback / total) * 100 if total > 0 else 0,
            })
        
        self.status_df = pd.DataFrame(results)
        return self.status_df
    
    def calculate_cb_benefit(self):
        """Calcula o benefício real do Circuit Breaker"""
        print(f"\n💡 Calculando benefícios do Circuit Breaker...")
        
        if 'V1' not in self.data or 'V2' not in self.data:
            print("  ⚠️  Dados insuficientes para calcular benefícios")
            return None
        
        v1_resp = self.response_df[self.response_df['Version'] == 'V1'].iloc[0]
        v2_resp = self.response_df[self.response_df['Version'] == 'V2'].iloc[0]
        
        v1_status = self.status_df[self.status_df['Version'] == 'V1'].iloc[0]
        v2_status = self.status_df[self.status_df['Version'] == 'V2'].iloc[0]
        
        # Cálculos de benefício
        response_improvement = ((v1_resp['Avg Response (ms)'] - v2_resp['Avg Response (ms)']) / 
                               v1_resp['Avg Response (ms)']) * 100
        
        p95_improvement = ((v1_resp['P95 (ms)'] - v2_resp['P95 (ms)']) / 
                          v1_resp['P95 (ms)']) * 100
        
        p99_improvement = ((v1_resp['P99 (ms)'] - v2_resp['P99 (ms)']) / 
                          v1_resp['P99 (ms)']) * 100
        
        # Requests protegidas pelo CB (503) que teriam falhado com timeout em V1
        protected_requests = v2_status['CB Open (503)']
        
        # NOVA MÉTRICA: Redução de falhas reais (500)
        v1_failure_rate = v2_status['API Failure Rate (%)']
        v2_failure_rate = v2_status['API Failure Rate (%)']
        failure_reduction = ((v1_status['API Failure Rate (%)'] - v2_status['API Failure Rate (%)']) / 
                            v1_status['API Failure Rate (%)']) * 100 if v1_status['API Failure Rate (%)'] > 0 else 0
        
        # Estimativa de tempo economizado
        # Assume que CB responde em ~50ms vs timeout de ~2500ms
        time_saved_per_req = 2500 - 50  # ms
        total_time_saved = (protected_requests * time_saved_per_req) / 1000  # segundos
        
        benefits = {
            'Scenario': self.scenario_name,
            'Response Time Improvement (%)': response_improvement,
            'P95 Improvement (%)': p95_improvement,
            'P99 Improvement (%)': p99_improvement,
            'Protected Requests': protected_requests,
            'Total Time Saved (s)': total_time_saved,
            'Failure Reduction (%)': failure_reduction,
            'V1 Failure Rate (%)': v1_status['API Failure Rate (%)'],
            'V2 Failure Rate (%)': v2_status['API Failure Rate (%)'],
            'Fast Response Increase (%)': v2_resp['Fast Requests (%)'] - v1_resp['Fast Requests (%)'],
            'Slow Response Decrease (%)': v1_resp['Slow Requests (%)'] - v2_resp['Slow Requests (%)'],
        }
        
        self.benefits = pd.DataFrame([benefits])
        
        print(f"\n  📈 Redução de falhas: {failure_reduction:.2f}%")
        print(f"  📈 Melhoria no tempo médio: {response_improvement:.2f}%")
        print(f"  📈 Melhoria no P95: {p95_improvement:.2f}%")
        print(f"  📈 Melhoria no P99: {p99_improvement:.2f}%")
        print(f"  🛡️  Requests protegidas: {protected_requests:.0f}")
        print(f"  ⏱️  Tempo economizado: {total_time_saved:.2f}s")
        
        return benefits
    
    def generate_plots(self):
        """Gera gráficos comparativos"""
        print(f"\n🎨 Gerando gráficos...")
        
        # 1. Comparação de tempos de resposta
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Percentis
        metrics = ['P50 (ms)', 'P95 (ms)', 'P99 (ms)']
        x = np.arange(len(metrics))
        width = 0.35
        
        v1_values = [self.response_df[self.response_df['Version'] == 'V1'][m].values[0] for m in metrics]
        v2_values = [self.response_df[self.response_df['Version'] == 'V2'][m].values[0] for m in metrics]
        
        axes[0].bar(x - width/2, v1_values, width, label='V1', color=PALETTE['V1'])
        axes[0].bar(x + width/2, v2_values, width, label='V2', color=PALETTE['V2'])
        axes[0].set_xlabel('Percentil')
        axes[0].set_ylabel('Tempo (ms)')
        axes[0].set_title('Comparação de Latência (P50, P95, P99)')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(metrics)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Distribuição de velocidade
        versions = ['V1', 'V2']
        fast = [self.response_df[self.response_df['Version'] == v]['Fast Requests (%)'].values[0] for v in versions]
        slow = [self.response_df[self.response_df['Version'] == v]['Slow Requests (%)'].values[0] for v in versions]
        
        x2 = np.arange(len(versions))
        axes[1].bar(x2, fast, 0.6, label='Rápidas (< 500ms)', color='#2ca02c')
        axes[1].bar(x2, slow, 0.6, bottom=fast, label='Lentas (> 2s)', color='#d62728')
        axes[1].set_ylabel('Percentual (%)')
        axes[1].set_title('Distribuição de Velocidade de Resposta')
        axes[1].set_xticks(x2)
        axes[1].set_xticklabels(versions)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, 'response_comparison.png'), dpi=150)
        plt.close()
        
        # 2. Status codes
        fig, ax = plt.subplots(figsize=(12, 6))
        
        status_data = self.status_df.set_index('Version')[
            ['Success Rate (%)', 'API Failure Rate (%)', 'CB Protection Rate (%)']
        ]
        
        status_data.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            color={
                'Success Rate (%)': '#2ca02c',
                'API Failure Rate (%)': '#d62728',
                'CB Protection Rate (%)': '#ff7f0e',
            }
        )
        ax.set_ylabel('Percentual (%)')
        ax.set_title(f'Distribuição de Respostas - {self.scenario_name.upper()}')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, 'status_distribution.png'), dpi=150)
        plt.close()
        
        print(f"  ✅ Gráficos salvos em {self.plots_dir}")
    
    def generate_report(self):
        """Gera relatório HTML"""
        print(f"\n📄 Gerando relatório HTML...")
        
        template_str = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Análise: {{ scenario_name }}</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 40px; 
                    background-color: #f5f5f5; 
                    color: #333; 
                }
                .container { 
                    max-width: 1400px; 
                    margin: 0 auto; 
                    background-color: #fff; 
                    padding: 40px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    border-radius: 8px;
                }
                h1 { 
                    color: #2c3e50; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 15px; 
                }
                h2 { 
                    color: #34495e; 
                    margin-top: 40px;
                    border-bottom: 2px solid #ecf0f1;
                    padding-bottom: 10px;
                }
                table { 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 25px 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                th, td { 
                    border: 1px solid #ddd; 
                    padding: 12px; 
                    text-align: left; 
                }
                th { 
                    background-color: #3498db; 
                    color: white; 
                    font-weight: 600;
                }
                tr:nth-child(even) { background-color: #f9f9f9; }
                tr:hover { background-color: #f5f5f5; }
                img { 
                    max-width: 100%; 
                    height: auto; 
                    margin: 20px 0;
                    border-radius: 5px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .metric-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .metric-card h3 {
                    margin: 0 0 10px 0;
                    color: white;
                }
                .improvement {
                    color: #27ae60;
                    font-weight: bold;
                }
                .degradation {
                    color: #e74c3c;
                    font-weight: bold;
                }
                .info-box {
                    background-color: #e8f4f8;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .warning-box {
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .success-box {
                    background-color: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Análise Detalhada: {{ scenario_name.upper() }}</h1>
                
                {% if scenario_name == 'catastrofe' %}
                <div class="info-box">
                    <h4>📌 Contexto do Cenário: Falha Catastrófica</h4>
                    <p><strong>Situação:</strong> API externa completamente indisponível por 5 minutos (100% de falhas).</p>
                    <p><strong>Objetivo do CB:</strong> Detectar a indisponibilidade e evitar sobrecarga, retornando respostas rápidas.</p>
                    <p><strong>Métrica chave:</strong> Taxa de sucesso e redução de falhas reais (500).</p>
                </div>
                {% elif scenario_name == 'degradacao' %}
                <div class="warning-box">
                    <h4>📌 Contexto do Cenário: Degradação Gradual</h4>
                    <p><strong>Situação:</strong> API externa degrada progressivamente (5% → 20% → 50% de falhas).</p>
                    <p><strong>Objetivo do CB:</strong> Detectar degradação precocemente e proteger contra sobrecarga.</p>
                    <p><strong>Interpretação correta:</strong> CB bloqueou {{  "%.1f"|format(benefits.get('Protected Requests', 0) / status_df[status_df['Version'] == 'V2']['Total Requests'].values[0] * 100) }}% das requests para <strong>evitar falhas</strong>. V2 reduziu falhas reais em {{ "%.1f"|format(benefits.get('Failure Reduction (%)', 0)) }}%.</p>
                </div>
                {% elif scenario_name == 'rajadas' %}
                <div class="warning-box">
                    <h4>📌 Contexto do Cenário: Rajadas Intermitentes</h4>
                    <p><strong>Situação:</strong> 3 períodos de falha total (100%) alternados com operação normal.</p>
                    <p><strong>Objetivo do CB:</strong> Abrir/fechar rapidamente em resposta às rajadas, protegendo em cada crise.</p>
                    <p><strong>Interpretação correta:</strong> CB bloqueou {{ "%.1f"|format(benefits.get('Protected Requests', 0) / status_df[status_df['Version'] == 'V2']['Total Requests'].values[0] * 100) }}% das requests nas rajadas para <strong>evitar timeouts de 3s</strong>. V2 reduziu falhas reais em {{ "%.1f"|format(benefits.get('Failure Reduction (%)', 0)) }}%.</p>
                </div>
                {% endif %}
                
                {% if benefits %}
                <div class="metric-card">
                    <h3>💎 BENEFÍCIOS DO CIRCUIT BREAKER</h3>
                    <ul>
                        <li><strong>Redução de Falhas (500):</strong> 
                            <span class="improvement">
                                {{ "%.2f"|format(benefits.get('Failure Reduction (%)', 0)) }}%
                            </span>
                        </li>
                        <li><strong>Melhoria no tempo médio:</strong> 
                            <span class="{% if benefits['Response Time Improvement (%)'] > 0 %}improvement{% else %}degradation{% endif %}">
                                {{ "%.2f"|format(benefits['Response Time Improvement (%)']) }}%
                            </span>
                        </li>
                        <li><strong>Melhoria no P95:</strong> 
                            <span class="{% if benefits['P95 Improvement (%)'] > 0 %}improvement{% else %}degradation{% endif %}">
                                {{ "%.2f"|format(benefits['P95 Improvement (%)']) }}%
                            </span>
                        </li>
                        <li><strong>Melhoria no P99:</strong> 
                            <span class="{% if benefits['P99 Improvement (%)'] > 0 %}improvement{% else %}degradation{% endif %}">
                                {{ "%.2f"|format(benefits['P99 Improvement (%)']) }}%
                            </span>
                        </li>
                        <li><strong>Requisições protegidas:</strong> {{ "%.0f"|format(benefits['Protected Requests']) }}</li>
                        <li><strong>Tempo total economizado:</strong> {{ "%.2f"|format(benefits['Total Time Saved (s)']) }}s</li>
                    </ul>
                </div>
                {% endif %}
                
                <h2>📊 Tempos de Resposta</h2>
                {{ response_table }}
                
                <h2>🔍 Distribuição de Status</h2>
                {{ status_table }}
                
                {% if scenario_name in ['degradacao', 'rajadas'] %}
                <div class="success-box">
                    <h4>✅ Por que a "baixa taxa de sucesso" do V2 é na verdade um SUCESSO?</h4>
                    <p><strong>V1 sem CB:</strong> Taxa de sucesso {{ "%.1f"|format(status_df[status_df['Version'] == 'V1']['Success Rate (%)'].values[0]) }}%, mas com {{ "%.1f"|format(status_df[status_df['Version'] == 'V1']['API Failure Rate (%)'].values[0]) }}% de falhas reais (500) e tempo médio de {{ "%.0f"|format(response_df[response_df['Version'] == 'V1']['Avg Response (ms)'].values[0]) }}ms (esperando timeouts).</p>
                    <p><strong>V2 com CB:</strong> Taxa de sucesso {{ "%.1f"|format(status_df[status_df['Version'] == 'V2']['Success Rate (%)'].values[0]) }}%, mas com apenas {{ "%.1f"|format(status_df[status_df['Version'] == 'V2']['API Failure Rate (%)'].values[0]) }}% de falhas reais (500) e tempo médio de {{ "%.0f"|format(response_df[response_df['Version'] == 'V2']['Avg Response (ms)'].values[0]) }}ms.</p>
                    <p><strong>Conclusão:</strong> CB bloqueou {{ "%.1f"|format(status_df[status_df['Version'] == 'V2']['CB Protection Rate (%)'].values[0]) }}% das requests (503) para <strong>proteger contra sobrecarga</strong> e <strong>evitar timeouts de 3 segundos</strong>. O resultado é <strong>{{ "%.1f"|format(benefits.get('Failure Reduction (%)', 0)) }}% menos falhas reais</strong> e <strong>{{ "%.1f"|format(benefits.get('Response Time Improvement (%)', 0)) }}% de melhoria no tempo de resposta</strong>!</p>
                </div>
                {% endif %}
                
                <h2>📈 Gráficos Comparativos</h2>
                <img src="plots/{{ scenario_name }}/response_comparison.png" alt="Comparação de Latência">
                <img src="plots/{{ scenario_name }}/status_distribution.png" alt="Distribuição de Status">
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        html_content = template.render(
            scenario_name=self.scenario_name,
            response_table=self.response_df.to_html(index=False, classes='table'),
            status_table=self.status_df.to_html(index=False, classes='table'),
            response_df=self.response_df,
            status_df=self.status_df,
            benefits=self.benefits.iloc[0].to_dict() if self.benefits is not None and len(self.benefits) > 0 else None
        )
        
        report_path = os.path.join(self.output_dir, f"{self.scenario_name}_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  ✅ Relatório salvo em {report_path}")
    
    def run_analysis(self):
        """Executa análise completa"""
        self.load_data()
        
        if not self.data:
            print("  ❌ Nenhum dado carregado. Abortando.")
            return
        
        self.analyze_response_times()
        self.analyze_status_codes()
        self.calculate_cb_benefit()
        self.generate_plots()
        self.generate_report()
        
        # Salva CSVs
        self.response_df.to_csv(
            os.path.join(self.csv_dir, f"{self.scenario_name}_response.csv"), 
            index=False
        )
        self.status_df.to_csv(
            os.path.join(self.csv_dir, f"{self.scenario_name}_status.csv"), 
            index=False
        )
        if self.benefits is not None:
            self.benefits.to_csv(
                os.path.join(self.csv_dir, f"{self.scenario_name}_benefits.csv"), 
                index=False
            )
        
        print(f"\n✅ Análise de {self.scenario_name} concluída!")


if __name__ == "__main__":
    import sys
    
    scenarios = ["catastrofe", "degradacao", "rajadas"]
    
    if len(sys.argv) > 1:
        scenarios = [sys.argv[1]]
    
    print("\n" + "="*60)
    print("  ANALISADOR DE CENÁRIOS CRÍTICOS - CIRCUIT BREAKER")
    print("="*60)
    
    all_benefits = []
    
    for scenario in scenarios:
        analyzer = ScenarioAnalyzer(scenario, RESULTS_DIR, OUTPUT_DIR)
        analyzer.run_analysis()
        
        if analyzer.benefits is not None:
            all_benefits.append(analyzer.benefits)
    
    # Relatório consolidado
    if all_benefits:
        print("\n" + "="*60)
        print("  RESUMO CONSOLIDADO DE TODOS OS CENÁRIOS")
        print("="*60)
        
        consolidated = pd.concat(all_benefits, ignore_index=True)
        print("\n", consolidated.to_string(index=False))
        
        consolidated.to_csv(
            os.path.join(CSV_DIR, "consolidated_benefits.csv"),
            index=False
        )
        
        print(f"\n✅ Análise consolidada salva em {CSV_DIR}/consolidated_benefits.csv")
    
    print("\n" + "="*60)
    print("  ✨ ANÁLISE COMPLETA FINALIZADA!")
    print("="*60 + "\n")
