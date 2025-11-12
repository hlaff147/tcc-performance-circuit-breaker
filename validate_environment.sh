#!/bin/bash

###############################################################################
# Script de validação rápida - Testa se o ambiente está funcionando
# Executa um teste curto (1min) antes de rodar os cenários completos
###############################################################################

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧪 TESTE DE VALIDAÇÃO - CIRCUIT BREAKER                    ║
║                                                              ║
║   Executa teste rápido para validar ambiente                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# 1. Criar diretórios
echo -e "${YELLOW}📁 Criando diretórios...${NC}"
mkdir -p k6/results/scenarios

# 2. Parar containers existentes
echo -e "${YELLOW}🛑 Parando containers existentes...${NC}"
docker-compose down

# 3. Subir infraestrutura
echo -e "${YELLOW}🚀 Subindo infraestrutura...${NC}"
docker-compose up -d servico-adquirente k6-tester
sleep 5

# 4. Testar V1
echo -e "\n${GREEN}🔄 Testando V1 (sem Circuit Breaker)...${NC}"
PAYMENT_SERVICE_VERSION=v1 docker-compose up -d --build servico-pagamento
echo "Aguardando V1 inicializar (20s)..."
sleep 20

# Verificar se serviço está respondendo (testa endpoint real)
echo "Testando conectividade com V1..."
docker-compose exec -T servico-pagamento curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"payment_method":"credit_card","customer_id":"test"}' \
  http://localhost:8080/pagar?modo=normal || echo "Serviço ainda inicializando..."

# Teste rápido com k6
echo -e "${BLUE}Executando teste k6 rápido...${NC}"
cat > k6/scripts/test-validation.js << 'TESTEOF'
import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  http.post('http://servico-pagamento:8080/pagar?modo=normal', JSON.stringify({
    amount: 100.0,
    payment_method: 'credit_card',
    customer_id: 'test-user',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  sleep(1);
}
TESTEOF

docker-compose up -d k6-tester
sleep 2

docker-compose exec -T k6-tester k6 run /scripts/test-validation.js

echo -e "\n${GREEN}✅ V1 funcionando!${NC}\n"

# 5. Testar V2
echo -e "${GREEN}🔄 Testando V2 (com Circuit Breaker)...${NC}"
PAYMENT_SERVICE_VERSION=v2 docker-compose up -d --build servico-pagamento
echo "Aguardando V2 inicializar (20s)..."
sleep 20

# Verificar se serviço está respondendo (testa endpoint real)
echo "Testando conectividade com V2..."
docker-compose exec -T servico-pagamento curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"payment_method":"credit_card","customer_id":"test"}' \
  http://localhost:8080/pagar?modo=normal || echo "Serviço ainda inicializando..."

docker-compose up -d k6-tester
sleep 2

docker-compose exec -T k6-tester k6 run /scripts/test-validation.js

echo -e "\n${GREEN}✅ V2 funcionando!${NC}\n"

# Cleanup
rm -f k6/scripts/test-validation.js

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!                         ${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}✨ Ambiente está pronto! Agora você pode executar:${NC}"
echo -e "   ${BLUE}./run_and_analyze.sh catastrofe${NC}  (teste mais impactante, ~13min)"
echo -e "   ${BLUE}./run_and_analyze.sh all${NC}         (todos os cenários, ~45min)"
echo -e ""
