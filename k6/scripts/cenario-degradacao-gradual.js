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
 * CENÁRIO 2: DEGRADAÇÃO GRADUAL
 * 
 * Simula uma API externa que começa saudável mas gradualmente degrada
 * (ex: memory leak, conexões esgotando, CPU aumentando).
 * 
 * Comportamento esperado:
 * - V1: Degrada junto com a API, afeta todos os usuários progressivamente
 * - V2: CB detecta degradação e isola o problema antes de cascata total
 * 
 * Benefícios esperados do CB:
 * - Detecção precoce de degradação
 * - Isolamento antes do colapso total
 * - Tempo de resposta mais previsível
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';

export const options = {
  stages: [
    // Sistema saudável
    { duration: '2m', target: 100 },
    
    // Início da degradação
    { duration: '3m', target: 150 },
    
    // Degradação crítica
    { duration: '3m', target: 200 },
    
    // Pós-incidente (sistema ainda se recuperando)
    { duration: '4m', target: 100 },
    
    // Cooldown
    { duration: '1m', target: 0 },
  ],
};

const PHASES = {
  degradeStart: 120,
  criticalStart: 300,
  recoveryStart: 480,
  testEnd: 720,
};

function elapsedSeconds() {
  return exec.instance.currentTestRunDuration / 1000;
}

export default function () {
  const elapsed = elapsedSeconds();
  let failureRate = 0.05;
  let latencyRate = 0.15;
  let fase = 'estavel';

  if (elapsed > PHASES.degradeStart && elapsed <= PHASES.criticalStart) {
    failureRate = 0.20;
    latencyRate = 0.30;
    fase = 'degradacao';
  } else if (elapsed > PHASES.criticalStart && elapsed <= PHASES.recoveryStart) {
    failureRate = 0.50;
    latencyRate = 0.40;
    fase = 'critico';
  } else if (elapsed > PHASES.recoveryStart && elapsed <= PHASES.testEnd) {
    failureRate = 0.15;
    latencyRate = 0.25;
    fase = 'recuperacao';
  }

  const rand = Math.random();
  let modo;
  
  if (rand < failureRate) {
    modo = 'falha';
  } else if (rand < failureRate + latencyRate) {
    modo = 'latencia';
  } else {
    modo = 'normal';
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
      fase,
      cenario: 'degradacao_gradual',
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
