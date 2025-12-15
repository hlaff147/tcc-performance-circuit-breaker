# =============================================================================
# Makefile - TCC: Análise de Performance do Circuit Breaker em Microserviços
# =============================================================================
# 
# Este Makefile automatiza as tarefas comuns do projeto:
# - Build dos serviços
# - Execução de testes
# - Análise de resultados
# - Geração de documentação
#
# Uso:
#   make help      - Mostra esta ajuda
#   make build     - Compila os serviços Java
#   make up        - Inicia toda a infraestrutura
#   make test      - Executa todos os cenários de teste
#   make analyze   - Executa análise dos resultados
#   make all       - Build + Test + Analyze
# =============================================================================

.PHONY: help build up down test test-normal test-catastrofe test-degradacao \
        test-rajadas test-indisponibilidade analyze clean logs monitoring \
        v1 v2 rebuild latex

# Variáveis
DOCKER_COMPOSE = docker-compose
PYTHON = python3
RESULTS_DIR = k6/results
ANALYSIS_DIR = analysis_results

# Cores para output (ANSI)
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# HELP
# =============================================================================

help:
	@echo ""
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  TCC - Circuit Breaker Performance Analysis                    ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Comandos disponíveis:$(NC)"
	@echo ""
	@echo "  $(YELLOW)Build & Infraestrutura:$(NC)"
	@echo "    make build          - Compila os serviços Java (Maven)"
	@echo "    make up             - Inicia toda a infraestrutura Docker"
	@echo "    make down           - Para todos os containers"
	@echo "    make rebuild        - Rebuild completo (down + build + up)"
	@echo "    make v1             - Inicia com servico-pagamento V1 (sem CB)"
	@echo "    make v2             - Inicia com servico-pagamento V2 (com CB)"
	@echo ""
	@echo "  $(YELLOW)Testes:$(NC)"
	@echo "    make test           - Executa TODOS os cenários de teste"
	@echo "    make test-normal    - Executa cenário de operação normal"
	@echo "    make test-catastrofe - Executa cenário de falha catastrófica"
	@echo "    make test-degradacao - Executa cenário de degradação gradual"
	@echo "    make test-rajadas   - Executa cenário de rajadas intermitentes"
	@echo "    make test-indisponibilidade - Executa cenário de indisponibilidade"
	@echo ""
	@echo "  $(YELLOW)Análise:$(NC)"
	@echo "    make analyze        - Executa análise completa dos resultados"
	@echo "    make latex          - Exporta resultados para LaTeX"
	@echo ""
	@echo "  $(YELLOW)Monitoramento:$(NC)"
	@echo "    make monitoring     - Abre Grafana e Prometheus no browser"
	@echo "    make logs           - Mostra logs de todos os serviços"
	@echo ""
	@echo "  $(YELLOW)Limpeza:$(NC)"
	@echo "    make clean          - Remove containers e volumes"
	@echo "    make clean-results  - Remove resultados de testes anteriores"
	@echo ""
	@echo "  $(YELLOW)Workflow completo:$(NC)"
	@echo "    make all            - Build + Test + Analyze"
	@echo ""

# =============================================================================
# BUILD
# =============================================================================

build:
	@echo "$(BLUE)🔨 Compilando serviços Java...$(NC)"
	@cd services/payment-service-v1 && mvn clean package -DskipTests -q
	@echo "$(GREEN)✓ payment-service-v1 compilado$(NC)"
	@cd services/payment-service-v2 && mvn clean package -DskipTests -q
	@echo "$(GREEN)✓ payment-service-v2 compilado$(NC)"
	@cd services/acquirer-service && mvn clean package -DskipTests -q
	@echo "$(GREEN)✓ acquirer-service compilado$(NC)"
	@echo "$(GREEN)✅ Build concluído!$(NC)"

build-docker:
	@echo "$(BLUE)🐳 Construindo imagens Docker...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Imagens Docker construídas!$(NC)"

# =============================================================================
# INFRAESTRUTURA
# =============================================================================

up:
	@echo "$(BLUE)🚀 Iniciando infraestrutura...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Infraestrutura iniciada!$(NC)"
	@echo ""
	@echo "$(YELLOW)📊 URLs de acesso:$(NC)"
	@echo "   - Grafana:    http://localhost:3000"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - cAdvisor:   http://localhost:8080"
	@echo ""

down:
	@echo "$(BLUE)🛑 Parando infraestrutura...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Infraestrutura parada!$(NC)"

v1:
	@echo "$(BLUE)🔄 Iniciando com V1 (sem Circuit Breaker)...$(NC)"
	PAYMENT_SERVICE_VERSION=v1 $(DOCKER_COMPOSE) up -d --build servico-pagamento
	@echo "$(GREEN)✅ Serviço V1 iniciado!$(NC)"

v2:
	@echo "$(BLUE)🔄 Iniciando com V2 (com Circuit Breaker)...$(NC)"
	PAYMENT_SERVICE_VERSION=v2 $(DOCKER_COMPOSE) up -d --build servico-pagamento
	@echo "$(GREEN)✅ Serviço V2 iniciado!$(NC)"

rebuild: down build build-docker up
	@echo "$(GREEN)✅ Rebuild completo!$(NC)"

logs:
	$(DOCKER_COMPOSE) logs -f

logs-payment:
	$(DOCKER_COMPOSE) logs -f servico-pagamento

logs-acquirer:
	$(DOCKER_COMPOSE) logs -f servico-adquirente

# =============================================================================
# TESTES
# =============================================================================

test:
	@echo "$(BLUE)🧪 Executando todos os cenários de teste...$(NC)"
	./run_scenario_tests.sh all
	@echo "$(GREEN)✅ Testes concluídos!$(NC)"

test-normal:
	@echo "$(BLUE)🧪 Executando cenário: Operação Normal$(NC)"
	./run_scenario_tests.sh normal

test-catastrofe:
	@echo "$(BLUE)🧪 Executando cenário: Falha Catastrófica$(NC)"
	./run_scenario_tests.sh catastrofe

test-degradacao:
	@echo "$(BLUE)🧪 Executando cenário: Degradação Gradual$(NC)"
	./run_scenario_tests.sh degradacao

test-rajadas:
	@echo "$(BLUE)🧪 Executando cenário: Rajadas Intermitentes$(NC)"
	./run_scenario_tests.sh rajadas

test-indisponibilidade:
	@echo "$(BLUE)🧪 Executando cenário: Indisponibilidade Extrema$(NC)"
	./run_scenario_tests.sh indisponibilidade

# =============================================================================
# ANÁLISE
# =============================================================================

analyze:
	@echo "$(BLUE)📊 Executando análise dos resultados...$(NC)"
	@mkdir -p $(ANALYSIS_DIR)
	$(PYTHON) analysis/scripts/analyzer.py
	@echo "$(GREEN)✅ Análise concluída!$(NC)"
	@echo "$(YELLOW)📁 Resultados em: $(ANALYSIS_DIR)/$(NC)"

analyze-scenarios:
	@echo "$(BLUE)📊 Analisando cenários específicos...$(NC)"
	$(PYTHON) analysis/scripts/scenario_analyzer.py
	@echo "$(GREEN)✅ Análise de cenários concluída!$(NC)"

latex:
	@echo "$(BLUE)📄 Exportando para LaTeX...$(NC)"
	$(PYTHON) -c "from analysis.scripts.analyzer import K6Analyzer; a = K6Analyzer('k6/results', 'analysis_results'); a.load_data(); a.process_data(); a.export_latex()"
	@echo "$(GREEN)✅ Arquivos LaTeX gerados em: $(ANALYSIS_DIR)/latex/$(NC)"

charts:
	@echo "$(BLUE)📈 Gerando gráficos finais...$(NC)"
	$(PYTHON) analysis/scripts/generate_final_charts.py
	@echo "$(GREEN)✅ Gráficos gerados!$(NC)"

# =============================================================================
# MONITORAMENTO
# =============================================================================

monitoring:
	@echo "$(BLUE)📊 Abrindo dashboards de monitoramento...$(NC)"
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Acesse: http://localhost:3000"
	@open http://localhost:9090 2>/dev/null || xdg-open http://localhost:9090 2>/dev/null || echo "Acesse: http://localhost:9090"

grafana:
	@open http://localhost:3000 2>/dev/null || echo "Acesse: http://localhost:3000"

prometheus:
	@open http://localhost:9090 2>/dev/null || echo "Acesse: http://localhost:9090"

# =============================================================================
# LIMPEZA
# =============================================================================

clean:
	@echo "$(BLUE)🧹 Limpando containers e volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

clean-results:
	@echo "$(BLUE)🧹 Removendo resultados anteriores...$(NC)"
	rm -rf $(RESULTS_DIR)/*.json
	rm -rf $(RESULTS_DIR)/scenarios/*.json
	rm -rf $(ANALYSIS_DIR)/plots/*
	rm -rf $(ANALYSIS_DIR)/csv/*
	rm -rf $(ANALYSIS_DIR)/latex/*
	rm -rf $(ANALYSIS_DIR)/markdown/*
	@echo "$(GREEN)✅ Resultados removidos!$(NC)"

clean-all: clean clean-results
	@echo "$(BLUE)🧹 Limpeza completa...$(NC)"
	@cd services/payment-service-v1 && mvn clean -q
	@cd services/payment-service-v2 && mvn clean -q
	@cd services/acquirer-service && mvn clean -q
	@echo "$(GREEN)✅ Limpeza completa concluída!$(NC)"

# =============================================================================
# WORKFLOW COMPLETO
# =============================================================================

all: build up test analyze
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║  ✅ WORKFLOW COMPLETO EXECUTADO COM SUCESSO!                   ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)📊 Relatório disponível em: $(ANALYSIS_DIR)/analysis_report.html$(NC)"
	@echo "$(YELLOW)📄 Tabelas LaTeX em: $(ANALYSIS_DIR)/latex/$(NC)"
	@echo ""

# =============================================================================
# VALIDAÇÃO
# =============================================================================

validate:
	@echo "$(BLUE)🔍 Validando ambiente...$(NC)"
	@./validate_environment.sh
	@echo "$(GREEN)✅ Ambiente validado!$(NC)"

check-deps:
	@echo "$(BLUE)🔍 Verificando dependências...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)❌ Docker não encontrado$(NC)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)❌ docker-compose não encontrado$(NC)"; exit 1; }
	@command -v mvn >/dev/null 2>&1 || { echo "$(RED)❌ Maven não encontrado$(NC)"; exit 1; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "$(RED)❌ Python3 não encontrado$(NC)"; exit 1; }
	@echo "$(GREEN)✅ Todas as dependências encontradas!$(NC)"

# =============================================================================
# UTILIDADES
# =============================================================================

status:
	@echo "$(BLUE)📋 Status dos serviços:$(NC)"
	@$(DOCKER_COMPOSE) ps

health:
	@echo "$(BLUE)🏥 Verificando saúde dos serviços...$(NC)"
	@curl -sf http://localhost:8080/actuator/health 2>/dev/null && echo "$(GREEN)✓ servico-pagamento: healthy$(NC)" || echo "$(RED)✗ servico-pagamento: unhealthy$(NC)"
	@curl -sf http://localhost:8081/actuator/health 2>/dev/null && echo "$(GREEN)✓ servico-adquirente: healthy$(NC)" || echo "$(RED)✗ servico-adquirente: unhealthy$(NC)"
	@curl -sf http://localhost:9090/-/healthy 2>/dev/null && echo "$(GREEN)✓ prometheus: healthy$(NC)" || echo "$(RED)✗ prometheus: unhealthy$(NC)"

cb-status:
	@echo "$(BLUE)🔌 Status do Circuit Breaker:$(NC)"
	@curl -sf http://localhost:8080/actuator/circuitbreakers 2>/dev/null | jq '.' || echo "$(YELLOW)⚠️ Endpoint não disponível (verifique se V2 está rodando)$(NC)"
