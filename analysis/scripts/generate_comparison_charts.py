#!/usr/bin/env python3
"""
Script to generate comparative charts V1 vs V2 for Bursts and Catastrophe scenarios.
Detailed focus on Circuit Breaker benefits in these critical scenarios.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np

# Configurações
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'sans-serif'

# Consistent colors
COLORS = {
    'V1': '#d62728',  # Red
    'V2': '#2ca02c',  # Green
    'Success_200': '#27ae60',  # Success green
    'Fallback_202': '#9b59b6',  # Fallback purple
    'Failure_500': '#e74c3c',  # Error red
}

# Directories
CSV_DIR = "analysis_results/scenarios/csv"
OUTPUT_DIR = "analysis_results/comparison_charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Target scenarios
TARGET_SCENARIOS = ['rajadas', 'catastrofe']


def load_scenario_data(scenario):
    """Load data from a specific scenario"""
    status = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
    response = pd.read_csv(f"{CSV_DIR}/{scenario}_response.csv")
    benefits = pd.read_csv(f"{CSV_DIR}/{scenario}_benefits.csv")
    
    return {
        'status': status,
        'response': response,
        'benefits': benefits,
        'name': scenario
    }


def scenario_label(name):
    """Convert scenario name to user-friendly label"""
    labels = {
        'rajadas': 'Intermittent Bursts',
        'catastrofe': 'Catastrophic Failure'
    }
    return labels.get(name, name.replace('_', ' ').title())


def plot_1_success_rate_comparison():
    """Chart 1: Success Rate Comparison V1 vs V2 (Bursts and Catastrophe)"""
    data = []
    
    for scenario in TARGET_SCENARIOS:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        v1 = df[df['Version'] == 'V1'].iloc[0]
        v2 = df[df['Version'] == 'V2'].iloc[0]
        
        data.append({
            'Scenario': scenario_label(scenario),
            'V1 Success Rate (%)': v1['Total Success Rate (%)'],
            'V2 Success Rate (%)': v2['Total Success Rate (%)'],
            'Gain (pp)': v2['Total Success Rate (%)'] - v1['Total Success Rate (%)']
        })
    
    df_plot = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(TARGET_SCENARIOS))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, df_plot['V1 Success Rate (%)'], width, 
                   label='V1 (Baseline - No Circuit Breaker)', 
                   color=COLORS['V1'], alpha=0.9, edgecolor='black', linewidth=1)
    bars2 = ax.bar(x + width/2, df_plot['V2 Success Rate (%)'], width, 
                   label='V2 (With Circuit Breaker)', 
                   color=COLORS['V2'], alpha=0.9, edgecolor='black', linewidth=1)
    
    # Add values on bars
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        h1, h2 = bar1.get_height(), bar2.get_height()
        ax.text(bar1.get_x() + bar1.get_width()/2., h1 + 1,
               f'{h1:.1f}%',
               ha='center', va='bottom', fontweight='bold', fontsize=12)
        ax.text(bar2.get_x() + bar2.get_width()/2., h2 + 1,
               f'{h2:.1f}%',
               ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Gain
        ganho = df_plot['Gain (pp)'].iloc[i]
        mid_x = (bar1.get_x() + bar2.get_x() + bar2.get_width()) / 2
        ax.annotate(f'+{ganho:.1f}pp', 
                   xy=(mid_x, max(h1, h2) + 8),
                   ha='center', fontsize=14, fontweight='bold', color='green',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', edgecolor='green', alpha=0.8))
    
    ax.set_ylabel('Total Success Rate (%)', fontsize=13, fontweight='bold')
    ax.set_title('Circuit Breaker Impact: Success Rate V1 vs V2\nBursts and Catastrophe Scenarios', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot['Scenario'], fontsize=12)
    ax.legend(fontsize=11, loc='lower right')
    ax.set_ylim(0, 115)
    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Ideal Availability')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/01_v1_v2_success_rate_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Chart 1 generated: Success Rate Comparison V1 vs V2")


def plot_2_response_composition():
    """Chart 2: Response Composition (200 + 202 + 500) by scenario"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    for idx, scenario in enumerate(TARGET_SCENARIOS):
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        ax = axes[idx]
        
        v1 = df[df['Version'] == 'V1'].iloc[0]
        v2 = df[df['Version'] == 'V2'].iloc[0]
        
        versions = ['V1\n(Baseline)', 'V2\n(Circuit Breaker)']
        x = np.arange(len(versions))
        width = 0.5
        
        # Stacked data
        success_200 = [v1['Success Rate (%)'], v2['Success Rate (%)']]
        fallback_202 = [0, v2['Fallback Rate (%)']]  # V1 has no fallback
        failure_500 = [v1['API Failure Rate (%)'], v2['API Failure Rate (%)']]
        
        # Stacked bars
        bars1 = ax.bar(x, success_200, width, label='Success (200)', 
                       color=COLORS['Success_200'], edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x, fallback_202, width, bottom=success_200, label='Fallback (202)',
                       color=COLORS['Fallback_202'], edgecolor='black', linewidth=0.5)
        bars3 = ax.bar(x, failure_500, width, 
                       bottom=[s + f for s, f in zip(success_200, fallback_202)],
                       label='Error (500)', color=COLORS['Failure_500'], edgecolor='black', linewidth=0.5)
        
        # Bar annotations
        for i, (s200, f202, e500) in enumerate(zip(success_200, fallback_202, failure_500)):
            if s200 > 3:
                ax.text(x[i], s200/2, f'{s200:.1f}%', ha='center', va='center', 
                       fontweight='bold', fontsize=11, color='white')
            if f202 > 3:
                ax.text(x[i], s200 + f202/2, f'{f202:.1f}%', ha='center', va='center',
                       fontweight='bold', fontsize=11, color='white')
            if e500 > 3:
                ax.text(x[i], s200 + f202 + e500/2, f'{e500:.1f}%', ha='center', va='center',
                       fontweight='bold', fontsize=11, color='white')
        
        ax.set_xticks(x)
        ax.set_xticklabels(versions, fontsize=12)
        ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{scenario_label(scenario)}', fontsize=13, fontweight='bold', pad=10)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        # Add "total success" line for V2
        total_success_v2 = success_200[1] + fallback_202[1]
        ax.axhline(y=total_success_v2, color='green', linestyle='--', alpha=0.7, linewidth=2)
        ax.text(1.3, total_success_v2, f'V2 Total Success:\n{total_success_v2:.1f}%', 
               fontsize=10, fontweight='bold', color='green', va='center')
    
    fig.suptitle('HTTP Response Composition: V1 vs V2\nCircuit Breaker transforms failures (500) into fallbacks (202)', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/02_response_composition.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Chart 2 generated: Response Composition")


def plot_3_failure_reduction():
    """Chart 3: Failure Reduction with CB"""
    data = []
    
    for scenario in TARGET_SCENARIOS:
        df = pd.read_csv(f"{CSV_DIR}/{scenario}_status.csv")
        v1 = df[df['Version'] == 'V1'].iloc[0]
        v2 = df[df['Version'] == 'V2'].iloc[0]
        
        reduction = ((v1['API Failure Rate (%)'] - v2['API Failure Rate (%)']) / 
                    v1['API Failure Rate (%)'] * 100) if v1['API Failure Rate (%)'] > 0 else 0
        
        data.append({
            'Scenario': scenario_label(scenario),
            'V1 Failures (%)': v1['API Failure Rate (%)'],
            'V2 Failures (%)': v2['API Failure Rate (%)'],
            'Reduction (%)': reduction
        })
    
    df_plot = pd.DataFrame(data)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Subplot 1: Antes e Depois
    x = np.arange(len(TARGET_SCENARIOS))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, df_plot['V1 Failures (%)'], width, 
                    label='V1 (No CB)', color=COLORS['V1'], alpha=0.9, edgecolor='black')
    bars2 = ax1.bar(x + width/2, df_plot['V2 Failures (%)'], width, 
                    label='V2 (With CB)', color=COLORS['V2'], alpha=0.9, edgecolor='black')
    
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    ax1.set_ylabel('HTTP 500 Failure Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Failure Rate: Before vs After Circuit Breaker', fontsize=13, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_plot['Scenario'], fontsize=11)
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # Subplot 2: Percentage Reduction
    bars = ax2.barh(df_plot['Scenario'], df_plot['Reduction (%)'], 
                    color='#27ae60', alpha=0.9, edgecolor='black', height=0.5)
    
    for i, bar in enumerate(bars):
        width_bar = bar.get_width()
        ax2.text(width_bar + 1, bar.get_y() + bar.get_height()/2.,
                f'-{width_bar:.1f}%',
                ha='left', va='center', fontweight='bold', fontsize=14,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', edgecolor='green', alpha=0.8))
    
    ax2.set_xlabel('Failure Reduction (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Failure Reduction with Circuit Breaker', fontsize=13, fontweight='bold', pad=15)
    ax2.grid(axis='x', alpha=0.3)
    ax2.set_xlim(0, max(df_plot['Reduction (%)']) * 1.2)
    
    # Add context
    ax2.text(0.5, -0.15, 'Circuit Breaker reduced failures by over 90% in both scenarios!', 
            transform=ax2.transAxes, ha='center', fontsize=11, style='italic', color='green')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_failure_reduction.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Chart 3 generated: Failure Reduction")


def plot_4_downtime_comparison():
    """Chart 4: Downtime Comparison"""
    data = []
    
    for scenario in TARGET_SCENARIOS:
        benefits = pd.read_csv(f"{CSV_DIR}/{scenario}_benefits.csv").iloc[0]
        
        v1_downtime = benefits.get('V1 Downtime (s)', 0) / 60 if pd.notna(benefits.get('V1 Downtime (s)', np.nan)) else 0
        v2_downtime = benefits.get('V2 Downtime (s)', 0) / 60 if pd.notna(benefits.get('V2 Downtime (s)', np.nan)) else 0
        
        data.append({
            'Scenario': scenario_label(scenario),
            'V1 Downtime (min)': v1_downtime,
            'V2 Downtime (min)': v2_downtime,
            'Reduction (%)': ((v1_downtime - v2_downtime) / v1_downtime * 100) if v1_downtime > 0 else 0
        })
    
    df_plot = pd.DataFrame(data)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(TARGET_SCENARIOS))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, df_plot['V1 Downtime (min)'], width, 
                   label='V1 (No CB)', color=COLORS['V1'], alpha=0.9, edgecolor='black')
    bars2 = ax.bar(x + width/2, df_plot['V2 Downtime (min)'], width, 
                   label='V2 (With CB)', color=COLORS['V2'], alpha=0.9, edgecolor='black')
    
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        h1, h2 = bar1.get_height(), bar2.get_height()
        ax.text(bar1.get_x() + bar1.get_width()/2., h1 + 0.2,
               f'{h1:.1f} min', ha='center', va='bottom', fontweight='bold', fontsize=11)
        ax.text(bar2.get_x() + bar2.get_width()/2., h2 + 0.2,
               f'{h2:.1f} min', ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Arrow indicating reduction
        reduction = df_plot['Reduction (%)'].iloc[i]
        mid_x = (bar1.get_x() + bar2.get_x() + bar2.get_width()) / 2
        ax.annotate(f'-{reduction:.0f}%\ndowntime', 
                   xy=(mid_x, max(h1, h2) + 1.5),
                   ha='center', fontsize=12, fontweight='bold', color='green',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', edgecolor='green', alpha=0.8))
    
    ax.set_ylabel('Downtime (minutes)', fontsize=12, fontweight='bold')
    ax.set_title('Downtime Reduction: V1 vs V2\nCircuit Breaker keeps system available with fallback', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot['Scenario'], fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_downtime_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Chart 4 generated: Downtime Comparison")


def plot_5_combined_summary():
    """Chart 5: Combined Summary - Side by Side Infographic"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Data
    scenarios = ['Intermittent\nBursts', 'Catastrophic\nFailure']
    v1_success = [63.04, 35.75]
    v2_success = [96.68, 95.05]
    v1_failures = [36.96, 64.25]
    v2_failures = [3.32, 4.95]
    failure_reduction = [91.0, 92.3]
    v2_fallback = [34.64, 62.08]
    
    # Chart 1: Success Rate
    ax1 = axes[0, 0]
    x = np.arange(2)
    width = 0.35
    ax1.bar(x - width/2, v1_success, width, label='V1', color=COLORS['V1'], alpha=0.9)
    ax1.bar(x + width/2, v2_success, width, label='V2', color=COLORS['V2'], alpha=0.9)
    ax1.set_ylabel('Success Rate (%)', fontweight='bold')
    ax1.set_title('Total Success Rate', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios)
    ax1.legend()
    ax1.set_ylim(0, 110)
    ax1.axhline(y=99, color='gray', linestyle='--', alpha=0.5)
    for i, (v1, v2) in enumerate(zip(v1_success, v2_success)):
        ax1.text(i - width/2, v1 + 2, f'{v1:.1f}%', ha='center', fontweight='bold', fontsize=10)
        ax1.text(i + width/2, v2 + 2, f'{v2:.1f}%', ha='center', fontweight='bold', fontsize=10)
    
    # Chart 2: Failure Rate
    ax2 = axes[0, 1]
    ax2.bar(x - width/2, v1_failures, width, label='V1', color=COLORS['V1'], alpha=0.9)
    ax2.bar(x + width/2, v2_failures, width, label='V2', color=COLORS['V2'], alpha=0.9)
    ax2.set_ylabel('Failure Rate (%)', fontweight='bold')
    ax2.set_title('Failure Rate (HTTP 500)', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios)
    ax2.legend()
    for i, (v1, v2) in enumerate(zip(v1_failures, v2_failures)):
        ax2.text(i - width/2, v1 + 1, f'{v1:.1f}%', ha='center', fontweight='bold', fontsize=10)
        ax2.text(i + width/2, v2 + 0.5, f'{v2:.1f}%', ha='center', fontweight='bold', fontsize=10)
    
    # Chart 3: Failure Reduction
    ax3 = axes[1, 0]
    colors_bar = ['#27ae60', '#2ecc71']
    bars = ax3.barh(['Bursts', 'Catastrophe'], failure_reduction, color=colors_bar, alpha=0.9, height=0.5)
    ax3.set_xlabel('Failure Reduction (%)', fontweight='bold')
    ax3.set_title('Failure Reduction with Circuit Breaker', fontsize=12, fontweight='bold')
    ax3.set_xlim(0, 100)
    for i, bar in enumerate(bars):
        ax3.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                f'-{failure_reduction[i]:.1f}%', va='center', fontweight='bold', fontsize=12, color='green')
    
    # Chart 4: Fallback Contribution
    ax4 = axes[1, 1]
    ax4.bar(x, v2_fallback, width=0.5, color=COLORS['Fallback_202'], alpha=0.9, label='Fallback (202)')
    ax4.set_ylabel('Fallback Rate (%)', fontweight='bold')
    ax4.set_title('Fallback (202) Contribution in V2', fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(scenarios)
    for i, fb in enumerate(v2_fallback):
        ax4.text(i, fb + 1, f'{fb:.1f}%', ha='center', fontweight='bold', fontsize=11)
    ax4.set_ylim(0, 80)
    
    fig.suptitle('Circuit Breaker Impact Summary: Bursts and Catastrophe\n'
                 'V1 (Baseline without resilience) vs V2 (With Circuit Breaker)', 
                 fontsize=15, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/05_combined_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Chart 5 generated: Combined Summary")


def generate_summary_markdown():
    """Generate markdown file with data summary"""
    summary = """# Comparative Analysis V1 vs V2: Bursts and Catastrophe Scenarios

## Executive Summary

The **Intermittent Bursts** and **Catastrophic Failure** scenarios compellingly demonstrate the benefits of the Circuit Breaker pattern for microservices resilience.

## Consolidated Data

| Scenario | V1 Success | V2 Success | Gain | Failure Reduction |
|---------|------------|------------|-------|----------------|
| **Intermittent Bursts** | 63.04% | **96.68%** | +33.64pp | -91.0% |
| **Catastrophic Failure** | 35.75% | **95.05%** | +59.30pp | -92.3% |

## V2 Response Composition

| Scenario | Success (200) | Fallback (202) | Error (500) | Total Success |
|---------|---------------|----------------|------------|---------------|
| **Bursts** | 62.04% | 34.64% | 3.32% | **96.68%** |
| **Catastrophe** | 32.97% | 62.08% | 4.95% | **95.05%** |

## Key Observations

1. **Error to Fallback Transformation**: Circuit Breaker transforms requests that would fail (500) into fallback responses (202), maintaining perceived availability.

2. **Elasticity in Bursts Scenario**: CB demonstrated the ability to open and close dynamically during intermittent spikes, protecting the system without hindering recovery.

3. **Protection in Total Catastrophe**: When the dependency became 100% unavailable, CB prevented system collapse, maintaining 95.05% availability via fallback.

4. **Consistent Failure Reduction**: In both scenarios, failure reduction exceeded 90%.

## Generated Charts

1. `01_v1_v2_success_rate_comparison.png` - Success rate comparison
2. `02_response_composition.png` - HTTP response composition
3. `03_failure_reduction.png` - Failure reduction
4. `04_downtime_comparison.png` - Downtime comparison
5. `05_combined_summary.png` - Combined summary
"""
    
    with open(f'{OUTPUT_DIR}/README.md', 'w') as f:
        f.write(summary)
    print("✅ README.md generated with data summary")


def main():
    """Generate all comparative charts"""
    print("\n" + "="*60)
    print("  V1 vs V2 COMPARATIVE CHART GENERATION")
    print("  Scenarios: Intermittent Bursts and Catastrophic Failure")
    print("="*60 + "\n")
    
    # Check if data exists
    for scenario in TARGET_SCENARIOS:
        status_path = f"{CSV_DIR}/{scenario}_status.csv"
        if not os.path.exists(status_path):
            print(f"❌ File not found: {status_path}")
            print("   Run the scenario analysis script first.")
            return
    
    try:
        plot_1_success_rate_comparison()
        plot_2_response_composition()
        plot_3_failure_reduction()
        plot_4_downtime_comparison()
        plot_5_combined_summary()
        generate_summary_markdown()
        
        print("\n" + "="*60)
        print(f"✅ ALL CHARTS GENERATED SUCCESSFULLY!")
        print(f"📁 Location: {OUTPUT_DIR}/")
        print("="*60 + "\n")
        
        print("Generated files:")
        print("  01_v1_v2_success_rate_comparison.png")
        print("  02_response_composition.png")
        print("  03_failure_reduction.png")
        print("  04_downtime_comparison.png")
        print("  05_combined_summary.png")
        print("  README.md")
        
    except Exception as e:
        print(f"\n❌ Error generating charts: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
