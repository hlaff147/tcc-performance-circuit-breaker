import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas customizadas
const responseTime = new Trend('response_time');
const successRate = new Rate('success_rate');
const failurePatterns = new Counter('failure_patterns');
const adaptationTime = new Trend('adaptation_time');

// Métricas de Circuit Breaker - CRÍTICAS para análise
const realFailures = new Counter('real_failures');           // HTTP 500/503 - Falhas REAIS
const fallbackResponses = new Counter('fallback_responses'); // HTTP 202 - Circuit Breaker ativado
const successfulResponses = new Counter('successful_responses'); // HTTP 200 - Sucesso real
const errorRate = new Rate('circuit_breaker_error_rate');    // Taxa de erro que ativa o CB

export const options = {
  scenarios: {
    falhas_intermitentes: {
      executor: 'constant-vus',
      vus: 100,
      duration: '5m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'],    // 95% das requisições < 2s
    success_rate: ['rate>0.85'],          // Taxa de sucesso > 85%
    circuit_breaker_error_rate: ['rate<0.40'], // Taxa de erro real < 40%
  },
};

const BASE_URL = 'http://servico-pagamento:8080/pagar?modo=falha';
const payload = JSON.stringify({ valor: 100.0, cartao: "1234..." });
const params = { headers: { 'Content-Type': 'application/json' } };

// Padrões de falha para simular diferentes cenários
const FAILURE_PATTERNS = {
  BURST: 'burst',           // Rajadas curtas de falhas
  GRADUAL: 'gradual',       // Aumento gradual de falhas
  RANDOM: 'random'          // Falhas aleatórias
};

let currentPattern = FAILURE_PATTERNS.RANDOM;
let patternStartTime = Date.now();
let failureCount = 0;

function shouldInduceFailure() {
  const elapsedTime = (Date.now() - patternStartTime) / 1000;  // segundos
  const randomFactor = Math.random();

  switch (currentPattern) {
    case FAILURE_PATTERNS.BURST:
      // Rajadas de 10 segundos a cada minuto
      return (elapsedTime % 60) < 10;
      
    case FAILURE_PATTERNS.GRADUAL:
      // Probabilidade crescente de falha ao longo de 1 minuto
      return randomFactor < (elapsedTime % 60) / 60;
      
    case FAILURE_PATTERNS.RANDOM:
      // 30% de chance de falha aleatória
      return randomFactor < 0.3;
      
    default:
      return false;
  }
}

function updateFailurePattern() {
  const now = Date.now();
  if (now - patternStartTime > 60000) {  // Muda o padrão a cada minuto
    patternStartTime = now;
    failureCount = 0;
    
    // Rotaciona entre os padrões
    switch (currentPattern) {
      case FAILURE_PATTERNS.BURST:
        currentPattern = FAILURE_PATTERNS.GRADUAL;
        break;
      case FAILURE_PATTERNS.GRADUAL:
        currentPattern = FAILURE_PATTERNS.RANDOM;
        break;
      default:
        currentPattern = FAILURE_PATTERNS.BURST;
    }
    failurePatterns.add(1, { pattern: currentPattern });
  }
}

export default function () {
  updateFailurePattern();
  
  const startTime = Date.now();
  let url = BASE_URL;
  
  // Induz falhas baseadas no padrão atual
  if (shouldInduceFailure()) {
    url += '&forceError=true';
    failureCount++;
  }
  
  const response = http.post(url, payload, params);
  const endTime = Date.now();
  
  // Registra tempos e sucessos
  const duration = endTime - startTime;
  responseTime.add(duration);
  
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
    errorRate.add(false); // Não é erro
  } else if (response.status === 202) {
    isFallback = true;
    fallbackResponses.add(1);
    successRate.add(true); // Sistema respondeu
    // IMPORTANTE: Fallback NÃO conta como erro na taxa, mas indica CB ativo
  } else if (response.status === 500 || response.status === 503) {
    isRealFailure = true;
    realFailures.add(1);
    successRate.add(false);
    errorRate.add(true); // É ERRO que ativa o CB
  }
  
  if ((isRealSuccess || isFallback) && failureCount > 0) {
    adaptationTime.add(endTime - patternStartTime);
  }
  
  check(response, {
    'status is valid (200, 202, or 500)': () => 
      response.status === 200 || response.status === 202 || response.status === 500,
    
    'successful transaction (200 only)': () => isRealSuccess,
    
    'fallback activated (202)': () => isFallback,
    
    'real failure (500/503)': () => isRealFailure,
    
    'adapts to failure pattern': () => {
      if (failureCount > 10) {  // Após várias falhas, deve usar fallback
        return response.status === 202;
      }
      return true;
    },
  });
  
  sleep(0.5);  // Pausa de 500ms entre requisições
}