"""
Módulo de Análise Estatística Científica para TCC

Este módulo implementa testes estatísticos rigorosos para comparação
entre V1 (baseline) e V2 (circuit breaker), incluindo:

- Mann-Whitney U Test: Teste não-paramétrico para diferença de distribuições
- Cliff's Delta: Tamanho do efeito para dados ordinais
- Bootstrap Confidence Intervals: Intervalos de confiança robustos
- Shapiro-Wilk Test: Teste de normalidade

Uso:
    from statistical_analyzer import StatisticalAnalyzer
    analyzer = StatisticalAnalyzer()
    results = analyzer.compare_versions(v1_latencies, v2_latencies)
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import json
import os


class StatisticalAnalyzer:
    """
    Analisador estatístico para comparação rigorosa entre versões.
    """
    
    # Limiares para interpretação do Cliff's Delta
    CLIFFS_DELTA_THRESHOLDS = {
        'negligible': 0.147,
        'small': 0.33,
        'medium': 0.474,
        'large': 1.0
    }
    
    def __init__(self, alpha: float = 0.05):
        """
        Inicializa o analisador.
        
        Args:
            alpha: Nível de significância para testes (padrão: 0.05)
        """
        self.alpha = alpha
        self.results = {}
    
    def cliffs_delta(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, str]:
        """
        Calcula o Cliff's Delta (tamanho do efeito) entre duas amostras.
        
        Cliff's Delta é uma medida não-paramétrica do tamanho do efeito
        que quantifica a probabilidade de um valor de uma amostra ser
        maior que um valor de outra amostra.
        
        Interpretação:
        - |d| < 0.147: Negligenciável
        - 0.147 <= |d| < 0.33: Pequeno
        - 0.33 <= |d| < 0.474: Médio
        - |d| >= 0.474: Grande
        
        Args:
            x: Primeira amostra (V1)
            y: Segunda amostra (V2)
            
        Returns:
            Tupla (delta, interpretação)
        """
        n_x, n_y = len(x), len(y)
        
        # Conta pares onde x > y, x < y
        dominance = 0
        for xi in x:
            dominance += np.sum(xi > y) - np.sum(xi < y)
        
        delta = dominance / (n_x * n_y)
        
        # Interpretação
        abs_delta = abs(delta)
        if abs_delta < self.CLIFFS_DELTA_THRESHOLDS['negligible']:
            interpretation = 'negligible'
        elif abs_delta < self.CLIFFS_DELTA_THRESHOLDS['small']:
            interpretation = 'small'
        elif abs_delta < self.CLIFFS_DELTA_THRESHOLDS['medium']:
            interpretation = 'medium'
        else:
            interpretation = 'large'
        
        return delta, interpretation
    
    def mann_whitney_u(self, x: np.ndarray, y: np.ndarray) -> Dict:
        """
        Executa o teste Mann-Whitney U (Wilcoxon rank-sum).
        
        Este é o teste não-paramétrico preferido para comparar duas
        distribuições independentes quando não podemos assumir normalidade.
        
        H0: As duas amostras vêm da mesma distribuição
        H1: As duas amostras vêm de distribuições diferentes
        
        Args:
            x: Primeira amostra (V1)
            y: Segunda amostra (V2)
            
        Returns:
            Dicionário com estatística U, p-valor e conclusão
        """
        statistic, p_value = stats.mannwhitneyu(x, y, alternative='two-sided')
        
        # Calcula rank-biserial correlation como medida de efeito
        n1, n2 = len(x), len(y)
        r = 1 - (2 * statistic) / (n1 * n2)
        
        return {
            'statistic': statistic,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'rank_biserial_r': r,
            'interpretation': 'Diferença significativa' if p_value < self.alpha else 'Sem diferença significativa'
        }
    
    def shapiro_wilk(self, x: np.ndarray, sample_size: int = 5000) -> Dict:
        """
        Executa o teste de normalidade Shapiro-Wilk.
        
        Nota: Para amostras muito grandes, usamos uma subamostra aleatória.
        
        Args:
            x: Amostra a ser testada
            sample_size: Tamanho máximo da amostra para o teste
            
        Returns:
            Dicionário com estatística, p-valor e conclusão
        """
        # Shapiro-Wilk tem limite de 5000 observações
        if len(x) > sample_size:
            x = np.random.choice(x, sample_size, replace=False)
        
        statistic, p_value = stats.shapiro(x)
        
        return {
            'statistic': statistic,
            'p_value': p_value,
            'is_normal': p_value >= self.alpha,
            'interpretation': 'Distribuição normal' if p_value >= self.alpha else 'Distribuição não-normal'
        }
    
    def bootstrap_ci(self, x: np.ndarray, statistic_func=np.mean, 
                     n_bootstrap: int = 10000, ci: float = 0.95) -> Dict:
        """
        Calcula intervalo de confiança usando bootstrap.
        
        Bootstrap é um método de reamostragem que não assume distribuição
        específica dos dados.
        
        Args:
            x: Amostra
            statistic_func: Função estatística (np.mean, np.median, etc.)
            n_bootstrap: Número de amostras bootstrap
            ci: Nível de confiança (padrão: 0.95)
            
        Returns:
            Dicionário com estimativa pontual e IC
        """
        n = len(x)
        bootstrap_stats = np.zeros(n_bootstrap)
        
        for i in range(n_bootstrap):
            sample = np.random.choice(x, n, replace=True)
            bootstrap_stats[i] = statistic_func(sample)
        
        alpha = 1 - ci
        lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
        upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
        
        return {
            'estimate': statistic_func(x),
            'ci_lower': lower,
            'ci_upper': upper,
            'ci_level': ci,
            'std_error': np.std(bootstrap_stats)
        }
    
    def compare_versions(self, v1_data: np.ndarray, v2_data: np.ndarray,
                         metric_name: str = 'latency') -> Dict:
        """
        Executa análise estatística completa comparando duas versões.
        
        Args:
            v1_data: Dados da V1 (baseline)
            v2_data: Dados da V2 (circuit breaker)
            metric_name: Nome da métrica sendo analisada
            
        Returns:
            Dicionário completo com todos os resultados estatísticos
        """
        results = {
            'metric': metric_name,
            'n_v1': len(v1_data),
            'n_v2': len(v2_data),
        }
        
        # Estatísticas descritivas
        results['descriptive'] = {
            'v1': {
                'mean': np.mean(v1_data),
                'median': np.median(v1_data),
                'std': np.std(v1_data),
                'min': np.min(v1_data),
                'max': np.max(v1_data),
                'p25': np.percentile(v1_data, 25),
                'p75': np.percentile(v1_data, 75),
                'p95': np.percentile(v1_data, 95),
                'p99': np.percentile(v1_data, 99),
            },
            'v2': {
                'mean': np.mean(v2_data),
                'median': np.median(v2_data),
                'std': np.std(v2_data),
                'min': np.min(v2_data),
                'max': np.max(v2_data),
                'p25': np.percentile(v2_data, 25),
                'p75': np.percentile(v2_data, 75),
                'p95': np.percentile(v2_data, 95),
                'p99': np.percentile(v2_data, 99),
            }
        }
        
        # Teste de normalidade
        results['normality'] = {
            'v1': self.shapiro_wilk(v1_data),
            'v2': self.shapiro_wilk(v2_data)
        }
        
        # Mann-Whitney U (teste não-paramétrico)
        results['mann_whitney'] = self.mann_whitney_u(v1_data, v2_data)
        
        # Cliff's Delta (tamanho do efeito)
        delta, interpretation = self.cliffs_delta(v1_data, v2_data)
        results['cliffs_delta'] = {
            'delta': delta,
            'interpretation': interpretation,
            'direction': 'V1 > V2' if delta > 0 else 'V2 > V1'
        }
        
        # Bootstrap CI para diferença das médias
        mean_diff = np.mean(v1_data) - np.mean(v2_data)
        results['mean_difference'] = {
            'value': mean_diff,
            'percent_change': (mean_diff / np.mean(v1_data)) * 100 if np.mean(v1_data) != 0 else 0
        }
        
        # Intervalos de confiança bootstrap
        results['bootstrap_ci'] = {
            'v1_mean': self.bootstrap_ci(v1_data, np.mean),
            'v2_mean': self.bootstrap_ci(v2_data, np.mean),
            'v1_median': self.bootstrap_ci(v1_data, np.median),
            'v2_median': self.bootstrap_ci(v2_data, np.median),
        }
        
        return results
    
    def generate_latex_table(self, results: Dict, caption: str = "Análise Estatística") -> str:
        """
        Gera tabela LaTeX formatada com os resultados.
        
        Args:
            results: Dicionário de resultados do compare_versions
            caption: Legenda da tabela
            
        Returns:
            String com código LaTeX da tabela
        """
        desc_v1 = results['descriptive']['v1']
        desc_v2 = results['descriptive']['v2']
        mw = results['mann_whitney']
        cd = results['cliffs_delta']
        
        latex = f"""
\\begin{{table}}[H]
\\centering
\\caption{{{caption}}}
\\label{{tab:{results['metric'].replace(' ', '_').lower()}}}
\\begin{{tabular}}{{lrrl}}
\\toprule
\\textbf{{Métrica}} & \\textbf{{V1 (Baseline)}} & \\textbf{{V2 (CB)}} & \\textbf{{Diferença}} \\\\
\\midrule
N (amostras) & {results['n_v1']:,} & {results['n_v2']:,} & -- \\\\
Média (ms) & {desc_v1['mean']:.2f} & {desc_v2['mean']:.2f} & {results['mean_difference']['percent_change']:.1f}\\% \\\\
Mediana (ms) & {desc_v1['median']:.2f} & {desc_v2['median']:.2f} & -- \\\\
Desvio Padrão & {desc_v1['std']:.2f} & {desc_v2['std']:.2f} & -- \\\\
P95 (ms) & {desc_v1['p95']:.2f} & {desc_v2['p95']:.2f} & -- \\\\
P99 (ms) & {desc_v1['p99']:.2f} & {desc_v2['p99']:.2f} & -- \\\\
\\midrule
\\multicolumn{{4}}{{l}}{{\\textit{{Testes Estatísticos}}}} \\\\
\\midrule
Mann-Whitney U & \\multicolumn{{2}}{{c}}{{p = {mw['p_value']:.4f}}} & {'Significativo' if mw['significant'] else 'Não significativo'} \\\\
Cliff's Delta & \\multicolumn{{2}}{{c}}{{$\\delta$ = {cd['delta']:.3f}}} & {cd['interpretation'].capitalize()} \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
        return latex
    
    def generate_summary_report(self, all_results: List[Dict], output_dir: str) -> None:
        """
        Gera relatório completo com todos os resultados estatísticos.
        
        Args:
            all_results: Lista de resultados de compare_versions
            output_dir: Diretório de saída
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Salvar JSON com todos os resultados
        json_path = os.path.join(output_dir, 'statistical_analysis.json')
        with open(json_path, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        # Gerar arquivo LaTeX com todas as tabelas
        latex_path = os.path.join(output_dir, 'statistical_tables.tex')
        with open(latex_path, 'w') as f:
            f.write("% Tabelas de Análise Estatística - Gerado Automaticamente\n")
            f.write("% Data: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            
            for result in all_results:
                caption = f"Análise Estatística - {result['metric'].replace('_', ' ').title()}"
                f.write(self.generate_latex_table(result, caption))
                f.write("\n\n")
        
        # Gerar resumo em Markdown
        md_path = os.path.join(output_dir, 'statistical_summary.md')
        with open(md_path, 'w') as f:
            f.write("# Resumo da Análise Estatística\n\n")
            f.write(f"**Data:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in all_results:
                mw = result['mann_whitney']
                cd = result['cliffs_delta']
                diff = result['mean_difference']
                
                f.write(f"## {result['metric'].replace('_', ' ').title()}\n\n")
                f.write(f"- **Amostras:** V1={result['n_v1']:,}, V2={result['n_v2']:,}\n")
                f.write(f"- **Diferença na Média:** {diff['percent_change']:.1f}%\n")
                f.write(f"- **Mann-Whitney U:** p={mw['p_value']:.4f} ({'✅ Significativo' if mw['significant'] else '❌ Não significativo'})\n")
                f.write(f"- **Cliff's Delta:** δ={cd['delta']:.3f} ({cd['interpretation']})\n")
                f.write(f"- **Direção:** {cd['direction']}\n\n")
        
        print(f"Relatórios estatísticos gerados em: {output_dir}")


def load_k6_latencies(json_path: str) -> np.ndarray:
    """
    Carrega latências de um arquivo de resultados K6.
    
    Args:
        json_path: Caminho para o arquivo JSON do K6
        
    Returns:
        Array numpy com as latências
    """
    latencies = []
    
    with open(json_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('type') == 'Point' and data.get('metric') == 'http_req_duration':
                    latencies.append(data['data']['value'])
            except json.JSONDecodeError:
                continue
    
    return np.array(latencies)


if __name__ == "__main__":
    # Exemplo de uso
    print("=" * 60)
    print("Análise Estatística - TCC Circuit Breaker")
    print("=" * 60)
    
    # Caminhos dos arquivos
    results_dir = "k6/results"
    output_dir = "analysis_results/statistical"
    
    v1_path = os.path.join(results_dir, "V1_Completo.json")
    v2_path = os.path.join(results_dir, "V2_Completo.json")
    
    if os.path.exists(v1_path) and os.path.exists(v2_path):
        print("\nCarregando dados...")
        v1_latencies = load_k6_latencies(v1_path)
        v2_latencies = load_k6_latencies(v2_path)
        
        print(f"V1: {len(v1_latencies):,} amostras")
        print(f"V2: {len(v2_latencies):,} amostras")
        
        # Executar análise
        analyzer = StatisticalAnalyzer()
        results = analyzer.compare_versions(v1_latencies, v2_latencies, 'Latência HTTP')
        
        # Gerar relatórios
        analyzer.generate_summary_report([results], output_dir)
        
        # Exibir resumo
        print("\n" + "=" * 60)
        print("RESUMO DOS RESULTADOS")
        print("=" * 60)
        
        print(f"\nMédia V1: {results['descriptive']['v1']['mean']:.2f} ms")
        print(f"Média V2: {results['descriptive']['v2']['mean']:.2f} ms")
        print(f"Diferença: {results['mean_difference']['percent_change']:.1f}%")
        
        print(f"\nMann-Whitney U: p={results['mann_whitney']['p_value']:.4f}")
        print(f"  → {'Diferença SIGNIFICATIVA' if results['mann_whitney']['significant'] else 'Sem diferença significativa'}")
        
        print(f"\nCliff's Delta: δ={results['cliffs_delta']['delta']:.3f}")
        print(f"  → Efeito: {results['cliffs_delta']['interpretation'].upper()}")
        print(f"  → {results['cliffs_delta']['direction']}")
        
    else:
        print(f"Arquivos não encontrados:")
        print(f"  V1: {v1_path} - {'✅' if os.path.exists(v1_path) else '❌'}")
        print(f"  V2: {v2_path} - {'✅' if os.path.exists(v2_path) else '❌'}")
        print("\nExecute os experimentos primeiro com: ./run-experiments.sh")
