import http from 'k6/http';
import { check, sleep } from 'k6';
import { 
  recordMetrics, 
  getV2Thresholds, 
  generatePaymentPayload, 
  getDefaultHeaders,
  successRate,
  fallbackRate,
  failureRate,
  availabilityRate
} from './lib/metrics.js';

// Configurações parametrizáveis via variáveis de ambiente para suportar execução local ou via Docker.
const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';
const VERSION = __ENV.VERSION || 'unknown';

const MODE_DISTRIBUTION = (__ENV.PAYMENT_MODE_DISTRIBUTION || 'normal:0.7,latencia:0.2,falha:0.1')
  .split(',')
  .map((item) => {
    const [mode, weight] = item.split(':');
    return { mode, weight: Number(weight || 0) };
  })
  .filter((entry) => entry.mode && !Number.isNaN(entry.weight));

const distributionTotal = MODE_DISTRIBUTION.reduce((sum, entry) => sum + entry.weight, 0) || 1;

function pickMode() {
  const target = Math.random() * distributionTotal;
  let cumulative = 0;

  for (const { mode, weight } of MODE_DISTRIBUTION) {
    cumulative += weight;
    if (target <= cumulative) {
      return mode;
    }
  }

  return MODE_DISTRIBUTION.length ? MODE_DISTRIBUTION[MODE_DISTRIBUTION.length - 1].mode : 'normal';
}

// Define os estágios para o cenário de teste de estresse
export const options = {
  stages: [
    // 1. Aquecimento (2m): Sobe gradualmente para 100 VUs.
    { duration: '2m', target: 100 },
    // 2. Carga Normal (5m): Mantém 100 VUs.
    { duration: '5m', target: 100 },
    // 3. Pico de Estresse (3m): Sobe agressivamente para 500 VUs.
    { duration: '3m', target: 500 },
    // 4. Manutenção do Estresse (15m): Mantém os 500 VUs para observar o comportamento sob carga extrema.
    { duration: '15m', target: 500 },
    // 5. Recuperação (5m): Reduz gradualmente para 0 VUs.
    { duration: '5m', target: 0 },
  ],
  thresholds: VERSION === 'v2' ? getV2Thresholds({
    'http_req_duration': ['p(95)<500'],
    'custom_availability_rate': ['rate>0.95'],
  }) : {
    'http_req_failed': ['rate<0.15'],
    'http_req_duration': ['p(95)<3000'],
  },
};

// Função principal do teste
export default function () {
  const modo = pickMode();
  const url = `${BASE_URL}/pagar?modo=${modo}`;

  const payload = generatePaymentPayload(__VU);

  const params = {
    headers: getDefaultHeaders(),
    tags: {
      modo,
      cenario: 'completo',
      versao: VERSION,
    },
  };

  // Envia a requisição POST
  const res = http.post(url, payload, params);

  // Registra métricas padronizadas
  recordMetrics(res);

  // Verifica se a requisição foi bem-sucedida (status 200 ou 201)
  check(res, {
    'status is 2xx or 202 fallback': (r) => r.status === 200 || r.status === 201 || r.status === 202,
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
  });

  // Pausa de 1 segundo entre as iterações de um mesmo usuário virtual
  sleep(1);
}
