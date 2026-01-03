#!/usr/bin/env python3
"""
Academic Chart Generator for TCC
Gera visualizações otimizadas para publicação acadêmica.

Features:
- Box plots com whiskers
- Heatmaps de correlação e performance
- Violin plots para distribuições
- Exportação em alta resolução (300 DPI)

Uso:
    python generate_academic_charts.py --data-dir analysis_results/ --output-dir analysis_results/academic_charts/
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

# Configuração acadêmica
plt.style.use('seaborn-v0_8-whitegrid')
ACADEMIC_CONFIG = {
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'figure.figsize': (10, 6),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.format': 'png',
    'savefig.bbox': 'tight',
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'axes.titleweight': 'bold',
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
}
plt.rcParams.update(ACADEMIC_CONFIG)

# Paletas de cores acadêmicas
COLORS = {
    'V1': '#7f8c8d',      # Cinza (baseline)
    'V2_equilibrado': '#27ae60',  # Verde
    'V2_conservador': '#2980b9',  # Azul
    'V2_agressivo': '#c0392b',    # Vermelho
    'V3': '#8e44ad',      # Roxo
    'V4': '#e67e22',      # Laranja Cenoura (acadêmico)
}

VERSION_LABELS = {
    'V1': 'V1 (Baseline)',
    'V2_equilibrado': 'V2 CB (Balanced)',
    'V2_conservador': 'V2 CB (Conservative)',
    'V2_agressivo': 'V2 CB (Aggressive)',
    'V3': 'V3 (Retry)',
    'V4': 'V4 (Retry + CB)',
}

# Bilingual labels
LABELS = {
    'en': {
        'scenarios': {'catastrofe': 'Catastrophe', 'rajadas': 'Bursts', 'indisponibilidade': 'Unavailability', 'degradacao': 'Degradation', 'normal': 'Normal'},
        'success_title': 'Success Rate (%) by Scenario and Version',
        'availability_title': 'Availability Comparison by Strategy',
        'availability_ylabel': 'Availability (%)',
        'latency_title': 'Average Latency (ms) by Scenario',
        'latency_ylabel': 'Latency (ms)',
        'version': 'Version',
        'scenario': 'Scenario',
        'value': 'Value',
        'correlation': 'Correlation',
        'mean': 'Mean',
        'boxplot_dist': 'Latency Distribution',
        'violin_dist': 'Latency Probability Density',
    },
    'pt': {
        'scenarios': {'catastrofe': 'Catástrofe', 'rajadas': 'Rajadas', 'indisponibilidade': 'Indisponibilidade', 'degradacao': 'Degradação', 'normal': 'Normal'},
        'success_title': 'Taxa de Sucesso (%) por Cenário e Versão',
        'availability_title': 'Comparação de Disponibilidade por Estratégia',
        'availability_ylabel': 'Disponibilidade (%)',
        'latency_title': 'Latência Média (ms) por Cenário',
        'latency_ylabel': 'Latência (ms)',
        'version': 'Versão',
        'scenario': 'Cenário',
        'value': 'Valor',
        'correlation': 'Correlação',
        'mean': 'Média',
        'boxplot_dist': 'Distribuição de Latência',
        'violin_dist': 'Densidade de Probabilidade de Latência',
    }
}

# Global language (set by main)
LANG = 'en'
LANG_SUFFIX = '_en'

def scenario_label(name):
    return LABELS[LANG]['scenarios'].get(name.lower(), name.replace('_', ' ').title())


class AcademicChartGenerator:
    """Gerador de gráficos para publicação acadêmica."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def boxplot_comparison(self, data: Dict[str, np.ndarray], title: str,
                           ylabel: str, filename: str, horizontal: bool = False):
        """
        Gera box plot comparativo com anotações estatísticas.
        
        Args:
            data: Dict {versão: array de valores}
            title: Título do gráfico
            ylabel: Label do eixo Y
            filename: Nome do arquivo de saída
            horizontal: Se True, gera box plot horizontal
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        versions = list(data.keys())
        values = [data[v] for v in versions]
        labels = [VERSION_LABELS.get(v, v) for v in versions]
        colors = [COLORS.get(v, '#333333') for v in versions]
        
        if horizontal:
            bp = ax.boxplot(values, vert=False, labels=labels, patch_artist=True)
            ax.set_xlabel(ylabel)
        else:
            bp = ax.boxplot(values, labels=labels, patch_artist=True)
            ax.set_ylabel(ylabel)
            plt.xticks(rotation=15, ha='right')
        
        # Colorir boxes
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            patch.set_edgecolor('black')
            patch.set_linewidth(1.5)
        
        # Estilizar mediana
        for median in bp['medians']:
            median.set(color='black', linewidth=2)
        
        # Adicionar pontos de média
        means = [np.mean(v) for v in values]
        if horizontal:
            ax.scatter(means, range(1, len(versions)+1), color='white', 
                      marker='D', s=50, zorder=3, edgecolors='black', linewidths=1)
        else:
            ax.scatter(range(1, len(versions)+1), means, color='white',
                      marker='D', s=50, zorder=3, edgecolors='black', linewidths=1)
        
        # Adicionar estatísticas
        stats_text = []
        for v, name in zip(values, labels):
            stats_text.append(f"{name}: μ={np.mean(v):.1f}, σ={np.std(v):.1f}")
        
        ax.set_title(title, fontweight='bold', pad=15)
        
        # Legenda para média
        diamond = mpatches.Patch(facecolor='white', edgecolor='black', label='Média (◇)')
        ax.legend(handles=[diamond], loc='upper right')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Box plot salvo: {filename}")
    
    def violin_plot(self, data: Dict[str, np.ndarray], title: str,
                    ylabel: str, filename: str):
        """
        Gera violin plot para mostrar distribuição completa.
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        versions = list(data.keys())
        values = [data[v] for v in versions]
        labels = [VERSION_LABELS.get(v, v) for v in versions]
        colors = [COLORS.get(v, '#333333') for v in versions]
        
        parts = ax.violinplot(values, positions=range(1, len(versions)+1),
                              showmeans=True, showmedians=True)
        
        # Colorir violins
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[i])
            pc.set_alpha(0.7)
            pc.set_edgecolor('black')
        
        # Estilizar linhas
        parts['cmeans'].set_color('red')
        parts['cmeans'].set_linewidth(2)
        parts['cmedians'].set_color('black')
        parts['cmedians'].set_linewidth(2)
        
        ax.set_xticks(range(1, len(versions)+1))
        ax.set_xticklabels(labels, rotation=15, ha='right')
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight='bold', pad=15)
        
        # Legenda
        mean_line = plt.Line2D([0], [0], color='red', linewidth=2, label='Média')
        median_line = plt.Line2D([0], [0], color='black', linewidth=2, label='Mediana')
        ax.legend(handles=[mean_line, median_line], loc='upper right')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Violin plot salvo: {filename}")
    
    def heatmap_performance(self, data: pd.DataFrame, title: str, filename: str,
                            cmap: str = 'RdYlGn', annot_fmt: str = '.1f'):
        """
        Gera heatmap de performance (cenários × versões).
        
        Args:
            data: DataFrame com índice = cenários, colunas = versões
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Normalizar para melhor visualização
        normalized = (data - data.min().min()) / (data.max().max() - data.min().min())
        
        sns.heatmap(data, annot=True, fmt=annot_fmt, cmap=cmap,
                    ax=ax, linewidths=0.5, linecolor='white',
                    cbar_kws={'label': 'Valor'},
                    annot_kws={'size': 11})
        
        ax.set_title(title, fontweight='bold', pad=15)
        ax.set_xlabel('Versão', fontweight='bold')
        ax.set_ylabel('Cenário', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Heatmap salvo: {filename}")
    
    def heatmap_correlation(self, data: pd.DataFrame, title: str, filename: str):
        """
        Gera heatmap de correlação entre métricas.
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        corr = data.corr()
        
        # Máscara triangular superior
        mask = np.triu(np.ones_like(corr, dtype=bool))
        
        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='coolwarm',
                    ax=ax, linewidths=0.5, vmin=-1, vmax=1,
                    cbar_kws={'label': 'Correlação'},
                    annot_kws={'size': 10})
        
        ax.set_title(title, fontweight='bold', pad=15)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Heatmap de correlação salvo: {filename}")
    
    def grouped_bar_chart(self, data: pd.DataFrame, title: str,
                          ylabel: str, filename: str):
        """
        Gera gráfico de barras agrupadas (cenários × versões).
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x = np.arange(len(data.index))
        width = 0.15
        multiplier = 0
        
        for column in data.columns:
            offset = width * multiplier
            color = COLORS.get(column, '#333333')
            label = VERSION_LABELS.get(column, column)
            bars = ax.bar(x + offset, data[column], width, label=label, 
                         color=color, alpha=0.8, edgecolor='black')
            
            # Adicionar valores nas barras
            ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=8, rotation=90)
            multiplier += 1
        
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=15)
        ax.set_xticks(x + width * (len(data.columns) - 1) / 2)
        ax.set_xticklabels(data.index)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_ylim(0, data.max().max() * 1.15)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico de barras salvo: {filename}")
    
    def line_chart_timeline(self, data: Dict[str, List[float]], 
                            x_labels: List[str], title: str,
                            ylabel: str, filename: str):
        """
        Gera gráfico de linha para timeline (evolução temporal).
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(x_labels))
        
        for version, values in data.items():
            color = COLORS.get(version, '#333333')
            label = VERSION_LABELS.get(version, version)
            ax.plot(x, values, marker='o', linewidth=2, markersize=8,
                   color=color, label=label)
        
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, rotation=45, ha='right')
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_xlabel('Fase do Teste', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=15)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico de linha salvo: {filename}")
    
    def generate_comparison_summary(self, scenarios: List[str],
                                    versions: List[str],
                                    metrics: Dict[str, pd.DataFrame]):
        """
        Gera conjunto completo de gráficos comparativos.
        """
        print("\n📊 Gerando conjunto de gráficos acadêmicos...\n")
        
        for metric_name, df in metrics.items():
            # Heatmap
            self.heatmap_performance(
                df, f'{metric_name} por Cenário e Versão',
                f'heatmap_{metric_name.lower().replace(" ", "_")}.png'
            )
            
            # Barras agrupadas
            self.grouped_bar_chart(
                df, f'Comparação de {metric_name}',
                metric_name,
                f'bars_{metric_name.lower().replace(" ", "_")}.png'
            )
        
        print(f"\n✅ Gráficos salvos em: {self.output_dir}/")


def main():
    global LANG, LANG_SUFFIX
    
    parser = argparse.ArgumentParser(description='Academic Chart Generator')
    parser.add_argument('--data-dir', default='analysis_results', help='Data directory')
    parser.add_argument('--output-dir', default='analysis_results/academic_charts', help='Output directory')
    parser.add_argument('--demo', action='store_true', help='Generate demo charts')
    parser.add_argument('--lang', choices=['en', 'pt'], default='en', help='Language for labels (en/pt)')
    
    args = parser.parse_args()
    
    LANG = args.lang
    LANG_SUFFIX = f'_{LANG}'
    
    generator = AcademicChartGenerator(args.output_dir)
    
    if args.demo:
        print("\n📊 Gerando gráficos de demonstração...\n")
        
        # Dados de exemplo
        np.random.seed(42)
        demo_data = {
            'V1': np.random.normal(500, 100, 500),
            'V2_equilibrado': np.random.normal(400, 80, 500),
            'V2_conservador': np.random.normal(420, 90, 500),
            'V2_agressivo': np.random.normal(380, 70, 500),
            'V3': np.random.normal(550, 120, 500),
        }
        
        # Box plot
        generator.boxplot_comparison(
            demo_data,
            'Distribuição de Latência por Versão',
            'Latência (ms)',
            'demo_boxplot_latency.png'
        )
        
        # Violin plot
        generator.violin_plot(
            demo_data,
            'Distribuição de Latência (Violin Plot)',
            'Latência (ms)',
            'demo_violin_latency.png'
        )
        
        # Heatmap de performance
        perf_data = pd.DataFrame({
            'V1': [90.0, 94.7, 94.9, 10.1],
            'V2 (CB)': [94.5, 94.9, 95.2, 97.1],
            'V3 (Retry)': [85.0, 94.5, 88.0, 5.0],
        }, index=['Catástrofe', 'Degradação', 'Rajadas', 'Indisponibilidade'])
        
        generator.heatmap_performance(
            perf_data,
            'Taxa de Sucesso (%) por Cenário',
            'demo_heatmap_success_rate.png'
        )
        
        # Barras agrupadas
        generator.grouped_bar_chart(
            perf_data,
            'Comparação de Taxa de Sucesso por Cenário',
            'Taxa de Sucesso (%)',
            'demo_bars_success_rate.png'
        )
        
        # Heatmap de correlação
        corr_data = pd.DataFrame({
            'Taxa Sucesso': np.random.random(100),
            'Latência Média': np.random.random(100) * 500,
            'Throughput': np.random.random(100) * 100,
            'Taxa Fallback': np.random.random(100) * 50,
            'Taxa Erro': np.random.random(100) * 10,
        })
        
        generator.heatmap_correlation(
            corr_data,
            'Correlação entre Métricas',
            'demo_heatmap_correlation.png'
        )
        
        print(f"\n✅ Gráficos de demonstração salvos em: {args.output_dir}/")
        return
    
    print(f"\n📊 Gerador de gráficos acadêmicos")
    print(f"📁 Saída: {args.output_dir}")
    
    if args.demo:
        print("\n📊 Gerando gráficos de demonstração...\n")
        # ... (demo code remains or is kept for reference)
        # For brevity, I'll keep the demo logic if --demo is used
        # but the default will be real data
    
    # 1. Localizar dados de performance nos CSVs de benefícios
    csv_dir = Path("analysis_results/scenarios/csv")
    if not csv_dir.exists():
        print("❌ Diretório de CSVs não encontrado. Execute os analisadores primeiro.")
        return
        
    # Carregar dados consolidados para heatmaps e barras
    perf_file = csv_dir / "consolidated_benefits.csv"
    if perf_file.exists():
        df_perf = pd.read_csv(perf_file)
        # Transformar para o formato esperado [Scenario x Version]
        # Atualmente o consolidated_benefits.csv tem colunas como 'V1 Success Rate (%)', etc.
        # Precisamos pivotar ou extrair
        
        # Como o formato do consolidated_benefits.csv pode variar, vamos reconstruir o DataFrame de performance
        scenarios = df_perf['Scenario'].unique()
        success_data = {}
        latency_data = {}
        
        for v in ['V1', 'V2', 'V3', 'V4']:
            success_col = f'{v} Availability (%)' # Ou Total Success
            latency_col = f'{v} Avg Response (ms)' # Precisamos verificar se existe no consolidated
            
            # Vamos carregar dos arquivos de status individuais que é mais garantido
            v_success = []
            v_latency = []
            valid_scenarios = []
            
            for s in scenarios:
                status_path = csv_dir / f"{s}_status.csv"
                resp_path = csv_dir / f"{s}_response.csv"
                
                if status_path.exists() and resp_path.exists():
                    df_s = pd.read_csv(status_path)
                    df_r = pd.read_csv(resp_path)
                    
                    if v in df_s['Version'].values:
                        v_success.append(df_s[df_s['Version'] == v]['Total Success Rate (%)'].values[0])
                        v_latency.append(df_r[df_r['Version'] == v]['Avg Response (ms)'].values[0])
                        if s not in valid_scenarios: valid_scenarios.append(s)
            
            if v_success:
                success_data[v] = v_success
                latency_data[v] = v_latency
        
        # Translate scenario names in index
        translated_scenarios = [scenario_label(s) for s in valid_scenarios]
        df_success = pd.DataFrame(success_data, index=translated_scenarios)
        df_latency = pd.DataFrame(latency_data, index=translated_scenarios)
        
        generator.heatmap_performance(df_success, LABELS[LANG]['success_title'], f"academic_heatmap_success{LANG_SUFFIX}.png")
        generator.grouped_bar_chart(df_success, LABELS[LANG]['availability_title'], LABELS[LANG]['availability_ylabel'], f"academic_bars_availability{LANG_SUFFIX}.png")
        generator.heatmap_performance(df_latency, LABELS[LANG]['latency_title'], f"academic_heatmap_latency{LANG_SUFFIX}.png", cmap='YlOrRd_r')

    # 2. Carregar amostras de latência dos parquets para BoxPlots/Violin
    cache_dirs = [Path('k6/results/.cache'), Path('k6/results/scenarios/.cache')]
    for scenario in ['Completo', 'catastrofe', 'degradacao']:
        scenario_data = {}
        for c_dir in cache_dirs:
            if not c_dir.exists(): continue
            for v in ['V1', 'V2', 'V3', 'V4']:
                p_file = c_dir / (f"{v}_{scenario}.parquet" if scenario == 'Completo' else f"{scenario}_{v}.parquet")
                if p_file.exists():
                    try:
                        df_p = pd.read_parquet(p_file)
                        col = 'latency' if 'latency' in df_p.columns else ('value' if 'value' in df_p.columns else df_p.select_dtypes(include=[np.number]).columns[0])
                        scenario_data[v] = df_p[col].values
                    except: continue
        
        if scenario_data:
            sc_label = scenario_label(scenario)
            generator.boxplot_comparison(scenario_data, f"{LABELS[LANG]['boxplot_dist']} - {sc_label}", LABELS[LANG]['latency_ylabel'], f"academic_boxplot_{scenario}{LANG_SUFFIX}.png")
            generator.violin_plot(scenario_data, f"{LABELS[LANG]['violin_dist']} - {sc_label}", LABELS[LANG]['latency_ylabel'], f"academic_violin_{scenario}{LANG_SUFFIX}.png")

    print(f"\n✨ Academic charts generated successfully! (Language: {LANG.upper()})")


if __name__ == '__main__':
    main()
