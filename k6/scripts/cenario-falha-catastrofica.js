import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { 
  recordMetrics, 
  generatePaymentPayload,
  getDefaultHeaders 
} from './lib/metrics.js';

/**
 * CENÁRIO 1: FALHA CATASTRÓFICA
 * 
 * Simula uma situação onde a API externa fica completamente indisponível
 * por períodos prolongados (ex: deploy com problema, servidor derrubado).
 * 
 * Comportamento esperado:
 * - V1: Todas as requisições falham durante a indisponibilidade (cascata de falhas)
 * - V2: CB abre rapidamente, evita sobrecarga e retorna respostas rápidas (503)
 * 
 * Benefícios esperados do CB:
 * - Redução drástica no tempo de resposta durante falhas (não espera timeout)
 * - Proteção contra sobrecarga da API externa
 * - Sistema continua responsivo mesmo com dependência fora
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';

export const options = {
  stages: [
    // Aquecimento: Sistema estável
    { duration: '1m', target: 50 },
    
    // Operação Normal: Tudo funcionando bem (70% normal, 20% latência, 10% falha)
    { duration: '3m', target: 100 },
    
    // CATÁSTROFE: API externa COMPLETAMENTE fora (100% falhas)
    // Este é o momento crítico para o CB brilhar
    { duration: '5m', target: 150 },  // Aumenta carga durante a falha
    
    // Recuperação: API volta ao normal
    { duration: '3m', target: 100 },
    
    // Cooldown
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000'],  // Durante CB aberto, deve ser muito rápido
  },
};

const TEST_SEGMENTS = {
  catastropheStart: 240,   // 4 minutos
  catastropheEnd: 540,     // 9 minutos
  recoveryEnd: 720,        // 12 minutos
};

function elapsedSeconds() {
  return exec.instance.currentTestRunDuration / 1000;
}

export default function () {
  const elapsed = elapsedSeconds();
  let modo;
  let fase = 'normal';

  if (elapsed >= TEST_SEGMENTS.catastropheStart && elapsed < TEST_SEGMENTS.catastropheEnd) {
    modo = 'falha';
    fase = 'catastrofe';
  } else if (elapsed >= TEST_SEGMENTS.catastropheEnd && elapsed < TEST_SEGMENTS.recoveryEnd) {
    const rand = Math.random();
    modo = rand < 0.6 ? 'normal' : rand < 0.85 ? 'latencia' : 'falha';
    fase = 'recuperacao';
  } else {
    const rand = Math.random();
    if (rand < 0.7) modo = 'normal';
    else if (rand < 0.9) modo = 'latencia';
    else modo = 'falha';
  }

  const url = `${BASE_URL}/pagar?modo=${modo}`;
  
  const payload = generatePaymentPayload(__VU);
  
  const params = {
    headers: getDefaultHeaders(),
    tags: { 
      modo,
      fase,
      cenario: 'falha_catastrofica',
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
