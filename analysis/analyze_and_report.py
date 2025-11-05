import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass
import gc  # Garbage collector para gerenciar memória
from scipy import stats

# Configurações globais
RESULTS_DIR = "k6/results"
OUTPUT_DIR = "analysis_results"
PLOT_DIR = os.path.join(OUTPUT_DIR, "plots")
MARKDOWN_DIR = os.path.join(OUTPUT_DIR, "markdown")

# Configuração de estilo para gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Criar diretórios necessários
for dir_path in [OUTPUT_DIR, PLOT_DIR, MARKDOWN_DIR]:
    os.makedirs(dir_path, exist_ok=True)

@dataclass
class ScenarioConfig:
    """Configuração específica para cada cenário"""
    name: str
    max_lines: int
    skip: bool = False
    
# Configurações otimizadas por cenário - EXCLUINDO ou LIMITANDO Estresse
SCENARIO_CONFIGS = {
    "Normal": ScenarioConfig("Normal", 50000, False),
    "Latencia": ScenarioConfig("Latencia", 50000, False),
    "Falha": ScenarioConfig("Falha", 50000, False),
    "Alta_Concorrencia": ScenarioConfig("Alta_Concorrencia", 200000, False),
    "Estresse": ScenarioConfig("Estresse", 50000, True),  # SKIP = True para ignorar
    "FalhasIntermitentes": ScenarioConfig("FalhasIntermitentes", 200000, False),
    "Recuperacao": ScenarioConfig("Recuperacao", 200000, False),
}

class TestAnalyzer:
    def __init__(self, use_sampling=False, sampling_rate=0.05):
        """
        Analisador otimizado com processamento em streaming
        
        Melhorias implementadas:
        1. Processamento em streaming (O(n) ao invés de O(n²))
        2. Uso de numpy arrays ao invés de listas Python
        3. Liberação de memória após processamento
        4. Configuração por cenário
        5. Opção de pular cenários pesados (Estresse)
        """
        self.scenarios = [name for name, cfg in SCENARIO_CONFIGS.items() if not cfg.skip]
        self.versions = ["V1", "V2"]
        self.df_summary = None
        self.use_sampling = use_sampling
        self.sampling_rate = sampling_rate
        self.detailed_metrics = {}  # Para análises estatísticas avançadas

    def _process_file_streaming(self, file_path: str, scenario: str) -> Dict[str, Any]:
        """
        Processa arquivo em streaming com complexidade O(n)
        Usa numpy arrays para melhor performance
        """
        config = SCENARIO_CONFIGS[scenario]
        max_lines = config.max_lines
        
        # Usar arrays numpy pré-alocados para melhor performance
        http_durations = []
        iteration_durations = []
        vus_list = []
        
        http_reqs = 0
        http_failed = 0
        http_success = 0
        line_count = 0
        sampled_count = 0
        
        print(f"   Processando: {file_path}")
        file_size = os.path.getsize(file_path)
        print(f"   - Tamanho: {file_size / 1024 / 1024:.2f} MB | Limite: {max_lines:,} linhas")
        
        with open(file_path, 'r') as f:
            for line in f:
                line_count += 1
                
                # Amostragem ou limite
                if self.use_sampling and np.random.random() > self.sampling_rate:
                    continue
                    
                if sampled_count >= max_lines:
                    break
                
                try:
                    point = json.loads(line)
                    if point.get('type') != 'Point':
                        continue
                    
                    metric = point.get('metric')
                    value = point.get('data', {}).get('value', 0)
                    tags = point.get('data', {}).get('tags', {})
                    
                    # Processamento otimizado - direto em arrays
                    if metric == 'http_req_duration':
                        http_durations.append(value)
                    elif metric == 'http_reqs':
                        http_reqs += 1
                        # CORREÇÃO: Verificar status HTTP para determinar sucesso/falha
                        status = tags.get('status', '200')
                        if status.startswith('2'):  # 2xx = sucesso
                            http_success += 1
                        else:  # Qualquer outro status = falha
                            http_failed += 1
                    elif metric == 'vus':
                        vus_list.append(value)
                    elif metric == 'iteration_duration':
                        iteration_durations.append(value)
                    
                    sampled_count += 1
                    
                    # Progresso a cada 50k linhas
                    if sampled_count % 50000 == 0:
                        print(f"   - {sampled_count:,} linhas processadas...")
                        
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Converter para numpy arrays para cálculos otimizados
        http_durations = np.array(http_durations) if http_durations else np.array([])
        iteration_durations = np.array(iteration_durations) if iteration_durations else np.array([])
        vus_array = np.array(vus_list) if vus_list else np.array([])
        
        print(f"   - Processados: {sampled_count:,} de {line_count:,} linhas")
        print(f"   - Requisições: Total={http_reqs}, Sucesso={http_success}, Falha={http_failed}")
        
        return {
            'http_durations': http_durations,
            'iteration_durations': iteration_durations,
            'vus': vus_array,
            'http_reqs': http_reqs,
            'http_failed': http_failed,
            'http_success': http_success,
            'lines_processed': sampled_count
        }
    
    def _calculate_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """
        Calcula estatísticas avançadas de forma otimizada
        Complexidade: O(n log n) devido ao sort para percentis
        """
        if len(data) == 0:
            return {
                'mean': 0, 'median': 0, 'std': 0,
                'min': 0, 'max': 0,
                'p50': 0, 'p75': 0, 'p90': 0, 'p95': 0, 'p99': 0,
                'cv': 0  # Coeficiente de variação
            }
        
        # Cálculos vetorizados - muito mais rápidos
        return {
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'p50': float(np.percentile(data, 50)),
            'p75': float(np.percentile(data, 75)),
            'p90': float(np.percentile(data, 90)),
            'p95': float(np.percentile(data, 95)),
            'p99': float(np.percentile(data, 99)),
            'cv': float(np.std(data) / np.mean(data)) if np.mean(data) > 0 else 0
        }

    def process_all_scenarios(self):
        """
        Processa todos os cenários de forma otimizada
        Libera memória após cada processamento
        """
        summary_data = []
        
        for version in self.versions:
            for scenario in self.scenarios:
                file_path = os.path.join(RESULTS_DIR, f"{version}_{scenario}.json")
                
                if not os.path.exists(file_path):
                    print(f"   ⚠ Arquivo não encontrado: {file_path}")
                    continue
                
                # Processar arquivo em streaming
                metrics = self._process_file_streaming(file_path, scenario)
                
                # Calcular estatísticas otimizadas
                duration_stats = self._calculate_statistics(metrics['http_durations'])
                iteration_stats = self._calculate_statistics(metrics['iteration_durations'])
                
                # Construir resumo
                summary = {
                    'version': version,
                    'scenario': scenario,
                    'total_requests': metrics['http_reqs'],
                    'failed_requests': metrics['http_failed'],
                    'error_rate': (metrics['http_failed'] / metrics['http_reqs'] * 100) if metrics['http_reqs'] > 0 else 0,
                    'max_vus': int(np.max(metrics['vus'])) if len(metrics['vus']) > 0 else 0,
                    'lines_processed': metrics['lines_processed'],
                    
                    # Estatísticas de duração HTTP
                    'avg_response_time': duration_stats['mean'],
                    'median_response_time': duration_stats['median'],
                    'std_response_time': duration_stats['std'],
                    'min_response_time': duration_stats['min'],
                    'max_response_time': duration_stats['max'],
                    'p50_response_time': duration_stats['p50'],
                    'p75_response_time': duration_stats['p75'],
                    'p90_response_time': duration_stats['p90'],
                    'p95_response_time': duration_stats['p95'],
                    'p99_response_time': duration_stats['p99'],
                    'cv_response_time': duration_stats['cv'],
                    
                    # Estatísticas de iteração
                    'avg_iteration_time': iteration_stats['mean'],
                    'p95_iteration_time': iteration_stats['p95'],
                }
                
                print(f"   ✓ {version}_{scenario}: {summary['total_requests']:,} reqs, "
                      f"Avg: {summary['avg_response_time']:.2f}ms, "
                      f"P95: {summary['p95_response_time']:.2f}ms, "
                      f"Erro: {summary['error_rate']:.2f}%")
                
                summary_data.append(summary)
                
                # Salvar métricas detalhadas para análises avançadas
                self.detailed_metrics[f"{version}_{scenario}"] = {
                    'durations': metrics['http_durations'],
                    'stats': duration_stats
                }
                
                # Liberar memória
                del metrics
                gc.collect()
        
        self.df_summary = pd.DataFrame(summary_data)
        print(f"\n   ✓ DataFrame criado com {len(self.df_summary)} cenários")
        return self.df_summary

    def create_comprehensive_plots(self):
        """Cria conjunto completo de gráficos otimizados"""
        if self.df_summary is None or len(self.df_summary) == 0:
            print("   ⚠ DataFrame vazio, pulando gráficos")
            return
        
        # 1. Gráfico de tempos de resposta (Média e P95)
        self._plot_response_times()
        
        # 2. Gráfico de taxas de erro
        self._plot_error_rates()
        
        # 3. Gráfico de distribuição (Box plot)
        self._plot_distribution()
        
        # 4. Gráfico de análise estatística avançada
        self._plot_statistical_analysis()
        
        print("   ✓ Todos os gráficos criados")
    
    def _plot_response_times(self):
        """Gráfico otimizado de tempos de resposta"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Preparar dados
        scenarios_present = self.df_summary['scenario'].unique()
        x = np.arange(len(scenarios_present))
        width = 0.35
        
        v1_data = self.df_summary[self.df_summary['version'] == 'V1'].set_index('scenario')
        v2_data = self.df_summary[self.df_summary['version'] == 'V2'].set_index('scenario')
        
        # Subplot 1: Média
        v1_avg = [v1_data.loc[s, 'avg_response_time'] if s in v1_data.index else 0 for s in scenarios_present]
        v2_avg = [v2_data.loc[s, 'avg_response_time'] if s in v2_data.index else 0 for s in scenarios_present]
        
        ax1.bar(x - width/2, v1_avg, width, label='V1 (Baseline)', alpha=0.8)
        ax1.bar(x + width/2, v2_avg, width, label='V2 (Circuit Breaker)', alpha=0.8)
        ax1.set_xlabel('Cenário', fontsize=12)
        ax1.set_ylabel('Tempo Médio (ms)', fontsize=12)
        ax1.set_title('Tempo de Resposta Médio', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenarios_present, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Subplot 2: P95
        v1_p95 = [v1_data.loc[s, 'p95_response_time'] if s in v1_data.index else 0 for s in scenarios_present]
        v2_p95 = [v2_data.loc[s, 'p95_response_time'] if s in v2_data.index else 0 for s in scenarios_present]
        
        ax2.bar(x - width/2, v1_p95, width, label='V1 (Baseline)', alpha=0.8)
        ax2.bar(x + width/2, v2_p95, width, label='V2 (Circuit Breaker)', alpha=0.8)
        ax2.set_xlabel('Cenário', fontsize=12)
        ax2.set_ylabel('P95 (ms)', fontsize=12)
        ax2.set_title('Tempo de Resposta P95', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenarios_present, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'response_times.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_error_rates(self):
        """Gráfico de taxas de erro"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        scenarios_present = self.df_summary['scenario'].unique()
        x = np.arange(len(scenarios_present))
        width = 0.35
        
        v1_data = self.df_summary[self.df_summary['version'] == 'V1'].set_index('scenario')
        v2_data = self.df_summary[self.df_summary['version'] == 'V2'].set_index('scenario')
        
        v1_errors = [v1_data.loc[s, 'error_rate'] if s in v1_data.index else 0 for s in scenarios_present]
        v2_errors = [v2_data.loc[s, 'error_rate'] if s in v2_data.index else 0 for s in scenarios_present]
        
        ax.bar(x - width/2, v1_errors, width, label='V1 (Baseline)', color='#d62728', alpha=0.8)
        ax.bar(x + width/2, v2_errors, width, label='V2 (Circuit Breaker)', color='#2ca02c', alpha=0.8)
        
        ax.set_xlabel('Cenário', fontsize=12)
        ax.set_ylabel('Taxa de Erro (%)', fontsize=12)
        ax.set_title('Comparação de Taxa de Erro por Cenário', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios_present, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'error_rates.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_distribution(self):
        """Box plot para visualizar distribuição"""
        scenarios_with_data = [s for s in self.scenarios if 
            (f"V1_{s}" in self.detailed_metrics or f"V2_{s}" in self.detailed_metrics)]
        
        if not scenarios_with_data:
            return
        
        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        axes = axes.flatten()
        
        for idx, scenario in enumerate(scenarios_with_data[:8]):  # Máximo 8 gráficos
            ax = axes[idx]
            
            data_to_plot = []
            labels = []
            
            for version in ['V1', 'V2']:
                key = f"{version}_{scenario}"
                if key in self.detailed_metrics and len(self.detailed_metrics[key]['durations']) > 0:
                    # Amostrar para evitar overhead em box plots
                    durations = self.detailed_metrics[key]['durations']
                    if len(durations) > 10000:
                        durations = np.random.choice(durations, 10000, replace=False)
                    data_to_plot.append(durations)
                    labels.append(version)
            
            if data_to_plot:
                bp = ax.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
                for patch, color in zip(bp['boxes'], ['lightblue', 'lightgreen']):
                    patch.set_facecolor(color)
                ax.set_title(scenario, fontsize=12, fontweight='bold')
                ax.set_ylabel('Tempo de Resposta (ms)', fontsize=10)
                ax.grid(axis='y', alpha=0.3)
        
        # Ocultar eixos extras
        for idx in range(len(scenarios_with_data), 8):
            axes[idx].axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'distribution_boxplot.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_statistical_analysis(self):
        """Gráfico de análise estatística (CV - Coeficiente de Variação)"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        scenarios_present = self.df_summary['scenario'].unique()
        x = np.arange(len(scenarios_present))
        width = 0.35
        
        v1_data = self.df_summary[self.df_summary['version'] == 'V1'].set_index('scenario')
        v2_data = self.df_summary[self.df_summary['version'] == 'V2'].set_index('scenario')
        
        v1_cv = [v1_data.loc[s, 'cv_response_time'] if s in v1_data.index else 0 for s in scenarios_present]
        v2_cv = [v2_data.loc[s, 'cv_response_time'] if s in v2_data.index else 0 for s in scenarios_present]
        
        ax.bar(x - width/2, v1_cv, width, label='V1 (Baseline)', alpha=0.8)
        ax.bar(x + width/2, v2_cv, width, label='V2 (Circuit Breaker)', alpha=0.8)
        
        ax.set_xlabel('Cenário', fontsize=12)
        ax.set_ylabel('Coeficiente de Variação', fontsize=12)
        ax.set_title('Variabilidade do Tempo de Resposta (CV)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios_present, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='CV=0.5 (referência)')
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'statistical_variability.png'), dpi=300, bbox_inches='tight')
        plt.close()

    def generate_markdown_report(self):
        """Gera relatório em Markdown com análises estatísticas avançadas"""
        if self.df_summary is None or len(self.df_summary) == 0:
            print("   ⚠ DataFrame vazio, não foi possível gerar relatório")
            return
        
        scenarios_present = sorted(self.df_summary['scenario'].unique())
        
        report = f"""# Relatório de Análise de Performance - Circuit Breaker

## Sumário Executivo

Este relatório apresenta uma análise comparativa detalhada entre a versão baseline (V1) e a versão com Circuit Breaker (V2) do serviço de pagamento.

**Data da Análise**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

**Cenários Analisados**: {len(scenarios_present)} cenários  
**Versões Comparadas**: V1 (Baseline) vs V2 (Circuit Breaker)

---

## 1. Métricas de Tempo de Resposta

### 1.1 Visão Geral

![Tempos de Resposta](../plots/response_times.png)

| Cenário | V1 Média (ms) | V2 Média (ms) | Melhoria (%) | V1 P95 (ms) | V2 P95 (ms) |
|---------|---------------|---------------|--------------|-------------|-------------|
"""
        
        for scenario in scenarios_present:
            v1 = self.df_summary[(self.df_summary['version'] == 'V1') & (self.df_summary['scenario'] == scenario)]
            v2 = self.df_summary[(self.df_summary['version'] == 'V2') & (self.df_summary['scenario'] == scenario)]
            
            if len(v1) > 0 and len(v2) > 0:
                v1_avg = v1['avg_response_time'].values[0]
                v2_avg = v2['avg_response_time'].values[0]
                improvement = ((v1_avg - v2_avg) / v1_avg * 100) if v1_avg > 0 else 0
                v1_p95 = v1['p95_response_time'].values[0]
                v2_p95 = v2['p95_response_time'].values[0]
                
                report += f"| {scenario} | {v1_avg:.2f} | {v2_avg:.2f} | {improvement:+.1f}% | {v1_p95:.2f} | {v2_p95:.2f} |\n"

        report += """
### 1.2 Distribuição de Tempos

![Distribuição](../plots/distribution_boxplot.png)

---

## 2. Análise de Confiabilidade

### 2.1 Taxas de Erro

![Taxas de Erro](../plots/error_rates.png)

| Cenário | V1 Erro (%) | V2 Erro (%) | Redução (p.p.) | V1 Reqs | V2 Reqs |
|---------|-------------|-------------|----------------|---------|---------|
"""

        for scenario in scenarios_present:
            v1 = self.df_summary[(self.df_summary['version'] == 'V1') & (self.df_summary['scenario'] == scenario)]
            v2 = self.df_summary[(self.df_summary['version'] == 'V2') & (self.df_summary['scenario'] == scenario)]
            
            if len(v1) > 0 and len(v2) > 0:
                v1_err = v1['error_rate'].values[0]
                v2_err = v2['error_rate'].values[0]
                reduction = v1_err - v2_err
                v1_reqs = v1['total_requests'].values[0]
                v2_reqs = v2['total_requests'].values[0]
                
                report += f"| {scenario} | {v1_err:.2f} | {v2_err:.2f} | {reduction:+.2f} | {v1_reqs:,.0f} | {v2_reqs:,.0f} |\n"

        report += """
---

## 3. Análise Estatística Avançada

### 3.1 Variabilidade (Coeficiente de Variação)

![Variabilidade](../plots/statistical_variability.png)

O Coeficiente de Variação (CV) indica a consistência do sistema:
- **CV < 0.3**: Excelente consistência
- **CV 0.3-0.5**: Boa consistência  
- **CV > 0.5**: Alta variabilidade

| Cenário | V1 CV | V2 CV | Interpretação |
|---------|-------|-------|---------------|
"""

        for scenario in scenarios_present:
            v1 = self.df_summary[(self.df_summary['version'] == 'V1') & (self.df_summary['scenario'] == scenario)]
            v2 = self.df_summary[(self.df_summary['version'] == 'V2') & (self.df_summary['scenario'] == scenario)]
            
            if len(v1) > 0 and len(v2) > 0:
                v1_cv = v1['cv_response_time'].values[0]
                v2_cv = v2['cv_response_time'].values[0]
                
                # Interpretação
                if v2_cv < v1_cv:
                    interp = "✅ V2 mais consistente"
                elif v2_cv > v1_cv:
                    interp = "⚠️ V1 mais consistente"
                else:
                    interp = "= Equivalente"
                
                report += f"| {scenario} | {v1_cv:.3f} | {v2_cv:.3f} | {interp} |\n"

        report += """
### 3.2 Percentis Detalhados

| Cenário | Versão | P50 (ms) | P75 (ms) | P90 (ms) | P95 (ms) | P99 (ms) | Max (ms) |
|---------|--------|----------|----------|----------|----------|----------|----------|
"""

        for scenario in scenarios_present:
            for version in ['V1', 'V2']:
                data = self.df_summary[(self.df_summary['version'] == version) & (self.df_summary['scenario'] == scenario)]
                if len(data) > 0:
                    row = data.iloc[0]
                    report += f"| {scenario} | {version} | {row['p50_response_time']:.2f} | {row['p75_response_time']:.2f} | {row['p90_response_time']:.2f} | {row['p95_response_time']:.2f} | {row['p99_response_time']:.2f} | {row['max_response_time']:.2f} |\n"

        report += """
---

## 4. Análise por Cenário

"""

        for scenario in scenarios_present:
            v1 = self.df_summary[(self.df_summary['version'] == 'V1') & (self.df_summary['scenario'] == scenario)]
            v2 = self.df_summary[(self.df_summary['version'] == 'V2') & (self.df_summary['scenario'] == scenario)]
            
            if len(v1) > 0 and len(v2) > 0:
                report += f"""
### 4.{scenarios_present.index(scenario) + 1} {scenario}

| Métrica | V1 | V2 | Comparação |
|---------|-----|-----|------------|
| Tempo Médio | {v1['avg_response_time'].values[0]:.2f} ms | {v2['avg_response_time'].values[0]:.2f} ms | {((v1['avg_response_time'].values[0] - v2['avg_response_time'].values[0]) / v1['avg_response_time'].values[0] * 100):+.1f}% |
| Tempo Mediano | {v1['median_response_time'].values[0]:.2f} ms | {v2['median_response_time'].values[0]:.2f} ms | {((v1['median_response_time'].values[0] - v2['median_response_time'].values[0]) / v1['median_response_time'].values[0] * 100) if v1['median_response_time'].values[0] > 0 else 0:+.1f}% |
| Desvio Padrão | {v1['std_response_time'].values[0]:.2f} ms | {v2['std_response_time'].values[0]:.2f} ms | - |
| P95 | {v1['p95_response_time'].values[0]:.2f} ms | {v2['p95_response_time'].values[0]:.2f} ms | {((v1['p95_response_time'].values[0] - v2['p95_response_time'].values[0]) / v1['p95_response_time'].values[0] * 100) if v1['p95_response_time'].values[0] > 0 else 0:+.1f}% |
| P99 | {v1['p99_response_time'].values[0]:.2f} ms | {v2['p99_response_time'].values[0]:.2f} ms | {((v1['p99_response_time'].values[0] - v2['p99_response_time'].values[0]) / v1['p99_response_time'].values[0] * 100) if v1['p99_response_time'].values[0] > 0 else 0:+.1f}% |
| Taxa de Erro | {v1['error_rate'].values[0]:.2f}% | {v2['error_rate'].values[0]:.2f}% | {v1['error_rate'].values[0] - v2['error_rate'].values[0]:+.2f} p.p. |
| Total Requisições | {v1['total_requests'].values[0]:,.0f} | {v2['total_requests'].values[0]:,.0f} | - |

"""

        report += """
---

## 5. Conclusões e Recomendações

### 5.1 Principais Descobertas

1. **Performance**: Análise comparativa dos tempos de resposta entre V1 e V2
2. **Resiliência**: Avaliação da capacidade de recuperação em cenários de falha
3. **Consistência**: Medição da variabilidade através do coeficiente de variação
4. **Escalabilidade**: Comportamento sob diferentes cargas de trabalho

### 5.2 Recomendações

1. **Otimizações**: Baseadas nas métricas de performance observadas
2. **Configuração do Circuit Breaker**: Ajustes nos thresholds com base nos resultados
3. **Monitoramento**: Métricas críticas a serem acompanhadas em produção
4. **Próximos Passos**: Testes adicionais e cenários complementares

---

**Nota**: Este relatório foi gerado automaticamente a partir dos dados de teste do k6.
Teste de Estresse foi limitado ou excluído devido ao tamanho excessivo dos logs.
"""

        report_path = os.path.join(MARKDOWN_DIR, 'analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Também salvar o DataFrame como CSV para análises posteriores
        csv_path = os.path.join(OUTPUT_DIR, 'summary_metrics.csv')
        self.df_summary.to_csv(csv_path, index=False)
        
        print(f"   ✓ Relatório Markdown: {report_path}")
        print(f"   ✓ Métricas CSV: {csv_path}")

def main():
    """
    Função principal otimizada
    
    MELHORIAS IMPLEMENTADAS:
    1. Processamento em streaming (O(n) ao invés de O(n²))
    2. Uso de numpy para cálculos vetorizados
    3. Liberação de memória com garbage collector
    4. Configuração por cenário (limites específicos)
    5. Exclusão do cenário Estresse (arquivos muito grandes)
    6. Métricas estatísticas avançadas (CV, percentis completos)
    7. Gráficos adicionais (box plot, variabilidade)
    """
    print("\n" + "="*80)
    print(" ANÁLISE DE PERFORMANCE - CIRCUIT BREAKER (VERSÃO OTIMIZADA)")
    print("="*80)
    
    # Configuração
    use_sampling = False
    sampling_rate = 0.05  # 5% se usar amostragem
    
    # Mostrar cenários que serão processados
    active_scenarios = [name for name, cfg in SCENARIO_CONFIGS.items() if not cfg.skip]
    skipped_scenarios = [name for name, cfg in SCENARIO_CONFIGS.items() if cfg.skip]
    
    print(f"\n📊 Cenários ativos: {', '.join(active_scenarios)}")
    if skipped_scenarios:
        print(f"⏭️  Cenários ignorados: {', '.join(skipped_scenarios)} (arquivos muito grandes)")
    
    print(f"\n⚙️  Modo: {'Amostragem ' + str(int(sampling_rate*100)) + '%' if use_sampling else 'Limite de linhas por cenário'}")
    print("\nLimites configurados:")
    for name, cfg in SCENARIO_CONFIGS.items():
        if not cfg.skip:
            print(f"  - {name}: {cfg.max_lines:,} linhas")
    
    print("\n" + "="*80)
    
    # Inicializar analisador
    analyzer = TestAnalyzer(use_sampling=use_sampling, sampling_rate=sampling_rate)
    
    # Processar dados
    print("\n🔄 ETAPA 1: Processando cenários...")
    print("-"*80)
    analyzer.process_all_scenarios()
    
    # Gerar gráficos
    print("\n📈 ETAPA 2: Gerando visualizações...")
    print("-"*80)
    analyzer.create_comprehensive_plots()
    
    # Gerar relatório
    print("\n📝 ETAPA 3: Gerando relatório...")
    print("-"*80)
    analyzer.generate_markdown_report()
    
    # Resumo final
    print("\n" + "="*80)
    print("✅ ANÁLISE COMPLETA!")
    print("="*80)
    print(f"\n📁 Resultados salvos em: {OUTPUT_DIR}/")
    print(f"\n  📊 Gráficos:")
    print(f"     - {PLOT_DIR}/response_times.png")
    print(f"     - {PLOT_DIR}/error_rates.png")
    print(f"     - {PLOT_DIR}/distribution_boxplot.png")
    print(f"     - {PLOT_DIR}/statistical_variability.png")
    print(f"\n  📄 Relatórios:")
    print(f"     - {MARKDOWN_DIR}/analysis_report.md")
    print(f"     - {OUTPUT_DIR}/summary_metrics.csv")
    print("\n" + "="*80 + "\n")
    
    # Mostrar preview dos resultados
    if analyzer.df_summary is not None and len(analyzer.df_summary) > 0:
        print("📋 Preview das métricas principais:\n")
        preview = analyzer.df_summary[['version', 'scenario', 'avg_response_time', 'p95_response_time', 'error_rate', 'total_requests']]
        print(preview.to_string(index=False))
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()