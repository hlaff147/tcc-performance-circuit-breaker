import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');

// Métricas de Circuit Breaker - CRÍTICAS para análise
const realFailures = new Counter('real_failures');           // HTTP 500/503 - Falhas REAIS
const fallbackResponses = new Counter('fallback_responses'); // HTTP 202 - Circuit Breaker ativado
const successfulResponses = new Counter('successful_responses'); // HTTP 200 - Sucesso real
const errorRate = new Rate('circuit_breaker_error_rate');    // Taxa de erro que ativa o CB

export const options = {
  vus: 50,
  duration: '1m', // 1 minuto de teste
  thresholds: {
    // V1 (Baseline) irá FALHAR nestes thresholds
    // V2 (Circuit Breaker) irá PASSAR
    http_req_failed: ['rate<0.50'], // Permite até 50% de falhas (antes do CB ativar)
    http_req_duration: ['p(95)<300'], // p(95) abaixo de 300ms (V1 estoura, V2 passa)
    circuit_breaker_error_rate: ['rate<0.50'], // Taxa de erro real
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=latencia';
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

  // Válido para V1 (que falha) e V2 (que retorna 202 - Accepted)
  check(response, {
    'status is 200 or 202': (res) => res.status === 200 || res.status === 202,
    'successful transaction (200 only)': () => isRealSuccess,
    'fallback activated (202)': () => isFallback,
  });

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
