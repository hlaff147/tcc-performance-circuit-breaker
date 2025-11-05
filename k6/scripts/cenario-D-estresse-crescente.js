import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas customizadas
const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');
const successRate = new Rate('success_rate');
const circuitBreakerTrips = new Counter('circuit_breaker_trips');
const concurrentRequests = new Trend('concurrent_requests');

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
    success_rate: ['rate>0.95'],          // Taxa de sucesso > 95%
    http_req_failed: ['rate<0.05'],       // Taxa de falha < 5%
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

  // Verifica sucesso (200 OK ou 202 Accepted para fallback)
  const isSuccess = response.status === 200 || response.status === 202;
  successRate.add(isSuccess);

  // Se receber 503, pode indicar Circuit Breaker aberto
  if (response.status === 503) {
    circuitBreakerTrips.add(1);
  }

  check(response, {
    'status is 200 or 202': () => isSuccess,
    'response time < 500ms': () => (endTime - startTime) < 500,
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