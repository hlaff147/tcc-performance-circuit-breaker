import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime

def load_k6_results(file_path):
    data = []
    metrics_of_interest = {
        'http_req_duration',
        'http_reqs',
        'vus',
        'iteration_duration',
        'http_req_failed',  # Para calcular taxa de falha
        'checks',  # Para verificar checks
        'real_failures',  # Falhas reais (500/503)
        'fallback_responses',  # Respostas de fallback (202)
        'successful_responses',  # Sucessos reais (200)
        'circuit_breaker_error_rate',  # Taxa de erro que ativa CB
        'circuit_state_changes',  # Mudanças de estado do CB
    }
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                metric = json.loads(line)
                if metric['type'] == 'Point' and metric['metric'] in metrics_of_interest:
                    timestamp = datetime.strptime(metric['data']['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    name = metric['metric']
                    value = metric['data']['value']
                    tags = metric['data'].get('tags', {})
                    
                    data.append({
                        'timestamp': timestamp,
                        'metric_name': name,
                        'value': value,
                        'tags': tags
                    })
            except json.JSONDecodeError:
                continue
            except KeyError:
                continue
    
    return pd.DataFrame(data)

def analyze_performance(v1_path, v2_path):
    # Carregar dados
    print("Carregando dados V1...")
    df_v1 = load_k6_results(v1_path)
    df_v1['version'] = 'V1 (Baseline)'
    
    print("Carregando dados V2...")
    df_v2 = load_k6_results(v2_path)
    df_v2['version'] = 'V2 (Circuit Breaker)'
    
    # Combinar dados
    df = pd.concat([df_v1, df_v2])
    
    print("Gerando gráficos...")
    # Configurar estilo dos gráficos
    plt.style.use('default')
    sns.set_theme(style="whitegrid")
    sns.set_palette("husl")
    
    # Criar subplots
    fig = plt.figure(figsize=(20, 15))
    
    # 1. Tempo de Resposta ao Longo do Tempo
    ax1 = plt.subplot(2, 2, 1)
    response_times = df[df['metric_name'] == 'http_req_duration']
    for version in ['V1 (Baseline)', 'V2 (Circuit Breaker)']:
        data = response_times[response_times['version'] == version]
        sns.lineplot(data=data, x='timestamp', y='value', label=version)
    plt.title('Tempo de Resposta ao Longo do Teste')
    plt.xlabel('Tempo')
    plt.ylabel('Tempo de Resposta (ms)')
    
    # 2. Distribuição dos Tempos de Resposta (Box Plot)
    ax2 = plt.subplot(2, 2, 2)
    sns.boxplot(data=response_times, x='version', y='value', showfliers=False)
    plt.title('Distribuição dos Tempos de Resposta')
    plt.xlabel('Versão')
    plt.ylabel('Tempo de Resposta (ms)')
    
    # 3. Usuários Virtuais Ativos
    ax3 = plt.subplot(2, 2, 3)
    vus = df[df['metric_name'] == 'vus']
    for version in ['V1 (Baseline)', 'V2 (Circuit Breaker)']:
        data = vus[vus['version'] == version]
        sns.lineplot(data=data, x='timestamp', y='value', label=version)
    plt.title('Usuários Virtuais Ativos')
    plt.xlabel('Tempo')
    plt.ylabel('Número de VUs')
    
    # 4. Taxa de Requisições
    ax4 = plt.subplot(2, 2, 4)
    reqs = df[df['metric_name'] == 'http_reqs']
    for version in ['V1 (Baseline)', 'V2 (Circuit Breaker)']:
        data = reqs[reqs['version'] == version]
        sns.lineplot(data=data, x='timestamp', y='value', label=version)
    plt.title('Taxa de Requisições')
    plt.xlabel('Tempo')
    plt.ylabel('Requisições/s')
    
    plt.tight_layout()
    plt.savefig('analysis/reports/high_concurrency_analysis.png', dpi=300, bbox_inches='tight')
    
    print("Calculando estatísticas...")
    
    # Função auxiliar para calcular métricas do Circuit Breaker
    def get_counter_total(df_version, metric_name):
        values = df_version[df_version['metric_name'] == metric_name]['value']
        if len(values) == 0:
            return 0
        return int(values.max())

    def calculate_cb_metrics(df_version):
        # Total de requisições registradas (cada ponto de http_req_failed representa uma tentativa)
        http_failed = df_version[df_version['metric_name'] == 'http_req_failed']['value']
        total_reqs = len(http_failed)

        # Falhas HTTP registradas pelo K6 (status >= 400)
        http_failures = int(http_failed.sum()) if total_reqs > 0 else 0

        # Contadores personalizados do Circuit Breaker
        real_failures = get_counter_total(df_version, 'real_failures')
        fallback_responses = get_counter_total(df_version, 'fallback_responses')
        successful_responses = get_counter_total(df_version, 'successful_responses')

        # Taxas derivadas
        error_rate = (real_failures / total_reqs * 100) if total_reqs > 0 else 0.0
        fallback_rate = (fallback_responses / total_reqs * 100) if total_reqs > 0 else 0.0
        success_rate = (successful_responses / total_reqs * 100) if total_reqs > 0 else 0.0

        # Mudanças de estado do CB
        cb_state_changes = get_counter_total(df_version, 'circuit_state_changes')

        return {
            'total_requests': total_reqs,
            'http_failures': http_failures,
            'real_failures': real_failures,
            'fallback_responses': fallback_responses,
            'successful_responses': successful_responses,
            'error_rate': round(error_rate, 2),
            'fallback_rate': round(fallback_rate, 2),
            'success_rate': round(success_rate, 2),
            'cb_state_changes': cb_state_changes
        }
    
    # Calcular métricas para V1 e V2
    cb_metrics_v1 = calculate_cb_metrics(df_v1)
    cb_metrics_v2 = calculate_cb_metrics(df_v2)
    
    # Gerar estatísticas
    stats = pd.DataFrame({
        'Métrica': [
            'Tempo de Resposta Médio (ms)',
            'Tempo de Resposta P95 (ms)',
            'Tempo de Resposta P99 (ms)',
            'Taxa de Requisições Média (req/s)',
            'Máximo de VUs',
            'Total de Requisições',
            '--- Circuit Breaker ---',
            'Falhas HTTP (>=400)',
            'Falhas Reais (500/503)',
            'Respostas Fallback (202)',
            'Sucessos Reais (200)',
            'Taxa de Erro Real (%)',
            'Taxa de Fallback (%)',
            'Taxa de Sucesso Real (%)',
            'Mudanças de Estado CB',
        ]
    })
    
    for version, cb_metrics in [('V1 (Baseline)', cb_metrics_v1), ('V2 (Circuit Breaker)', cb_metrics_v2)]:
        rt_data = response_times[response_times['version'] == version]['value']
        req_data = reqs[reqs['version'] == version]['value']
        vu_data = vus[vus['version'] == version]['value']
        
        stats[version] = [
            round(rt_data.mean(), 2) if len(rt_data) > 0 else 0,
            round(rt_data.quantile(0.95), 2) if len(rt_data) > 0 else 0,
            round(rt_data.quantile(0.99), 2) if len(rt_data) > 0 else 0,
            round(req_data.mean(), 2) if len(req_data) > 0 else 0,
            int(vu_data.max()) if len(vu_data) > 0 else 0,
            cb_metrics['total_requests'],
            '---',
            cb_metrics['http_failures'],
            cb_metrics['real_failures'],
            cb_metrics['fallback_responses'],
            cb_metrics['successful_responses'],
            cb_metrics['error_rate'],
            cb_metrics['fallback_rate'],
            cb_metrics['success_rate'],
            cb_metrics['cb_state_changes'],
        ]
    
    stats.to_csv('analysis/reports/high_concurrency_stats.csv', index=False)
    
    # Imprimir explicação
    print("\n" + "="*80)
    print("EXPLICAÇÃO DAS MÉTRICAS DO CIRCUIT BREAKER")
    print("="*80)
    print("\n📊 V1 (Sem Circuit Breaker):")
    print(f"  • Total de Requisições: {cb_metrics_v1['total_requests']:,}")
    print(f"  • Falhas HTTP (>=400): {cb_metrics_v1['http_failures']:,}")
    print(f"  • Falhas Reais: {cb_metrics_v1['real_failures']:,}")
    print(f"  • Fallbacks: {cb_metrics_v1['fallback_responses']:,}")
    print(f"  • Sucessos Reais: {cb_metrics_v1['successful_responses']:,}")
    print(f"  • Taxa de Erro Real: {cb_metrics_v1['error_rate']}%")
    print(f"  • Mudanças de Estado: {cb_metrics_v1['cb_state_changes']}")

    print("\n📊 V2 (Com Circuit Breaker):")
    print(f"  • Total de Requisições: {cb_metrics_v2['total_requests']:,}")
    print(f"  • Falhas HTTP (>=400): {cb_metrics_v2['http_failures']:,}")
    print(f"  • Falhas Reais: {cb_metrics_v2['real_failures']:,} → Estas falhas ATIVARAM o Circuit Breaker")
    print(f"  • Respostas Fallback: {cb_metrics_v2['fallback_responses']:,} → Circuit Breaker ATIVO protegendo o sistema")
    print(f"  • Sucessos Reais: {cb_metrics_v2['successful_responses']:,} → Transações processadas com sucesso")
    print(f"  • Taxa de Erro Real: {cb_metrics_v2['error_rate']}% → Percentual de requisições que FALHARAM e ativaram o CB")
    print(f"  • Taxa de Fallback: {cb_metrics_v2['fallback_rate']}% → Percentual atendido via fallback")
    print(f"  • Taxa de Sucesso Real: {cb_metrics_v2['success_rate']}% → Processamento completo")
    print(f"  • Mudanças de Estado: {cb_metrics_v2['cb_state_changes']} transições → CB abrindo/fechando conforme necessário")
    print("\n" + "="*80)
    
    return stats

if __name__ == "__main__":
    v1_path = "k6/results/V1_Alta_Concorrencia.json"
    v2_path = "k6/results/V2_Alta_Concorrencia.json"
    
    stats = analyze_performance(v1_path, v2_path)
    print("\nEstatísticas Comparativas:")
    print(stats.to_string())
