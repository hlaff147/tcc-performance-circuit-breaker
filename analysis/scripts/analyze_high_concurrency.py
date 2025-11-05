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
        'iteration_duration'
    }
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                metric = json.loads(line)
                if metric['type'] == 'Point' and metric['metric'] in metrics_of_interest:
                    timestamp = datetime.strptime(metric['data']['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    name = metric['metric']
                    value = metric['data']['value']
                    
                    data.append({
                        'timestamp': timestamp,
                        'metric_name': name,
                        'value': value
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
    # Gerar estatísticas
    stats = pd.DataFrame({
        'Métrica': [
            'Tempo de Resposta Médio (ms)',
            'Tempo de Resposta P95 (ms)',
            'Tempo de Resposta P99 (ms)',
            'Taxa de Requisições Média (req/s)',
            'Máximo de VUs',
            'Total de Requisições'
        ]
    })
    
    for version in ['V1 (Baseline)', 'V2 (Circuit Breaker)']:
        rt_data = response_times[response_times['version'] == version]['value']
        req_data = reqs[reqs['version'] == version]['value']
        vu_data = vus[vus['version'] == version]['value']
        
        stats[version] = [
            round(rt_data.mean(), 2),
            round(rt_data.quantile(0.95), 2),
            round(rt_data.quantile(0.99), 2),
            round(req_data.mean(), 2),
            int(vu_data.max()),
            int(req_data.sum())
        ]
    
    stats.to_csv('analysis/reports/high_concurrency_stats.csv', index=False)
    return stats

if __name__ == "__main__":
    v1_path = "k6/results/V1_Alta_Concorrencia.json"
    v2_path = "k6/results/V2_Alta_Concorrencia.json"
    
    stats = analyze_performance(v1_path, v2_path)
    print("\nEstatísticas Comparativas:")
    print(stats.to_string())