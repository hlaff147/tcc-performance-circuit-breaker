import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');

export const options = {
  vus: 50,
  duration: '1m',
  thresholds: {
    // V1 (Baseline) irá FALHAR (100% de erro)
    // V2 (Circuit Breaker) irá PASSAR (0% de erro)
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  const response = http.post(BASE_URL, payload, params);

  // Válido para V1 (que falha) e V2 (que retorna 202 - Accepted)
  check(response, {
    'status is 200 or 202': (res) => res.status === 200 || res.status === 202,
  });

  ttfbTrend.add(response.timings.ttfb);
  waitingTrend.add(response.timings.waiting);

  sleep(1);
}
