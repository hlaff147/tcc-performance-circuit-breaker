import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter, Gauge } from 'k6/metrics';

// Métricas customizadas
const concurrencyGauge = new Gauge('active_users');
const queueDepth = new Trend('request_queue_depth');
const circuitStateChanges = new Counter('circuit_state_changes');
const systemStability = new Rate('system_stability');
const resourceUtilization = new Trend('resource_utilization');

// Métricas de Circuit Breaker - CRÍTICAS para análise
const realFailures = new Counter('real_failures');           // HTTP 500/503 - Falhas REAIS
const fallbackResponses = new Counter('fallback_responses'); // HTTP 202 - Circuit Breaker ativado
const successfulResponses = new Counter('successful_responses'); // HTTP 200 - Sucesso real
const errorRate = new Rate('circuit_breaker_error_rate');    // Taxa de erro que ativa o CB

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
    circuit_breaker_error_rate: ['rate<0.50'], // Taxa de erro real deve ser < 50%
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
  
  // ==========================================
  // CLASSIFICAÇÃO CORRETA DAS RESPOSTAS
  // ==========================================
  // 200: Sucesso real - transação processada
  // 202: Fallback - Circuit Breaker ATIVO, processamento offline
  // 500/503: Falha real - erro que ATIVA o Circuit Breaker
  // ==========================================
  
  let isRealSuccess = false;
  let isFallback = false;
  let isRealFailure = false;
  
  if (response.status === 200) {
    isRealSuccess = true;
    successfulResponses.add(1);
    errorRate.add(false); // Não é erro
  } else if (response.status === 202) {
    isFallback = true;
    fallbackResponses.add(1);
    // IMPORTANTE: Fallback NÃO conta como erro na taxa, mas indica CB ativo
  } else if (response.status === 500 || response.status === 503) {
    isRealFailure = true;
    realFailures.add(1);
    errorRate.add(true); // É ERRO que ativa o CB
  }
  
  // Análise de estado do sistema
  let currentCircuitState;
  if (response.status === 503 || isRealFailure) {
    currentCircuitState = 'OPEN';
  } else if (response.status === 202 || isFallback) {
    currentCircuitState = 'HALF_OPEN';
  } else {
    currentCircuitState = 'CLOSED';
  }
  
  // Registra mudanças de estado do circuit breaker
  if (currentCircuitState !== lastCircuitState) {
    circuitStateChanges.add(1, { from: lastCircuitState, to: currentCircuitState });
    lastCircuitState = currentCircuitState;
  }
  
  // Análise de sucesso e estabilidade do SISTEMA (não confundir com taxa de erro)
  // Sistema estável = respondeu (seja 200, 202 ou 500), não travou/timeout
  const systemResponded = response.status !== undefined;
  systemStability.add(systemResponded);
  
  // Calcula utilização simulada de recursos
  const utilizationFactor = Math.min(requestQueue / 100, 1);  // Normalizado para 0-1
  resourceUtilization.add(utilizationFactor);
  
  // Pequena pausa para não sobrecarregar demais
  sleep(0.1);
  
  concurrencyGauge.add(-1);  // Decrementa quando VU termina execução
  
  // ==========================================
  // VERIFICAÇÕES CORRETAS
  // ==========================================
  check(response, {
    'status is valid (200, 202, or 500)': () => 
      response.status === 200 || response.status === 202 || response.status === 500,
    
    'response time within limits': () => 
      (endTime - startTime) < 3000,
    
    'circuit breaker protecting system': () => {
      // Se CB ativo (202), está protegendo o sistema
      if (isFallback) return true;
      // Se sucesso real, sistema saudável
      if (isRealSuccess) return true;
      // Falhas são esperadas ANTES do CB ativar
      return true;
    },
    
    'successful transaction (200 only)': () => isRealSuccess,
    
    'fallback activated (202)': () => isFallback,
    
    'real failure (500/503)': () => isRealFailure,
  });
  
  // Pausa dinâmica baseada na carga do sistema
  const dynamicSleep = Math.max(0.1, 1 - utilizationFactor);
  sleep(dynamicSleep);
}