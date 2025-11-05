import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas customizadas
const recoveryTime = new Trend('recovery_time');
const successRate = new Rate('success_rate');
const circuitState = new Counter('circuit_state');  // 0=OPEN, 1=CLOSED, 2=HALF_OPEN
const activeVUs = new Trend('active_vus');

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
    http_req_duration: ['p(95)<1500'],    // 95% das requisições < 1.5s
    success_rate: ['rate>0.90'],          // Taxa de sucesso > 90%
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  // Registra VUs ativos usando a variável global __VU
  activeVUs.add(__VU);

  const startTime = Date.now();
  const response = http.post(BASE_URL, payload, params);

  // Registra métricas
  recoveryTime.add(Date.now() - startTime);
  successRate.add(response.status === 200 || response.status === 202);

  // Atualiza estado do circuito
  if (response.status === 503) {
    circuitState.add(0); // OPEN
  } else if (response.status === 202) {
    circuitState.add(2); // HALF_OPEN
  } else if (response.status === 200) {
    circuitState.add(1); // CLOSED
  }

  // Aguarda entre requisições (variável para simular comportamento real)
  sleep(Math.random() * 0.5);
}