#!/usr/bin/env python3
"""
Advanced Visualizations Generator for TCC Article
Generates CB state transition charts and metric correlation heatmaps
with data from all versions (V1, V2, V3, V4).
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Style configuration for academic publication
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
    'figure.figsize': (12, 8),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'axes.titleweight': 'bold',
})

RESULTS_DIR = "analysis_results/csv"
OUTPUT_DIR = "analysis_results/academic_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Academic color palette matching the project standard
COLORS = {
    'V1': '#7f8c8d',      # Gray (baseline)
    'V2': '#27ae60',      # Green (Circuit Breaker)
    'V3': '#8e44ad',      # Purple (Retry)
    'V4': '#e67e22',      # Orange (Composition)
}

VERSION_LABELS = {
    'V1': 'V1 (Baseline)',
    'V2': 'V2 (Circuit Breaker)',
    'V3': 'V3 (Retry)',
    'V4': 'V4 (Retry + CB)',
}


def generate_cb_state_chart():
    """
    Generates a multi-panel timeline chart showing latency profiles 
    and inferred Circuit Breaker states for all versions.
    
    For V2 and V4 (CB-enabled versions), low latency periods indicate 
    the CB is in OPEN state (fail-fast/fallback active).
    """
    versions = ['V1', 'V2', 'V3', 'V4']
    data = {}
    
    # Load timeline data for all versions
    for v in versions:
        file_path = os.path.join(RESULTS_DIR, f"timeline_{v}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            data[v] = df
    
    if not data:
        print("❌ No timeline data found. Run analysis first.")
        return
    
    # Create multi-panel figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    axes = axes.flatten()
    
    for idx, (version, df) in enumerate(data.items()):
        ax = axes[idx]
        color = COLORS.get(version, '#333333')
        label = VERSION_LABELS.get(version, version)
        
        # Calculate time in minutes from start
        time_minutes = (df.index * 5) / 60
        
        # Plot latency
        ax.plot(time_minutes, df['Média'], color=color, linewidth=1.5, alpha=0.8)
        ax.fill_between(time_minutes, 0, df['Média'], alpha=0.3, color=color)
        
        ax.set_title(f'{label}', fontweight='bold', fontsize=12)
        ax.set_ylabel('Latency (ms)')
        ax.set_yscale('log')
        ax.set_ylim(1, 10000)
        ax.grid(True, alpha=0.3)
        
        # Add statistics annotation
        avg_latency = df['Média'].mean()
        min_latency = df['Média'].min()
        ax.annotate(f'Avg: {avg_latency:.0f}ms\nMin: {min_latency:.1f}ms', 
                   xy=(0.02, 0.98), xycoords='axes fraction',
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Common x-label
    for ax in axes[2:]:
        ax.set_xlabel('Time (minutes)')
    
    plt.suptitle('Circuit Breaker State Transitions and Latency Profiles (V1-V4)', 
                fontweight='bold', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "cb_state_transitions.png"))
    plt.close()
    print("✅ Generated: cb_state_transitions.png (V1-V4)")


def generate_correlation_heatmap():
    """
    Generates a comprehensive correlation heatmap showing relationships
    between key metrics across all versions (V1, V2, V3, V4).
    """
    summary_path = os.path.join(RESULTS_DIR, "summary_analysis.csv")
    if not os.path.exists(summary_path):
        print(f"❌ File not found: {summary_path}")
        return

    df = pd.read_csv(summary_path)
    
    # Rename columns for better readability in the heatmap
    column_renames = {
        'Total Requests': 'Total Requests',
        'Avg Response Time (ms)': 'Avg Latency',
        'P95 Response Time (ms)': 'P95 Latency',
        'Success Rate (%)': 'Success Rate',
        'Fallback Rate (%)': 'Fallback Rate',
        'API Failure Rate (%)': 'Failure Rate'
    }
    
    # Select and rename numeric columns (excluding CB Open Rate)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Remove CB Open Rate column if exists
    numeric_cols = [c for c in numeric_cols if 'Circuit Breaker Open' not in c and 'CB Open' not in c]
    df_numeric = df[['Version'] + numeric_cols].copy()
    df_numeric = df_numeric.rename(columns=column_renames)
    
    # Create a transposed view for better visualization
    # Rows = Metrics, Columns = Versions
    df_transposed = df_numeric.set_index('Version').T
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Left: Metric values heatmap (versions × metrics)
    sns.heatmap(df_transposed, annot=True, fmt='.1f', cmap='YlOrRd',
                ax=ax1, linewidths=0.5, cbar_kws={'label': 'Value'})
    ax1.set_title('Metric Values by Version', fontweight='bold')
    ax1.set_xlabel('Version')
    ax1.set_ylabel('Metric')
    
    # Right: Correlation matrix between metrics
    # Need more data points for meaningful correlation
    # Load scenario data for richer correlation analysis
    scenarios_dir = "analysis_results/scenarios/csv"
    all_data = []
    
    for scenario in ['catastrofe', 'degradacao', 'rajadas', 'indisponibilidade', 'normal']:
        status_file = os.path.join(scenarios_dir, f"{scenario}_status.csv")
        if os.path.exists(status_file):
            df_scenario = pd.read_csv(status_file)
            df_scenario['Scenario'] = scenario
            all_data.append(df_scenario)
    
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        
        # Select numeric columns for correlation
        numeric_scenario_cols = df_all.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_scenario_cols) >= 2:
            corr_matrix = df_all[numeric_scenario_cols].corr()
            
            # Rename for readability (exclude 503 as it's not used in this project)
            rename_map = {
                'Total Success Rate (%)': 'Success Rate',
                'Success Rate (%)': 'Success Rate',
                'Fallback Rate (%)': 'Fallback Rate',
                'API Failure Rate (%)': 'Errors Rate',
            }
            
            # Drop CB Open (503) column and row if it exists (not used in this project)
            cols_to_drop = ['CB Open (503)', 'CB Protection Rate (%)', 'HTTP 503 (%)']
            for col in cols_to_drop:
                if col in corr_matrix.columns:
                    corr_matrix = corr_matrix.drop(col, axis=0, errors='ignore')
                    corr_matrix = corr_matrix.drop(col, axis=1, errors='ignore')
            
            # Also drop non-percentage columns for cleaner visualization
            cols_to_drop_extra = ['Total Requests', 'Success (200)', 'Fallback (202)', 'API Failure (500)']
            for col in cols_to_drop_extra:
                if col in corr_matrix.columns:
                    corr_matrix = corr_matrix.drop(col, axis=0, errors='ignore')
                    corr_matrix = corr_matrix.drop(col, axis=1, errors='ignore')
            
            corr_matrix = corr_matrix.rename(index=rename_map, columns=rename_map)
            
            # Mask upper triangle
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            
            sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                       cmap='RdYlGn', center=0, vmin=-1, vmax=1,
                       ax=ax2, linewidths=0.5,
                       cbar_kws={'label': 'Correlation'})
            ax2.set_title('Metric Correlation Matrix (All Scenarios)', fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'Insufficient data for correlation', 
                ha='center', va='center', fontsize=12)
        ax2.set_title('Metric Correlation Matrix', fontweight='bold')
    
    plt.suptitle('Metric Analysis: Values and Correlations (V1, V2, V3, V4)', 
                fontweight='bold', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "metric_correlation_heatmap.png"))
    plt.close()
    print("✅ Generated: metric_correlation_heatmap.png (V1-V4)")


def copy_to_article():
    """Copy generated images to artigo_latex/images/ directory."""
    import shutil
    
    article_images_dir = "artigo_latex/images"
    os.makedirs(article_images_dir, exist_ok=True)
    
    files_to_copy = [
        "cb_state_transitions.png",
        "metric_correlation_heatmap.png"
    ]
    
    for filename in files_to_copy:
        src = os.path.join(OUTPUT_DIR, filename)
        dst = os.path.join(article_images_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"📋 Copied: {filename} → artigo_latex/images/")
        else:
            print(f"⚠️ Not found: {filename}")


if __name__ == "__main__":
    print("\n📊 Generating Advanced Visualizations (V1-V4)...\n")
    generate_cb_state_chart()
    generate_correlation_heatmap()
    copy_to_article()
    print(f"\n✨ All visualizations saved to: {OUTPUT_DIR}/")
