```mermaid
sequenceDiagram
    participant Client as K6 Client
    participant V2 as V2 Payment Service
    participant CB as Circuit Breaker
    participant Acquirer as Acquirer Service

    rect rgb(200, 230, 200)
        Note over Client,Acquirer: Normal Operation (Circuit CLOSED)
        Client->>V2: POST /payment
        V2->>CB: Check state
        CB-->>V2: CLOSED (allow)
        V2->>Acquirer: POST /authorize
        Acquirer-->>V2: 200 OK
        V2-->>Client: 200 OK (Payment authorized)
    end

    rect rgb(255, 200, 200)
        Note over Client,Acquirer: Failure Scenario (Circuit OPENS)
        Client->>V2: POST /payment
        V2->>CB: Check state
        CB-->>V2: CLOSED (allow)
        V2->>Acquirer: POST /authorize
        Acquirer-->>V2: 500 Error
        V2->>CB: Record failure
        Note over CB: Threshold exceeded!
        CB-->>CB: State → OPEN
    end

    rect rgb(255, 230, 150)
        Note over Client,Acquirer: Fail-Fast Mode (Circuit OPEN)
        Client->>V2: POST /payment
        V2->>CB: Check state
        CB-->>V2: OPEN (reject)
        Note over V2: Fallback triggered
        V2-->>Client: 202 Accepted (Scheduled)
    end

    rect rgb(200, 200, 255)
        Note over Client,Acquirer: Recovery (Circuit HALF-OPEN)
        Note over CB: 15s elapsed
        CB-->>CB: State → HALF-OPEN
        Client->>V2: POST /payment
        V2->>CB: Check state
        CB-->>V2: HALF-OPEN (probe)
        V2->>Acquirer: POST /authorize
        Acquirer-->>V2: 200 OK
        V2->>CB: Record success
        Note over CB: Probes OK!
        CB-->>CB: State → CLOSED
        V2-->>Client: 200 OK
    end
```

## Sequence Flow Explanation

1. **Normal Operation** (Green): Circuit is CLOSED, requests flow normally
2. **Failure Detection** (Red): Failures recorded, circuit trips to OPEN
3. **Fail-Fast** (Yellow): Immediate fallback, no backend calls
4. **Recovery** (Blue): After wait, probes test if backend recovered
