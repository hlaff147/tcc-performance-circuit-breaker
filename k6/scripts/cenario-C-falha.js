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
  duration: '1m',
  thresholds: {
    // V1 (Baseline) irá FALHAR (100% de erro)
    // V2 (Circuit Breaker) terá FALHAS INICIAIS seguidas de fallback
    http_req_failed: ['rate<0.50'],  // Permite até 50% de falhas (antes do CB ativar)
    circuit_breaker_error_rate: ['rate<0.50'], // Taxa de erro real
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
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
    // IMPORTANTE: Fallback NÃO conta como erro na taxa, mas indica CB ativo
  } else if (response.status === 500 || response.status === 503) {
    isRealFailure = true;
    realFailures.add(1);
    errorRate.add(true); // É ERRO que ativa o CB
  }

  check(response, {
    'status is valid (200, 202, or 500)': () => 
      response.status === 200 || response.status === 202 || response.status === 500,
    
    'successful transaction (200 only)': () => isRealSuccess,
    
    'fallback activated (202)': () => isFallback,
    
    'real failure (500/503)': () => isRealFailure,
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
