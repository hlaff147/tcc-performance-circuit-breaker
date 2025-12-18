#!/usr/bin/env python3
"""
Profile Comparison Analyzer
Analisa resultados de testes comparativos entre perfis de Circuit Breaker

Uso:
    python profile_comparison_analyzer.py --scenario catastrofe --timestamp 20231215_143000
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Configuração de estilo para gráficos acadêmicos
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'figure.figsize': (12, 8),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'legend.fontsize': 10,
})

# Cores para cada perfil
PROFILE_COLORS = {
    'equilibrado': '#2ecc71',  # Verde
    'conservador': '#3498db',  # Azul
    'agressivo': '#e74c3c',    # Vermelho
    'V1': '#95a5a6',           # Cinza
    'V3_retry': '#9b59b6',     # Roxo
}

PROFILE_LABELS = {
    'equilibrado': 'Equilibrado (50%)',
    'conservador': 'Conservador (60%)',
    'agressivo': 'Agressivo (30%)',
}


def load_summary_json(filepath: str) -> Dict:
    """Carrega arquivo JSON de sumário do k6."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Arquivo não encontrado: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️ Erro ao decodificar JSON: {e}")
        return {}


def extract_metrics(summary: Dict) -> Dict:
    """Extrai métricas relevantes do sumário k6."""
    metrics = {}
    
    if not summary:
        return metrics
    
    # Métricas HTTP
    if 'metrics' in summary:
        m = summary['metrics']
        
        # Duração das requisições
        if 'http_req_duration' in m:
            duration = m['http_req_duration']
            metrics['latency_avg'] = duration.get('avg', 0)
            metrics['latency_p50'] = duration.get('med', 0)
            metrics['latency_p95'] = duration.get('p(95)', 0)
            metrics['latency_p99'] = duration.get('p(99)', 0)
            metrics['latency_min'] = duration.get('min', 0)
            metrics['latency_max'] = duration.get('max', 0)
        
        # Contagem de requisições
        if 'http_reqs' in m:
            metrics['total_requests'] = m['http_reqs'].get('count', 0)
            metrics['throughput'] = m['http_reqs'].get('rate', 0)
        
        # Métricas customizadas
        for key in ['custom_success_responses', 'custom_fallback_responses', 
                    'custom_api_failures', 'custom_circuit_breaker_open']:
            if key in m:
                metrics[key.replace('custom_', '')] = m[key].get('count', 0)
    
    # Calcular taxas
    total = metrics.get('total_requests', 1)
    if total > 0:
        metrics['success_rate'] = (metrics.get('success_responses', 0) / total) * 100
        metrics['fallback_rate'] = (metrics.get('fallback_responses', 0) / total) * 100
        metrics['failure_rate'] = (metrics.get('api_failures', 0) / total) * 100
        metrics['availability'] = metrics['success_rate'] + metrics['fallback_rate']
    
    return metrics


def compare_profiles(results_dir: str, scenario: str, timestamp: str) -> pd.DataFrame:
    """Compara métricas entre os 3 perfis de CB."""
    profiles = ['equilibrado', 'conservador', 'agressivo']
    data = []
    
    for profile in profiles:
        summary_path = f"{results_dir}/json/{scenario}_{profile}_{timestamp}_summary.json"
        summary = load_summary_json(summary_path)
        metrics = extract_metrics(summary)
        
        if metrics:
            metrics['profile'] = profile
            metrics['profile_label'] = PROFILE_LABELS.get(profile, profile)
            data.append(metrics)
    
    return pd.DataFrame(data)


def generate_comparison_table(df: pd.DataFrame, output_dir: str, scenario: str):
    """Gera tabela comparativa em CSV e Markdown."""
    if df.empty:
        print("⚠️ DataFrame vazio, não é possível gerar tabela")
        return
    
    # Selecionar colunas relevantes
    cols = ['profile_label', 'success_rate', 'fallback_rate', 'failure_rate', 
            'availability', 'latency_avg', 'latency_p95', 'throughput']
    
    available_cols = [c for c in cols if c in df.columns]
    table = df[available_cols].copy()
    
    # Renomear colunas para português
    rename_map = {
        'profile_label': 'Perfil',
        'success_rate': 'Taxa Sucesso (%)',
        'fallback_rate': 'Taxa Fallback (%)',
        'failure_rate': 'Taxa Falha (%)',
        'availability': 'Disponibilidade (%)',
        'latency_avg': 'Latência Média (ms)',
        'latency_p95': 'P95 (ms)',
        'throughput': 'Throughput (req/s)',
    }
    table.rename(columns={k: v for k, v in rename_map.items() if k in table.columns}, inplace=True)
    
    # Salvar CSV
    csv_path = f"{output_dir}/csv/{scenario}_profile_comparison.csv"
    table.to_csv(csv_path, index=False)
    print(f"✅ Tabela CSV salva: {csv_path}")
    
    # Gerar Markdown
    md_path = f"{output_dir}/{scenario}_profile_comparison.md"
    with open(md_path, 'w') as f:
        f.write(f"# Comparação de Perfis CB - Cenário: {scenario.upper()}\n\n")
        f.write(table.to_markdown(index=False))
        f.write("\n")
    print(f"✅ Tabela Markdown salva: {md_path}")


def generate_boxplot(df: pd.DataFrame, output_dir: str, scenario: str, metric: str, title: str):
    """Gera box plot para uma métrica específica."""
    if df.empty or metric not in df.columns:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = [PROFILE_COLORS.get(p, '#333333') for p in df['profile']]
    
    # Box plot
    positions = range(len(df))
    bp = ax.boxplot([df[df['profile'] == p][metric].values for p in df['profile'].unique()],
                    positions=positions,
                    patch_artist=True)
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_xticklabels([PROFILE_LABELS.get(p, p) for p in df['profile'].unique()])
    ax.set_ylabel(title)
    ax.set_title(f'{title} por Perfil de CB - {scenario.upper()}')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/plots/{scenario}_{metric}_boxplot.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Box plot salvo: {scenario}_{metric}_boxplot.png")


def generate_bar_comparison(df: pd.DataFrame, output_dir: str, scenario: str):
    """Gera gráfico de barras comparando métricas principais."""
    if df.empty:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    metrics = [
        ('success_rate', 'Taxa de Sucesso (%)', axes[0, 0]),
        ('fallback_rate', 'Taxa de Fallback (%)', axes[0, 1]),
        ('latency_avg', 'Latência Média (ms)', axes[1, 0]),
        ('throughput', 'Throughput (req/s)', axes[1, 1]),
    ]
    
    for metric, title, ax in metrics:
        if metric not in df.columns:
            continue
            
        colors = [PROFILE_COLORS.get(p, '#333333') for p in df['profile']]
        bars = ax.bar(df['profile_label'], df[metric], color=colors, alpha=0.8, edgecolor='black')
        
        ax.set_ylabel(title)
        ax.set_title(title)
        
        # Adicionar valores nas barras
        for bar, val in zip(bars, df[metric]):
            height = bar.get_height()
            ax.annotate(f'{val:.1f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=10)
    
    plt.suptitle(f'Comparação de Perfis CB - Cenário: {scenario.upper()}', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/plots/{scenario}_profile_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico de barras salvo: {scenario}_profile_comparison.png")


def generate_heatmap(df: pd.DataFrame, output_dir: str, scenario: str):
    """Gera heatmap de correlação entre métricas."""
    if df.empty:
        return
    
    # Selecionar apenas colunas numéricas
    numeric_cols = ['success_rate', 'fallback_rate', 'failure_rate', 'latency_avg', 
                    'latency_p95', 'throughput']
    available_cols = [c for c in numeric_cols if c in df.columns]
    
    if len(available_cols) < 2:
        return
    
    numeric_df = df[available_cols]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Heatmap de valores normalizados
    normalized = (numeric_df - numeric_df.min()) / (numeric_df.max() - numeric_df.min())
    normalized.index = df['profile_label']
    
    sns.heatmap(normalized.T, annot=True, fmt='.2f', cmap='RdYlGn', 
                ax=ax, cbar_kws={'label': 'Valor Normalizado'})
    
    ax.set_title(f'Performance Normalizada por Perfil - {scenario.upper()}')
    ax.set_xlabel('Perfil de Circuit Breaker')
    ax.set_ylabel('Métrica')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/plots/{scenario}_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Heatmap salvo: {scenario}_heatmap.png")


def run_statistical_tests(df: pd.DataFrame, output_dir: str, scenario: str):
    """Executa testes estatísticos entre perfis."""
    if df.empty or len(df) < 2:
        print("⚠️ Dados insuficientes para testes estatísticos")
        return
    
    results = []
    metrics = ['success_rate', 'latency_avg', 'throughput']
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        values = df[metric].values
        
        # ANOVA (se 3+ grupos)
        if len(values) >= 3:
            # Simular grupos (em produção, usar dados raw)
            f_stat, p_value = stats.f_oneway(
                [values[0]], [values[1]], [values[2]]
            )
            results.append({
                'metric': metric,
                'test': 'ANOVA',
                'statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            })
    
    if results:
        stats_df = pd.DataFrame(results)
        stats_path = f"{output_dir}/csv/{scenario}_statistical_tests.csv"
        stats_df.to_csv(stats_path, index=False)
        print(f"✅ Testes estatísticos salvos: {stats_path}")


def main():
    parser = argparse.ArgumentParser(description='Analisar comparação de perfis de CB')
    parser.add_argument('--scenario', required=True, help='Nome do cenário')
    parser.add_argument('--timestamp', required=True, help='Timestamp da execução')
    parser.add_argument('--output-dir', default='analysis_results/profile_comparison',
                       help='Diretório de saída')
    
    args = parser.parse_args()
    
    print(f"\n📊 Analisando cenário: {args.scenario}")
    print(f"⏰ Timestamp: {args.timestamp}")
    print(f"📁 Output: {args.output_dir}\n")
    
    # Criar diretórios
    os.makedirs(f"{args.output_dir}/csv", exist_ok=True)
    os.makedirs(f"{args.output_dir}/plots", exist_ok=True)
    
    # Carregar e comparar dados
    df = compare_profiles(args.output_dir, args.scenario, args.timestamp)
    
    if df.empty:
        print("❌ Nenhum dado encontrado para análise")
        sys.exit(1)
    
    print(f"✅ Carregados dados de {len(df)} perfis\n")
    
    # Gerar outputs
    generate_comparison_table(df, args.output_dir, args.scenario)
    generate_bar_comparison(df, args.output_dir, args.scenario)
    generate_heatmap(df, args.output_dir, args.scenario)
    run_statistical_tests(df, args.output_dir, args.scenario)
    
    print(f"\n✅ Análise completa! Verifique: {args.output_dir}/")


if __name__ == '__main__':
    main()
