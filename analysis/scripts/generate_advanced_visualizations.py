#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'figure.figsize': (12, 6),
    'figure.dpi': 300,
    'savefig.dpi': 300,
})

RESULTS_DIR = "analysis_results/csv"
OUTPUT_DIR = "analysis_results/academic_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_cb_state_chart():
    """Generates a timeline showing V2 success rate and inferred CB state."""
    file_path = os.path.join(RESULTS_DIR, "timeline_V2.csv")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # We infer CB state: if latencies are very low (< 5ms) and count is high, it's likely OPEN
    # Realistically, we should use the 503 vs 202 vs 200 counts if available per window.
    # Since timeline_V2.csv only has latency stats, we look for 'valleys' in latency 
    # that correspond to high fallback rates.
    
    # For a better plot, let's load the consolidated benefits to see scenario timings if possible
    # or just use the latency drops.
    
    fig, ax1 = plt.subplots(figsize=(12, 6))

    color_latency = '#1f77b4'
    ax1.set_xlabel('Time (min)')
    ax1.set_ylabel('Latency (ms)', color=color_latency)
    ax1.plot(df.index * 5 / 60, df['Média'], color=color_latency, label='Avg Latency', linewidth=1.5)
    ax1.tick_params(axis='y', labelcolor=color_latency)
    ax1.set_yscale('log')

    # Shade areas where latency is extremely low (Open/Fallback active)
    cb_open = df['Média'] < 10
    ax1.fill_between(df.index * 5 / 60, 0, df['Média'].max(), where=cb_open, 
                    color='orange', alpha=0.2, label='CB Open/Fallback')

    plt.title('V2: Latency and Circuit Breaker State Transitions')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "cb_state_transitions.png"))
    plt.close()
    print("Generated: cb_state_transitions.png")

def generate_correlation_heatmap():
    """Generates a heatmap showing correlations between metrics."""
    # We use the summary analysis per version or scenario
    summary_path = os.path.join(RESULTS_DIR, "summary_analysis.csv")
    if not os.path.exists(summary_path):
        return

    df = pd.read_csv(summary_path)
    # Filter numeric cols
    numeric_df = df.select_dtypes(include=[np.number])
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(numeric_df.corr(), annot=True, cmap='RdYlGn', fmt=".2f")
    plt.title('Metric Correlation Heatmap (V1, V2, V3)')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "metric_correlation_heatmap.png"))
    plt.close()
    print("Generated: metric_correlation_heatmap.png")

if __name__ == "__main__":
    generate_cb_state_chart()
    generate_correlation_heatmap()
