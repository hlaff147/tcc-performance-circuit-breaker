import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const ttfbTrend = new Trend('ttfb');
const waitingTrend = new Trend('waiting_time');

export const options = {
  vus: 50,
  duration: '1m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<300'],
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=latencia';
const payload = JSON.stringify({ valor: 100.0, cartao: '1234...' });
const params = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  const response = http.post(BASE_URL, payload, params);

  check(response, {
    'status is 200 or 202': (res) => res.status === 200 || res.status === 202,
  });

  ttfbTrend.add(response.timings.ttfb);
  waitingTrend.add(response.timings.waiting);

  sleep(1);
}
