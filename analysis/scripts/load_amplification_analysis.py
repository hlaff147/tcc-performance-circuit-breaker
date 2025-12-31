#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add current scripts directory to path to import fast_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from fast_loader import FastK6Loader
except ImportError:
    print("Error: fast_loader.py not found in the same directory.")
    sys.exit(1)

RESULTS_DIR = "k6/results"
OUTPUT_DIR = "analysis_results/csv"
SCENARIOS = ["catastrofe", "degradacao", "rajadas", "indisponibilidade"]

def calculate_amplification():
    loader = FastK6Loader(results_dir=RESULTS_DIR, use_cache=True)
    results = []
    
    for scenario in SCENARIOS:
        print(f"Analyzing Load Amplification for scenario: {scenario}")
        data = loader.load_scenario(scenario, versions=["V1", "V3"])
        
        if "V1" in data and "V3" in data:
            v1_reqs = data["V1"][data["V1"]['metric'] == 'http_reqs']['value'].sum()
            v3_reqs = data["V3"][data["V3"]['metric'] == 'http_reqs']['value'].sum()
            
            amplification = v3_reqs / v1_reqs if v1_reqs > 0 else 0
            
            results.append({
                'Scenario': scenario,
                'V1 Total Requests': v1_reqs,
                'V3 Total Requests': v3_reqs,
                'Amplification Factor': amplification,
                'Additional Load (%)': (amplification - 1) * 100 if amplification > 0 else 0
            })
        else:
            print(f"  Missing data for {scenario}")

    if results:
        df = pd.DataFrame(results)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "load_amplification.csv")
        df.to_csv(output_path, index=False)
        print(f"\nSaved load amplification analysis to {output_path}")
        print(df.to_string(index=False))
    else:
        print("No results to save.")

if __name__ == "__main__":
    calculate_amplification()
