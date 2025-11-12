#!/bin/bash

###############################################################################
# Script ALL-IN-ONE: Executa testes E análises automaticamente
#
# Uso:
#   ./run_and_analyze.sh [cenario]
#
# Cenários disponíveis:
#   - catastrofe: Falha catastrófica (API 100% fora)
#   - degradacao: Degradação gradual
#   - rajadas: Rajadas intermitentes
#   - all: Todos os cenários (demora ~45min)
###############################################################################

set -e

SCENARIO=${1:-catastrofe}

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 TESTE E ANÁLISE AUTOMÁTICA - CIRCUIT BREAKER           ║
║                                                              ║
║   Executa testes de carga e gera relatórios automaticamente ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Verifica se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker não está rodando. Iniciando Docker...${NC}"
    open -a Docker
    echo "Aguardando Docker iniciar..."
    sleep 10
fi

# 0. Rebuild das imagens para pegar código atualizado
echo -e "${BLUE}🔨 ETAPA 0: Rebuilding Docker images...${NC}\n"
docker-compose down
docker-compose build --no-cache servico-pagamento servico-adquirente
docker-compose up -d
echo "Aguardando serviços inicializarem (30s)..."
sleep 30
echo -e "${GREEN}✅ Ambiente preparado${NC}\n"

# 1. Executa os testes
echo -e "${GREEN}📊 ETAPA 1: Executando testes de carga...${NC}\n"
./run_scenario_tests.sh "$SCENARIO"

# 2. Analisa os resultados
echo -e "\n${GREEN}📈 ETAPA 2: Analisando resultados...${NC}\n"

if [ "$SCENARIO" = "all" ]; then
    python3 analysis/scripts/scenario_analyzer.py
else
    python3 analysis/scripts/scenario_analyzer.py "$SCENARIO"
fi

# 3. Abre os relatórios
echo -e "\n${GREEN}📄 ETAPA 3: Abrindo relatórios...${NC}\n"

if [ "$SCENARIO" = "all" ]; then
    open analysis_results/scenarios/catastrofe_report.html
    open analysis_results/scenarios/degradacao_report.html
    open analysis_results/scenarios/rajadas_report.html
else
    open "analysis_results/scenarios/${SCENARIO}_report.html"
fi

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ PROCESSO COMPLETO FINALIZADO COM SUCESSO!               ${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}📁 Resultados disponíveis em:${NC}"
echo -e "   - Dados brutos: k6/results/scenarios/"
echo -e "   - Relatórios HTML: analysis_results/scenarios/"
echo -e "   - CSVs: analysis_results/scenarios/csv/"
echo -e "   - Gráficos: analysis_results/scenarios/plots/"
echo -e "\n${YELLOW}💡 Dica: Use os dados do CSV consolidado para tabelas no TCC!${NC}\n"
