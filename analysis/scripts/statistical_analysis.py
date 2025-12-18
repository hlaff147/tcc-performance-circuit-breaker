#!/usr/bin/env python3
"""
Statistical Analysis for TCC - Circuit Breaker Performance
Implementa testes estatísticos para validar hipóteses do TCC.

Testes implementados:
- Teste t de Student (comparação de 2 grupos)
- ANOVA (comparação de múltiplos grupos)
- Intervalos de Confiança (95%)
- Cohen's d (Effect Size)
- Teste de Shapiro-Wilk (normalidade)

Uso:
    python statistical_analysis.py --data-dir analysis_results/ --output-dir analysis_results/statistics/
"""

import argparse
import json
import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')

# Configuração de estilo para gráficos acadêmicos
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'figure.figsize': (12, 8),
    'figure.dpi': 300,
    'savefig.dpi': 300,
})


class StatisticalAnalyzer:
    """Classe para análise estatística dos resultados de experimentos."""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'plots').mkdir(exist_ok=True)
        (self.output_dir / 'csv').mkdir(exist_ok=True)
    
    def t_test(self, group1: np.ndarray, group2: np.ndarray, 
               group1_name: str = "V1", group2_name: str = "V2") -> Dict:
        """
        Teste t de Student para comparar duas amostras independentes.
        
        Hipóteses:
        - H0: μ1 = μ2 (não há diferença significativa)
        - H1: μ1 ≠ μ2 (há diferença significativa)
        
        Returns:
            Dict com estatística t, p-value e interpretação
        """
        # Verificar normalidade primeiro
        _, p_norm1 = stats.shapiro(group1[:min(len(group1), 5000)])
        _, p_norm2 = stats.shapiro(group2[:min(len(group2), 5000)])
        
        # Teste t
        t_stat, p_value = stats.ttest_ind(group1, group2)
        
        # Effect size (Cohen's d)
        cohens_d = self.cohens_d(group1, group2)
        
        # Interpretação
        significant = p_value < 0.05
        effect_interpretation = self._interpret_cohens_d(cohens_d)
        
        return {
            'test': 't-test',
            'group1': group1_name,
            'group2': group2_name,
            'group1_mean': float(np.mean(group1)),
            'group2_mean': float(np.mean(group2)),
            'group1_std': float(np.std(group1)),
            'group2_std': float(np.std(group2)),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'cohens_d': float(cohens_d),
            'effect_size': effect_interpretation,
            'significant': significant,
            'normal_distribution': p_norm1 > 0.05 and p_norm2 > 0.05,
            'interpretation': f"{'Há' if significant else 'Não há'} diferença estatisticamente significativa entre {group1_name} e {group2_name} (p={p_value:.4f}). Tamanho do efeito: {effect_interpretation} (d={cohens_d:.3f})"
        }
    
    def mann_whitney(self, group1: np.ndarray, group2: np.ndarray,
                     group1_name: str = "V1", group2_name: str = "V2") -> Dict:
        """
        Teste Mann-Whitney U para comparação não-paramétrica.
        Usar quando dados não seguem distribuição normal.
        """
        u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
        
        # Effect size: rank-biserial correlation
        n1, n2 = len(group1), len(group2)
        r = 1 - (2 * u_stat) / (n1 * n2)
        
        return {
            'test': 'Mann-Whitney U',
            'group1': group1_name,
            'group2': group2_name,
            'u_statistic': float(u_stat),
            'p_value': float(p_value),
            'effect_size_r': float(r),
            'significant': p_value < 0.05,
            'interpretation': f"{'Há' if p_value < 0.05 else 'Não há'} diferença significativa (p={p_value:.4f})"
        }
    
    def anova(self, groups: List[np.ndarray], group_names: List[str]) -> Dict:
        """
        ANOVA (Análise de Variância) para comparar 3+ grupos.
        
        Hipóteses:
        - H0: μ1 = μ2 = μ3 = ... (todas as médias são iguais)
        - H1: Pelo menos uma média é diferente
        """
        # ANOVA one-way
        f_stat, p_value = stats.f_oneway(*groups)
        
        # Effect size: Eta-squared
        # η² = SS_between / SS_total
        all_data = np.concatenate(groups)
        grand_mean = np.mean(all_data)
        
        ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups)
        ss_total = sum((x - grand_mean)**2 for x in all_data)
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        # Interpretação do η²
        if eta_squared < 0.01:
            eta_interpretation = "negligível"
        elif eta_squared < 0.06:
            eta_interpretation = "pequeno"
        elif eta_squared < 0.14:
            eta_interpretation = "médio"
        else:
            eta_interpretation = "grande"
        
        result = {
            'test': 'ANOVA',
            'groups': group_names,
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'eta_squared': float(eta_squared),
            'effect_size': eta_interpretation,
            'significant': p_value < 0.05,
            'group_means': {name: float(np.mean(g)) for name, g in zip(group_names, groups)},
            'group_stds': {name: float(np.std(g)) for name, g in zip(group_names, groups)},
            'interpretation': f"{'Há' if p_value < 0.05 else 'Não há'} diferença significativa entre os grupos (F={f_stat:.2f}, p={p_value:.4f}). η²={eta_squared:.3f} ({eta_interpretation})"
        }
        
        # Post-hoc Tukey HSD se significativo
        if p_value < 0.05 and len(groups) > 2:
            result['post_hoc'] = self._tukey_hsd(groups, group_names)
        
        return result
    
    def _tukey_hsd(self, groups: List[np.ndarray], group_names: List[str]) -> List[Dict]:
        """Teste post-hoc Tukey HSD para identificar quais grupos diferem."""
        from itertools import combinations
        
        results = []
        for (i, name1), (j, name2) in combinations(enumerate(group_names), 2):
            t_result = self.t_test(groups[i], groups[j], name1, name2)
            # Correção de Bonferroni para múltiplas comparações
            n_comparisons = len(list(combinations(range(len(groups)), 2)))
            adjusted_alpha = 0.05 / n_comparisons
            
            results.append({
                'comparison': f"{name1} vs {name2}",
                'p_value': t_result['p_value'],
                'cohens_d': t_result['cohens_d'],
                'significant': t_result['p_value'] < adjusted_alpha
            })
        
        return results
    
    def confidence_interval(self, data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float, float]:
        """
        Calcula intervalo de confiança para a média.
        
        Returns:
            Tuple (média, limite_inferior, limite_superior)
        """
        mean = np.mean(data)
        sem = stats.sem(data)  # Standard error of mean
        ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=sem)
        return mean, ci[0], ci[1]
    
    def cohens_d(self, group1: np.ndarray, group2: np.ndarray) -> float:
        """
        Calcula Cohen's d - medida do tamanho do efeito.
        
        Interpretação:
        - |d| < 0.2: negligível
        - 0.2 ≤ |d| < 0.5: pequeno
        - 0.5 ≤ |d| < 0.8: médio
        - |d| ≥ 0.8: grande
        """
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
        
        if pooled_std == 0:
            return 0.0
        
        return (np.mean(group1) - np.mean(group2)) / pooled_std
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpreta o tamanho do efeito de Cohen's d."""
        d_abs = abs(d)
        if d_abs < 0.2:
            return "negligível"
        elif d_abs < 0.5:
            return "pequeno"
        elif d_abs < 0.8:
            return "médio"
        else:
            return "grande"
    
    def shapiro_wilk(self, data: np.ndarray, name: str = "data") -> Dict:
        """
        Teste de Shapiro-Wilk para verificar normalidade.
        
        Hipóteses:
        - H0: Os dados seguem distribuição normal
        - H1: Os dados não seguem distribuição normal
        """
        # Shapiro-Wilk é limitado a 5000 amostras
        sample = data[:min(len(data), 5000)]
        stat, p_value = stats.shapiro(sample)
        
        return {
            'test': 'Shapiro-Wilk',
            'variable': name,
            'statistic': float(stat),
            'p_value': float(p_value),
            'normal': p_value > 0.05,
            'interpretation': f"Os dados {'seguem' if p_value > 0.05 else 'NÃO seguem'} distribuição normal (p={p_value:.4f})"
        }
    
    def generate_boxplot(self, groups: List[np.ndarray], group_names: List[str],
                         title: str, ylabel: str, filename: str):
        """Gera box plot comparativo com anotações estatísticas."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Box plot
        bp = ax.boxplot(groups, labels=group_names, patch_artist=True)
        
        # Cores
        colors = plt.cm.Set2(np.linspace(0, 1, len(groups)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Adicionar médias
        means = [np.mean(g) for g in groups]
        ax.scatter(range(1, len(groups)+1), means, color='red', marker='D', s=50, zorder=3, label='Média')
        
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'plots' / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Box plot salvo: {filename}")
    
    def generate_ci_plot(self, results: List[Dict], title: str, filename: str):
        """Gera gráfico de intervalos de confiança."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        y_positions = range(len(results))
        
        for i, r in enumerate(results):
            mean = r['mean']
            ci_lower = r['ci_lower']
            ci_upper = r['ci_upper']
            
            ax.errorbar(mean, i, xerr=[[mean-ci_lower], [ci_upper-mean]], 
                       fmt='o', capsize=5, capthick=2, markersize=8)
            ax.annotate(f'{mean:.2f}', (mean, i), textcoords="offset points", 
                       xytext=(0, 10), ha='center')
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels([r['name'] for r in results])
        ax.set_xlabel('Valor (IC 95%)')
        ax.set_title(title)
        ax.axvline(x=np.mean([r['mean'] for r in results]), color='gray', 
                   linestyle='--', alpha=0.5, label='Média geral')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'plots' / filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico de IC salvo: {filename}")
    
    def run_full_analysis(self, data: Dict[str, Dict[str, np.ndarray]]) -> pd.DataFrame:
        """
        Executa análise estatística completa.
        
        Args:
            data: Dict no formato {scenario: {version: values}}
        
        Returns:
            DataFrame com todos os resultados
        """
        all_results = []
        
        for scenario, versions in data.items():
            version_names = list(versions.keys())
            version_data = [versions[v] for v in version_names]
            
            # ANOVA se há 3+ grupos
            if len(version_data) >= 3:
                anova_result = self.anova(version_data, version_names)
                anova_result['scenario'] = scenario
                all_results.append(anova_result)
            
            # t-tests pairwise
            from itertools import combinations
            for (n1, v1), (n2, v2) in combinations(zip(version_names, version_data), 2):
                t_result = self.t_test(v1, v2, n1, n2)
                t_result['scenario'] = scenario
                all_results.append(t_result)
        
        # Salvar resultados
        df = pd.DataFrame(all_results)
        df.to_csv(self.output_dir / 'csv' / 'statistical_tests_results.csv', index=False)
        print(f"✅ Resultados salvos: statistical_tests_results.csv")
        
        return df
    
    def generate_summary_table(self, df: pd.DataFrame) -> str:
        """Gera tabela resumo em Markdown."""
        md_lines = ["# Resultados Estatísticos - TCC Circuit Breaker", ""]
        md_lines.append("## Resumo dos Testes")
        md_lines.append("")
        
        # Filtrar t-tests
        t_tests = df[df['test'] == 't-test']
        if not t_tests.empty:
            md_lines.append("### Comparações Pairwise (t-test)")
            md_lines.append("")
            md_lines.append("| Cenário | Comparação | p-value | Cohen's d | Efeito | Significativo |")
            md_lines.append("|---------|------------|---------|-----------|--------|---------------|")
            
            for _, row in t_tests.iterrows():
                sig = "✅ Sim" if row['significant'] else "❌ Não"
                md_lines.append(
                    f"| {row.get('scenario', 'N/A')} | {row['group1']} vs {row['group2']} | "
                    f"{row['p_value']:.4f} | {row['cohens_d']:.3f} | {row['effect_size']} | {sig} |"
                )
            md_lines.append("")
        
        # ANOVA
        anovas = df[df['test'] == 'ANOVA']
        if not anovas.empty:
            md_lines.append("### ANOVA (Múltiplos Grupos)")
            md_lines.append("")
            md_lines.append("| Cenário | Grupos | F | p-value | η² | Significativo |")
            md_lines.append("|---------|--------|---|---------|-----|---------------|")
            
            for _, row in anovas.iterrows():
                groups_str = ", ".join(row.get('groups', []))
                sig = "✅ Sim" if row['significant'] else "❌ Não"
                md_lines.append(
                    f"| {row.get('scenario', 'N/A')} | {groups_str} | "
                    f"{row['f_statistic']:.2f} | {row['p_value']:.4f} | {row['eta_squared']:.3f} | {sig} |"
                )
        
        md_content = "\n".join(md_lines)
        
        with open(self.output_dir / 'statistical_summary.md', 'w') as f:
            f.write(md_content)
        
        print(f"✅ Sumário Markdown salvo: statistical_summary.md")
        return md_content


def main():
    parser = argparse.ArgumentParser(description='Análise estatística para TCC')
    parser.add_argument('--data-dir', default='analysis_results', help='Diretório com dados')
    parser.add_argument('--output-dir', default='analysis_results/statistics', help='Diretório de saída')
    parser.add_argument('--validate', action='store_true', help='Executar validação com dados de exemplo')
    
    args = parser.parse_args()
    
    analyzer = StatisticalAnalyzer(args.data_dir, args.output_dir)
    
    if args.validate:
        print("\n🧪 Executando validação com dados de exemplo...\n")
        
        # Dados de exemplo para validação
        np.random.seed(42)
        v1_latency = np.random.normal(500, 100, 1000)  # V1: média 500ms
        v2_latency = np.random.normal(400, 80, 1000)   # V2: média 400ms
        v3_latency = np.random.normal(550, 120, 1000)  # V3: média 550ms
        
        # Teste t
        print("📊 Teste t (V1 vs V2):")
        t_result = analyzer.t_test(v1_latency, v2_latency, "V1", "V2")
        print(f"   {t_result['interpretation']}")
        print()
        
        # ANOVA
        print("📊 ANOVA (V1 vs V2 vs V3):")
        anova_result = analyzer.anova(
            [v1_latency, v2_latency, v3_latency],
            ["V1", "V2", "V3"]
        )
        print(f"   {anova_result['interpretation']}")
        print()
        
        # Intervalo de confiança
        print("📊 Intervalos de Confiança (95%):")
        for name, data in [("V1", v1_latency), ("V2", v2_latency), ("V3", v3_latency)]:
            mean, ci_lower, ci_upper = analyzer.confidence_interval(data)
            print(f"   {name}: {mean:.2f} [{ci_lower:.2f}, {ci_upper:.2f}]")
        print()
        
        # Gerar visualizações
        print("📊 Gerando visualizações...")
        analyzer.generate_boxplot(
            [v1_latency, v2_latency, v3_latency],
            ["V1 (Baseline)", "V2 (CB)", "V3 (Retry)"],
            "Comparação de Latência por Versão",
            "Latência (ms)",
            "validation_boxplot.png"
        )
        
        print("\n✅ Validação concluída!")
        return
    
    print(f"\n📊 Análise estatística")
    print(f"📁 Dados: {args.data_dir}")
    print(f"📁 Saída: {args.output_dir}\n")
    
    # Aqui você pode adicionar lógica para carregar dados reais
    print("ℹ️ Use --validate para testar com dados de exemplo")
    print("ℹ️ Integre com seus dados reais modificando a função main()")


if __name__ == '__main__':
    main()
