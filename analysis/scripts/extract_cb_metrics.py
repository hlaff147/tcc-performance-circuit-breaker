#!/usr/bin/env python3
"""
Script para extrair métricas CORRETAS do Circuit Breaker dos resultados K6 existentes.
Como os testes antigos não tinham as métricas customizadas, este script infere
as métricas baseado nos dados disponíveis.
"""

import json
import sys
from collections import defaultdict

def extract_metrics_from_json(file_path):
    """Extrai métricas de um arquivo JSON do K6"""
    
    metrics = {
        'total_requests': 0,
        'http_200': 0,  # Sucessos reais
        'http_202': 0,  # Fallbacks
        'http_500': 0,  # Falhas
        'http_503': 0,  # Circuit Breaker Open
        'http_req_failed_true': 0,
        'http_req_failed_false': 0,
        'checks_passed': 0,
        'checks_failed': 0,
        'circuit_state_changes': 0,
        'state_transitions': defaultdict(int),
    }
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Contar requisições HTTP
                if data.get('type') == 'Point':
                    metric_name = data.get('metric')
                    value = data.get('data', {}).get('value')
                    tags = data.get('data', {}).get('tags', {})
                    
                    # HTTP requests totais
                    if metric_name == 'http_req_failed':
                        metrics['total_requests'] += 1
                        if value == 1:
                            metrics['http_req_failed_true'] += 1
                        else:
                            metrics['http_req_failed_false'] += 1
                    
                    # Status codes (se disponível nos tags)
                    if metric_name == 'http_req_duration':
                        status = tags.get('status')
                        if status:
                            if status == '200':
                                metrics['http_200'] += 1
                            elif status == '202':
                                metrics['http_202'] += 1
                            elif status == '500':
                                metrics['http_500'] += 1
                            elif status == '503':
                                metrics['http_503'] += 1
                    
                    # Checks
                    if metric_name == 'checks':
                        if value == 1:
                            metrics['checks_passed'] += 1
                        else:
                            metrics['checks_failed'] += 1
                    
                    # Circuit Breaker state changes
                    if metric_name == 'circuit_state_changes':
                        metrics['circuit_state_changes'] += 1
                        from_state = tags.get('from', 'UNKNOWN')
                        to_state = tags.get('to', 'UNKNOWN')
                        transition = f"{from_state} → {to_state}"
                        metrics['state_transitions'][transition] += 1
                        
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"Erro ao processar linha: {e}", file=sys.stderr)
                continue
    
    return metrics

def calculate_cb_stats(metrics):
    """Calcula estatísticas do Circuit Breaker"""
    
    total = metrics['total_requests']
    if total == 0:
        return None
    
    # Tentamos inferir os valores se não temos status codes diretos
    if metrics['http_200'] == 0 and metrics['http_202'] == 0 and metrics['http_500'] == 0:
        # Inferir baseado em http_req_failed
        # Se failed=false e checks passaram = sucesso (200)
        # Se failed=false e checks falharam = fallback (202)
        # Se failed=true = falha (500/503)
        
        # Esta é uma aproximação - os dados reais viriam dos novos testes
        metrics['http_500'] = metrics['http_req_failed_true']
        metrics['http_202'] = metrics['checks_passed']
        metrics['http_200'] = max(0, metrics['http_req_failed_false'] - metrics['http_202'])
    
    real_failures = metrics['http_500'] + metrics['http_503']
    fallback_responses = metrics['http_202']
    successful_responses = metrics['http_200']
    
    error_rate = (real_failures / total * 100) if total > 0 else 0
    fallback_rate = (fallback_responses / total * 100) if total > 0 else 0
    success_rate = (successful_responses / total * 100) if total > 0 else 0
    
    return {
        'total_requests': total,
        'real_failures': real_failures,
        'fallback_responses': fallback_responses,
        'successful_responses': successful_responses,
        'error_rate': round(error_rate, 2),
        'fallback_rate': round(fallback_rate, 2),
        'success_rate': round(success_rate, 2),
        'circuit_state_changes': metrics['circuit_state_changes'],
        'state_transitions': dict(metrics['state_transitions']),
    }

def print_comparison(v1_file, v2_file):
    """Imprime comparação entre V1 e V2"""
    
    print("="*80)
    print("ANÁLISE DE MÉTRICAS DO CIRCUIT BREAKER")
    print("="*80)
    
    print("\n🔍 Extraindo métricas de V1 (Baseline)...")
    v1_metrics = extract_metrics_from_json(v1_file)
    v1_stats = calculate_cb_stats(v1_metrics)
    
    print("🔍 Extraindo métricas de V2 (Circuit Breaker)...")
    v2_metrics = extract_metrics_from_json(v2_file)
    v2_stats = calculate_cb_stats(v2_metrics)
    
    if not v1_stats or not v2_stats:
        print("❌ Erro: Não foi possível calcular estatísticas")
        return
    
    print("\n" + "="*80)
    print("📊 RESULTADOS")
    print("="*80)
    
    print("\n📍 V1 (Sem Circuit Breaker):")
    print(f"   Total de Requisições:    {v1_stats['total_requests']:,}")
    print(f"   Falhas Reais (500/503):  {v1_stats['real_failures']:,} ({v1_stats['error_rate']}%)")
    print(f"   Fallbacks (202):         {v1_stats['fallback_responses']:,} ({v1_stats['fallback_rate']}%)")
    print(f"   Sucessos (200):          {v1_stats['successful_responses']:,} ({v1_stats['success_rate']}%)")
    print(f"   Mudanças de Estado CB:   {v1_stats['circuit_state_changes']}")
    
    print("\n📍 V2 (Com Circuit Breaker):")
    print(f"   Total de Requisições:    {v2_stats['total_requests']:,}")
    print(f"   Falhas Reais (500/503):  {v2_stats['real_failures']:,} ({v2_stats['error_rate']}%)")
    print(f"   Fallbacks (202):         {v2_stats['fallback_responses']:,} ({v2_stats['fallback_rate']}%)")
    print(f"   Sucessos (200):          {v2_stats['successful_responses']:,} ({v2_stats['success_rate']}%)")
    print(f"   Mudanças de Estado CB:   {v2_stats['circuit_state_changes']}")
    
    if v2_stats['state_transitions']:
        print("\n   Transições de Estado do CB:")
        for transition, count in v2_stats['state_transitions'].items():
            print(f"      {transition}: {count}")
    
    print("\n" + "="*80)
    print("🎯 INTERPRETAÇÃO")
    print("="*80)
    
    if v2_stats['circuit_state_changes'] > 0:
        print("\n✅ Circuit Breaker ATIVO:")
        print(f"   • {v2_stats['circuit_state_changes']} mudanças de estado detectadas")
        print(f"   • {v2_stats['error_rate']}% de taxa de erro REAL (não 0%!)")
        print(f"   • {v2_stats['fallback_rate']}% de fallbacks protegendo o sistema")
        
        if v2_stats['error_rate'] > 0:
            print("\n✅ CORRETO: Houve falhas iniciais que ATIVARAM o Circuit Breaker")
        else:
            print("\n⚠️  ATENÇÃO: Taxa de erro 0% - pode indicar dados incompletos nos JSONs antigos")
            print("   Recomendação: REEXECUTAR os testes com as métricas corrigidas")
    else:
        print("\n⚠️  Circuit Breaker NÃO detectado ou dados incompletos")
        print("   Recomendação: REEXECUTAR os testes com as métricas corrigidas")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python extract_cb_metrics.py <V1_file.json> <V2_file.json>")
        print("\nExemplo:")
        print("  python analysis/scripts/extract_cb_metrics.py \\")
        print("    k6/results/V1_Alta_Concorrencia.json \\")
        print("    k6/results/V2_Alta_Concorrencia.json")
        sys.exit(1)
    
    v1_file = sys.argv[1]
    v2_file = sys.argv[2]
    
    print_comparison(v1_file, v2_file)
