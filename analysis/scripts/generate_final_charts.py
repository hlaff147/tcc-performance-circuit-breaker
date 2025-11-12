#!/usr/bin/env python3
"""
Script para gerar gráficos consolidados da análise final do TCC.
Gera visualizações comparativas dos 3 cenários críticos.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configurações
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11

# Cores consistentes
COLORS = {
    'V1': '#d62728',  # Vermelho
    'V2': '#2ca02c',  # Verde
    'Success': '#2ca02c',
    'Failure': '#d62728',
    'CB_Open': '#ff7f0e',
    'Fallback': '#9467bd'
}

# Diretórios
CSV_DIR = "analysis_results/scenarios/csv"
OUTPUT_DIR = "analysis_results/final_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_scenario_data(scenario):
    """Carrega dados de um cenário específico"""
    status = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
    response = pd.read_csv(f"{CSV_DIR}/{scenario}_response.csv")
    benefits = pd.read_csv(f"{CSV_DIR}/{scenario}_benefits.csv")
    
    return {
        'status': status,
        'response': response,
        'benefits': benefits,
        'name': scenario
    }

def plot_1_success_rates_comparison():
    """Gráfico 1: Comparação de Taxa de Sucesso entre Cenários"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    data = []
    
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        data.append({
            'Cenário': scenario.capitalize(),
            'V1': df[df['Version'] == 'V1']['Success Rate (%)'].values[0],
            'V2': df[df['Version'] == 'V2']['Success Rate (%)'].values[0]
        })
    
    df_plot = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(scenarios))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, df_plot['V1'], width, label='V1 (Sem CB)', 
                   color=COLORS['V1'], alpha=0.8)
    bars2 = ax.bar(x + width/2, df_plot['V2'], width, label='V2 (Com CB)', 
                   color=COLORS['V2'], alpha=0.8)
    
    # Adicionar valores nas barras
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Taxa de Sucesso (%)', fontsize=12, fontweight='bold')
    ax.set_title('Taxa de Sucesso: V1 vs V2 por Cenário', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot['Cenário'])
    ax.legend(fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_success_rates_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 1 gerado: Taxa de Sucesso por Cenário")

def plot_2_failure_reduction():
    """Gráfico 2: Redução de Falhas (500) em cada Cenário"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    data = []
    
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        v1_failures = df[df['Version'] == 'V1']['API Failure Rate (%)'].values[0]
        v2_failures = df[df['Version'] == 'V2']['API Failure Rate (%)'].values[0]
        reduction = ((v1_failures - v2_failures) / v1_failures * 100) if v1_failures > 0 else 0
        
        data.append({
            'Cenário': scenario.capitalize(),
            'V1 Falhas (%)': v1_failures,
            'V2 Falhas (%)': v2_failures,
            'Redução (%)': reduction
        })
    
    df_plot = pd.DataFrame(data)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Subplot 1: Falhas absolutas
    x = np.arange(len(scenarios))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, df_plot['V1 Falhas (%)'], width, 
                    label='V1 (Sem CB)', color=COLORS['V1'], alpha=0.8)
    bars2 = ax1.bar(x + width/2, df_plot['V2 Falhas (%)'], width, 
                    label='V2 (Com CB)', color=COLORS['V2'], alpha=0.8)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontweight='bold')
    
    ax1.set_ylabel('Taxa de Falhas (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Falhas (500) por Cenário', fontsize=13, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_plot['Cenário'])
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # Subplot 2: Redução percentual
    bars = ax2.barh(df_plot['Cenário'], df_plot['Redução (%)'], 
                    color=COLORS['Success'], alpha=0.8)
    
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2.,
                f'-{width:.1f}%',
                ha='left', va='center', fontweight='bold', fontsize=12)
    
    ax2.set_xlabel('Redução de Falhas (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Redução de Falhas com Circuit Breaker', fontsize=13, fontweight='bold', pad=15)
    ax2.grid(axis='x', alpha=0.3)
    ax2.set_xlim(0, max(df_plot['Redução (%)']) * 1.2)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/02_failure_reduction.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 2 gerado: Redução de Falhas")

def plot_3_response_time_percentiles():
    """Gráfico 3: Percentis de Tempo de Resposta (P50, P95, P99)"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, scenario in enumerate(scenarios):
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_response.csv")
        
        metrics = ['P50 (ms)', 'P95 (ms)', 'P99 (ms)']
        v1_values = df[df['Version'] == 'V1'][metrics].values[0]
        v2_values = df[df['Version'] == 'V2'][metrics].values[0]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax = axes[idx]
        bars1 = ax.bar(x - width/2, v1_values, width, label='V1', 
                      color=COLORS['V1'], alpha=0.8)
        bars2 = ax.bar(x + width/2, v2_values, width, label='V2', 
                      color=COLORS['V2'], alpha=0.8)
        
        # Adicionar valores
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_ylabel('Tempo (ms)', fontsize=11, fontweight='bold')
        ax.set_title(f'{scenario.capitalize()}', fontsize=12, fontweight='bold', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
    
    fig.suptitle('Percentis de Tempo de Resposta por Cenário', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_response_time_percentiles.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 3 gerado: Percentis de Tempo de Resposta")

def plot_4_throughput_comparison():
    """Gráfico 4: Comparação de Throughput (Total de Requisições)"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    data = []
    
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        v1_total = df[df['Version'] == 'V1']['Total Requests'].values[0]
        v2_total = df[df['Version'] == 'V2']['Total Requests'].values[0]
        variation = ((v2_total - v1_total) / v1_total * 100)
        
        data.append({
            'Cenário': scenario.capitalize(),
            'V1': v1_total,
            'V2': v2_total,
            'Variação (%)': variation
        })
    
    df_plot = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(scenarios))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, df_plot['V1'], width, label='V1 (Sem CB)', 
                   color=COLORS['V1'], alpha=0.8)
    bars2 = ax.bar(x + width/2, df_plot['V2'], width, label='V2 (Com CB)', 
                   color=COLORS['V2'], alpha=0.8)
    
    # Adicionar valores e variação
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        h1, h2 = bar1.get_height(), bar2.get_height()
        var = df_plot['Variação (%)'].iloc[i]
        
        ax.text(bar1.get_x() + bar1.get_width()/2., h1,
               f'{int(h1):,}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(bar2.get_x() + bar2.get_width()/2., h2,
               f'{int(h2):,}\n({var:+.1f}%)',
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel('Total de Requisições', fontsize=12, fontweight='bold')
    ax.set_title('Throughput: Total de Requisições por Cenário', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot['Cenário'])
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 4 gerado: Comparação de Throughput")

def plot_5_status_distribution():
    """Gráfico 5: Distribuição de Status HTTP por Cenário"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, scenario in enumerate(scenarios):
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        
        # V1
        ax = axes[idx]
        v1 = df[df['Version'] == 'V1'].iloc[0]
        sizes = [v1['Success (200)'], v1['API Failure (500)']]
        labels = [f"Sucesso (200)\n{v1['Success Rate (%)']:.1f}%", 
                 f"Falha (500)\n{v1['API Failure Rate (%)']:.1f}%"]
        colors = [COLORS['Success'], COLORS['Failure']]
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                           autopct='%1.1f%%', startangle=90,
                                           textprops={'fontsize': 10, 'fontweight': 'bold'})
        ax.set_title(f'V1 - {scenario.capitalize()}', fontsize=12, fontweight='bold', pad=10)
        
        # V2
        ax = axes[idx + 3]
        v2 = df[df['Version'] == 'V2'].iloc[0]
        
        sizes = [v2['Success (200)'], v2['API Failure (500)']]
        labels = [f"Sucesso (200)\n{v2['Success Rate (%)']:.1f}%", 
                 f"Falha (500)\n{v2['API Failure Rate (%)']:.1f}%"]
        
        # Adicionar fallback se existir
        if v2['Fallback (202)'] > 0:
            sizes.append(v2['Fallback (202)'])
            labels.append(f"Fallback (202)\n{v2['Fallback Rate (%)']:.1f}%")
            colors_v2 = [COLORS['Success'], COLORS['Failure'], COLORS['Fallback']]
        else:
            colors_v2 = colors
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_v2, 
                                           autopct='%1.1f%%', startangle=90,
                                           textprops={'fontsize': 10, 'fontweight': 'bold'})
        ax.set_title(f'V2 - {scenario.capitalize()}', fontsize=12, fontweight='bold', pad=10)
    
    fig.suptitle('Distribuição de Status HTTP: V1 vs V2', 
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/05_status_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 5 gerado: Distribuição de Status HTTP")

def plot_6_consolidated_metrics():
    """Gráfico 6: Métricas Consolidadas - Radar Chart"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    
    # Preparar dados
    metrics_data = {
        'V1': {'Success': [], 'AvgTime': [], 'P95': []},
        'V2': {'Success': [], 'AvgTime': [], 'P95': []}
    }
    
    for scenario in scenarios:
        status = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        response = pd.read_csv(f"{CSV_DIR}/{scenario}_response.csv")
        
        for version in ['V1', 'V2']:
            st = status[status['Version'] == version].iloc[0]
            resp = response[response['Version'] == version].iloc[0]
            
            metrics_data[version]['Success'].append(st['Success Rate (%)'])
            # Normalizar tempo (inverter - quanto menor melhor)
            metrics_data[version]['AvgTime'].append(100 - min(resp['Avg Response (ms)'] / 10, 100))
            metrics_data[version]['P95'].append(100 - min(resp['P95 (ms)'] / 30, 100))
    
    # Criar radar chart
    categories = [s.capitalize() for s in scenarios]
    N = len(categories)
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), subplot_kw=dict(projection='polar'))
    
    metric_names = ['Taxa de Sucesso', 'Desempenho (Avg)', 'Desempenho (P95)']
    metric_keys = ['Success', 'AvgTime', 'P95']
    
    for idx, (metric_name, metric_key) in enumerate(zip(metric_names, metric_keys)):
        ax = axes[idx]
        
        values_v1 = metrics_data['V1'][metric_key] + metrics_data['V1'][metric_key][:1]
        values_v2 = metrics_data['V2'][metric_key] + metrics_data['V2'][metric_key][:1]
        
        ax.plot(angles, values_v1, 'o-', linewidth=2, label='V1', color=COLORS['V1'])
        ax.fill(angles, values_v1, alpha=0.15, color=COLORS['V1'])
        
        ax.plot(angles, values_v2, 'o-', linewidth=2, label='V2', color=COLORS['V2'])
        ax.fill(angles, values_v2, alpha=0.15, color=COLORS['V2'])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 100)
        ax.set_title(metric_name, fontsize=12, fontweight='bold', pad=15)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.grid(True)
    
    fig.suptitle('Análise Comparativa Multi-dimensional: V1 vs V2', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_consolidated_metrics_radar.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 6 gerado: Métricas Consolidadas (Radar)")

def plot_7_catastrofe_timeline():
    """Gráfico 7: Timeline do Cenário Catástrofe (ilustrativo)"""
    # Dados ilustrativos baseados no cenário
    time_points = [0, 1, 4, 9, 12, 13]
    v1_success = [70, 70, 0, 70, 70, 70]  # Falha total entre 4-9min
    v2_success = [90, 90, 88, 90, 90, 90]  # CB protege durante falha
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(time_points, v1_success, 'o-', linewidth=3, markersize=8,
            label='V1 (Sem CB)', color=COLORS['V1'])
    ax.plot(time_points, v2_success, 'o-', linewidth=3, markersize=8,
            label='V2 (Com CB)', color=COLORS['V2'])
    
    # Marcar zona de catástrofe
    ax.axvspan(4, 9, alpha=0.2, color='red', label='Catástrofe (API 100% fora)')
    
    ax.set_xlabel('Tempo (minutos)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Taxa de Sucesso (%)', fontsize=12, fontweight='bold')
    ax.set_title('Timeline: Falha Catastrófica - Comportamento V1 vs V2', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=11, loc='lower left')
    ax.grid(True, alpha=0.3)
    
    # Anotações
    ax.annotate('Operação Normal', xy=(2, 75), fontsize=10, ha='center')
    ax.annotate('Catástrofe Total\nV1 colapsa', xy=(6.5, 35), fontsize=10, 
                ha='center', color='red', fontweight='bold')
    ax.annotate('CB Protege V2', xy=(6.5, 88), fontsize=10, ha='center', 
                color='green', fontweight='bold')
    ax.annotate('Recuperação', xy=(10.5, 75), fontsize=10, ha='center')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/07_catastrofe_timeline.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 7 gerado: Timeline Catástrofe")

def generate_summary_table():
    """Gera tabela resumo em formato markdown"""
    scenarios = ['catastrofe', 'degradacao', 'rajadas']
    summary = []
    
    for scenario in scenarios:
        status = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        
        v1 = status[status['Version'] == 'V1'].iloc[0]
        v2 = status[status['Version'] == 'V2'].iloc[0]
        
        failure_reduction = ((v1['API Failure Rate (%)'] - v2['API Failure Rate (%)']) / 
                            v1['API Failure Rate (%)'] * 100) if v1['API Failure Rate (%)'] > 0 else 0
        
        summary.append({
            'Cenário': scenario.capitalize(),
            'V1 Sucesso': f"{v1['Success Rate (%)']:.1f}%",
            'V2 Sucesso': f"{v2['Success Rate (%)']:.1f}%",
            'Ganho': f"+{v2['Success Rate (%)'] - v1['Success Rate (%)']:.1f}pp",
            'Red. Falhas': f"-{failure_reduction:.1f}%"
        })
    
    df = pd.DataFrame(summary)
    
    # Salvar como CSV
    df.to_csv(f'{OUTPUT_DIR}/summary_table.csv', index=False)
    
    # Gerar markdown
    md_table = df.to_markdown(index=False)
    with open(f'{OUTPUT_DIR}/summary_table.md', 'w') as f:
        f.write("# Tabela Resumo - Análise Final\n\n")
        f.write(md_table)
    
    print("✅ Tabela resumo gerada")
    print(df.to_string(index=False))

def main():
    """Gera todos os gráficos"""
    print("\n" + "="*60)
    print("  GERAÇÃO DE GRÁFICOS - ANÁLISE FINAL TCC")
    print("="*60 + "\n")
    
    try:
        plot_1_success_rates_comparison()
        plot_2_failure_reduction()
        plot_3_response_time_percentiles()
        plot_4_throughput_comparison()
        plot_5_status_distribution()
        plot_6_consolidated_metrics()
        plot_7_catastrofe_timeline()
        generate_summary_table()
        
        print("\n" + "="*60)
        print(f"✅ TODOS OS GRÁFICOS GERADOS COM SUCESSO!")
        print(f"📁 Localização: {OUTPUT_DIR}/")
        print("="*60 + "\n")
        
        print("Arquivos gerados:")
        print("  01_success_rates_comparison.png")
        print("  02_failure_reduction.png")
        print("  03_response_time_percentiles.png")
        print("  04_throughput_comparison.png")
        print("  05_status_distribution.png")
        print("  06_consolidated_metrics_radar.png")
        print("  07_catastrofe_timeline.png")
        print("  summary_table.csv")
        print("  summary_table.md")
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar gráficos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
