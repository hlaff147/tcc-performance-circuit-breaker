import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { Counter, Trend, Rate } from 'k6/metrics';

// ============================================================================
// MÉTRICAS CUSTOMIZADAS - Análise mais rica do comportamento do sistema
// ============================================================================
const fallbackResponses = new Counter('custom_fallback_responses');      // HTTP 202
const circuitBreakerOpen = new Counter('custom_circuit_breaker_open');   // HTTP 503
const apiFailures = new Counter('custom_api_failures');                   // HTTP 500
const successResponses = new Counter('custom_success_responses');         // HTTP 200/201

const responseTimeFallback = new Trend('custom_response_time_fallback');
const responseTimeSuccess = new Trend('custom_response_time_success');
const responseTimeFailure = new Trend('custom_response_time_failure');

const successRate = new Rate('custom_success_rate');
const availabilityRate = new Rate('custom_availability_rate');  // 200 + 202 = disponível

/**
 * CENÁRIO 3: RAJADAS INTERMITENTES
 * 
 * Simula falhas em rajadas: períodos de 100% falha alternados com períodos normais.
 * Este é o PIOR cenário para sistemas sem CB, pois os sistemas ficam
 * constantemente tentando se recuperar.
 * 
 * Padrão:
 * - 2min normal → 1min de falha total → 2min normal → 1min falha → ...
 * 
 * Comportamento esperado:
 * - V1: Sofre com cada rajada, usuários experimentam alta latência e falhas
 * - V2: CB abre rapidamente nas rajadas e fecha quando estabiliza
 * 
 * Benefícios esperados do CB:
 * - Resposta rápida a mudanças de estado (abrir/fechar dinâmico)
 * - Proteção em cada rajada sem comprometer disponibilidade entre elas
 * - Demonstra elasticidade do CB
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';

export const options = {
  stages: [
    // Aquecimento
    { duration: '1m', target: 100 },
    
    // Ciclo 1: Normal → Rajada → Normal → Rajada
    { duration: '2m', target: 150 },  // Normal
    { duration: '1m', target: 200 },  // Rajada 1
    { duration: '2m', target: 150 },  // Normal
    { duration: '1m', target: 200 },  // Rajada 2
    
    // Ciclo 2: Repetição
    { duration: '2m', target: 150 },  // Normal
    { duration: '1m', target: 200 },  // Rajada 3
    { duration: '2m', target: 150 },  // Normal
    
    // Cooldown
    { duration: '1m', target: 0 },
  ],
};

const BURSTS = [
  { start: 180, end: 240 },
  { start: 360, end: 420 },
  { start: 540, end: 600 },
];

function elapsedSeconds() {
  return exec.instance.currentTestRunDuration / 1000;
}

export default function () {
  const elapsed = elapsedSeconds();
  const inBurst = BURSTS.some(({ start, end }) => elapsed >= start && elapsed < end);

  let modo;
  
  if (inBurst) {
    // Durante rajadas: 100% falhas
    modo = 'falha';
  } else {
    // Fora das rajadas: distribuição normal
    const rand = Math.random();
    if (rand < 0.80) modo = 'normal';      // 80% normal
    else if (rand < 0.95) modo = 'latencia'; // 15% latência
    else modo = 'falha';                     // 5% falha
  }
  
  const url = `${BASE_URL}/pagar?modo=${modo}`;
  
  const payload = JSON.stringify({
    amount: 100.0,
    payment_method: 'credit_card',
    customer_id: `customer-${__VU}`,
  });
  
  const params = {
    headers: { 'Content-Type': 'application/json' },
    tags: { 
      modo,
      fase: inBurst ? 'rajada' : 'normal',
      cenario: 'rajadas_intermitentes',
      versao: __ENV.VERSION || 'unknown',
    },
  };
  
  const res = http.post(url, payload, params);
  
  // ============================================================================
  // COLETA DE MÉTRICAS CUSTOMIZADAS
  // ============================================================================
  const status = res.status;
  const duration = res.timings.duration;
  
  if (status === 200 || status === 201) {
    successResponses.add(1);
    responseTimeSuccess.add(duration);
    successRate.add(true);
    availabilityRate.add(true);
  } else if (status === 202) {
    fallbackResponses.add(1);
    responseTimeFallback.add(duration);
    successRate.add(false);
    availabilityRate.add(true);
  } else if (status === 503) {
    circuitBreakerOpen.add(1);
    responseTimeFailure.add(duration);
    successRate.add(false);
    availabilityRate.add(false);
  } else if (status === 500) {
    apiFailures.add(1);
    responseTimeFailure.add(duration);
    successRate.add(false);
    availabilityRate.add(false);
  }
  
  check(res, {
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
    'status is 2xx or 202 fallback': (r) => r.status === 200 || r.status === 201 || r.status === 202,
  });
  
  sleep(1);
}
