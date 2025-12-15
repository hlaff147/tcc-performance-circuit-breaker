# 🔧 Correções Críticas - TCC v2.0.0

**Aplicar ANTES de rodar experimento comparativo**

---

## Fix #1: Parser de Arquivos no Analyzer

**Problema:** Quebra com cenários que contêm hífen (ex: `indisponibilidade-extrema`)

**Arquivo:** `analysis/scripts/comparative_analyzer.py`

**Localização:** Função `load_summary_files()`, linha ~40

**Código atual:**
```python
parts = f.stem.replace("_summary", "").split("_")
if len(parts) >= 3:
    scenario = parts[0]  # ❌ Pega só "indisponibilidade"
    treatment = parts[1]
    run = int(parts[2].replace("run", ""))
```

**Código corrigido:**
```python
import re  # Adicionar no topo do arquivo

# Dentro de load_summary_files():
filename = f.stem.replace("_summary", "")

# Padrão: qualquer_coisa_v1_run1, qualquer_coisa_v2_run2, etc
match = re.match(r"^(.+)_(v\d+)_(run\d+)$", filename)

if match:
    scenario = match.group(1)  # ✅ Captura tudo antes de _vN
    treatment = match.group(2)
    run = int(match.group(3).replace("run", ""))
    
    with open(f) as fp:
        data = json.load(fp)
    # ... resto do código
```

---

## Fix #2: RuntimeException em retryExceptions

**Problema:** Exceções genéicas não disparam retry

**Arquivos:**
- `services/payment-service-v3/src/main/resources/application.yml`
- `services/payment-service-v4/src/main/resources/application.yml`

**Adicionar em ambos:**

```yaml
resilience4j.retry.instances.adquirente-retry:
  retryExceptions:
    - java.net.SocketTimeoutException
    - java.net.ConnectException
    - java.io.IOException
    - feign.FeignException.ServiceUnavailable
    - feign.FeignException.InternalServerError
    - feign.RetryableException
    - org.springframework.web.client.HttpServerErrorException
    # ✅ ADICIONAR:
    - java.lang.RuntimeException
    - br.ufpe.cin.tcc.pagamento.service.PaymentService$AcquirerServiceException
```

---

## Fix #3: Health Check Robusto

**Problema:** Só verifica HTTP 200, não valida conteúdo JSON

**Arquivo:** `run_comparative_experiment.sh`

**Substituir função `wait_for_healthy()`:**

```bash
wait_for_healthy() {
    local max_attempts=30
    local attempt=1
    
    echo -n "  Aguardando serviço ficar saudável"
    while [ $attempt -le $max_attempts ]; do
        # Verifica status UP no JSON de health
        if health_status=$(curl -sf http://localhost:8080/actuator/health 2>/dev/null); then
            if echo "$health_status" | grep -q '"status":"UP"'; then
                echo -e " ${GREEN}OK${NC}"
                return 0
            fi
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e " ${RED}FALHOU após ${max_attempts} tentativas${NC}"
    echo "Últimos 30 logs do serviço:"
    docker-compose logs --tail=30 servico-pagamento
    return 1
}
```

---

## Fix #4: Correção de Bonferroni para p-values

**Problema:** 30 testes simultâneos inflam falsos positivos

**Arquivo:** `analysis/scripts/comparative_analyzer.py`

**Adicionar no início de `main()`:**

```python
def main():
    # ... código existente ...
    
    # Após carregar dados
    print(f"Cenários: {df['scenario'].unique()}")
    print(f"Tratamentos: {df['treatment'].unique()}")
    
    # ✅ ADICIONAR:
    comparisons = [
        ("v1", "v2", "H1: CB reduz falhas vs baseline"),
        ("v1", "v3", "H2: Retry vs baseline"),
        ("v3", "v2", "H3: CB vs Retry"),
        ("v2", "v4", "H4: CB+Retry vs CB"),
        ("v3", "v4", "H5: CB+Retry vs Retry"),
    ]
    metrics = ["success_rate", "avg_duration_ms", "p95_duration_ms"]
    
    num_scenarios = len(df["scenario"].unique())
    ALPHA = 0.05
    NUM_TESTS = len(comparisons) * len(metrics) * num_scenarios
    BONFERRONI_ALPHA = ALPHA / NUM_TESTS
    
    print(f"\n=== CORREÇÃO PARA COMPARAÇÕES MÚLTIPLAS ===")
    print(f"Número de testes: {NUM_TESTS}")
    print(f"Alpha original: {ALPHA}")
    print(f"Alpha ajustado (Bonferroni): {BONFERRONI_ALPHA:.6f}")
    print()
```

**Modificar função de teste:**

```python
def mann_whitney_test(group_a: np.ndarray, group_b: np.ndarray, 
                      alpha: float = 0.05) -> Dict:
    """Executa teste Mann-Whitney U com alpha configurável."""
    if len(group_a) < 2 or len(group_b) < 2:
        return {
            "u_statistic": None, 
            "p_value": None, 
            "significant": False,
            "alpha_used": alpha
        }
    
    try:
        stat, p_value = stats.mannwhitneyu(group_a, group_b, 
                                          alternative='two-sided')
        return {
            "u_statistic": stat,
            "p_value": p_value,
            "significant": p_value < alpha,  # ✅ Usa alpha passado
            "alpha_used": alpha
        }
    except Exception:
        return {
            "u_statistic": None, 
            "p_value": None, 
            "significant": False,
            "alpha_used": alpha
        }
```

**Chamar com alpha ajustado:**

```python
# Na função analyze_treatment_comparison():
mw_test = mann_whitney_test(data_a, data_b, alpha=BONFERRONI_ALPHA)
```

---

## Fix #5: ThreadLocal Cleanup

**Problema:** Potencial memory leak em thread pools

**Arquivos:**
- `services/payment-service-v3/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java`
- `services/payment-service-v4/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java`

**Modificar método `processPayment()`:**

```java
@Retry(name = RETRY_NAME, fallbackMethod = "processPaymentFallback")
@Timed(value = "payment.processing.time", description = "...")
public PaymentResponse processPayment(String modo, PaymentRequest request) {
    try {
        int currentAttempt = attemptTracker.get().incrementAndGet();
        
        log.info("Processando pagamento [v3-retry] - modo: {}, cliente: {}, tentativa: {}", 
                modo, request.customerId(), currentAttempt);
        
        // ... resto do código permanece igual ...
        
    } finally {
        // ✅ ADICIONAR: Limpa ThreadLocal para evitar leak
        // Nota: só limpa se não for fallback (fallback precisa do valor)
        if (!Thread.currentThread().isInterrupted()) {
            attemptTracker.remove();
        }
    }
}
```

**⚠️ ATENÇÃO:** Remover chamadas `resetAttemptTracker()` do corpo do método, pois agora é feito no `finally`.

**Alternativa mais simples (recomendada):**

```java
// Manter resetAttemptTracker() como está, mas modificar:
private void resetAttemptTracker() {
    attemptTracker.get().set(0);
    attemptTracker.remove();  // ✅ ADICIONAR esta linha
}
```

---

## 🧪 Validação das Correções

### Teste 1: Parser de Arquivos

```bash
# Criar arquivo de teste
echo '{"metrics":{}}' > test_indisponibilidade-extrema_v1_run1_summary.json

# Rodar analyzer
python3 analysis/scripts/comparative_analyzer.py .

# Deve reconhecer cenário como "indisponibilidade-extrema"
```

### Teste 2: Health Check

```bash
# Iniciar serviço
PAYMENT_SERVICE_VERSION=v3 docker-compose up -d servico-pagamento

# Função deve verificar JSON
curl -sf http://localhost:8080/actuator/health | grep -q '"status":"UP"'
echo $?  # Deve retornar 0 se OK
```

### Teste 3: Retry com RuntimeException

```bash
# Adicionar log temporário no PaymentService
log.error("Retry disparado por: {}", e.getClass().getName());

# Forçar erro e verificar logs
docker-compose logs servico-pagamento | grep "Retry disparado"
```

---

## 📋 Checklist de Aplicação

Ordem recomendada:

- [ ] Fix #2: RuntimeException (V3 e V4)
- [ ] Fix #5: ThreadLocal cleanup (V3 e V4)
- [ ] Fix #1: Parser do analyzer
- [ ] Fix #4: Bonferroni no analyzer
- [ ] Fix #3: Health check no script

**Recompilar serviços após Fix #2 e #5:**

```bash
cd services/payment-service-v3 && mvn clean package
cd ../payment-service-v4 && mvn clean package
```

**Testar analyzer após Fix #1 e #4:**

```bash
# Usar dados existentes se disponível
python3 analysis/scripts/comparative_analyzer.py k6/results/comparative/experiment_latest
```

---

## 🚀 Próximo Passo

Após aplicar correções:

```bash
# Teste piloto (1 run apenas)
./run_comparative_experiment.sh --pilot

# Se OK, rodar experimento completo
./run_comparative_experiment.sh
```

---

**Estimativa de tempo:** 15-20 minutos para aplicar todas as correções
