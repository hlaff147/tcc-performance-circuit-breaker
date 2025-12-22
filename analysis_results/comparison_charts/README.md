# Comparative Analysis V1 vs V2: Bursts and Catastrophe Scenarios

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
