#!/bin/bash
# ==============================================================================
# validate_corrections.sh
# Valida que todas as correções críticas foram aplicadas corretamente
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  VALIDAÇÃO DAS CORREÇÕES - TCC v2.0.0${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# ==============================================================================
# Teste 1: Parser de arquivos com regex
# ==============================================================================
echo -e "${YELLOW}[1/6] Validando parser de arquivos...${NC}"
if grep -q "re.match" analysis/scripts/comparative_analyzer.py; then
    if grep -q "import re" analysis/scripts/comparative_analyzer.py; then
        echo -e "  ${GREEN}✓ Parser com regex implementado${NC}"
    else
        echo -e "  ${RED}✗ 'import re' não encontrado${NC}"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗ Parser ainda usa split() sem regex${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Teste 2: RuntimeException em V3
# ==============================================================================
echo -e "${YELLOW}[2/6] Validando RuntimeException em V3...${NC}"
if grep -q "java.lang.RuntimeException" services/payment-service-v3/src/main/resources/application.yml; then
    echo -e "  ${GREEN}✓ RuntimeException configurado em V3${NC}"
else
    echo -e "  ${RED}✗ RuntimeException faltando em V3${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Teste 3: RuntimeException em V4
# ==============================================================================
echo -e "${YELLOW}[3/6] Validando RuntimeException em V4...${NC}"
if grep -q "java.lang.RuntimeException" services/payment-service-v4/src/main/resources/application.yml; then
    echo -e "  ${GREEN}✓ RuntimeException configurado em V4${NC}"
else
    echo -e "  ${RED}✗ RuntimeException faltando em V4${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Teste 4: ThreadLocal cleanup em V3
# ==============================================================================
echo -e "${YELLOW}[4/6] Validando ThreadLocal cleanup em V3...${NC}"
if grep -q "attemptTracker.remove()" services/payment-service-v3/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java; then
    echo -e "  ${GREEN}✓ ThreadLocal cleanup implementado em V3${NC}"
else
    echo -e "  ${RED}✗ ThreadLocal.remove() faltando em V3${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Teste 5: ThreadLocal cleanup em V4
# ==============================================================================
echo -e "${YELLOW}[5/6] Validando ThreadLocal cleanup em V4...${NC}"
if grep -q "attemptTracker.remove()" services/payment-service-v4/src/main/java/br/ufpe/cin/tcc/pagamento/service/PaymentService.java; then
    echo -e "  ${GREEN}✓ ThreadLocal cleanup implementado em V4${NC}"
else
    echo -e "  ${RED}✗ ThreadLocal.remove() faltando em V4${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Teste 6: Correção de Bonferroni
# ==============================================================================
echo -e "${YELLOW}[6/6] Validando correção de Bonferroni...${NC}"
if grep -q "BONFERRONI_ALPHA" analysis/scripts/comparative_analyzer.py; then
    if grep -q "alpha=" analysis/scripts/comparative_analyzer.py; then
        echo -e "  ${GREEN}✓ Correção de Bonferroni implementada${NC}"
    else
        echo -e "  ${YELLOW}⚠ BONFERRONI_ALPHA definido mas não passado para testes${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}✗ Correção de Bonferroni não implementada${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Testes de Compilação
# ==============================================================================
echo ""
echo -e "${BLUE}--- Testes de Compilação ---${NC}"

echo -e "${YELLOW}[COMP] Compilando payment-service-v3...${NC}"
cd services/payment-service-v3
if mvn clean compile -q > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ V3 compila sem erros${NC}"
else
    echo -e "  ${RED}✗ V3 falhou na compilação${NC}"
    ((ERRORS++))
fi
cd ../..

echo -e "${YELLOW}[COMP] Compilando payment-service-v4...${NC}"
cd services/payment-service-v4
if mvn clean compile -q > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ V4 compila sem erros${NC}"
else
    echo -e "  ${RED}✗ V4 falhou na compilação${NC}"
    ((ERRORS++))
fi
cd ../..

# ==============================================================================
# Testes de Sintaxe Python
# ==============================================================================
echo ""
echo -e "${BLUE}--- Testes de Sintaxe Python ---${NC}"

echo -e "${YELLOW}[PYTHON] Validando comparative_analyzer.py...${NC}"
if python3 -m py_compile analysis/scripts/comparative_analyzer.py 2>/dev/null; then
    echo -e "  ${GREEN}✓ Analyzer tem sintaxe Python válida${NC}"
else
    echo -e "  ${RED}✗ Analyzer tem erros de sintaxe${NC}"
    ((ERRORS++))
fi

# ==============================================================================
# Testes de Versão
# ==============================================================================
echo ""
echo -e "${BLUE}--- Validação de Versões ---${NC}"

echo -e "${YELLOW}[VER] Verificando versões em POMs...${NC}"
V3_VERSION=$(grep -A1 "artifactId>servico-pagamento-v3" services/payment-service-v3/pom.xml | grep "<version>" | sed 's/.*<version>\(.*\)<\/version>.*/\1/')
V4_VERSION=$(grep -A1 "artifactId>servico-pagamento-v4" services/payment-service-v4/pom.xml | grep "<version>" | sed 's/.*<version>\(.*\)<\/version>.*/\1/')

if [ "$V3_VERSION" = "2.0.0" ] && [ "$V4_VERSION" = "2.0.0" ]; then
    echo -e "  ${GREEN}✓ Versões consistentes: V3=$V3_VERSION, V4=$V4_VERSION${NC}"
else
    echo -e "  ${YELLOW}⚠ Versões: V3=$V3_VERSION, V4=$V4_VERSION (esperado 2.0.0)${NC}"
    ((WARNINGS++))
fi

# ==============================================================================
# Resumo Final
# ==============================================================================
echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  RESUMO DA VALIDAÇÃO${NC}"
echo -e "${BLUE}=================================================${NC}"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ TODAS AS CORREÇÕES CRÍTICAS FORAM APLICADAS${NC}"
    echo -e "${GREEN}  Código pronto para execução do experimento.${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS avisos não-críticos encontrados${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Próximo passo recomendado:${NC}"
    echo -e "  ${GREEN}./run_comparative_experiment.sh --pilot${NC}"
    
    exit 0
else
    echo -e "${RED}✗ $ERRORS ERROS ENCONTRADOS${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS avisos${NC}"
    fi
    
    echo ""
    echo -e "${RED}AÇÃO NECESSÁRIA:${NC}"
    echo -e "  Revisar os erros acima e aplicar correções manualmente."
    echo -e "  Consultar: ${BLUE}CRITICAL_FIXES.md${NC}"
    
    exit 1
fi
