#!/usr/bin/env python3
"""
comparative_analyzer.py
=======================
Análise estatística comparativa para experimento CB vs Retry.

Funcionalidades:
- Carrega resultados de múltiplas repetições
- Calcula IC 95% via bootstrap
- Executa teste Mann-Whitney para comparações
- Gera tabelas e gráficos comparativos

Uso:
    python3 comparative_analyzer.py <experiment_dir>
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats

# Tentativa de importar scipy.stats.bootstrap (Python 3.9+)
try:
    from scipy.stats import bootstrap
    HAS_BOOTSTRAP = True
except ImportError:
    HAS_BOOTSTRAP = False


def load_summary_files(experiment_dir: str) -> pd.DataFrame:
    """Carrega todos os arquivos *_summary.json do diretório."""
    records = []
    
    for f in Path(experiment_dir).glob("*_summary.json"):
        filename = f.stem.replace("_summary", "")
        # Formato: cenario_treatment_runN (cenario pode conter hífens)
        match = re.match(r"^(.+)_(v\d+)_(run\d+)$", filename)
        
        if match:
            scenario = match.group(1)
            treatment = match.group(2)
            run = int(match.group(3).replace("run", ""))
            
            with open(f) as fp:
                data = json.load(fp)
            
            metrics = data.get("metrics", {})
            
            record = {
                "scenario": scenario,
                "treatment": treatment,
                "run": run,
                "total_requests": metrics.get("http_reqs", {}).get("count", 0),
                "success_rate": metrics.get("http_req_failed", {}).get("rate", 0),
                "avg_duration_ms": metrics.get("http_req_duration", {}).get("avg", 0),
                "p95_duration_ms": metrics.get("http_req_duration", {}).get("p(95)", 0),
                "p99_duration_ms": metrics.get("http_req_duration", {}).get("p(99)", 0),
            }
            records.append(record)
    
    return pd.DataFrame(records)


def calculate_confidence_interval(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Calcula IC usando bootstrap ou método t (fallback)."""
    if len(data) < 2:
        return (np.mean(data), np.mean(data))
    
    if HAS_BOOTSTRAP and len(data) >= 5:
        try:
            res = bootstrap((data,), np.mean, confidence_level=confidence, 
                          method='BCa', n_resamples=10000)
            return (res.confidence_interval.low, res.confidence_interval.high)
        except Exception:
            pass
    
    # Fallback: intervalo t
    mean = np.mean(data)
    se = stats.sem(data)
    h = se * stats.t.ppf((1 + confidence) / 2, len(data) - 1)
    return (mean - h, mean + h)


def mann_whitney_test(group_a: np.ndarray, group_b: np.ndarray, alpha: float = 0.05) -> Dict:
    """Executa teste Mann-Whitney U com alpha configurável (para correção Bonferroni)."""
    if len(group_a) < 2 or len(group_b) < 2:
        return {"u_statistic": None, "p_value": None, "significant": False, "alpha_used": alpha}
    
    try:
        stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
        return {
            "u_statistic": stat,
            "p_value": p_value,
            "significant": p_value < alpha,  # Usa alpha ajustado
            "alpha_used": alpha
        }
    except Exception:
        return {"u_statistic": None, "p_value": None, "significant": False, "alpha_used": alpha}


def analyze_treatment_comparison(df: pd.DataFrame, scenario: str, 
                                  treatment_a: str, treatment_b: str,
                                  metric: str, alpha: float = 0.05) -> Dict:
    """Compara dois tratamentos para uma métrica específica."""
    data_a = df[(df["scenario"] == scenario) & (df["treatment"] == treatment_a)][metric].values
    data_b = df[(df["scenario"] == scenario) & (df["treatment"] == treatment_b)][metric].values
    
    if len(data_a) == 0 or len(data_b) == 0:
        return None
    
    mean_a, mean_b = np.mean(data_a), np.mean(data_b)
    ci_a = calculate_confidence_interval(data_a)
    ci_b = calculate_confidence_interval(data_b)
    mw_test = mann_whitney_test(data_a, data_b, alpha=alpha)
    
    return {
        "scenario": scenario,
        "comparison": f"{treatment_a} vs {treatment_b}",
        "metric": metric,
        f"{treatment_a}_mean": mean_a,
        f"{treatment_a}_ci_low": ci_a[0],
        f"{treatment_a}_ci_high": ci_a[1],
        f"{treatment_b}_mean": mean_b,
        f"{treatment_b}_ci_low": ci_b[0],
        f"{treatment_b}_ci_high": ci_b[1],
        "difference": mean_b - mean_a,
        "difference_pct": ((mean_b - mean_a) / mean_a * 100) if mean_a != 0 else 0,
        "p_value": mw_test["p_value"],
        "significant": mw_test["significant"]
    }


def generate_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Gera tabela resumo por tratamento × cenário."""
    summary = df.groupby(["scenario", "treatment"]).agg({
        "total_requests": ["mean", "std"],
        "success_rate": ["mean", "std"],
        "avg_duration_ms": ["mean", "std"],
        "p95_duration_ms": ["mean", "std"],
        "p99_duration_ms": ["mean", "std"],
    }).round(2)
    
    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    return summary.reset_index()


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 comparative_analyzer.py <experiment_dir>")
        sys.exit(1)
    
    experiment_dir = sys.argv[1]
    
    if not os.path.exists(experiment_dir):
        print(f"Diretório não encontrado: {experiment_dir}")
        sys.exit(1)
    
    print(f"Carregando resultados de: {experiment_dir}")
    df = load_summary_files(experiment_dir)
    
    if df.empty:
        print("Nenhum resultado encontrado!")
        sys.exit(1)
    
    print(f"Carregados {len(df)} registros")
    print(f"Cenários: {df['scenario'].unique()}")
    print(f"Tratamentos: {df['treatment'].unique()}")
    print()
    
    # Configurar correção de Bonferroni
    num_scenarios = len(df['scenario'].unique())
    ALPHA = 0.05
    comparisons_list = [
        ("v1", "v2", "H1: CB reduz falhas vs baseline"),
        ("v1", "v3", "H2: Retry vs baseline"),
        ("v3", "v2", "H3: CB vs Retry"),
        ("v2", "v4", "H4: CB+Retry vs CB"),
        ("v3", "v4", "H5: CB+Retry vs Retry"),
    ]
    metrics_list = ["success_rate", "avg_duration_ms", "p95_duration_ms"]
    NUM_TESTS = len(comparisons_list) * len(metrics_list) * num_scenarios
    BONFERRONI_ALPHA = ALPHA / NUM_TESTS
    
    print(f"=== CORREÇÃO PARA COMPARAÇÕES MÚLTIPLAS ===")
    print(f"Número de testes simultâneos: {NUM_TESTS}")
    print(f"Alpha sem correção: {ALPHA}")
    print(f"Alpha ajustado (Bonferroni): {BONFERRONI_ALPHA:.6f}")
    print(f"  → Evita inflação de falsos positivos de {ALPHA} para {1-(1-ALPHA)**NUM_TESTS:.2%}")
    print()
    
    # Tabela resumo
    summary = generate_summary_table(df)
    print("=== TABELA RESUMO ===")
    print(summary.to_string())
    print()
    
    # Salvar CSV
    output_dir = Path(experiment_dir) / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    summary.to_csv(output_dir / "summary_by_treatment.csv", index=False)
    print(f"Resumo salvo em: {output_dir / 'summary_by_treatment.csv'}")
    
    # Comparações estatísticas
    comparisons = [
        ("v1", "v2", "H1: CB reduz falhas vs baseline"),
        ("v1", "v3", "H2: Retry vs baseline"),
        ("v3", "v2", "H3: CB vs Retry"),
        ("v2", "v4", "H4: CB+Retry vs CB"),
        ("v3", "v4", "H5: CB+Retry vs Retry"),
    ]
    
    metrics = ["success_rate", "avg_duration_ms", "p95_duration_ms"]
    
    comparison_results = []
    for scenario in df["scenario"].unique():
        for t_a, t_b, hypothesis in comparisons:
            for metric in metrics:
                result = analyze_treatment_comparison(df, scenario, t_a, t_b, metric)
                if result:
                    result["hypothesis"] = hypothesis
                    comparison_results.append(result)
    
    if comparison_results:
        comp_df = pd.DataFrame(comparison_results)
        comp_df.to_csv(output_dir / "statistical_comparisons.csv", index=False)
        
        print("\n=== COMPARAÇÕES ESTATÍSTICAS ===")
        significant = comp_df[comp_df["significant"] == True]
        if not significant.empty:
            print("Diferenças significativas (p < 0.05):")
            print(significant[["scenario", "comparison", "metric", "difference_pct", "p_value"]].to_string())
        else:
            print("Nenhuma diferença estatisticamente significativa encontrada.")
        
        print(f"\nComparações salvas em: {output_dir / 'statistical_comparisons.csv'}")
    
    print("\nAnálise concluída!")


if __name__ == "__main__":
    main()
