```mermaid
flowchart TB
    subgraph Scenarios["📊 Test Scenarios"]
        Normal["🟢 Normal\n100% Available"]
        Degradation["🟡 Degradation\nGradual latency increase"]
        Bursts["🟠 Bursts\nIntermittent failures"]
        Unavailability["🔴 Unavailability\n75% error rate"]
        Catastrophe["💀 Catastrophe\n100% failure (5min)"]
    end

    subgraph Results["📈 Perceived Availability Results"]
        R_Normal["V1: 100% | V2: 100% | V4: 100%"]
        R_Degradation["V1: 75.3% | V2: 95.7% | V4: 96.7%"]
        R_Bursts["V1: 62.9% | V2: 96.7% | V4: 96.6%"]
        R_Unavailability["V1: 10.3% | V2: 99.1% | V4: 99.4%"]
        R_Catastrophe["V1: 35.7% | V2: 95.1% | V4: 95.1%"]
    end

    Normal --> R_Normal
    Degradation --> R_Degradation
    Bursts --> R_Bursts
    Unavailability --> R_Unavailability
    Catastrophe --> R_Catastrophe

    style Normal fill:#C8E6C9,stroke:#388E3C
    style Degradation fill:#FFF9C4,stroke:#FBC02D
    style Bursts fill:#FFE0B2,stroke:#F57C00
    style Unavailability fill:#FFCDD2,stroke:#D32F2F
    style Catastrophe fill:#B71C1C,stroke:#B71C1C,color:#fff

    style R_Normal fill:#E8F5E9
    style R_Degradation fill:#E8F5E9
    style R_Bursts fill:#E8F5E9
    style R_Unavailability fill:#E8F5E9
    style R_Catastrophe fill:#E8F5E9
```

## Scenario Descriptions

| Scenario | Duration | Failure Pattern | Purpose |
|----------|----------|-----------------|---------|
| **Normal** | 13min | None | Baseline validation |
| **Degradation** | 15min | 10%→50% gradual | Progressive stress |
| **Bursts** | 15min | 30s on/off cycles | Intermittent failures |
| **Unavailability** | 15min | 75% constant | High error rate |
| **Catastrophe** | 13min | 100% for 5min | Total outage |

## Key Insight
V4 (Composition) matches V2's protection while absorbing transient jitters through its retry layer.
