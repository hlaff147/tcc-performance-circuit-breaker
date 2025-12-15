"""
Gerador de Artefatos LaTeX para TCC

Este módulo gera tabelas e figuras em formato LaTeX prontas para
inclusão no documento final do TCC.

Características:
- Tabelas formatadas com booktabs
- Gráficos em 300 DPI (qualidade de impressão)
- Figuras com labels e captions em português
- Exportação automática de dados para CSV
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend não-interativo para gerar arquivos
import seaborn as sns
from typing import Dict, List, Optional
from datetime import datetime

# Configurações de estilo
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.figsize': (8, 5),
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})

# Paleta de cores consistente
COLORS = {
    'v1': '#E74C3C',      # Vermelho para baseline
    'v2': '#27AE60',      # Verde para CB
    'success': '#2ECC71', # Verde claro
    'fallback': '#F39C12', # Laranja
    'failure': '#E74C3C', # Vermelho
    'cb_open': '#9B59B6', # Roxo
}


class LaTeXGenerator:
    """
    Gerador de artefatos LaTeX para o TCC.
    """
    
    def __init__(self, output_dir: str = "analysis_results"):
        """
        Inicializa o gerador.
        
        Args:
            output_dir: Diretório base para saída
        """
        self.output_dir = output_dir
        self.latex_dir = os.path.join(output_dir, "latex")
        self.figures_dir = os.path.join(output_dir, "figures_hires")
        self.csv_dir = os.path.join(output_dir, "csv")
        
        # Criar diretórios
        for d in [self.latex_dir, self.figures_dir, self.csv_dir]:
            os.makedirs(d, exist_ok=True)
    
    def generate_comparison_table(self, scenarios: List[Dict], 
                                   caption: str = "Comparação de Métricas V1 vs V2") -> str:
        """
        Gera tabela LaTeX comparando métricas entre cenários.
        
        Args:
            scenarios: Lista de dicionários com dados dos cenários
            caption: Legenda da tabela
            
        Returns:
            Código LaTeX da tabela
        """
        latex = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{{caption}}}
\\label{{tab:comparacao_cenarios}}
\\begin{{tabular}}{{@{{}}lrrrrr@{{}}}}
\\toprule
\\textbf{{Cenário}} & \\textbf{{Sucesso V1}} & \\textbf{{Disp. V2}} & \\textbf{{Fallback V2}} & \\textbf{{Redução Falhas}} & \\textbf{{Ganho Latência}} \\\\
\\midrule
"""
        
        for scenario in scenarios:
            name = scenario.get('name', 'N/A')
            success_v1 = scenario.get('success_v1', 0)
            availability_v2 = scenario.get('availability_v2', 0)
            fallback_v2 = scenario.get('fallback_v2', 0)
            failure_reduction = scenario.get('failure_reduction', 0)
            latency_gain = scenario.get('latency_gain', 0)
            
            latex += f"{name} & {success_v1:.1f}\\% & {availability_v2:.1f}\\% & {fallback_v2:.1f}\\% & {failure_reduction:.1f}\\% & {latency_gain:.1f}\\% \\\\\n"
        
        latex += """\\bottomrule
\\end{tabular}
\\end{table}
"""
        return latex
    
    def generate_statistical_table(self, stats: Dict, 
                                    caption: str = "Análise Estatística") -> str:
        """
        Gera tabela LaTeX com resultados estatísticos.
        """
        latex = f"""
\\begin{{table}}[htbp]
\\centering
\\caption{{{caption}}}
\\label{{tab:estatistica}}
\\begin{{tabular}}{{@{{}}lcc@{{}}}}
\\toprule
\\textbf{{Teste}} & \\textbf{{Estatística}} & \\textbf{{Resultado}} \\\\
\\midrule
Mann-Whitney U & $p = {stats.get('p_value', 0):.4f}$ & {('Significativo ($p < 0.05$)' if stats.get('significant', False) else 'Não significativo')} \\\\
Cliff's Delta & $\\delta = {stats.get('cliffs_delta', 0):.3f}$ & Efeito {stats.get('effect_size', 'N/A')} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
        return latex
    
    def plot_response_time_comparison(self, v1_times: np.ndarray, v2_times: np.ndarray,
                                       filename: str = "response_times_comparison.png") -> str:
        """
        Gera gráfico de comparação de tempos de resposta.
        
        Returns:
            Caminho do arquivo gerado
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Boxplot
        ax1 = axes[0]
        data = [v1_times, v2_times]
        bp = ax1.boxplot(data, labels=['V1 (Baseline)', 'V2 (Circuit Breaker)'],
                         patch_artist=True, showfliers=False)
        bp['boxes'][0].set_facecolor(COLORS['v1'])
        bp['boxes'][1].set_facecolor(COLORS['v2'])
        bp['boxes'][0].set_alpha(0.7)
        bp['boxes'][1].set_alpha(0.7)
        ax1.set_ylabel('Tempo de Resposta (ms)')
        ax1.set_title('Distribuição do Tempo de Resposta')
        
        # Histograma
        ax2 = axes[1]
        ax2.hist(v1_times, bins=50, alpha=0.6, label='V1', color=COLORS['v1'], density=True)
        ax2.hist(v2_times, bins=50, alpha=0.6, label='V2', color=COLORS['v2'], density=True)
        ax2.set_xlabel('Tempo de Resposta (ms)')
        ax2.set_ylabel('Densidade')
        ax2.set_title('Distribuição de Latência')
        ax2.legend()
        
        plt.tight_layout()
        filepath = os.path.join(self.figures_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def plot_scenario_comparison(self, scenarios_data: List[Dict],
                                  filename: str = "scenarios_comparison.png") -> str:
        """
        Gera gráfico de barras comparando cenários.
        """
        names = [s['name'] for s in scenarios_data]
        v1_success = [s.get('success_v1', 0) for s in scenarios_data]
        v2_availability = [s.get('availability_v2', 0) for s in scenarios_data]
        
        x = np.arange(len(names))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width/2, v1_success, width, label='V1 (Sucesso)', 
                       color=COLORS['v1'], alpha=0.8)
        bars2 = ax.bar(x + width/2, v2_availability, width, label='V2 (Disponibilidade)', 
                       color=COLORS['v2'], alpha=0.8)
        
        ax.set_ylabel('Taxa (%)')
        ax.set_title('Comparação de Disponibilidade por Cenário')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=15, ha='right')
        ax.legend()
        ax.set_ylim(0, 105)
        
        # Adicionar valores nas barras
        for bar in bars1 + bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}%',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        filepath = os.path.join(self.figures_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def plot_status_distribution(self, v1_status: Dict, v2_status: Dict,
                                  filename: str = "status_distribution.png") -> str:
        """
        Gera gráfico de pizza mostrando distribuição de status HTTP.
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # V1
        labels_v1 = list(v1_status.keys())
        values_v1 = list(v1_status.values())
        colors_v1 = [COLORS.get(l.lower(), '#888888') for l in labels_v1]
        axes[0].pie(values_v1, labels=labels_v1, autopct='%1.1f%%', colors=colors_v1)
        axes[0].set_title('V1 - Distribuição de Respostas')
        
        # V2
        labels_v2 = list(v2_status.keys())
        values_v2 = list(v2_status.values())
        colors_v2 = [COLORS.get(l.lower(), '#888888') for l in labels_v2]
        axes[1].pie(values_v2, labels=labels_v2, autopct='%1.1f%%', colors=colors_v2)
        axes[1].set_title('V2 - Distribuição de Respostas')
        
        plt.tight_layout()
        filepath = os.path.join(self.figures_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def plot_timeline(self, v1_timeline: pd.DataFrame, v2_timeline: pd.DataFrame,
                      metric: str = 'latency', filename: str = "timeline.png") -> str:
        """
        Gera gráfico de série temporal.
        """
        fig, ax = plt.subplots(figsize=(12, 5))
        
        ax.plot(v1_timeline['timestamp'], v1_timeline[metric], 
                label='V1', color=COLORS['v1'], alpha=0.7, linewidth=1)
        ax.plot(v2_timeline['timestamp'], v2_timeline[metric], 
                label='V2', color=COLORS['v2'], alpha=0.7, linewidth=1)
        
        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel('Latência (ms)' if metric == 'latency' else metric)
        ax.set_title('Evolução Temporal da Latência')
        ax.legend()
        
        plt.tight_layout()
        filepath = os.path.join(self.figures_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_figure_latex(self, filepath: str, caption: str, label: str,
                               width: str = "0.9\\textwidth") -> str:
        """
        Gera código LaTeX para incluir uma figura.
        """
        filename = os.path.basename(filepath)
        
        return f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width={width}]{{images/{filename}}}
\\caption{{{caption}}}
\\label{{fig:{label}}}
\\end{{figure}}
"""
    
    def generate_all_artifacts(self, data: Dict) -> Dict[str, str]:
        """
        Gera todos os artefatos LaTeX e figuras.
        
        Args:
            data: Dicionário com todos os dados necessários
            
        Returns:
            Dicionário com caminhos dos arquivos gerados
        """
        generated = {}
        
        # Gerar arquivo principal LaTeX
        latex_content = f"""% Artefatos LaTeX - TCC Circuit Breaker
% Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
% 
% Para usar, inclua no seu documento LaTeX:
%   \\input{{analysis_results/latex/tables.tex}}

"""
        
        # Adicionar tabelas se houver dados
        if 'scenarios' in data:
            latex_content += self.generate_comparison_table(data['scenarios'])
            latex_content += "\n"
        
        if 'statistics' in data:
            latex_content += self.generate_statistical_table(data['statistics'])
            latex_content += "\n"
        
        # Salvar arquivo LaTeX
        latex_path = os.path.join(self.latex_dir, "tables.tex")
        with open(latex_path, 'w') as f:
            f.write(latex_content)
        generated['latex_tables'] = latex_path
        
        # Gerar figuras se houver dados de latência
        if 'v1_latencies' in data and 'v2_latencies' in data:
            fig_path = self.plot_response_time_comparison(
                data['v1_latencies'], 
                data['v2_latencies']
            )
            generated['response_times_figure'] = fig_path
        
        if 'scenarios' in data:
            fig_path = self.plot_scenario_comparison(data['scenarios'])
            generated['scenarios_figure'] = fig_path
        
        # Gerar arquivo de figuras LaTeX
        figures_latex = "% Figuras - TCC Circuit Breaker\n\n"
        for key, path in generated.items():
            if 'figure' in key:
                label = key.replace('_figure', '')
                caption = key.replace('_', ' ').title()
                figures_latex += self.generate_figure_latex(path, caption, label)
        
        figures_path = os.path.join(self.latex_dir, "figures.tex")
        with open(figures_path, 'w') as f:
            f.write(figures_latex)
        generated['latex_figures'] = figures_path
        
        print(f"\nArtefatos gerados:")
        for name, path in generated.items():
            print(f"  {name}: {path}")
        
        return generated


if __name__ == "__main__":
    print("=" * 60)
    print("Gerador de Artefatos LaTeX - TCC Circuit Breaker")
    print("=" * 60)
    
    # Dados de exemplo (substituir por dados reais)
    sample_data = {
        'scenarios': [
            {'name': 'Catástrofe', 'success_v1': 90.0, 'availability_v2': 94.5, 
             'fallback_v2': 59.0, 'failure_reduction': 44.8, 'latency_gain': 60.0},
            {'name': 'Degradação', 'success_v1': 94.7, 'availability_v2': 94.9, 
             'fallback_v2': 0.0, 'failure_reduction': 4.2, 'latency_gain': 0.4},
            {'name': 'Rajadas', 'success_v1': 94.9, 'availability_v2': 95.2, 
             'fallback_v2': 10.2, 'failure_reduction': 5.8, 'latency_gain': 11.0},
            {'name': 'Extrema (75% OFF)', 'success_v1': 10.1, 'availability_v2': 97.1, 
             'fallback_v2': 92.8, 'failure_reduction': 96.8, 'latency_gain': 75.0},
        ],
        'statistics': {
            'p_value': 0.0001,
            'significant': True,
            'cliffs_delta': 0.45,
            'effect_size': 'médio'
        },
        'v1_latencies': np.random.exponential(500, 10000),
        'v2_latencies': np.random.exponential(300, 10000),
    }
    
    generator = LaTeXGenerator()
    artifacts = generator.generate_all_artifacts(sample_data)
    
    print("\n✅ Artefatos LaTeX gerados com sucesso!")
    print(f"\nPara usar no LaTeX, adicione no preâmbulo:")
    print("  \\usepackage{booktabs}")
    print("  \\usepackage{graphicx}")
    print("\nE inclua as tabelas com:")
    print("  \\input{analysis_results/latex/tables.tex}")
