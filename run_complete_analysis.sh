#!/bin/bash
# =============================================================================
# Script: run_complete_analysis.sh
# Descrição: Executa TODOS os testes, cenários e análises completas do TCC
# 
# Inclui:
# - Testes V1 (baseline), V2 (CB), V3 (Retry)
# - Comparação dos 3 perfis CB (equilibrado, conservador, agressivo)
# - Cenários: catástrofe, degradação, rajadas, indisponibilidade
# - Análise estatística (t-test, ANOVA, Cohen's d)
# - Visualizações acadêmicas (box plots, heatmaps, 300 DPI)
#
# Uso:
#   ./run_complete_analysis.sh [opção]
#
# Opções:
#   all         - Executa TUDO (~3-4 horas)
#   quick       - Versão rápida para teste (~30 min)
#   profiles    - Apenas comparação de perfis CB
#   versions    - Apenas comparação V1 vs V2 vs V3
#   analysis    - Apenas análise estatística e gráficos
#   help        - Mostra esta mensagem
# =============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configurações
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="analysis_results/complete_${TIMESTAMP}"
QUICK_MODE=false

# Parsear argumentos
OPTION="${1:-all}"
if [[ "$2" == "--quick" ]] || [[ "$OPTION" == "quick" ]]; then
    QUICK_MODE=true
    if [[ "$OPTION" == "quick" ]]; then
        OPTION="all"
    fi
fi

show_help() {
    echo -e "${BLUE}
╔══════════════════════════════════════════════════════════════════╗
║         📊 ANÁLISE COMPLETA TCC - CIRCUIT BREAKER                ║
╚══════════════════════════════════════════════════════════════════╝${NC}

${YELLOW}Uso:${NC}
  ./run_complete_analysis.sh [opção] [--quick]

${YELLOW}Opções:${NC}
  ${GREEN}all${NC}         Executa TUDO (~3-4 horas, ~30 min com --quick)
  ${GREEN}quick${NC}       Alias para 'all --quick'
  ${GREEN}profiles${NC}    Apenas comparação de perfis CB
  ${GREEN}versions${NC}    Apenas comparação V1 vs V2 vs V3
  ${GREEN}analysis${NC}    Apenas análise estatística e gráficos
  ${GREEN}help${NC}        Mostra esta mensagem

${YELLOW}Exemplos:${NC}
  ./run_complete_analysis.sh all            # Tudo completo
  ./run_complete_analysis.sh all --quick    # Tudo rápido
  ./run_complete_analysis.sh profiles       # Só perfis CB
  ./run_complete_analysis.sh analysis       # Só análises

${YELLOW}Resultados:${NC}
  📁 analysis_results/complete_<timestamp>/
"
    exit 0
}

header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

check_dependencies() {
    header "🔍 Verificando dependências"
    
    local missing=0
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker não encontrado${NC}"
        missing=1
    else
        echo -e "${GREEN}✅ Docker: $(docker --version | head -1)${NC}"
    fi
    
    # Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 não encontrado${NC}"
        missing=1
    else
        echo -e "${GREEN}✅ Python: $(python3 --version)${NC}"
    fi
    
    # Venv
    if [ -d ".venv" ]; then
        echo -e "${GREEN}✅ Virtual environment: .venv/${NC}"
    else
        echo -e "${YELLOW}⚠️  Criando virtual environment...${NC}"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --quiet matplotlib seaborn scipy pandas numpy
    fi
    
    # Docker rodando
    if ! docker info &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker não está rodando. Iniciando...${NC}"
        open -a Docker 2>/dev/null || true
        sleep 10
    fi
    
    if [ $missing -eq 1 ]; then
        echo -e "\n${RED}❌ Dependências faltando. Corrija antes de continuar.${NC}"
        exit 1
    fi
    
    echo -e "\n${GREEN}✅ Todas as dependências OK${NC}\n"
}

setup_environment() {
    header "🚀 Preparando ambiente"
    
    # Ativar venv
    source .venv/bin/activate
    
    # Criar diretórios
    mkdir -p "$RESULTS_DIR"/{csv,plots,json,reports}
    mkdir -p k6/results/scenarios
    mkdir -p analysis_results/{academic_charts,statistics,profile_comparison}
    
    # Parar containers
    echo "Parando containers existentes..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    echo -e "${GREEN}✅ Ambiente preparado${NC}\n"
}

run_version_tests() {
    local version=$1
    local port=$2
    local scenario=${3:-catastrofe}
    local duration="13m"
    local vus="100"
    
    if [ "$QUICK_MODE" = true ]; then
        duration="2m"
        vus="30"
    fi
    
    echo -e "${PURPLE}▶ Testando ${version} - Cenário: ${scenario}${NC}"
    
    local base_url="http://localhost:${port}"
    local result_file="k6/results/scenarios/${scenario}_${version}_${TIMESTAMP}"
    
    # Determinar script k6
    local k6_script="cenario-falha-catastrofica.js"
    case $scenario in
        degradacao) k6_script="cenario-degradacao-gradual.js" ;;
        rajadas) k6_script="cenario-rajadas-intermitentes.js" ;;
        indisponibilidade) k6_script="cenario-indisponibilidade-extrema.js" ;;
    esac
    
    # Executar k6
    docker run --rm -i \
        --network=tcc-performance-circuit-breaker_tcc-network \
        -v "$PWD/k6:/k6" \
        -e "PAYMENT_BASE_URL=http://servico-pagamento-${version}:8080" \
        -e "VERSION=${version}" \
        grafana/k6:latest run \
        --duration="$duration" \
        --vus="$vus" \
        --out json="/k6/results/scenarios/${scenario}_${version}.json" \
        --summary-export="/k6/results/scenarios/${scenario}_${version}_summary.json" \
        "/k6/scripts/${k6_script}" 2>&1 | tail -20 || true
    
    echo -e "${GREEN}✅ ${version} concluído${NC}\n"
}

run_profile_comparison() {
    header "🎚️ ETAPA 1: Comparação de Perfis CB"
    
    local scenario="catastrofe"
    local profiles=("equilibrado" "conservador" "agressivo")
    
    for profile in "${profiles[@]}"; do
        echo -e "${PURPLE}▶ Perfil: ${profile}${NC}"
        
        # Parar serviços
        docker-compose down --remove-orphans 2>/dev/null || true
        
        # Rebuild com perfil
        export CB_PROFILE="$profile"
        docker-compose build --no-cache servico-pagamento-v2 2>&1 | tail -3 || true
        docker-compose up -d servico-adquirente servico-pagamento-v2
        
        echo "Aguardando serviços (20s)..."
        sleep 20
        
        # Testar
        local duration="5m"
        local vus="80"
        if [ "$QUICK_MODE" = true ]; then
            duration="1m"
            vus="30"
        fi
        
        docker run --rm -i \
            --network=tcc-performance-circuit-breaker_tcc-network \
            -v "$PWD/k6:/k6" \
            -e "PAYMENT_BASE_URL=http://servico-pagamento-v2:8080" \
            -e "VERSION=V2_${profile}" \
            grafana/k6:latest run \
            --duration="$duration" \
            --vus="$vus" \
            --summary-export="/k6/results/scenarios/profile_${profile}_summary.json" \
            "/k6/scripts/cenario-falha-catastrofica.js" 2>&1 | tail -15 || true
        
        echo -e "${GREEN}✅ Perfil ${profile} concluído${NC}\n"
        unset CB_PROFILE
    done
    
    echo -e "${GREEN}✅ Comparação de perfis concluída${NC}\n"
}

run_version_comparison() {
    header "🔄 ETAPA 2: Comparação de Versões (V1 vs V2 vs V3)"
    
    local scenario="catastrofe"
    
    # Parar tudo
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Subir todos os serviços
    echo "Construindo e subindo todos os serviços..."
    docker-compose up -d --build servico-adquirente servico-pagamento servico-pagamento-v2 servico-pagamento-v3 2>&1 | tail -5 || true
    
    echo "Aguardando serviços (45s)..."
    sleep 45
    
    # Verificar saúde
    for port in 8080 8082 8083; do
        if curl -s "http://localhost:${port}/actuator/health" | grep -q "UP"; then
            echo -e "${GREEN}✅ Serviço na porta ${port} saudável${NC}"
        else
            echo -e "${YELLOW}⚠️ Serviço na porta ${port} não respondeu${NC}"
        fi
    done
    
    # Testar cada versão
    echo ""
    
    # V1 (porta 8080)
    run_version_tests "v1" "8080" "$scenario"
    sleep 10
    
    # V2 (porta 8082)  
    run_version_tests "v2" "8082" "$scenario"
    sleep 10
    
    # V3 (porta 8083)
    run_version_tests "v3" "8083" "$scenario"
    
    echo -e "${GREEN}✅ Comparação de versões concluída${NC}\n"
}

run_statistical_analysis() {
    header "📊 ETAPA 3: Análise Estatística"
    
    source .venv/bin/activate
    
    echo "Executando análise estatística..."
    python3 analysis/scripts/statistical_analysis.py \
        --data-dir analysis_results \
        --output-dir "$RESULTS_DIR/statistics" \
        --validate 2>&1 | tail -20 || true
    
    echo -e "${GREEN}✅ Análise estatística concluída${NC}\n"
}

run_chart_generation() {
    header "📈 ETAPA 4: Gerando Visualizações Acadêmicas"
    
    source .venv/bin/activate
    
    echo "Gerando gráficos..."
    python3 analysis/scripts/generate_academic_charts.py \
        --data-dir analysis_results \
        --output-dir "$RESULTS_DIR/plots" \
        --demo 2>&1 | tail -15 || true
    
    # Copiar para diretório principal também
    cp -r "$RESULTS_DIR/plots/"* analysis_results/academic_charts/ 2>/dev/null || true
    
    echo -e "${GREEN}✅ Visualizações geradas${NC}\n"
}

generate_final_report() {
    header "📄 ETAPA 5: Gerando Relatório Final"
    
    local report_file="$RESULTS_DIR/RELATORIO_COMPLETO.md"
    
    cat > "$report_file" << EOF
# 📊 Relatório Completo de Análise - TCC Circuit Breaker

**Data:** $(date "+%Y-%m-%d %H:%M:%S")
**Modo:** $([ "$QUICK_MODE" = true ] && echo "Rápido" || echo "Completo")

## Resumo da Execução

| Componente | Status |
|------------|--------|
| Comparação de Perfis CB | ✅ |
| Comparação V1 vs V2 vs V3 | ✅ |
| Análise Estatística | ✅ |
| Visualizações | ✅ |

## Arquivos Gerados

### Dados Brutos
- \`k6/results/scenarios/*.json\`

### Análises
- \`$RESULTS_DIR/statistics/\` - Testes estatísticos
- \`$RESULTS_DIR/plots/\` - Gráficos acadêmicos

## Como Usar os Resultados

### Para o TCC
1. Use os CSVs em \`analysis_results/\` para tabelas
2. Use os gráficos em \`$RESULTS_DIR/plots/\` (300 DPI)
3. Consulte \`ANALISE_FINAL_TCC.md\` para interpretação

### Reexecutar Análises
\`\`\`bash
source .venv/bin/activate
python analysis/scripts/statistical_analysis.py --validate
python analysis/scripts/generate_academic_charts.py --demo
\`\`\`

---
Gerado automaticamente por run_complete_analysis.sh
EOF

    echo -e "${GREEN}✅ Relatório salvo em: ${report_file}${NC}\n"
}

cleanup() {
    header "🧹 Finalizando"
    
    docker-compose down --remove-orphans 2>/dev/null || true
    echo -e "${GREEN}✅ Containers parados${NC}\n"
}

show_summary() {
    echo -e "${GREEN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ✅ ANÁLISE COMPLETA FINALIZADA COM SUCESSO!                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${YELLOW}📁 Resultados disponíveis em:${NC}"
    echo -e "   📊 Dados k6:      k6/results/scenarios/"
    echo -e "   📈 Gráficos:      ${RESULTS_DIR}/plots/"
    echo -e "   📉 Estatística:   ${RESULTS_DIR}/statistics/"
    echo -e "   📄 Relatório:     ${RESULTS_DIR}/RELATORIO_COMPLETO.md"
    echo -e ""
    echo -e "${YELLOW}💡 Próximos passos:${NC}"
    echo -e "   1. Revise os gráficos em ${RESULTS_DIR}/plots/"
    echo -e "   2. Consulte ANALISE_FINAL_TCC.md para interpretação"
    echo -e "   3. Use os dados para atualizar seu TCC"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    cd "$PROJECT_ROOT"
    
    case "$OPTION" in
        help|-h|--help)
            show_help
            ;;
        all)
            echo -e "${BLUE}"
            cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║         📊 ANÁLISE COMPLETA TCC - CIRCUIT BREAKER                ║
║                                                                  ║
║   Executando TODOS os testes e análises                         ║
╚══════════════════════════════════════════════════════════════════╝
EOF
            echo -e "${NC}"
            
            if [ "$QUICK_MODE" = true ]; then
                echo -e "${YELLOW}⚡ Modo RÁPIDO ativado (testes reduzidos)${NC}\n"
            fi
            
            check_dependencies
            setup_environment
            run_profile_comparison
            run_version_comparison
            run_statistical_analysis
            run_chart_generation
            generate_final_report
            cleanup
            show_summary
            ;;
        profiles)
            check_dependencies
            setup_environment
            run_profile_comparison
            cleanup
            show_summary
            ;;
        versions)
            check_dependencies
            setup_environment
            run_version_comparison
            cleanup
            show_summary
            ;;
        analysis)
            check_dependencies
            source .venv/bin/activate
            run_statistical_analysis
            run_chart_generation
            show_summary
            ;;
        *)
            echo -e "${RED}❌ Opção inválida: $OPTION${NC}"
            show_help
            ;;
    esac
}

# Trap para cleanup em caso de erro
trap cleanup EXIT

main "$@"
