import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

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
      fase: inBurst ? 'rajada' : 'normal'
    },
  };
  
  const res = http.post(url, payload, params);
  
  check(res, {
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
    'status is 2xx or 202 fallback': (r) => r.status === 200 || r.status === 201 || r.status === 202,
  });
  
  sleep(1);
}
