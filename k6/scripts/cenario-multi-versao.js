import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import {
    recordMetrics,
    generatePaymentPayload,
    getDefaultHeaders
} from './lib/metrics.js';

/**
 * CENÁRIO: COMPARAÇÃO MULTI-VERSÃO
 * 
 * Script que testa V1, V2 (3 perfis) e V3 em sequência para comparação direta.
 * Ideal para executar todos os testes de uma vez e gerar dados comparativos.
 * 
 * Uso:
 *   export VERSION=V1 && k6 run cenario-multi-versao.js
 *   export VERSION=V2_equilibrado && k6 run cenario-multi-versao.js
 *   export VERSION=V2_conservador && k6 run cenario-multi-versao.js
 *   export VERSION=V2_agressivo && k6 run cenario-multi-versao.js
 *   export VERSION=V3 && k6 run cenario-multi-versao.js
 * 
 * Ou use o script de comparação automatizado:
 *   ./run_cb_profile_comparison.sh catastrofe
 */

// Configuração do endpoint baseado na versão
const VERSION = __ENV.VERSION || 'V2_equilibrado';
const BASE_URLS = {
    'V1': 'http://servico-pagamento:8080',
    'V2_equilibrado': 'http://servico-pagamento-v2:8080',
    'V2_conservador': 'http://servico-pagamento-v2:8080',
    'V2_agressivo': 'http://servico-pagamento-v2:8080',
    'V3': 'http://servico-pagamento-v3:8080',
};

const BASE_URL = BASE_URLS[VERSION] || 'http://servico-pagamento-v2:8080';

export const options = {
    stages: [
        // Fase 1: Aquecimento
        { duration: '30s', target: 50 },

        // Fase 2: Operação Normal
        { duration: '2m', target: 100 },

        // Fase 3: Stress (50% falhas)
        { duration: '2m', target: 150 },

        // Fase 4: Falha Catastrófica (100% falhas)
        { duration: '2m', target: 150 },

        // Fase 5: Recuperação
        { duration: '2m', target: 100 },

        // Fase 6: Cooldown
        { duration: '30s', target: 0 },
    ],
    thresholds: {
        'http_req_duration': ['p(95)<3000'],
        'http_req_failed': ['rate<0.5'],
    },
    tags: {
        version: VERSION,
        test_type: 'multi_version_comparison',
    },
};

// Timeline das fases (em segundos)
const PHASES = {
    warmup: { start: 0, end: 30 },
    normal: { start: 30, end: 150 },
    stress: { start: 150, end: 270 },
    catastrophe: { start: 270, end: 390 },
    recovery: { start: 390, end: 510 },
    cooldown: { start: 510, end: 540 },
};

function getCurrentPhase(elapsed) {
    for (const [phase, { start, end }] of Object.entries(PHASES)) {
        if (elapsed >= start && elapsed < end) {
            return phase;
        }
    }
    return 'unknown';
}

function getModoForPhase(phase) {
    const rand = Math.random();

    switch (phase) {
        case 'warmup':
        case 'normal':
            // 80% normal, 15% latência, 5% falha
            if (rand < 0.8) return 'normal';
            if (rand < 0.95) return 'latencia';
            return 'falha';

        case 'stress':
            // 50% normal, 25% latência, 25% falha
            if (rand < 0.5) return 'normal';
            if (rand < 0.75) return 'latencia';
            return 'falha';

        case 'catastrophe':
            // 100% falha
            return 'falha';

        case 'recovery':
            // 60% normal, 25% latência, 15% falha
            if (rand < 0.6) return 'normal';
            if (rand < 0.85) return 'latencia';
            return 'falha';

        case 'cooldown':
            return 'normal';

        default:
            return 'normal';
    }
}

export default function () {
    const elapsed = exec.instance.currentTestRunDuration / 1000;
    const phase = getCurrentPhase(elapsed);
    const modo = getModoForPhase(phase);

    const url = `${BASE_URL}/pagar?modo=${modo}`;
    const payload = generatePaymentPayload(__VU);

    const params = {
        headers: getDefaultHeaders(),
        tags: {
            modo,
            phase,
            version: VERSION,
            cenario: 'multi_version',
        },
        timeout: '5s',
    };

    const res = http.post(url, payload, params);

    // Registrar métricas customizadas
    recordMetrics(res);

    // Checks específicos por versão
    const checks = {
        'resposta válida': (r) => [200, 201, 202, 500, 503].includes(r.status),
    };

    // V2 e V3 podem ter respostas específicas
    if (VERSION.startsWith('V2')) {
        checks['CB fallback ou sucesso'] = (r) => [200, 201, 202].includes(r.status);
    } else if (VERSION === 'V3') {
        checks['Retry sucesso'] = (r) => [200, 201].includes(r.status);
    }

    check(res, checks);

    sleep(0.5 + Math.random() * 0.5); // 0.5-1s entre requisições
}

export function handleSummary(data) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    return {
        [`/scripts/results/multi_version_${VERSION}_${timestamp}.json`]: JSON.stringify(data, null, 2),
        stdout: textSummary(data, { indent: '  ', enableColors: true }),
    };
}

function textSummary(data, options) {
    const metrics = data.metrics;
    const version = VERSION;

    let output = `\n${'='.repeat(60)}\n`;
    output += `RESULTADO: ${version}\n`;
    output += `${'='.repeat(60)}\n\n`;

    if (metrics.http_reqs) {
        output += `Total de requisições: ${metrics.http_reqs.values.count}\n`;
        output += `Requisições/segundo:  ${metrics.http_reqs.values.rate.toFixed(2)}\n`;
    }

    if (metrics.http_req_duration) {
        output += `\nLatência:\n`;
        output += `  Média:  ${metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
        output += `  P50:    ${metrics.http_req_duration.values.med.toFixed(2)}ms\n`;
        output += `  P95:    ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
        output += `  P99:    ${metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
    }

    if (metrics.http_req_failed) {
        const failRate = (metrics.http_req_failed.values.rate * 100).toFixed(2);
        output += `\nTaxa de falha: ${failRate}%\n`;
    }

    output += `\n${'='.repeat(60)}\n`;

    return output;
}
