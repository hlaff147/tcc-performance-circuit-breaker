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
 * CENÁRIO 0: OPERAÇÃO NORMAL (BASELINE)
 * 
 * Objetivo: Demonstrar que o Circuit Breaker NÃO introduz overhead em condições
 * normais de operação ("céu azul"). Este cenário serve como baseline para 
 * comparação com os cenários de estresse.
 * 
 * Configuração:
 * - 100% das requisições em modo=normal
 * - 5 minutos de teste estável
 * - Carga moderada e constante (100 VUs)
 * 
 * Comportamento esperado:
 * - V1 e V2 devem ter performance IDÊNTICA ou muito próxima
 * - Latência P95 < 200ms
 * - Taxa de sucesso > 99%
 * - Fallback e CB Open = 0%
 * 
 * Métricas importantes:
 * - Overhead do CB = (latência_V2 - latência_V1) / latência_V1
 * - Se overhead < 5%, CB é considerado "transparente"
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';

export const options = {
  stages: [
    // Aquecimento gradual
    { duration: '30s', target: 50 },
    
    // Carga estável para medição
    { duration: '4m', target: 100 },
    
    // Cooldown
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // Thresholds rigorosos para cenário normal
    'http_req_duration': ['p(95)<200', 'p(99)<500'],
    'http_req_failed': ['rate<0.01'],  // Menos de 1% de falha
    'custom_success_rate': ['rate>0.99'],  // Mais de 99% de sucesso
  },
};

function elapsedSeconds() {
  return exec.instance.currentTestRunDuration / 1000;
}

export default function () {
  // 100% modo normal - sem falhas induzidas
  const modo = 'normal';
  const fase = 'estavel';
  
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
      cenario: 'operacao_normal',
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
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has valid response body': (r) => r.body && r.body.length > 0,
  });
  
  sleep(1);
}

/**
 * Função de setup - executada uma vez antes do teste
 */
export function setup() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  CENÁRIO: OPERAÇÃO NORMAL (BASELINE)                       ║');
  console.log('║  Objetivo: Validar que CB não introduz overhead            ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  
  // Verifica se o serviço está disponível
  const healthCheck = http.get(`${BASE_URL}/actuator/health`);
  if (healthCheck.status !== 200) {
    console.warn('⚠️  Serviço pode não estar totalmente saudável');
  }
}

/**
 * Função de teardown - executada uma vez após o teste
 */
export function teardown(data) {
  console.log('');
  console.log('════════════════════════════════════════════════════════════');
  console.log('  TESTE CONCLUÍDO - Verifique as métricas customizadas:');
  console.log('  - custom_success_rate: Taxa de sucesso real');
  console.log('  - custom_response_time_success: Latência de requisições OK');
  console.log('════════════════════════════════════════════════════════════');
}
