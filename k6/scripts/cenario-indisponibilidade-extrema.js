import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { 
  recordMetrics, 
  generatePaymentPayload,
  getDefaultHeaders,
  getV2Thresholds
} from './lib/metrics.js';

/**
 * CENÁRIO EXTRA: INDISPONIBILIDADE EXTREMA (75% OFF)
 *
 * Objetivo: demonstrar o ganho máximo do Circuit Breaker quando a API externa
 * passa a maior parte do tempo fora do ar. Forçamos janelas longas de
 * indisponibilidade (manutenção) intercaladas com períodos curtíssimos de
 * recuperação para que o CB mantenha o sistema utilizável.
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';
const CYCLE_LENGTH = 80;                // segundos por ciclo completo
const DOWNTIME_RATIO = 0.75;            // 75% do tempo indisponível
const DOWNTIME_WINDOW = CYCLE_LENGTH * DOWNTIME_RATIO;
const CYCLE_OFFSET = 20;                // atraso para garantir início saudável
const EXTREME_OUTAGE = { start: 180, end: 420 }; // janela contínua de 4min

export const options = {
  stages: [
    { duration: '45s', target: 80 },    // aquecimento controlado
    { duration: '45s', target: 140 },   // operação saudável
    { duration: '4m', target: 180 },    // falha prolongada (CB precisa abrir)
    { duration: '2m', target: 200 },    // rajadas adicionais durante instabilidade
    { duration: '1m', target: 140 },    // recuperação gradual
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1200'],
    'http_req_failed': ['rate<0.25'],
  },
};

function elapsedSeconds() {
  return exec.instance.currentTestRunDuration / 1000;
}

export default function () {
  const elapsed = elapsedSeconds();
  const cyclePosition = (elapsed + CYCLE_OFFSET) % CYCLE_LENGTH;
  const forcedOutage = elapsed >= EXTREME_OUTAGE.start && elapsed < EXTREME_OUTAGE.end;
  const inDowntimeWindow = cyclePosition < DOWNTIME_WINDOW;
  const inDowntime = forcedOutage || inDowntimeWindow;

  let modo;
  let fase;

  if (forcedOutage) {
    modo = 'falha';
    fase = 'manutencao_prolongada';
  } else if (inDowntime) {
    const rand = Math.random();
    modo = rand < 0.9 ? 'falha' : 'latencia';
    fase = 'janela_inoperante';
  } else {
    const rand = Math.random();
    if (rand < 0.6) modo = 'normal';
    else if (rand < 0.8) modo = 'latencia';
    else modo = 'falha';
    fase = 'recuperacao';
  }

  const url = `${BASE_URL}/pagar?modo=${modo}`;

  const payload = generatePaymentPayload(__VU);

  const params = {
    headers: getDefaultHeaders(),
    tags: { 
      modo, 
      fase,
      cenario: 'indisponibilidade_extrema',
      versao: __ENV.VERSION || 'unknown',
    },
  };

  const res = http.post(url, payload, params);

  // Usar módulo padronizado de métricas
  recordMetrics(res);

  check(res, {
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
    'status is 2xx or 202 fallback': (r) => r.status === 200 || r.status === 201 || r.status === 202,
  });

  sleep(1);
}
