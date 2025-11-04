import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas customizadas
const recoveryTime = new Trend('recovery_time');
const successRate = new Rate('success_rate');
const circuitState = new Counter('circuit_state');  // 0=OPEN, 1=CLOSED, 2=HALF_OPEN

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
    success_rate: ['rate>0.90'],          // Taxa de sucesso > 90%
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
  
  // Análise do estado do circuito baseado no status
  if (response.status === 503 && !isCircuitOpen) {
    // Circuito acabou de abrir
    isCircuitOpen = true;
    lastFailureTime = startTime;
    circuitState.add(0);  // OPEN
  } else if (response.status === 202) {
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

  // Registra sucesso (200 OK ou 202 Accepted para fallback)
  const isSuccess = response.status === 200 || response.status === 202;
  successRate.add(isSuccess);

  check(response, {
    'status is 200 or 202': () => isSuccess,
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