import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas customizadas
const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');
const successRate = new Rate('success_rate');
const circuitBreakerTrips = new Counter('circuit_breaker_trips');
const concurrentRequests = new Trend('concurrent_requests');

// Métricas de Circuit Breaker - CRÍTICAS para análise
const realFailures = new Counter('real_failures');           // HTTP 500/503 - Falhas REAIS
const fallbackResponses = new Counter('fallback_responses'); // HTTP 202 - Circuit Breaker ativado
const successfulResponses = new Counter('successful_responses'); // HTTP 200 - Sucesso real
const errorRate = new Rate('circuit_breaker_error_rate');    // Taxa de erro que ativa o CB

export const options = {
  scenarios: {
    estresse_crescente: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 50 },   // Aquecimento suave
        { duration: '1m', target: 100 },   // Aumento moderado
        { duration: '2m', target: 200 },   // Estresse alto
        { duration: '1m', target: 300 },   // Pico de estresse
        { duration: '30s', target: 0 },    // Redução rápida
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000'],    // 95% das requisições abaixo de 1s
    success_rate: ['rate>0.85'],          // Taxa de sucesso > 85%
    http_req_failed: ['rate<0.50'],       // Taxa de falha < 50%
    circuit_breaker_error_rate: ['rate<0.50'], // Taxa de erro real
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  // Registra a concorrência atual usando __VU (variável global do k6)
  concurrentRequests.add(__VU);

  const startTime = Date.now();
  const response = http.post(BASE_URL, payload, params);
  const endTime = Date.now();

  // ==========================================
  // CLASSIFICAÇÃO CORRETA DAS RESPOSTAS
  // ==========================================
  let isRealSuccess = false;
  let isFallback = false;
  let isRealFailure = false;
  
  if (response.status === 200) {
    isRealSuccess = true;
    successfulResponses.add(1);
    successRate.add(true);
    errorRate.add(false);
  } else if (response.status === 202) {
    isFallback = true;
    fallbackResponses.add(1);
    successRate.add(true); // Sistema respondeu
  } else if (response.status === 500 || response.status === 503) {
    isRealFailure = true;
    realFailures.add(1);
    successRate.add(false);
    errorRate.add(true);
    
    // Se receber 503, pode indicar Circuit Breaker aberto
    if (response.status === 503) {
      circuitBreakerTrips.add(1);
    }
  }

  check(response, {
    'status is valid (200, 202, or 500)': () => 
      isRealSuccess || isFallback || isRealFailure,
    'response time < 500ms': () => (endTime - startTime) < 500,
    'successful transaction (200 only)': () => isRealSuccess,
    'fallback activated (202)': () => isFallback,
  });

  // Coleta métricas detalhadas
  const { timings = {} } = response;
  const { ttfb, waiting } = timings;

  if (Number.isFinite(ttfb)) ttfbTrend.add(ttfb);
  if (Number.isFinite(waiting)) waitingTrend.add(waiting);

  // Pausa variável baseada na carga
  const pauseTime = Math.max(0.1, 1 - (options.scenarios.estresse_crescente.executor.vusActive / 300));
  sleep(pauseTime);
}