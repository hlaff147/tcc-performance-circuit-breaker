#!/usr/bin/env python3
import os
import pandas as pd

RESULTS_DIR = "analysis_results/csv"
SCENARIO_RESULTS_DIR = "analysis_results/scenarios/csv"
OUTPUT_DIR = "artigo_latex/tables"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def export_comprehensive_results():
    """Generates a single comprehensive table for the article spanning two columns."""
    scenarios = ["catastrofe", "degradacao", "indisponibilidade", "rajadas"]
    rows = []
    
    for s in scenarios:
        path = os.path.join(SCENARIO_RESULTS_DIR, f"{s}_benefits.csv")
        status_path = os.path.join(SCENARIO_RESULTS_DIR, f"{s}_status.csv")
        
        if os.path.exists(path) and os.path.exists(status_path):
            df_ben = pd.read_csv(path)
            df_stat = pd.read_csv(status_path)
            
            v1_avail = df_stat[df_stat['Version'] == 'V1']['Total Success Rate (%)'].values[0]
            v2_avail = df_stat[df_stat['Version'] == 'V2']['Total Success Rate (%)'].values[0]
            v3_avail = df_stat[df_stat['Version'] == 'V3']['Total Success Rate (%)'].values[0]
            v2_fallback = df_stat[df_stat['Version'] == 'V2']['Fallback Rate (%)'].values[0]
            fail_red = df_ben['Failure Reduction (%)'].values[0]
            
            row = [
                s.capitalize() if s != 'indisponibilidade' else 'Unavailability',
                f"{v1_avail:.1f}\\%",
                f"{v2_avail:.1f}\\%",
                f"{v2_fallback:.1f}\\%",
                f"{v3_avail:.1f}\\%",
                f"{fail_red:.1f}\\%"
            ]
            rows.append(row)

    # Manual LaTeX construction for maximum control and avoiding pandas signature issues
    latex_content = [
        "\\begin{table*}[!t]",
        "\\centering",
        "\\caption{Comprehensive Performance Comparison: Perceived Availability across Failure Scenarios}",
        "\\label{tab:comprehensive-results}",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Scenario & V1 Avail. & V2 Avail. & V2 Fallback & V3 Avail. & Fail. Red. (V2) \\\\",
        "\\midrule"
    ]
    
    for r in rows:
        latex_content.append(" & ".join(r) + " \\\\")
        
    latex_content.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}"
    ])
    
    with open(os.path.join(OUTPUT_DIR, "comprehensive_results.tex"), 'w') as f:
        f.write("\n".join(latex_content) + "\n")
    print("Generated: comprehensive_results.tex")

if __name__ == "__main__":
    export_comprehensive_results()
