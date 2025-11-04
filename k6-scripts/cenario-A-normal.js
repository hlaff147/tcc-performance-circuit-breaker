import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

// Métricas de Tendência customizadas para mais detalhes nos gráficos
const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');

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

  check(response, {
    'status is 200': (res) => res.status === 200,
  });

  // Coleta métricas de tempo detalhadas
  ttfbTrend.add(response.timings.ttfb);
  waitingTrend.add(response.timings.waiting);

  sleep(1);
}
