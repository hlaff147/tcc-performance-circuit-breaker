import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import {
    recordMetrics,
    generatePaymentPayload,
    getDefaultHeaders
} from './lib/metrics.js';

/**
 * CENÁRIO: TIMEOUT VARIÁVEL
 * 
 * Objetivo: Testar o comportamento do slowCallRateThreshold do Circuit Breaker.
 * A latência aumenta gradualmente para verificar quando o CB detecta "slow calls".
 * 
 * Este cenário é importante para validar:
 * - Threshold de chamadas lentas (slowCallRateThreshold)
 * - Threshold de duração lenta (slowCallDurationThreshold)
 * - Comportamento do sistema sob degradação gradual de latência
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';

export const options = {
    stages: [
        // Fase 1: Baseline (latência normal)
        { duration: '2m', target: 100 },

        // Fase 2: Latência crescente (20% lentas)
        { duration: '2m', target: 100 },

        // Fase 3: Latência alta (50% lentas)
        { duration: '2m', target: 100 },

        // Fase 4: Latência muito alta (80% lentas)
        { duration: '2m', target: 100 },

        // Fase 5: Recuperação
        { duration: '2m', target: 100 },

        // Fase 6: Cooldown
        { duration: '1m', target: 0 },
    ],
    thresholds: {
        'http_req_duration': ['p(95)<5000'],
    },
};

const PHASES = {
    baseline: { start: 0, end: 120, latencyRate: 0.05 },      // 5% latência
    degrading: { start: 120, end: 240, latencyRate: 0.20 },   // 20% latência
    slow: { start: 240, end: 360, latencyRate: 0.50 },        // 50% latência
    very_slow: { start: 360, end: 480, latencyRate: 0.80 },   // 80% latência
    recovery: { start: 480, end: 600, latencyRate: 0.10 },    // 10% latência
    cooldown: { start: 600, end: 660, latencyRate: 0.05 },    // 5% latência
};

function getCurrentPhase(elapsed) {
    for (const [phase, config] of Object.entries(PHASES)) {
        if (elapsed >= config.start && elapsed < config.end) {
            return { name: phase, ...config };
        }
    }
    return { name: 'unknown', latencyRate: 0.05 };
}

export default function () {
    const elapsed = exec.instance.currentTestRunDuration / 1000;
    const phase = getCurrentPhase(elapsed);

    // Determina se esta requisição será lenta ou normal
    const rand = Math.random();
    let modo;

    if (rand < phase.latencyRate) {
        modo = 'latencia';  // Será lenta (slowCallDurationThreshold)
    } else if (rand < phase.latencyRate + 0.05) {
        modo = 'falha';     // Pequena taxa de falha (5%)
    } else {
        modo = 'normal';
    }

    const url = `${BASE_URL}/pagar?modo=${modo}`;
    const payload = generatePaymentPayload(__VU);

    const params = {
        headers: getDefaultHeaders(),
        tags: {
            modo,
            phase: phase.name,
            cenario: 'timeout_variavel',
            versao: __ENV.VERSION || 'unknown',
        },
        timeout: '6s',
    };

    const res = http.post(url, payload, params);

    recordMetrics(res);

    check(res, {
        'resposta válida': (r) => [200, 201, 202, 500, 503].includes(r.status),
        'sucesso ou fallback': (r) => [200, 201, 202].includes(r.status),
    });

    sleep(0.5);
}
