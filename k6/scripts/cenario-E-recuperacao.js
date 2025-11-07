import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas customizadas
const recoveryTime = new Trend('recovery_time');
const successRate = new Rate('success_rate');
const circuitState = new Counter('circuit_state');  // 0=OPEN, 1=CLOSED, 2=HALF_OPEN

// Métricas de Circuit Breaker - CRÍTICAS para análise
const realFailures = new Counter('real_failures');           // HTTP 500/503 - Falhas REAIS
const fallbackResponses = new Counter('fallback_responses'); // HTTP 202 - Circuit Breaker ativado
const successfulResponses = new Counter('successful_responses'); // HTTP 200 - Sucesso real
const errorRate = new Rate('circuit_breaker_error_rate');    // Taxa de erro que ativa o CB

export const options = {
  scenarios: {
    recuperacao: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        // Fase 1: Induzir falhas para abrir o circuito
        { duration: '30s', target: 100 },  // Carga intensa com falhas
        
        // Fase 2: Período de recuperação
        { duration: '1m', target: 10 },    // Reduz carga para permitir recuperação
        
        // Fase 3: Teste de recuperação
        { duration: '2m', target: 50 },    // Aumenta gradualmente para testar estabilidade
        
        // Fase 4: Validação final
        { duration: '1m', target: 100 },   // Teste de carga normal
      ],
    },
  },
  thresholds: {
    recovery_time: ['p(95)<5000'],        // Tempo de recuperação < 5s
    success_rate: ['rate>0.85'],          // Taxa de sucesso > 85%
    circuit_breaker_error_rate: ['rate<0.50'], // Taxa de erro real
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

let lastFailureTime = 0;
let isCircuitOpen = false;

export default function () {
  const startTime = Date.now();
  const response = http.post(BASE_URL, payload, params);
  
  // ==========================================
  // CLASSIFICAÇÃO CORRETA DAS RESPOSTAS
  // ==========================================
  let isRealSuccess = false;
  let isFallback = false;
  let isRealFailure = false;
  
  if (response.status === 200) {
    isRealSuccess = true;
    successfulResponses.add(1);
    successRate.add(true);
    errorRate.add(false);
  } else if (response.status === 202) {
    isFallback = true;
    fallbackResponses.add(1);
    successRate.add(true); // Sistema respondeu
  } else if (response.status === 500 || response.status === 503) {
    isRealFailure = true;
    realFailures.add(1);
    successRate.add(false);
    errorRate.add(true);
  }
  
  // Análise do estado do circuito baseado no status
  if (response.status === 503 && !isCircuitOpen) {
    // Circuito acabou de abrir
    isCircuitOpen = true;
    lastFailureTime = startTime;
    circuitState.add(0);  // OPEN
  } else if (response.status === 202 || isFallback) {
    // Fallback em ação (circuito ainda aberto)
    circuitState.add(0);  // OPEN
  } else if (response.status === 200 && isCircuitOpen) {
    // Circuito recuperou
    isCircuitOpen = false;
    const recoveryDuration = startTime - lastFailureTime;
    recoveryTime.add(recoveryDuration);
    circuitState.add(1);  // CLOSED
  } else if (response.status === 200) {
    circuitState.add(1);  // CLOSED
  }

  check(response, {
    'status is valid (200, 202, or 500/503)': () => 
      isRealSuccess || isFallback || isRealFailure,
    'successful transaction (200 only)': () => isRealSuccess,
    'fallback activated (202)': () => isFallback,
    'recovery time < 5s': () => {
      if (isCircuitOpen && response.status === 200) {
        return (startTime - lastFailureTime) < 5000;
      }
      return true;
    },
  });

  // Pausa dinâmica baseada na fase do teste
  const currentStage = Math.floor(startTime / 60000);  // Minutos desde o início
  if (currentStage < 1) {
    sleep(0.1);  // Fase de indução de falhas
  } else if (currentStage < 2) {
    sleep(1);    // Fase de recuperação
  } else {
    sleep(0.5);  // Fases de teste
  }
}