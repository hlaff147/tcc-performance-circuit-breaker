/**
 * Módulo de métricas padronizadas para testes K6 do TCC.
 * 
 * Este módulo define as métricas customizadas utilizadas em TODOS os cenários
 * para garantir consistência na coleta e análise de dados.
 * 
 * Métricas expostas:
 * - Taxas (Rate): successRate, fallbackRate, failureRate, availabilityRate
 * - Contadores (Counter): successCount, fallbackCount, failureCount, cbOpenCount
 * - Tendências (Trend): responseTimeSuccess, responseTimeFallback, responseTimeFailure
 */

import { Counter, Rate, Trend } from 'k6/metrics';

// =============================================================================
// TAXAS (Rate) - Proporção de requisições por categoria
// =============================================================================

/** Taxa de requisições com sucesso (HTTP 200/201) */
export const successRate = new Rate('custom_success_rate');

/** Taxa de requisições com fallback (HTTP 202) */
export const fallbackRate = new Rate('custom_fallback_rate');

/** Taxa de requisições com falha (HTTP 5xx) */
export const failureRate = new Rate('custom_failure_rate');

/** 
 * Taxa de disponibilidade total = sucesso + fallback
 * Métrica chave para comparação V1 vs V2
 */
export const availabilityRate = new Rate('custom_availability_rate');

// =============================================================================
// CONTADORES (Counter) - Total absoluto por categoria
// =============================================================================

/** Total de requisições bem-sucedidas (HTTP 200/201) */
export const successCount = new Counter('custom_success_count');

/** Total de requisições com fallback (HTTP 202) */
export const fallbackCount = new Counter('custom_fallback_count');

/** Total de requisições com falha da API (HTTP 500) */
export const failureCount = new Counter('custom_failure_count');

/** Total de requisições bloqueadas pelo Circuit Breaker (HTTP 503) */
export const cbOpenCount = new Counter('custom_cb_open_count');

// =============================================================================
// TENDÊNCIAS (Trend) - Distribuição de tempo de resposta por categoria
// =============================================================================

/** Tempo de resposta para requisições bem-sucedidas */
export const responseTimeSuccess = new Trend('custom_response_time_success');

/** Tempo de resposta para requisições com fallback */
export const responseTimeFallback = new Trend('custom_response_time_fallback');

/** Tempo de resposta para requisições com falha */
export const responseTimeFailure = new Trend('custom_response_time_failure');

/** Tempo total de resposta (todas as requisições) */
export const responseTimeTotal = new Trend('custom_response_time_total');

// =============================================================================
// FUNÇÕES HELPER
// =============================================================================

/**
 * Registra métricas baseado no código de status HTTP da resposta.
 * 
 * @param {Object} response - Resposta HTTP do k6
 */
export function recordMetrics(response) {
    const status = response.status;
    const duration = response.timings.duration;
    
    // Registra tempo total
    responseTimeTotal.add(duration);
    
    // Classifica por status e registra métricas apropriadas
    if (status >= 200 && status < 300 && status !== 202) {
        // Sucesso real (200, 201)
        successRate.add(true);
        fallbackRate.add(false);
        failureRate.add(false);
        availabilityRate.add(true);
        
        successCount.add(1);
        responseTimeSuccess.add(duration);
        
    } else if (status === 202) {
        // Fallback (Circuit Breaker ativo, mas resposta controlada)
        successRate.add(false);
        fallbackRate.add(true);
        failureRate.add(false);
        availabilityRate.add(true); // Ainda é "disponível" para o usuário
        
        fallbackCount.add(1);
        responseTimeFallback.add(duration);
        
    } else if (status === 503) {
        // Circuit Breaker aberto (sem fallback)
        successRate.add(false);
        fallbackRate.add(false);
        failureRate.add(true);
        availabilityRate.add(false);
        
        cbOpenCount.add(1);
        responseTimeFailure.add(duration);
        
    } else if (status >= 500) {
        // Erro do servidor (500, 502, etc)
        successRate.add(false);
        fallbackRate.add(false);
        failureRate.add(true);
        availabilityRate.add(false);
        
        failureCount.add(1);
        responseTimeFailure.add(duration);
        
    } else {
        // Outros (4xx, etc) - conta como falha
        successRate.add(false);
        fallbackRate.add(false);
        failureRate.add(true);
        availabilityRate.add(false);
        
        failureCount.add(1);
        responseTimeFailure.add(duration);
    }
}

/**
 * Retorna thresholds padronizados para cenários V2 (com Circuit Breaker).
 * 
 * @param {Object} overrides - Sobrescrever valores padrão
 * @returns {Object} Objeto de thresholds para k6
 */
export function getV2Thresholds(overrides = {}) {
    return {
        // Taxa de disponibilidade mínima (sucesso + fallback)
        'custom_availability_rate': ['rate>0.90'],
        
        // Taxa de falha máxima aceitável
        'custom_failure_rate': ['rate<0.15'],
        
        // Latência P95 aceitável
        'http_req_duration': ['p(95)<3000'],
        
        // Fallback deve ser rápido (< 100ms no P95)
        'custom_response_time_fallback': ['p(95)<100'],
        
        ...overrides
    };
}

/**
 * Retorna thresholds padronizados para cenários V1 (baseline, sem CB).
 * V1 é esperado que falhe mais, então thresholds são mais permissivos para coleta de dados.
 * 
 * @param {Object} overrides - Sobrescrever valores padrão
 * @returns {Object} Objeto de thresholds para k6
 */
export function getV1Thresholds(overrides = {}) {
    return {
        // V1 não tem garantia de disponibilidade alta
        'custom_availability_rate': ['rate>0.50'],
        
        // Latência pode ser maior devido a timeouts
        'http_req_duration': ['p(95)<5000'],
        
        ...overrides
    };
}

/**
 * Gera payload padrão para requisições de pagamento.
 * 
 * @param {number} vuId - ID do usuário virtual
 * @returns {string} JSON stringificado do payload
 */
export function generatePaymentPayload(vuId) {
    return JSON.stringify({
        amount: 100.0 + Math.random() * 900, // Valor entre 100 e 1000
        payment_method: 'credit_card',
        customer_id: `customer-${vuId}-${Date.now()}`,
        timestamp: new Date().toISOString()
    });
}

/**
 * Retorna headers padrão para requisições.
 */
export function getDefaultHeaders() {
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
}
