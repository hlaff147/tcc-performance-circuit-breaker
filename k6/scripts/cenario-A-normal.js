import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas de Tendência customizadas para mais detalhes nos gráficos
const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');

// Métricas de Circuit Breaker - CRÍTICAS para análise
const realFailures = new Counter('real_failures');           // HTTP 500/503 - Falhas REAIS
const fallbackResponses = new Counter('fallback_responses'); // HTTP 202 - Circuit Breaker ativado
const successfulResponses = new Counter('successful_responses'); // HTTP 200 - Sucesso real
const errorRate = new Rate('circuit_breaker_error_rate');    // Taxa de erro que ativa o CB

export const options = {
  vus: 50,
  duration: '1m',
  thresholds: {
    http_req_failed: ['rate<0.01'], // Menos de 1% de falhas
    http_req_duration: ['p(95)<200'], // 95% das reqs abaixo de 200ms
    ttfb: ['p(95)<150'], // TTFB p(95) abaixo de 150ms
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=normal';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  const response = http.post(BASE_URL, payload, params);

  // ==========================================
  // CLASSIFICAÇÃO CORRETA DAS RESPOSTAS
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
  } else if (response.status === 500 || response.status === 503) {
    isRealFailure = true;
    realFailures.add(1);
    errorRate.add(true); // É ERRO que ativa o CB
  }

  check(response, {
    'status is 200': (res) => res.status === 200,
  });

  // Coleta métricas de tempo detalhadas
  const { timings = {} } = response;
  const { ttfb, waiting } = timings;

  if (Number.isFinite(ttfb)) {
    ttfbTrend.add(ttfb);
  }

  if (Number.isFinite(waiting)) {
    waitingTrend.add(waiting);
  }

  sleep(1);
}
