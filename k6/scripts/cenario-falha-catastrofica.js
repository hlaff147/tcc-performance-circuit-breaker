import http from 'k6/http';
import { check, sleep } from 'k6';

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

export default function () {
  const now = new Date();
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();
  const totalSeconds = (minutes * 60) + seconds;
  
  // Determina o modo baseado no estágio do teste
  // 0-4min: Aquecimento + Normal (modo misto)
  // 4-9min: CATÁSTROFE (100% falha)
  // 9-12min: Recuperação (modo misto)
  let modo;
  
  if (totalSeconds >= 240 && totalSeconds < 540) {
    // Durante a catástrofe: 100% falhas
    modo = 'falha';
  } else {
    // Fora da catástrofe: distribuição normal
    const rand = Math.random();
    if (rand < 0.7) modo = 'normal';
    else if (rand < 0.9) modo = 'latencia';
    else modo = 'falha';
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
      fase: totalSeconds >= 240 && totalSeconds < 540 ? 'catastrofe' : 'normal'
    },
  };
  
  const res = http.post(url, payload, params);
  
  check(res, {
    'resposta valida': (r) => [200, 201, 202, 500, 503].includes(r.status),
  });
  
  sleep(1);
}
