import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import {
    recordMetrics,
    generatePaymentPayload,
    getDefaultHeaders
} from './lib/metrics.js';

/**
 * CENÁRIO: RECUPERAÇÃO RÁPIDA
 * 
 * Objetivo: Medir o tempo de recuperação do Circuit Breaker após uma falha.
 * Este cenário aplica falha total e depois recupera, medindo:
 * - Tempo até o CB abrir
 * - Tempo em estado OPEN
 * - Tempo até fechamento após recuperação
 * - Taxa de sucesso durante transição HALF_OPEN
 */

const BASE_URL = __ENV.PAYMENT_BASE_URL || 'http://servico-pagamento:8080';

export const options = {
    stages: [
        // Fase 1: Baseline estável
        { duration: '1m', target: 100 },

        // Fase 2: Falha súbita (100% falha)
        { duration: '30s', target: 100 },

        // Fase 3: Manter falha
        { duration: '1m', target: 100 },

        // Fase 4: Recuperação súbita (100% normal)
        { duration: '30s', target: 100 },

        // Fase 5: Observar fechamento do CB
        { duration: '1m', target: 100 },

        // Fase 6: Validar operação normal
        { duration: '1m', target: 100 },

        // Cooldown
        { duration: '30s', target: 0 },
    ],
    thresholds: {
        'http_req_duration': ['p(95)<3000'],
    },
};

const PHASES = {
    baseline: { start: 0, end: 60, failureRate: 0.0 },
    failure_start: { start: 60, end: 90, failureRate: 1.0 },
    failure_sustained: { start: 90, end: 150, failureRate: 1.0 },
    recovery_start: { start: 150, end: 180, failureRate: 0.0 },
    recovery_observe: { start: 180, end: 240, failureRate: 0.0 },
    validation: { start: 240, end: 300, failureRate: 0.05 },
    cooldown: { start: 300, end: 330, failureRate: 0.0 },
};

function getCurrentPhase(elapsed) {
    for (const [phase, config] of Object.entries(PHASES)) {
        if (elapsed >= config.start && elapsed < config.end) {
            return { name: phase, ...config };
        }
    }
    return { name: 'unknown', failureRate: 0.0 };
}

export default function () {
    const elapsed = exec.instance.currentTestRunDuration / 1000;
    const phase = getCurrentPhase(elapsed);

    // Determina modo baseado na fase
    const rand = Math.random();
    let modo;

    if (rand < phase.failureRate) {
        modo = 'falha';
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
            cenario: 'recuperacao_rapida',
            versao: __ENV.VERSION || 'unknown',
            // Tag especial para marcação temporal
            elapsed_seconds: Math.floor(elapsed),
        },
        timeout: '5s',
    };

    const res = http.post(url, payload, params);

    recordMetrics(res);

    // Checks específicos para medir recuperação
    check(res, {
        'resposta válida': (r) => [200, 201, 202, 500, 503].includes(r.status),
        'sucesso real (200/201)': (r) => [200, 201].includes(r.status),
        'fallback (202)': (r) => r.status === 202,
        'CB aberto (503)': (r) => r.status === 503,
        'falha propagada (500)': (r) => r.status === 500,
    });

    // Logging para debug de transições
    if (res.status === 503) {
        console.log(`[${elapsed.toFixed(1)}s] CB OPEN - Phase: ${phase.name}`);
    }

    sleep(0.3);
}
