import http from 'k6/http';
import { check, sleep } from 'k6';

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

export default function () {
  const now = new Date();
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();
  const totalSeconds = (minutes * 60) + seconds;
  
  // Degradação gradual ao longo do tempo
  let failureRate = 0.05;  // Começa com 5% falha
  let latencyRate = 0.15;  // 15% latência
  
  if (totalSeconds > 120 && totalSeconds <= 300) {
    // Fase 2: Degradação inicial (2-5min)
    failureRate = 0.20;   // 20% falhas
    latencyRate = 0.30;   // 30% latência
  } else if (totalSeconds > 300 && totalSeconds <= 480) {
    // Fase 3: Degradação crítica (5-8min)
    failureRate = 0.50;   // 50% falhas
    latencyRate = 0.40;   // 40% latência
  } else if (totalSeconds > 480 && totalSeconds <= 720) {
    // Fase 4: Recuperação gradual (8-12min)
    failureRate = 0.15;   // 15% falhas
    latencyRate = 0.25;   // 25% latência
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
    tags: { modo },
  };
  
  const res = http.post(url, payload, params);
  
  check(res, {
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
  });
  
  sleep(1);
}
