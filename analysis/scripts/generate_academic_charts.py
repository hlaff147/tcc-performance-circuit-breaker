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
}

VERSION_LABELS = {
    'V1': 'V1 (Baseline)',
    'V2_equilibrado': 'V2 CB (Equilibrado)',
    'V2_conservador': 'V2 CB (Conservador)',
    'V2_agressivo': 'V2 CB (Agressivo)',
    'V3': 'V3 (Retry)',
}


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
    parser = argparse.ArgumentParser(description='Gerador de gráficos acadêmicos')
    parser.add_argument('--data-dir', default='analysis_results', help='Diretório com dados')
    parser.add_argument('--output-dir', default='analysis_results/academic_charts', help='Diretório de saída')
    parser.add_argument('--demo', action='store_true', help='Gerar gráficos de demonstração')
    
    args = parser.parse_args()
    
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
    print(f"📁 Dados: {args.data_dir}")
    print(f"📁 Saída: {args.output_dir}")
    print("\nℹ️ Use --demo para gerar gráficos de demonstração")


if __name__ == '__main__':
    main()
