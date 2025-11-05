import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter, Gauge } from 'k6/metrics';

// Métricas customizadas
const concurrencyGauge = new Gauge('active_users');
const queueDepth = new Trend('request_queue_depth');
const circuitStateChanges = new Counter('circuit_state_changes');
const systemStability = new Rate('system_stability');
const resourceUtilization = new Trend('resource_utilization');

export const options = {
  scenarios: {
    alta_concorrencia: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 500,
      stages: [
        // Fase 1: Aquecimento gradual
        { duration: '1m', target: 50 },    // 50 req/s
        
        // Fase 2: Alta carga sustentada
        { duration: '2m', target: 200 },   // 200 req/s
        
        // Fase 3: Pico de carga
        { duration: '1m', target: 400 },   // 400 req/s
        
        // Fase 4: Recuperação
        { duration: '1m', target: 50 },    // Volta para 50 req/s
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<3000'],     // 95% das requisições < 3s
    system_stability: ['rate>0.90'],       // Sistema estável 90% do tempo
    request_queue_depth: ['p(95)<100'],    // Fila não deve passar de 100
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

// Controle de estado global do teste
let lastCircuitState = 'CLOSED';
let requestQueue = 0;
let totalRequests = 0;
let successfulRequests = 0;

export default function () {
  // Atualiza métricas de concorrência
  const currentTime = Date.now();
  concurrencyGauge.add(1);  // Incrementa quando VU inicia execução
  
  requestQueue++;
  queueDepth.add(requestQueue);
  
  const startTime = currentTime;
  const response = http.post(BASE_URL, payload, params);
  const endTime = Date.now();
  
  requestQueue--;
  
  // Análise da resposta
  const duration = endTime - startTime;
  resourceUtilization.add(duration);
  
  requestQueue--;
  
  // Análise de estado do sistema
  let currentCircuitState;
  if (response.status === 503) {
    currentCircuitState = 'OPEN';
  } else if (response.status === 202) {
    currentCircuitState = 'HALF_OPEN';
  } else {
    currentCircuitState = 'CLOSED';
  }
  
  // Registra mudanças de estado do circuit breaker
  if (currentCircuitState !== lastCircuitState) {
    circuitStateChanges.add(1, { from: lastCircuitState, to: currentCircuitState });
    lastCircuitState = currentCircuitState;
  }
  
  // Análise de sucesso e estabilidade
  const isSuccess = response.status === 200 || response.status === 202;
  totalRequests++;
  if (isSuccess) successfulRequests++;
  
  systemStability.add(isSuccess);
  
  // Calcula utilização simulada de recursos
  const utilizationFactor = Math.min(requestQueue / 100, 1);  // Normalizado para 0-1
  resourceUtilization.add(utilizationFactor);
  
  // Pequena pausa para não sobrecarregar demais
  sleep(0.1);
  
  concurrencyGauge.add(-1);  // Decrementa quando VU termina execução
  
  // Verificações detalhadas
  check(response, {
    'status is 200 or 202': () => isSuccess,
    'response time within limits': () => (endTime - startTime) < 3000,
    'circuit breaker functioning': () => {
      if (utilizationFactor > 0.8) {
        // Em alta carga, circuit breaker deve atuar
        return response.status === 202 || response.status === 503;
      }
      return true;
    },
  });
  
  // Pausa dinâmica baseada na carga do sistema
  const dynamicSleep = Math.max(0.1, 1 - utilizationFactor);
  sleep(dynamicSleep);
}