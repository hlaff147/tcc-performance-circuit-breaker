"""
Script para análise robusta e modular dos resultados dos testes de carga do k6.

Este script substitui o Jupyter Notebook 'analysis_v2.ipynb', focando em
reprodutibilidade, modularidade e geração de artefatos para publicação acadêmica.

Autor: Humberto
Data: 2025-12-17
"""

import os
import re
import json
import logging
import warnings
from pathlib import Path
from itertools import combinations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from tqdm import tqdm

# --- Configuração do Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Captura warnings das bibliotecas e redireciona para o logging
logging.captureWarnings(True)
warnings.filterwarnings('ignore', category=FutureWarning)

# --- Constantes e Configurações ---

# Define o diretório base do projeto (assumindo que o script está em 'analysis/')
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretório de entrada contendo os resultados do k6
EXPERIMENT_DIR = BASE_DIR / 'k6' / 'results' / 'comparative' / 'experiment_20251216_101442'

# Diretórios de saída para os artefatos gerados
OUTPUT_VERSION = 'v2.0.0'
ANALYSIS_RESULTS_DIR = BASE_DIR / 'analysis_results' / OUTPUT_VERSION
PLOTS_DIR = ANALYSIS_RESULTS_DIR / 'plots'
LATEX_DIR = ANALYSIS_RESULTS_DIR / 'latex'
TIMESERIES_PLOTS_DIR = ANALYSIS_RESULTS_DIR / 'plots_timeseries'

# Métricas a serem extraídas e analisadas
METRICS_TO_EXTRACT = {
    "total_requests": ("http_reqs", "count", 0),
    "fail_rate": ("http_req_failed", "rate", 0),
    "avg_duration_ms": ("http_req_duration", "avg", 0),
    "p95_duration_ms": ("http_req_duration", "p(95)", 0),
    "p99_duration_ms": ("http_req_duration", "p(99)", 0),
}

# Métricas para análise estatística
METRICS_FOR_STATS = ['avg_duration_ms', 'success_rate']

# Configurações de visualização para os gráficos
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.figsize': (10, 6),
    'figure.dpi': 300
})


def load_summary_files(experiment_dir: Path) -> pd.DataFrame:
    """
    Carrega e processa todos os arquivos *_summary.json de um diretório de experimento.

    Args:
        experiment_dir: O caminho para o diretório do experimento.

    Returns:
        Um DataFrame do Pandas com os dados consolidados.
    """
    records = []
    
    logger.info(f"Carregando dados de: {experiment_dir}")
    
    for f in experiment_dir.glob("*_summary.json"):
        filename = f.stem.replace("_summary", "")
        match = re.match(r"^(.+)_(v\d+)_(run\d+)$", filename)
        
        if not match:
            logger.warning(f"O arquivo {f.name} não corresponde ao padrão esperado e será ignorado.")
            continue
            
        scenario, treatment, run_str = match.groups()
        run = int(run_str.replace("run", ""))
        
        with open(f) as fp:
            data = json.load(fp)
        
        metrics_data = data.get("metrics", {})
        record = {
            "scenario": scenario,
            "treatment": treatment,
            "run": run,
        }
        
        for metric_name, (k6_metric, key, default) in METRICS_TO_EXTRACT.items():
            record[metric_name] = metrics_data.get(k6_metric, {}).get(key, default)
            
        records.append(record)
    
    if not records:
        raise FileNotFoundError(f"Nenhum arquivo de sumário encontrado em {experiment_dir}")

    df = pd.DataFrame(records)
    df['success_rate'] = 1 - df['fail_rate']
    
    logger.info(f"{len(df)} registros carregados com sucesso.")
    return df


def load_raw_timeseries_data(experiment_dir: Path, time_bucket: str = '5s') -> pd.DataFrame:
    """
    Carrega e processa os dados brutos de todos os arquivos *.json (não-sumários)
    de um diretório de experimento, agregando-os em janelas de tempo.

    Args:
        experiment_dir: O caminho para o diretório do experimento.
        time_bucket: A janela de tempo para agregação (ex: '1s', '5s').

    Returns:
        Um DataFrame do Pandas com os dados de série temporal.
    """
    logger.info(f"Carregando dados brutos de série temporal de: {experiment_dir}")
    
    all_points = []
    
    # Usamos tqdm para uma barra de progresso, pois isso pode demorar
    file_list = list(experiment_dir.glob("*.json"))
    file_list = [f for f in file_list if '_summary' not in f.name]

    for f in tqdm(file_list, desc="Processando arquivos brutos"):
        filename = f.stem
        match = re.match(r"^(.+)_(v\d+)_(run\d+)$", filename)
        
        if not match:
            continue
            
        scenario, treatment, run_str = match.groups()
        run = int(run_str.replace("run", ""))

        with open(f, 'r') as fp:
            for line in fp:
                try:
                    log_entry = json.loads(line)
                    if log_entry.get('type') == 'Point' and 'metric' in log_entry and log_entry['metric'].startswith('http_req'):
                        # Apenas métricas de requisição HTTP
                        point_data = log_entry['data']
                        all_points.append({
                            'time': point_data['time'],
                            'metric': log_entry['metric'],
                            'value': point_data['value'],
                            'status': point_data.get('tags', {}).get('status'),
                            'scenario': scenario,
                            'treatment': treatment,
                            'run': run
                        })
                except json.JSONDecodeError:
                    # Ignora linhas que não são JSON válidos
                    continue
    
    if not all_points:
        logger.warning("Nenhum dado de série temporal encontrado nos arquivos brutos.")
        return pd.DataFrame()

    df = pd.DataFrame(all_points)
    df['time'] = pd.to_datetime(df['time'])
    
    # Define o início do tempo de teste para cada execução para normalizar o eixo X
    df['time_offset'] = df.groupby(['scenario', 'treatment', 'run'])['time'].transform(lambda x: (x - x.min()).dt.total_seconds())

    # Agrega os dados em janelas de tempo
    logger.info(f"Agregando dados em janelas de {time_bucket}...")
    
    # Separa duração e falhas para agregação correta
    df_duration = df[df['metric'] == 'http_req_duration'].copy()
    df_failed = df[df['metric'] == 'http_req_failed'].copy()

    # Agrega tempo de resposta
    agg_duration = df_duration.groupby(['scenario', 'treatment', pd.Grouper(key='time', freq=time_bucket)]).agg(
        p95_duration_ms=('value', lambda x: x.quantile(0.95)),
        p99_duration_ms=('value', lambda x: x.quantile(0.99))
    ).reset_index()

    # Agrega requisições e falhas
    df_reqs = df[df['metric'] == 'http_reqs'].copy()
    # Converte status para numérico (pode vir como string do JSON)
    df_reqs['status_code'] = pd.to_numeric(df_reqs['status'], errors='coerce')
    df_reqs['success'] = df_reqs['status_code'].notna() & (df_reqs['status_code'] < 400)
    df_reqs['failed'] = ~df_reqs['success']

    agg_rps = df_reqs.groupby(['scenario', 'treatment', pd.Grouper(key='time', freq=time_bucket)]).agg(
        rps_total=('value', 'count'),
        rps_success=('success', 'sum'),
        rps_failed=('failed', 'sum')
    ).reset_index()
    
    # Converte para RPS dividindo pelo tamanho da janela em segundos
    bucket_seconds = pd.to_timedelta(time_bucket).total_seconds()
    agg_rps['rps_total'] /= bucket_seconds
    agg_rps['rps_success'] /= bucket_seconds
    agg_rps['rps_failed'] /= bucket_seconds
    agg_rps['error_rate'] = agg_rps['rps_failed'] / agg_rps['rps_total']

    # Junta os dataframes agregados
    timeseries_df = pd.merge(agg_duration, agg_rps, on=['scenario', 'treatment', 'time'], how='outer').fillna(0)
    
    # Normaliza o tempo para o início do cenário
    timeseries_df['time_offset'] = timeseries_df.groupby(['scenario', 'treatment'])['time'].transform(lambda x: (x - x.min()).dt.total_seconds())

    logger.info("Dados de série temporal processados com sucesso.")
    return timeseries_df


def perform_exploratory_analysis(df: pd.DataFrame):
    """
    Realiza e exibe a análise exploratória dos dados.

    Args:
        df: DataFrame com os dados dos testes.
    """
    logger.info("Iniciando Análise Exploratória de Dados (EDA)")
    
    # Ordena para melhor visualização
    treatments_order = sorted(df['treatment'].unique())
    
    grouped_analysis = df.groupby(['scenario', 'treatment']).agg(
        avg_success_rate=('success_rate', 'mean'),
        median_success_rate=('success_rate', 'median'),
        avg_p95_duration=('p95_duration_ms', 'mean'),
        median_p95_duration=('p95_duration_ms', 'median'),
        run_count=('run', 'count')
    ).reset_index()
    
    # Reordena o tratamento para uma apresentação lógica
    grouped_analysis['treatment'] = pd.Categorical(grouped_analysis['treatment'], categories=treatments_order, ordered=True)
    grouped_analysis = grouped_analysis.sort_values(['scenario', 'treatment'])
    
    logger.info("Resumo das médias e medianas por cenário e tratamento:")
    logger.info(f"\n{grouped_analysis.to_string(index=False)}")
    
    return grouped_analysis


def run_statistical_analysis(df: pd.DataFrame, reference_version: str = 'v2') -> pd.DataFrame:
    """
    Realiza o teste U de Mann-Whitney para comparar a versão de referência com as outras.

    Args:
        df: DataFrame com os dados dos testes.
        reference_version: A versão a ser usada como controle (ex: 'v2').

    Returns:
        Um DataFrame com os resultados dos testes estatísticos.
    """
    logger.info(f"Iniciando Análise Estatística (Teste U de Mann-Whitney) comparando com '{reference_version}'")
    
    statistical_results = []
    scenarios = df['scenario'].unique()
    treatments = sorted(df['treatment'].unique())
    
    # Garante que a versão de referência exista
    if reference_version not in treatments:
        raise ValueError(f"A versão de referência '{reference_version}' não foi encontrada nos dados.")

    other_versions = [t for t in treatments if t != reference_version]

    for scenario in scenarios:
        for metric in METRICS_FOR_STATS:
            for other_v in other_versions:
                data_ref = df[(df['scenario'] == scenario) & (df['treatment'] == reference_version)][metric]
                data_other = df[(df['scenario'] == scenario) & (df['treatment'] == other_v)][metric]
                
                if len(data_ref) > 1 and len(data_other) > 1:
                    try:
                        stat, p_value = stats.mannwhitneyu(data_ref, data_other, alternative='two-sided')
                        
                        statistical_results.append({
                            'scenario': scenario,
                            'metric': metric,
                            'comparison': f'{reference_version} vs {other_v}',
                            'statistic': stat,
                            'p_value': p_value,
                            'significant_at_5%': 'Sim' if p_value < 0.05 else 'Não'
                        })
                    except ValueError as e:
                        logger.warning(f"Não foi possível calcular o teste para {scenario}, {metric}, {reference_version} vs {other_v}. Erro: {e}")


    if not statistical_results:
        logger.warning("Nenhum resultado estatístico foi gerado.")
        return pd.DataFrame()

    stats_df = pd.DataFrame(statistical_results)
    logger.info("Resultados dos testes estatísticos:")
    logger.info(f"\n{stats_df.to_string(index=False)}")
    
    return stats_df


# Nomes descritivos para as versões (para legendas e títulos)
VERSION_LABELS = {
    'v1': 'V1 (Sem CB)',
    'v2': 'V2 (CB Básico)',
    'v3': 'V3 (CB + Retry)',
    'v4': 'V4 (CB + Fallback)'
}

# Cores distintas para cada versão
VERSION_COLORS = {
    'v1': '#e41a1c',  # Vermelho
    'v2': '#377eb8',  # Azul
    'v3': '#4daf4a',  # Verde
    'v4': '#984ea3'   # Roxo
}

# Marcadores distintos para gráficos de linha
VERSION_MARKERS = {
    'v1': 'o',
    'v2': 's',
    'v3': '^',
    'v4': 'D'
}

REFERENCE_VERSION = 'v2'


def generate_visualizations(df: pd.DataFrame, grouped_df: pd.DataFrame):
    """
    Gera e salva os gráficos comparativos com melhor visualização.
    Inclui gráficos agregados e comparações 2 a 2.

    Args:
        df: O DataFrame completo com dados por execução.
        grouped_df: O DataFrame com dados agregados.
    """
    logger.info("Gerando visualizações comparativas")
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    scenarios = df['scenario'].unique()
    treatments_order = sorted(df['treatment'].unique())
    other_versions = [v for v in treatments_order if v != REFERENCE_VERSION]
    
    # Paleta de cores ordenada
    palette = [VERSION_COLORS[v] for v in treatments_order]

    for scenario in scenarios:
        scenario_title = scenario.replace("-", " ").title()
        scenario_data = grouped_df[grouped_df['scenario'] == scenario]
        scenario_raw = df[df['scenario'] == scenario]
        
        # =====================================================================
        # 1. GRÁFICOS AGREGADOS (todas as versões)
        # =====================================================================
        
        # Gráfico de Barras - Taxa de Sucesso (com valores anotados)
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = sns.barplot(
            data=scenario_data,
            x='treatment',
            y='avg_success_rate',
            hue='treatment',
            order=treatments_order,
            hue_order=treatments_order,
            palette=palette,
            legend=False,
            ax=ax
        )
        # Adiciona valores nas barras
        for i, (idx, row) in enumerate(scenario_data.set_index('treatment').loc[treatments_order].iterrows()):
            ax.annotate(f'{row["avg_success_rate"]:.1%}', 
                       xy=(i, row["avg_success_rate"]), 
                       ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_title(f'Taxa de Sucesso Média por Versão\n{scenario_title}', fontsize=14, fontweight='bold')
        ax.set_ylabel('Taxa de Sucesso Média')
        ax.set_xlabel('Versão do Serviço')
        ax.set_xticks(range(len(treatments_order)))
        ax.set_xticklabels([VERSION_LABELS.get(v, v) for v in treatments_order])
        ax.set_ylim(0, 1.15)
        ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5, label='100%')
        plt.tight_layout()
        plot_path = PLOTS_DIR / f'bar_success_rate_{scenario}.png'
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico salvo em: {plot_path}")

        # Gráfico de Barras - Tempo de Resposta p95 (com valores anotados)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=scenario_data,
            x='treatment',
            y='avg_p95_duration',
            hue='treatment',
            order=treatments_order,
            hue_order=treatments_order,
            palette=palette,
            legend=False,
            ax=ax
        )
        # Adiciona valores nas barras
        for i, (idx, row) in enumerate(scenario_data.set_index('treatment').loc[treatments_order].iterrows()):
            val = row["avg_p95_duration"]
            label = f'{val:.0f}ms' if val < 1000 else f'{val/1000:.1f}s'
            ax.annotate(label, xy=(i, val), ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_title(f'Tempo de Resposta Médio (p95) por Versão\n{scenario_title}', fontsize=14, fontweight='bold')
        ax.set_ylabel('Tempo de Resposta p95 (ms) - Escala Log')
        ax.set_xlabel('Versão do Serviço')
        ax.set_xticks(range(len(treatments_order)))
        ax.set_xticklabels([VERSION_LABELS.get(v, v) for v in treatments_order])
        ax.set_yscale('log')
        plt.tight_layout()
        plot_path = PLOTS_DIR / f'bar_p95_duration_{scenario}.png'
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico salvo em: {plot_path}")

        # Boxplot - Distribuição do Tempo de Resposta Médio
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(
            data=scenario_raw,
            x='treatment',
            y='avg_duration_ms',
            hue='treatment',
            order=treatments_order,
            hue_order=treatments_order,
            palette=palette,
            legend=False,
            ax=ax
        )
        ax.set_title(f'Distribuição do Tempo de Resposta (Médio)\n{scenario_title}', fontsize=14, fontweight='bold')
        ax.set_ylabel('Tempo de Resposta Médio (ms) - Escala Log')
        ax.set_xlabel('Versão do Serviço')
        ax.set_xticks(range(len(treatments_order)))
        ax.set_xticklabels([VERSION_LABELS.get(v, v) for v in treatments_order])
        ax.set_yscale('log')
        plt.tight_layout()
        plot_path = PLOTS_DIR / f'boxplot_avg_duration_{scenario}.png'
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico salvo em: {plot_path}")
        
        # =====================================================================
        # 2. COMPARAÇÕES 2 A 2 (Referência vs cada alternativa)
        # =====================================================================
        
        for other_v in other_versions:
            comparison_versions = [REFERENCE_VERSION, other_v]
            comparison_data = scenario_data[scenario_data['treatment'].isin(comparison_versions)]
            comparison_raw = scenario_raw[scenario_raw['treatment'].isin(comparison_versions)]
            comp_palette = [VERSION_COLORS[v] for v in comparison_versions]
            
            # --- Comparação Taxa de Sucesso ---
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Barras lado a lado
            ax1 = axes[0]
            sns.barplot(
                data=comparison_data,
                x='treatment',
                y='avg_success_rate',
                hue='treatment',
                order=comparison_versions,
                hue_order=comparison_versions,
                palette=comp_palette,
                legend=False,
                ax=ax1
            )
            for i, v in enumerate(comparison_versions):
                row = comparison_data[comparison_data['treatment'] == v].iloc[0]
                ax1.annotate(f'{row["avg_success_rate"]:.1%}', 
                           xy=(i, row["avg_success_rate"]), 
                           ha='center', va='bottom', fontsize=12, fontweight='bold')
            ax1.set_title('Taxa de Sucesso Média', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Taxa de Sucesso')
            ax1.set_xlabel('')
            ax1.set_xticks(range(len(comparison_versions)))
            ax1.set_xticklabels([VERSION_LABELS.get(v, v) for v in comparison_versions])
            ax1.set_ylim(0, 1.15)
            
            # Boxplot lado a lado
            ax2 = axes[1]
            sns.boxplot(
                data=comparison_raw,
                x='treatment',
                y='success_rate',
                hue='treatment',
                order=comparison_versions,
                hue_order=comparison_versions,
                palette=comp_palette,
                legend=False,
                ax=ax2
            )
            ax2.set_title('Distribuição da Taxa de Sucesso', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Taxa de Sucesso')
            ax2.set_xlabel('')
            ax2.set_xticks(range(len(comparison_versions)))
            ax2.set_xticklabels([VERSION_LABELS.get(v, v) for v in comparison_versions])
            ax2.set_ylim(0, 1.05)
            
            fig.suptitle(f'Comparação: {VERSION_LABELS[REFERENCE_VERSION]} vs {VERSION_LABELS[other_v]}\n{scenario_title}', 
                        fontsize=14, fontweight='bold')
            plt.tight_layout()
            plot_path = PLOTS_DIR / f'comparison_{REFERENCE_VERSION}_vs_{other_v}_success_{scenario}.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            logger.info(f"Gráfico de comparação salvo em: {plot_path}")
            
            # --- Comparação Tempo de Resposta ---
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Barras p95
            ax1 = axes[0]
            sns.barplot(
                data=comparison_data,
                x='treatment',
                y='avg_p95_duration',
                hue='treatment',
                order=comparison_versions,
                hue_order=comparison_versions,
                palette=comp_palette,
                legend=False,
                ax=ax1
            )
            for i, v in enumerate(comparison_versions):
                row = comparison_data[comparison_data['treatment'] == v].iloc[0]
                val = row["avg_p95_duration"]
                label = f'{val:.0f}ms' if val < 1000 else f'{val/1000:.1f}s'
                ax1.annotate(label, xy=(i, val), ha='center', va='bottom', fontsize=11, fontweight='bold')
            ax1.set_title('Tempo de Resposta p95 (Média)', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Tempo (ms) - Escala Log')
            ax1.set_xlabel('')
            ax1.set_xticks(range(len(comparison_versions)))
            ax1.set_xticklabels([VERSION_LABELS.get(v, v) for v in comparison_versions])
            ax1.set_yscale('log')
            
            # Boxplot tempo médio
            ax2 = axes[1]
            sns.boxplot(
                data=comparison_raw,
                x='treatment',
                y='avg_duration_ms',
                hue='treatment',
                order=comparison_versions,
                hue_order=comparison_versions,
                palette=comp_palette,
                legend=False,
                ax=ax2
            )
            ax2.set_title('Distribuição Tempo de Resposta (Médio)', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Tempo (ms) - Escala Log')
            ax2.set_xlabel('')
            ax2.set_xticks(range(len(comparison_versions)))
            ax2.set_xticklabels([VERSION_LABELS.get(v, v) for v in comparison_versions])
            ax2.set_yscale('log')
            
            fig.suptitle(f'Comparação: {VERSION_LABELS[REFERENCE_VERSION]} vs {VERSION_LABELS[other_v]}\n{scenario_title}', 
                        fontsize=14, fontweight='bold')
            plt.tight_layout()
            plot_path = PLOTS_DIR / f'comparison_{REFERENCE_VERSION}_vs_{other_v}_latency_{scenario}.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            logger.info(f"Gráfico de comparação salvo em: {plot_path}")


def generate_timeseries_visualizations(ts_df: pd.DataFrame):
    """
    Gera e salva os gráficos de série temporal com melhor visualização.
    Inclui gráficos em painel (facet) e comparações 2 a 2.

    Args:
        ts_df: DataFrame com os dados de série temporal agregados.
    """
    if ts_df.empty:
        logger.warning("Nenhum dado de série temporal para gerar visualizações.")
        return
        
    logger.info("Gerando visualizações de série temporal")
    TIMESERIES_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    scenarios = ts_df['scenario'].unique()
    treatments_order = sorted(ts_df['treatment'].unique())
    other_versions = [v for v in treatments_order if v != REFERENCE_VERSION]
    
    # Paleta de cores ordenada
    palette = [VERSION_COLORS[v] for v in treatments_order]
    palette_dict = {v: VERSION_COLORS[v] for v in treatments_order}

    for scenario in scenarios:
        scenario_title = scenario.replace("-", " ").title()
        scenario_df = ts_df[ts_df['scenario'] == scenario].copy()
        
        # Adiciona labels descritivos para legendas
        scenario_df['version_label'] = scenario_df['treatment'].map(VERSION_LABELS)

        # =====================================================================
        # 1. GRÁFICOS EM PAINEL (FACET) - cada versão em seu próprio painel
        # =====================================================================
        
        # Facet Grid: Tempo de Resposta p95 por versão
        g = sns.FacetGrid(scenario_df, col='treatment', col_order=treatments_order, 
                         col_wrap=2, height=4, aspect=1.5, sharey=True)
        g.map_dataframe(sns.lineplot, x='time_offset', y='p95_duration_ms', 
                       color='steelblue', linewidth=1.5)
        g.set_axis_labels('Tempo de Teste (s)', 'p95 Latência (ms)')
        g.set_titles(col_template='{col_name}')
        # Renomeia títulos com labels descritivos
        for ax, v in zip(g.axes.flat, treatments_order):
            ax.set_title(VERSION_LABELS.get(v, v), fontsize=11, fontweight='bold')
            ax.set_yscale('log')
        g.figure.suptitle(f'Tempo de Resposta (p95) por Versão\n{scenario_title}', 
                         fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plot_path = TIMESERIES_PLOTS_DIR / f'facet_p95_duration_{scenario}.png'
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico facet salvo em: {plot_path}")

        # Facet Grid: Taxa de Erro por versão
        g = sns.FacetGrid(scenario_df, col='treatment', col_order=treatments_order, 
                         col_wrap=2, height=4, aspect=1.5, sharey=True)
        g.map_dataframe(sns.lineplot, x='time_offset', y='error_rate', 
                       color='crimson', linewidth=1.5)
        g.set_axis_labels('Tempo de Teste (s)', 'Taxa de Erro')
        for ax, v in zip(g.axes.flat, treatments_order):
            ax.set_title(VERSION_LABELS.get(v, v), fontsize=11, fontweight='bold')
            ax.set_ylim(0, 1.05)
        g.figure.suptitle(f'Taxa de Erro por Versão\n{scenario_title}', 
                         fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plot_path = TIMESERIES_PLOTS_DIR / f'facet_error_rate_{scenario}.png'
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico facet salvo em: {plot_path}")

        # =====================================================================
        # 2. COMPARAÇÕES 2 A 2 (Referência vs cada alternativa) - Série Temporal
        # =====================================================================
        
        for other_v in other_versions:
            comparison_versions = [REFERENCE_VERSION, other_v]
            comparison_df = scenario_df[scenario_df['treatment'].isin(comparison_versions)]
            comp_palette = {v: VERSION_COLORS[v] for v in comparison_versions}
            
            # Gráfico comparativo: Latência p95
            fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
            
            # Painel superior: Latência p95
            ax1 = axes[0]
            for v in comparison_versions:
                v_data = comparison_df[comparison_df['treatment'] == v]
                ax1.plot(v_data['time_offset'], v_data['p95_duration_ms'], 
                        color=VERSION_COLORS[v], linewidth=2, 
                        marker=VERSION_MARKERS[v], markevery=10, markersize=6,
                        label=VERSION_LABELS[v])
            ax1.set_ylabel('Tempo de Resposta p95 (ms)', fontsize=11)
            ax1.set_yscale('log')
            ax1.legend(loc='upper right', fontsize=10)
            ax1.set_title('Latência (p95)', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Painel inferior: Taxa de Erro
            ax2 = axes[1]
            for v in comparison_versions:
                v_data = comparison_df[comparison_df['treatment'] == v]
                ax2.plot(v_data['time_offset'], v_data['error_rate'], 
                        color=VERSION_COLORS[v], linewidth=2, 
                        marker=VERSION_MARKERS[v], markevery=10, markersize=6,
                        label=VERSION_LABELS[v], linestyle='--')
            ax2.set_ylabel('Taxa de Erro', fontsize=11)
            ax2.set_xlabel('Tempo de Teste (segundos)', fontsize=11)
            ax2.set_ylim(0, 1.05)
            ax2.legend(loc='upper right', fontsize=10)
            ax2.set_title('Taxa de Erro', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            fig.suptitle(f'Comparação Temporal: {VERSION_LABELS[REFERENCE_VERSION]} vs {VERSION_LABELS[other_v]}\n{scenario_title}', 
                        fontsize=14, fontweight='bold')
            plt.tight_layout()
            plot_path = TIMESERIES_PLOTS_DIR / f'comparison_{REFERENCE_VERSION}_vs_{other_v}_{scenario}.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            logger.info(f"Gráfico de comparação temporal salvo em: {plot_path}")

        # =====================================================================
        # 3. GRÁFICO RESUMO AGREGADO (todas as versões, melhor visualização)
        # =====================================================================
        
        # Gráfico com subplots lado a lado para latência e erro
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Latência p95
        ax1 = axes[0]
        for v in treatments_order:
            v_data = scenario_df[scenario_df['treatment'] == v]
            ax1.plot(v_data['time_offset'], v_data['p95_duration_ms'], 
                    color=VERSION_COLORS[v], linewidth=2, 
                    marker=VERSION_MARKERS[v], markevery=15, markersize=5,
                    label=VERSION_LABELS[v], alpha=0.8)
        ax1.set_ylabel('Tempo de Resposta p95 (ms)', fontsize=11)
        ax1.set_xlabel('Tempo de Teste (segundos)', fontsize=11)
        ax1.set_yscale('log')
        ax1.legend(loc='upper right', fontsize=9)
        ax1.set_title('Latência (p95)', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Taxa de Erro
        ax2 = axes[1]
        for v in treatments_order:
            v_data = scenario_df[scenario_df['treatment'] == v]
            ax2.plot(v_data['time_offset'], v_data['error_rate'], 
                    color=VERSION_COLORS[v], linewidth=2, 
                    marker=VERSION_MARKERS[v], markevery=15, markersize=5,
                    label=VERSION_LABELS[v], alpha=0.8)
        ax2.set_ylabel('Taxa de Erro', fontsize=11)
        ax2.set_xlabel('Tempo de Teste (segundos)', fontsize=11)
        ax2.set_ylim(0, 1.05)
        ax2.legend(loc='upper right', fontsize=9)
        ax2.set_title('Taxa de Erro', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        fig.suptitle(f'Evolução Temporal - Todas as Versões\n{scenario_title}', 
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plot_path = TIMESERIES_PLOTS_DIR / f'summary_all_versions_{scenario}.png'
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        logger.info(f"Gráfico resumo salvo em: {plot_path}")


def export_to_latex(grouped_df: pd.DataFrame, stats_df: pd.DataFrame):
    """
    Exporta os DataFrames de resultados para arquivos .tex.

    Args:
        grouped_df: DataFrame da análise exploratória.
        stats_df: DataFrame com os resultados estatísticos.
    """
    logger.info("Exportando tabelas para LaTeX")
    LATEX_DIR.mkdir(parents=True, exist_ok=True)

    # Tabela de Resumo EDA
    try:
        latex_eda = grouped_df.to_latex(
            index=False,
            float_format="%.3f",
            caption='Análise Agrupada das Métricas de Performance.',
            label='tab:grouped_analysis',
            longtable=True
        )
        path_eda = LATEX_DIR / 'tabela_resumo_eda.tex'
        with open(path_eda, 'w') as f:
            f.write(latex_eda)
        logger.info(f"Tabela de resumo salva em: {path_eda}")
    except Exception as e:
        logger.error(f"Erro ao exportar tabela EDA para LaTeX: {e}")

    # Tabela de Resultados Estatísticos
    if not stats_df.empty:
        try:
            latex_stats = stats_df.to_latex(
                index=False,
                float_format="%.4f",
                caption='Resultados do Teste U de Mann-Whitney.',
                label='tab:mann_whitney_results',
                longtable=True
            )
            path_stats = LATEX_DIR / 'tabela_resultados_estatisticos.tex'
            with open(path_stats, 'w') as f:
                f.write(latex_stats)
            logger.info(f"Tabela de estatísticas salva em: {path_stats}")
        except Exception as e:
            logger.error(f"Erro ao exportar tabela de estatísticas para LaTeX: {e}")


def main():
    """
    Função principal para orquestrar a análise de dados.
    """
    logger.info("Iniciando a análise de performance...")
    
    # --- Análise de Sumários ---
    logger.info("*** Iniciando Análise de Sumários ***")
    try:
        summary_df = load_summary_files(EXPERIMENT_DIR)
        
        # Análise Exploratória
        grouped_analysis_df = perform_exploratory_analysis(summary_df)
        
        # Análise Estatística
        statistical_results_df = run_statistical_analysis(summary_df, reference_version='v2')
        
        # Geração de Gráficos (Barras, Boxplots)
        generate_visualizations(summary_df, grouped_analysis_df)
        
        # Exportação para LaTeX
        export_to_latex(grouped_analysis_df, statistical_results_df)

    except FileNotFoundError as e:
        logger.error(f"Erro na análise de sumários: {e}")
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado na análise de sumários: {e}")


    # --- Análise de Série Temporal ---
    logger.info("*** Iniciando Análise de Série Temporal (Dados Brutos) ***")
    try:
        timeseries_df = load_raw_timeseries_data(EXPERIMENT_DIR, time_bucket='2s')
        
        # Geração de Gráficos de Série Temporal
        generate_timeseries_visualizations(timeseries_df)

    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado na análise de série temporal: {e}")

    
    logger.info("Análise concluída com sucesso!")


if __name__ == '__main__':
    main()
