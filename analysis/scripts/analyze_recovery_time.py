#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add current scripts directory to path to import fast_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from fast_loader import FastK6Loader
except ImportError:
    print("Error: fast_loader.py not found.")
    sys.exit(1)

RESULTS_DIR = "k6/results"
OUTPUT_FILE = "analysis_results/csv/recovery_analysis.csv"

# Configuration of failure windows for recovery analysis (in seconds from start)
# This matches the k6 scripts behavior
SCENARIO_CONFIG = {
    "catastrofe": {"fail_start": 30, "fail_end": 330}, # 5 min failure starting at 30s
    "rajadas": {"fail_start": 30, "fail_end": 150},    # First burst end
}

def analyze_recovery(scenario_name, loader):
    print(f"Analyzing recovery for {scenario_name}...")
    
    data = loader.load_scenario(scenario_name, versions=["V2"])
    if "V2" not in data:
        print(f"  No V2 data for {scenario_name}")
        return None
    
    df = data["V2"]
    if 'time' not in df.columns or 'metric' not in df.columns:
        print(f"  Incomplete columns for {scenario_name}")
        return None
    
    # Get configuration
    config = SCENARIO_CONFIG.get(scenario_name)
    if not config:
        print(f"  No recovery config for {scenario_name}, using default.")
        return None

    # Filter for successes
    # Convert 'time' to seconds from start
    df['timestamp'] = pd.to_datetime(df['time'])
    start_time = df['timestamp'].min()
    df['seconds'] = (df['timestamp'] - start_time).dt.total_seconds()
    
    # Successes (200) after failure end
    successes = df[(df['metric'] == 'http_reqs') & 
                   (df['tags'].apply(lambda x: str(x.get('status')) == '200')) &
                   (df['seconds'] >= config['fail_end'])]
    
    if successes.empty:
        print(f"  No successes found after failure end for {scenario_name}")
        recovery_delta = 999 # Indicator of no recovery within test
    else:
        first_success_time = successes['seconds'].min()
        recovery_delta = first_success_time - config['fail_end']
        print(f"  Recovery delta for {scenario_name}: {recovery_delta:.2f}s")

    return {
        'Scenario': scenario_name,
        'Failure End (s)': config['fail_end'],
        'First Success (s)': first_success_time if not successes.empty else None,
        'V2 Recovery Delta (s)': round(recovery_delta, 2),
        'Status': 'Recovered' if not successes.empty else 'Failed to Recover'
    }

if __name__ == "__main__":
    loader = FastK6Loader(results_dir=RESULTS_DIR, use_cache=True)
    scenarios = ["catastrofe", "rajadas"]
    all_results = []
    
    for s in scenarios:
        res = analyze_recovery(s, loader)
        if res:
            all_results.append(res)
        
    if all_results:
        df = pd.DataFrame(all_results)
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nRecovery analysis saved to {OUTPUT_FILE}")
        print(df.to_string(index=False))
