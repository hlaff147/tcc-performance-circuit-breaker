```mermaid
stateDiagram-v2
    [*] --> Closed : Initial State
    
    Closed --> Open : Failure threshold exceeded\n(≥50% in 20 calls)
    Closed --> Closed : Success / Failure below threshold
    
    Open --> HalfOpen : Wait duration expires\n(15 seconds)
    Open --> Open : All requests fail-fast\n(Return HTTP 202)
    
    HalfOpen --> Closed : Probe succeeds\n(≥3 of 5 calls OK)
    HalfOpen --> Open : Probe fails\n(≥50% failures)
    
    note right of Closed
        Normal operation
        All requests go through
        Monitoring failure rate
    end note
    
    note right of Open
        Circuit tripped
        Fail-fast mode
        Fallback returns 202
    end note
    
    note right of HalfOpen
        Recovery probing
        Limited requests allowed
        Testing if service recovered
    end note
```

## Circuit Breaker States

| State | Behavior | Duration |
|-------|----------|----------|
| **Closed** | Normal - all requests forwarded | Until failure threshold |
| **Open** | Fail-fast - returns HTTP 202 fallback | 15 seconds |
| **Half-Open** | Probing - 5 test requests allowed | Until success/failure threshold |

## Configuration (V2/V4)
- `failureRateThreshold`: 50%
- `slidingWindowSize`: 20 calls
- `waitDurationInOpenState`: 15s
- `permittedNumberOfCallsInHalfOpenState`: 5
