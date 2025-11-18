import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

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
    tags: { modo, fase },
  };
  
  const res = http.post(url, payload, params);
  
  check(res, {
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
    'status is 2xx or 202 fallback': (r) => r.status === 200 || r.status === 201 || r.status === 202,
  });
  
  sleep(1);
}
