#!/bin/bash

###############################################################################
# Script para alternar entre perfis do Circuit Breaker
#
# Uso:
#   ./switch_cb_profile.sh [equilibrado|conservador|agressivo]
###############################################################################

set -e

PROFILE=${1:-equilibrado}

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

CONFIG_FILE="services/payment-service-v2/src/main/resources/application.yml"

echo -e "${BLUE}🎚️  Alterando perfil do Circuit Breaker para: ${YELLOW}${PROFILE}${NC}\n"

case $PROFILE in
    equilibrado)
        cat > "$CONFIG_FILE" << 'EOF'
server:
  port: 8080

resilience4j:
  circuitbreaker:
    instances:
      adquirente-cb:
        # PERFIL EQUILIBRADO (RECOMENDADO)
        failureRateThreshold: 50
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 20
        minimumNumberOfCalls: 10
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 5
        registerHealthIndicator: true
        slowCallDurationThreshold: 2000ms
        slowCallRateThreshold: 80
  timelimiter:
    instances:
      adquirente-cb:
        timeoutDuration: 2500ms

management:
  endpoints:
    web:
      exposure:
        include: health,circuitbreakers
  health:
    circuitbreakers:
      enabled: true
EOF
        echo -e "${GREEN}✅ Perfil EQUILIBRADO aplicado${NC}"
        echo -e "   • failureRateThreshold: 50%"
        echo -e "   • slidingWindowSize: 20"
        echo -e "   • timeout: 2500ms"
        ;;
        
    conservador)
        cat > "$CONFIG_FILE" << 'EOF'
server:
  port: 8080

resilience4j:
  circuitbreaker:
    instances:
      adquirente-cb:
        # PERFIL CONSERVADOR (Mais Tolerante)
        failureRateThreshold: 60
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 30
        minimumNumberOfCalls: 15
        waitDurationInOpenState: 15s
        permittedNumberOfCallsInHalfOpenState: 10
        registerHealthIndicator: true
        slowCallDurationThreshold: 3000ms
        slowCallRateThreshold: 90
  timelimiter:
    instances:
      adquirente-cb:
        timeoutDuration: 3000ms

management:
  endpoints:
    web:
      exposure:
        include: health,circuitbreakers
  health:
    circuitbreakers:
      enabled: true
EOF
        echo -e "${GREEN}✅ Perfil CONSERVADOR aplicado${NC}"
        echo -e "   • failureRateThreshold: 60%"
        echo -e "   • slidingWindowSize: 30"
        echo -e "   • timeout: 3000ms"
        ;;
        
    agressivo)
        cat > "$CONFIG_FILE" << 'EOF'
server:
  port: 8080

resilience4j:
  circuitbreaker:
    instances:
      adquirente-cb:
        # PERFIL AGRESSIVO (Proteção Máxima)
        failureRateThreshold: 30
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        waitDurationInOpenState: 5s
        permittedNumberOfCallsInHalfOpenState: 3
        registerHealthIndicator: true
        slowCallDurationThreshold: 1500ms
        slowCallRateThreshold: 50
  timelimiter:
    instances:
      adquirente-cb:
        timeoutDuration: 1500ms

management:
  endpoints:
    web:
      exposure:
        include: health,circuitbreakers
  health:
    circuitbreakers:
      enabled: true
EOF
        echo -e "${RED}⚠️  Perfil AGRESSIVO aplicado${NC}"
        echo -e "   • failureRateThreshold: 30%"
        echo -e "   • slidingWindowSize: 10"
        echo -e "   • timeout: 1500ms"
        echo -e "${YELLOW}   AVISO: Pode bloquear muitas requests!${NC}"
        ;;
        
    *)
        echo -e "${RED}❌ Perfil inválido: $PROFILE${NC}"
        echo "Uso: $0 [equilibrado|conservador|agressivo]"
        exit 1
        ;;
esac

echo -e "\n${BLUE}🔄 Próximos passos:${NC}"
echo -e "   1. Rebuild do serviço V2:"
echo -e "      ${YELLOW}docker-compose down${NC}"
echo -e "      ${YELLOW}PAYMENT_SERVICE_VERSION=v2 docker-compose build --no-cache servico-pagamento${NC}"
echo -e "      ${YELLOW}docker-compose up -d${NC}"
echo -e ""
echo -e "   2. Executar testes:"
echo -e "      ${YELLOW}./run_and_analyze.sh catastrofe${NC}"
echo -e ""
echo -e "   3. Comparar resultados em:"
echo -e "      ${YELLOW}analysis_results/scenarios/catastrofe_report.html${NC}"
echo -e ""
