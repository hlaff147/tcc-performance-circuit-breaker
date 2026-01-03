#!/usr/bin/env python3
"""
Script para gerar gráficos consolidados da análise final do TCC.
Gera visualizações comparativas dos 3 cenários críticos.
Supports --lang en/pt for bilingual output.
"""

import os
import argparse
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
    'V3': '#1f77b4',  # Azul
    'V4': '#ff7f0e',  # Laranja
    'Success': '#2ca02c',
    'Failure': '#d62728',
    'CB_Open': '#f0f000', # Amarelo para CB Aberto
    'Fallback': '#9467bd'  # Roxo para Fallback
}

# Bilingual Labels
LABELS = {
    'en': {
        'scenarios': {'catastrofe': 'Catastrophe', 'rajadas': 'Bursts', 'indisponibilidade': 'Unavailability', 'degradacao': 'Degradation', 'normal': 'Normal'},
        'success_rate': 'Total Success Rate (%)',
        'success_title': 'Total Success Rate (200 + 202): V1-V4 Comparison',
        'failure_rate': 'Failure Rate (%)',
        'failures_title': 'Failures (500) per Scenario',
        'failure_reduction': 'Failure Reduction (%)',
        'reduction_title': 'Failure Reduction (Baseline: V1)',
        'time_ms': 'Time (ms)',
        'response_percentiles': 'Response Time Percentiles per Scenario',
        'total_requests': 'Total Requests',
        'throughput_title': 'Throughput: Total Requests per Scenario (V1 Baseline)',
        'status_dist_title': 'HTTP Status Distribution by Version and Scenario',
        'radar_success': 'Success Rate', 'radar_avg': 'Performance (Avg)', 'radar_p95': 'Performance (P95)',
        'radar_title': 'Multi-dimensional Comparative Analysis (V1-V4)',
        'timeline_no_cb': 'V1 (No CB)', 'timeline_with_cb': 'V2 (With CB)', 'timeline_catastrophe': 'Catastrophe (API 100% Down)',
        'timeline_xlabel': 'Time (minutes)', 'timeline_ylabel': 'Success Rate (%)', 'timeline_title': 'Timeline: Catastrophic Failure - V1 vs V2 Behavior',
        'timeline_normal': 'Normal Operation', 'timeline_collapse': 'Total Catastrophe\nV1 Collapses', 'timeline_protect': 'CB Protects V2', 'timeline_recovery': 'Recovery',
        'fallback_pct': 'Percentage (%)', 'fallback_composition': 'Response Composition (Versions with CB)',
        'fallback_rate': 'Fallback Rate (%)', 'fallback_contrib': 'Fallback 202 Contribution (V2/V4)', 'fallback_none': 'No scenario\nwith Fallback 202',
        'fallback_title': 'Fallback 202 Analysis: Impact on Total Success',
        'mean_response': 'Mean Response Time (ms)', 'mean_title': 'Mean Response Time per Scenario',
        'error_rate': 'Error Rate 500 (%)', 'error_title': 'Error Rate (HTTP 500) - V1 to V4',
        'downtime': 'Effective Downtime (min)', 'downtime_title': 'Estimated Downtime (Uptime = 200 + 202)',
        'availability': 'Availability (%)', 'availability_title': 'Effective Availability (200 + 202)',
        'summary_header': '# Summary Table - Final Analysis\n\n',
    },
    'pt': {
        'scenarios': {'catastrofe': 'Catástrofe', 'rajadas': 'Rajadas', 'indisponibilidade': 'Indisponibilidade', 'degradacao': 'Degradação', 'normal': 'Normal'},
        'success_rate': 'Taxa de Sucesso Total (%)',
        'success_title': 'Taxa de Sucesso Total (200 + 202): Comparação V1-V4',
        'failure_rate': 'Taxa de Falhas (%)',
        'failures_title': 'Falhas (500) por Cenário',
        'failure_reduction': 'Redução de Falhas (%)',
        'reduction_title': 'Redução de Falhas (Base: V1)',
        'time_ms': 'Tempo (ms)',
        'response_percentiles': 'Percentis de Tempo de Resposta por Cenário',
        'total_requests': 'Total de Requisições',
        'throughput_title': 'Throughput: Total de Requisições por Cenário (V1 Baseline)',
        'status_dist_title': 'Distribuição de Status HTTP por Versão e Cenário',
        'radar_success': 'Taxa de Sucesso', 'radar_avg': 'Desempenho (Avg)', 'radar_p95': 'Desempenho (P95)',
        'radar_title': 'Análise Comparativa Multi-dimensional (V1-V4)',
        'timeline_no_cb': 'V1 (Sem CB)', 'timeline_with_cb': 'V2 (Com CB)', 'timeline_catastrophe': 'Catástrofe (API 100% fora)',
        'timeline_xlabel': 'Tempo (minutos)', 'timeline_ylabel': 'Taxa de Sucesso (%)', 'timeline_title': 'Timeline: Falha Catastrófica - Comportamento V1 vs V2',
        'timeline_normal': 'Operação Normal', 'timeline_collapse': 'Catástrofe Total\nV1 colapsa', 'timeline_protect': 'CB Protege V2', 'timeline_recovery': 'Recuperação',
        'fallback_pct': 'Percentual (%)', 'fallback_composition': 'Composição das Respostas (Versões com CB)',
        'fallback_rate': 'Taxa de Fallback (%)', 'fallback_contrib': 'Contribuição do Fallback 202 (V2/V4)', 'fallback_none': 'Nenhum cenário\ncom Fallback 202',
        'fallback_title': 'Análise do Fallback 202: Impacto no Sucesso Total',
        'mean_response': 'Tempo Médio de Resposta (ms)', 'mean_title': 'Tempo Médio de Resposta por Cenário',
        'error_rate': 'Taxa de Erro 500 (%)', 'error_title': 'Taxa de Erro (HTTP 500) - V1 a V4',
        'downtime': 'Downtime Efetivo (min)', 'downtime_title': 'Downtime Estimado (Uptime = 200 + 202)',
        'availability': 'Disponibilidade (%)', 'availability_title': 'Disponibilidade Efetiva (200 + 202)',
        'summary_header': '# Tabela Resumo - Análise Final\n\n',
    }
}

# Global language settings (set by main)
LANG = 'en'
LANG_SUFFIX = '_en'

# Diretórios
CSV_DIR = "analysis_results/scenarios/csv"
OUTPUT_DIR = "analysis_results/final_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_available_scenarios():
    files = [f for f in os.listdir(CSV_DIR) if f.endswith('_status.csv')]
    return sorted({f.replace('_status.csv', '') for f in files})

def scenario_label(name):
    return LABELS[LANG]['scenarios'].get(name.lower(), name.replace('_', ' ').title())

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

def plot_1_success_rates_comparison(scenarios):
    """Gráfico 1: Comparação de Taxa de Sucesso entre Scenarios (incluindo Fallback)"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 1")
        return
    data = []
    
    available_versions = ['V1', 'V2', 'V3', 'V4']
    
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        row = {'Scenario': scenario_label(scenario)}
        for v in available_versions:
            if v in df['Version'].values:
                row[v] = df[df['Version'] == v]['Total Success Rate (%)'].values[0]
            else:
                row[v] = 0
        data.append(row)
    
    df_plot = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(scenarios))
    n_versions = len(available_versions)
    width = 0.8 / n_versions
    
    for i, v in enumerate(available_versions):
        offset = (i - n_versions/2.5) * width
        bars = ax.bar(x + offset, df_plot[v], width, label=f'{v}', 
                      color=COLORS.get(v, '#333333'), alpha=0.8)
        
        # Adicionar valores nas barras
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontweight='bold', fontsize=8, rotation=90)
    
    ax.set_ylabel('Total Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Total Success Rate (200 + 202): V1-V4 Comparison', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot['Scenario'])
    ax.legend(fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_success_rates_comparison{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 1 gerado: Taxa de Sucesso por Scenario")

def plot_2_failure_reduction(scenarios):
    """Gráfico 2: Redução de Falhas (500) em cada Scenario"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 2")
        return
    data = []
    
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        v1_failures = df[df['Version'] == 'V1']['API Failure Rate (%)'].values[0]
        
        row = {'Scenario': scenario_label(scenario), 'V1': v1_failures}
        for v in ['V2', 'V3', 'V4']:
            if v in df['Version'].values:
                v_failures = df[df['Version'] == v]['API Failure Rate (%)'].values[0]
                reduction = ((v1_failures - v_failures) / v1_failures * 100) if v1_failures > 0 else 0
                row[f'{v} Redução (%)'] = reduction
                row[f'{v} Falhas (%)'] = v_failures
        
        data.append(row)
    
    df_plot = pd.DataFrame(data)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Subplot 1: Falhas absolutas
    x = np.arange(len(scenarios))
    versions_to_plot = ['V1', 'V2', 'V3', 'V4']
    width = 0.8 / len(versions_to_plot)
    
    for i, v in enumerate(versions_to_plot):
        col = 'V1' if v == 'V1' else f'{v} Falhas (%)'
        if col in df_plot.columns:
            offset = (i - len(versions_to_plot)/2.5) * width
            bars = ax1.bar(x + offset, df_plot[col], width, 
                          label=f'{v}', color=COLORS.get(v), alpha=0.8)
            
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%', ha='center', va='bottom', 
                        fontweight='bold', fontsize=8, rotation=90)
    
    ax1.set_ylabel('Failure Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Failures (500) per Scenario', fontsize=13, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_plot['Scenario'])
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    
    # Subplot 2: Redução percentual comparativa
    y_pos = np.arange(len(scenarios))
    height = 0.25
    reductions = ['V2 Redução (%)', 'V3 Redução (%)', 'V4 Redução (%)']
    
    for i, red_col in enumerate(reductions):
        if red_col in df_plot.columns:
            v_name = red_col.split(' ')[0]
            bars = ax2.barh(y_pos + (i * height) - height, df_plot[red_col], height, 
                            label=f'Redução {v_name}', color=COLORS.get(v_name), alpha=0.8)
            
            for bar in bars:
                width = bar.get_width()
                ax2.text(width, bar.get_y() + bar.get_height()/2.,
                        f' -{width:.1f}%', ha='left', va='center', 
                        fontweight='bold', fontsize=9)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_plot['Scenario'])
    ax2.set_xlabel('Failure Reduction (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Failure Reduction (Baseline: V1)', fontsize=13, fontweight='bold', pad=15)
    ax2.grid(axis='x', alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_xlim(0, 115)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/02_failure_reduction{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 2 gerado: Redução de Falhas")

def plot_3_response_time_percentiles(scenarios):
    """Gráfico 3: Percentis de Tempo de Resposta (P50, P95, P99)"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 3")
        return
    
    fig, axes = plt.subplots(1, len(scenarios), figsize=(6 * len(scenarios), 6))
    if len(scenarios) == 1:
        axes = [axes]
    
    for idx, scenario in enumerate(scenarios):
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_response.csv")
        metrics = ['P50 (ms)', 'P95 (ms)', 'P99 (ms)']
        available_versions = df['Version'].unique()
        
        x = np.arange(len(metrics))
        width = 0.8 / len(available_versions)
        
        ax = axes[idx]
        for i, v in enumerate(available_versions):
            v_values = df[df['Version'] == v][metrics].values[0]
            offset = (i - len(available_versions)/2.5) * width
            bars = ax.bar(x + offset, v_values, width, label=f'{v}', 
                          color=COLORS.get(v), alpha=0.8)
            
            # Adicionar valores
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=8, fontweight='bold', rotation=45)
        
        ax.set_ylabel('Time (ms)', fontsize=11, fontweight='bold')
        ax.set_title(f'{scenario_label(scenario)}', fontsize=12, fontweight='bold', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
    
    fig.suptitle('Response Time Percentiles per Scenario', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_response_time_percentiles{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 3 gerado: Percentis de Tempo de Resposta")

def plot_4_throughput_comparison(scenarios):
    """Gráfico 4: Comparação de Throughput (Total de Requisições)"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 4")
        return
    data = []
    
    available_versions = ['V1', 'V2', 'V3', 'V4']
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        row = {'Scenario': scenario_label(scenario)}
        v1_total = df[df['Version'] == 'V1']['Total Requests'].values[0]
        
        for v in available_versions:
            if v in df['Version'].values:
                v_total = df[df['Version'] == v]['Total Requests'].values[0]
                variation = ((v_total - v1_total) / v1_total * 100) if v1_total > 0 else 0
                row[v] = v_total
                row[f'{v}_var'] = variation
        data.append(row)
    
    df_plot = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(scenarios))
    n_versions = len(available_versions)
    width = 0.8 / n_versions
    
    for i, v in enumerate(available_versions):
        offset = (i - n_versions/2.5) * width
        bars = ax.bar(x + offset, df_plot[v], width, label=f'{v}', 
                      color=COLORS.get(v), alpha=0.8)
        
        # Adicionar valores e variação
        for j, bar in enumerate(bars):
            height = bar.get_height()
            var = df_plot[f'{v}_var'].iloc[j]
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}\n({var:+.1f}%)',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax.set_ylabel('Total Requests', fontsize=12, fontweight='bold')
    ax.set_title('Throughput: Total Requests per Scenario (V1 Baseline)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot['Scenario'])
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_throughput_comparison{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 4 gerado: Comparação de Throughput")

def plot_5_status_distribution(scenarios):
    """Gráfico 5: Distribuição de Status HTTP por Scenario"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 5")
        return
    
    available_versions = ['V1', 'V2', 'V3', 'V4']
    fig, axes = plt.subplots(len(available_versions), len(scenarios), figsize=(6 * len(scenarios), 4 * len(available_versions)))
    
    for s_idx, scenario in enumerate(scenarios):
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        
        for v_idx, v in enumerate(available_versions):
            ax = axes[v_idx, s_idx]
            v_data = df[df['Version'] == v].iloc[0]
            
            sizes = [v_data['Success (200)'], v_data['API Failure (500)']]
            labels = [f"OK (200)", f"Err (500)"]
            colors = [COLORS['Success'], COLORS['Failure']]
            
            if v_data['Fallback (202)'] > 0:
                sizes.append(v_data['Fallback (202)'])
                labels.append(f"FB (202)")
                colors.append(COLORS['Fallback'])
            
            if v_data['CB Open (503)'] > 0:
                sizes.append(v_data['CB Open (503)'])
                labels.append(f"CB (503)")
                colors.append(COLORS['CB_Open'])

            ax.pie(sizes, labels=labels, colors=colors,
                      autopct='%1.1f%%', startangle=90,
                      textprops={'fontsize': 8, 'fontweight': 'bold'})
            ax.set_title(f'{v} - {scenario_label(scenario)}', fontsize=10, fontweight='bold')
    
    fig.suptitle('HTTP Status Distribution by Version and Scenario', 
                 fontsize=16, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/05_status_distribution{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 5 gerado: Distribuição de Status HTTP")

def plot_6_consolidated_metrics(scenarios):
    """Gráfico 6: Métricas Consolidadas - Radar Chart"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 6")
        return
    
    available_versions = ['V1', 'V2', 'V3', 'V4']
    metrics_data = {v: {'Success': [], 'AvgTime': [], 'P95': []} for v in available_versions}
    
    for scenario in scenarios:
        status = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        response = pd.read_csv(f"{CSV_DIR}/{scenario}_response.csv")
        
        for version in available_versions:
            if version in status['Version'].values:
                st = status[status['Version'] == version].iloc[0]
                resp = response[response['Version'] == version].iloc[0]
                
                metrics_data[version]['Success'].append(st['Total Success Rate (%)'])
                metrics_data[version]['AvgTime'].append(100 - min(resp['Avg Response (ms)'] / 10, 100))
                metrics_data[version]['P95'].append(100 - min(resp['P95 (ms)'] / 30, 100))
            else:
                metrics_data[version]['Success'].append(0)
                metrics_data[version]['AvgTime'].append(0)
                metrics_data[version]['P95'].append(0)
    
    # Criar radar chart
    categories = [scenario_label(s) for s in scenarios]
    N = len(categories)
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), subplot_kw=dict(projection='polar'))
    
    metric_names = ['Success Rate', 'Performance (Avg)', 'Performance (P95)']
    metric_keys = ['Success', 'AvgTime', 'P95']
    
    for idx, (metric_name, metric_key) in enumerate(zip(metric_names, metric_keys)):
        ax = axes[idx]
        
        for v in available_versions:
            values = metrics_data[v][metric_key] + metrics_data[v][metric_key][:1]
            ax.plot(angles, values, 'o-', linewidth=2, label=v, color=COLORS.get(v))
            ax.fill(angles, values, alpha=0.1, color=COLORS.get(v))
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=8)
        ax.set_ylim(0, 100)
        ax.set_title(metric_name, fontsize=12, fontweight='bold', pad=15)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=8)
        ax.grid(True)
    
    fig.suptitle('Multi-dimensional Comparative Analysis (V1-V4)', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_consolidated_metrics_radar{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 6 gerado: Métricas Consolidadas (Radar)")

def plot_7_catastrofe_timeline():
    """Gráfico 7: Timeline do Scenario Catástrofe (ilustrativo)"""
    # Dados ilustrativos baseados no cenário
    time_points = [0, 1, 4, 9, 12, 13]
    v1_success = [70, 70, 0, 70, 70, 70]  # Falha total entre 4-9min
    v2_success = [90, 90, 88, 90, 90, 90]  # CB protege durante falha
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(time_points, v1_success, 'o-', linewidth=3, markersize=8,
            label='V1 (No CB)', color=COLORS['V1'])
    ax.plot(time_points, v2_success, 'o-', linewidth=3, markersize=8,
            label='V2 (With CB)', color=COLORS['V2'])
    
    # Marcar zona de catástrofe
    ax.axvspan(4, 9, alpha=0.2, color='red', label='Catastrophe (API 100% Down)')
    
    ax.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Timeline: Catastrophic Failure - V1 vs V2 Behavior', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=11, loc='lower left')
    ax.grid(True, alpha=0.3)
    
    # Anotações
    ax.annotate('Normal Operation', xy=(2, 75), fontsize=10, ha='center')
    ax.annotate('Total Catastrophe\nV1 Collapses', xy=(6.5, 35), fontsize=10, 
                ha='center', color='red', fontweight='bold')
    ax.annotate('CB Protects V2', xy=(6.5, 88), fontsize=10, ha='center', 
                color='green', fontweight='bold')
    ax.annotate('Recovery', xy=(10.5, 75), fontsize=10, ha='center')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/07_catastrofe_timeline{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 7 gerado: Timeline Catástrofe")

def plot_8_fallback_contribution(scenarios):
    """Gráfico 8: Response Composition - apenas barras empilhadas"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 8")
        return
    data = []
    
    for scenario in scenarios:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        for v in ['V2', 'V4']:
            if v in df['Version'].values:
                v_data = df[df['Version'] == v].iloc[0]
                if v_data['Fallback (202)'] > 0:
                    data.append({
                        'Version': v,
                        'Scenario': scenario_label(scenario),
                        'Success 200 (%)': v_data['Success Rate (%)'],
                        'Fallback 202 (%)': v_data['Fallback Rate (%)'],
                        'Failure 500 (%)': v_data['API Failure Rate (%)'],
                        'Total Success': v_data['Total Success Rate (%)']
                    })
    
    df_plot = pd.DataFrame(data)
    if df_plot.empty:
        print("⚠️ No Fallback data for plot 8")
        return

    # Single plot: Response Composition only
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x_labels = [f"{row['Version']} - {row['Scenario']}" for _, row in df_plot.iterrows()]
    x = np.arange(len(x_labels))
    width = 0.6
    
    bars1 = ax.bar(x, df_plot['Success 200 (%)'], width, 
                    label='Success 200', color=COLORS['Success'], alpha=0.9)
    bars2 = ax.bar(x, df_plot['Fallback 202 (%)'], width, 
                    bottom=df_plot['Success 200 (%)'],
                    label='Fallback 202', color=COLORS['Fallback'], alpha=0.9)
    bars3 = ax.bar(x, df_plot['Failure 500 (%)'], width,
                    bottom=df_plot['Success 200 (%)'] + df_plot['Fallback 202 (%)'],
                    label='Failure 500', color=COLORS['Failure'], alpha=0.9)
    
    for i, (b1, b2, b3) in enumerate(zip(bars1, bars2, bars3)):
        if df_plot['Success 200 (%)'].iloc[i] > 2:
            ax.text(b1.get_x() + b1.get_width()/2., 
                    df_plot['Success 200 (%)'].iloc[i]/2,
                    f"{df_plot['Success 200 (%)'].iloc[i]:.1f}%",
                    ha='center', va='center', fontweight='bold', fontsize=10, color='white')
        
        if df_plot['Fallback 202 (%)'].iloc[i] > 2:
            ax.text(b2.get_x() + b2.get_width()/2., 
                    df_plot['Success 200 (%)'].iloc[i] + df_plot['Fallback 202 (%)'].iloc[i]/2,
                    f"{df_plot['Fallback 202 (%)'].iloc[i]:.1f}%",
                    ha='center', va='center', fontweight='bold', fontsize=10, color='white')
        
        if df_plot['Failure 500 (%)'].iloc[i] > 2:
            ax.text(b3.get_x() + b3.get_width()/2., 
                    df_plot['Success 200 (%)'].iloc[i] + df_plot['Fallback 202 (%)'].iloc[i] + df_plot['Failure 500 (%)'].iloc[i]/2,
                    f"{df_plot['Failure 500 (%)'].iloc[i]:.1f}%",
                    ha='center', va='center', fontweight='bold', fontsize=10, color='white')
    
    ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title('Response Composition (Versions with CB)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=11, loc='upper right')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/08_fallback_contribution{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 8 gerado: Response Composition")

def plot_9_avg_response_times(scenarios):
    """Gráfico 9: Tempo médio de resposta (V1 vs V2)"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 9")
        return

    records = []
    for scenario in scenarios:
        path = f"{CSV_DIR}/{scenario}_response.csv"
        if not os.path.exists(path):
            print(f"⚠️  Sem response.csv para {scenario}")
            continue
        df = pd.read_csv(path)
        for version in ['V1', 'V2', 'V3', 'V4']:
            if version in df['Version'].values:
                value = df[df['Version'] == version]['Avg Response (ms)'].values[0]
                records.append({
                    'Scenario': scenario_label(scenario),
                    'Version': version,
                    'Mean Response Time (ms)': value
                })

    if not records:
        print("⚠️  Sem dados para o gráfico 9")
        return

    df_plot = pd.DataFrame(records)
    unique_scenarios = [scenario_label(s) for s in scenarios if scenario_label(s) in df_plot['Scenario'].unique()]
    if not unique_scenarios:
        print("⚠️  Sem cenários válidos para o gráfico 9")
        return
    x = np.arange(len(unique_scenarios))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 6))
    available_versions = df_plot['Version'].unique()
    available_versions = sorted(available_versions, key=lambda v: int(v[1:])) # Sort versions V1, V2, V3, V4
    width = 0.8 / len(available_versions)
    
    for i, v in enumerate(available_versions):
        v_data = [df_plot[(df_plot['Scenario'] == label) & (df_plot['Version'] == v)]['Mean Response Time (ms)'].iloc[0] 
                  if not df_plot[(df_plot['Scenario'] == label) & (df_plot['Version'] == v)].empty else 0 
                  for label in unique_scenarios]
        offset = (i - len(available_versions)/2.0 + 0.5) * width # Center the group of bars
        bars = ax.bar(x + offset, v_data, width, label=f'{v}', color=COLORS.get(v), alpha=0.85)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height, f"{height:.0f}", 
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(unique_scenarios)
    ax.set_ylabel('Mean Response Time (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Mean Response Time per Scenario', fontsize=14, fontweight='bold', pad=15)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/09_avg_response_times{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 9 gerado: Tempo Médio de Resposta")

def plot_10_error_rates(scenarios):
    """Gráfico 10: Taxa de erro (HTTP 500)"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 10")
        return

    data = []
    for scenario in scenarios:
        path = f"{CSV_DIR}/{scenario}_status.csv"
        if not os.path.exists(path):
            print(f"⚠️  Sem status.csv para {scenario}")
            continue
        df = pd.read_csv(path)
        for version in ['V1', 'V2', 'V3', 'V4']:
            if version in df['Version'].values:
                value = df[df['Version'] == version]['API Failure Rate (%)'].values[0]
                data.append({
                    'Scenario': scenario_label(scenario),
                    'Version': version,
                    'Error Rate (%)': value
                })

    if not data:
        print("⚠️  Sem dados para o gráfico 10")
        return

    df_plot = pd.DataFrame(data)
    unique_scenarios = [scenario_label(s) for s in scenarios if scenario_label(s) in df_plot['Scenario'].unique()]
    if not unique_scenarios:
        print("⚠️  Sem cenários válidos para o gráfico 10")
        return
    x = np.arange(len(unique_scenarios))
    
    fig, ax = plt.subplots(figsize=(14, 6))
    available_versions = df_plot['Version'].unique()
    available_versions = sorted(available_versions, key=lambda v: int(v[1:])) # Sort versions V1, V2, V3, V4
    width = 0.8 / len(available_versions)

    for i, v in enumerate(available_versions):
        v_data = [df_plot[(df_plot['Scenario'] == label) & (df_plot['Version'] == v)]['Error Rate (%)'].iloc[0]
                  if not df_plot[(df_plot['Scenario'] == label) & (df_plot['Version'] == v)].empty else 0
                  for label in unique_scenarios]
        offset = (i - len(available_versions)/2.0 + 0.5) * width # Center the group of bars
        bars = ax.bar(x + offset, v_data, width, label=v, color=COLORS.get(v), alpha=0.85)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height, f"{height:.1f}%", 
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(unique_scenarios)
    ax.set_ylabel('Error Rate 500 (%)', fontsize=12, fontweight='bold')
    ax.set_title('Error Rate (HTTP 500) - V1 to V4', fontsize=14, fontweight='bold', pad=15)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/10_error_rates{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 10 gerado: Taxa de Erro HTTP 500")

def plot_11_downtime_availability(scenarios):
    """Gráfico 11: Downtime e Disponibilidade estimados"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para o gráfico 11")
        return

    downtime_records = []
    availability_records = []

    for scenario in scenarios:
        path = f"{CSV_DIR}/{scenario}_benefits.csv"
        if not os.path.exists(path):
            print(f"⚠️  Sem benefits.csv para {scenario}")
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue
        row = df.iloc[0]  # Benefits CSV has one row per scenario
        for v in ['V1', 'V2']:
            avail_col = f'{v} Availability (%)'
            down_col = f'{v} Downtime (s)'
            if avail_col in df.columns:
                downtime_records.append({
                    'Scenario': scenario_label(scenario),
                    'Version': v,
                    'Value': row.get(down_col, 0) / 60 if pd.notna(row.get(down_col, np.nan)) else 0,
                })
                availability_records.append({
                    'Scenario': scenario_label(scenario),
                    'Version': v,
                    'Value': row.get(avail_col, 0),
                })

    if not downtime_records:
        print("⚠️  Sem dados de downtime para o gráfico 11")
        return

    downtime_df = pd.DataFrame(downtime_records)
    availability_df = pd.DataFrame(availability_records)
    unique_scenarios = downtime_df['Scenario'].unique()
    x = np.arange(len(unique_scenarios))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    available_versions = downtime_df['Version'].unique()
    available_versions = sorted(available_versions, key=lambda v: int(v[1:])) # Sort versions V1, V2, V3, V4
    width = 0.8 / len(available_versions)

    for i, v in enumerate(available_versions):
        v_data = [downtime_df[(downtime_df['Scenario'] == label) & (downtime_df['Version'] == v)]['Value'].iloc[0] 
                  if not downtime_df[(downtime_df['Scenario'] == label) & (downtime_df['Version'] == v)].empty else 0
                  for label in unique_scenarios]
        offset = (i - len(available_versions)/2.0 + 0.5) * width # Center the group of bars
        bars = ax1.bar(x + offset, v_data, width, label=v, color=COLORS.get(v), alpha=0.85)
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height, f"{height:.1f}", 
                        ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(unique_scenarios)
    ax1.set_ylabel('Effective Downtime (min)', fontsize=12, fontweight='bold')
    ax1.set_title('Estimated Downtime (Uptime = 200 + 202)', fontsize=13, fontweight='bold', pad=15)
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)

    for v in available_versions:
        v_data = [availability_df[(availability_df['Scenario'] == label) & (availability_df['Version'] == v)]['Value'].iloc[0] 
                  if not availability_df[(availability_df['Scenario'] == label) & (availability_df['Version'] == v)].empty else 0
                  for label in unique_scenarios]
        ax2.plot(unique_scenarios, v_data, 'o-', label=v, color=COLORS.get(v), linewidth=2)
    
    ax2.set_ylabel('Availability (%)', fontsize=12, fontweight='bold')
    ax2.set_ylim(-5, 105)
    ax2.set_title('Effective Availability (200 + 202)', fontsize=13, fontweight='bold', pad=15)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/11_downtime_availability{LANG_SUFFIX}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Gráfico 11 gerado: Downtime e Disponibilidade")

def generate_summary_table(scenarios):
    """Gera tabela resumo em formato markdown"""
    if not scenarios:
        print("⚠️  Nenhum cenário disponível para a tabela resumo")
        return
    summary = []
    
    for scenario in scenarios:
        status = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        v1 = status[status['Version'] == 'V1'].iloc[0]
        
        row = {'Scenario': scenario_label(scenario)}
        for v in ['V1', 'V2', 'V3', 'V4']:
            if v in status['Version'].values:
                v_data = status[status['Version'] == v].iloc[0]
                row[f'{v} Success'] = f"{v_data['Total Success Rate (%)']:.1f}%"
                if v != 'V1':
                    row[f'Gain {v}'] = f"{v_data['Total Success Rate (%)'] - v1['Total Success Rate (%)']:+.1f}pp"
        
        summary.append(row)
    
    df = pd.DataFrame(summary)
    
    # Salvar como CSV
    df.to_csv(f'{OUTPUT_DIR}/summary_table.csv', index=False)
    
    # Gerar markdown
    md_table = df.to_markdown(index=False)
    with open(f'{OUTPUT_DIR}/summary_table.md', 'w') as f:
        f.write("# Summary Table - Final Analysis\n\n")
        f.write(md_table)
    
    print("✅ Tabela resumo gerada")
    print(df.to_string(index=False))

def main():
    """Generates all charts"""
    global LANG, LANG_SUFFIX
    
    parser = argparse.ArgumentParser(description='Generate final charts for TCC analysis')
    parser.add_argument('--lang', choices=['en', 'pt'], default='en', help='Language for labels (en/pt)')
    args = parser.parse_args()
    
    LANG = args.lang
    LANG_SUFFIX = f'_{LANG}'
    
    print("\n" + "="*60)
    print(f"  CHART GENERATION - TCC FINAL ANALYSIS ({LANG.upper()})")
    print("="*60 + "\n")
    scenarios = get_available_scenarios()
    if not scenarios:
        print("❌ Nenhum cenário encontrado em analysis_results/scenarios/csv")
        return
    
    try:
        plot_1_success_rates_comparison(scenarios)
        plot_2_failure_reduction(scenarios)
        plot_3_response_time_percentiles(scenarios)
        plot_4_throughput_comparison(scenarios)
        plot_5_status_distribution(scenarios)
        plot_6_consolidated_metrics(scenarios)
        plot_7_catastrofe_timeline()
        plot_8_fallback_contribution(scenarios)
        plot_9_avg_response_times(scenarios)
        plot_10_error_rates(scenarios)
        plot_11_downtime_availability(scenarios)
        generate_summary_table(scenarios)
        
        print("\n" + "="*60)
        print(f"✅ ALL CHARTS GENERATED SUCCESSFULLY! (Language: {LANG.upper()})")
        print(f"📁 Location: {OUTPUT_DIR}/")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar gráficos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
