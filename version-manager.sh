#!/bin/bash

###############################################################################
# Script de Gerenciamento de Versões e Resultados
#
# Este script gerencia o versionamento dos resultados do experimento,
# garantindo que execuções anteriores não sejam sobrescritas.
#
# Uso:
#   ./version-manager.sh [comando] [argumentos]
#
# Comandos:
#   show              - Mostra a versão atual
#   bump [major|minor|patch] - Incrementa a versão
#   archive           - Arquiva os resultados atuais
#   prepare           - Prepara pastas para nova execução
#   list              - Lista todas as versões arquivadas
###############################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretórios
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$PROJECT_ROOT/VERSION"
ARCHIVE_DIR="$PROJECT_ROOT/results_archive"
K6_RESULTS="$PROJECT_ROOT/k6/results"
ANALYSIS_RESULTS="$PROJECT_ROOT/analysis_results"

# Carregar versão atual
load_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        source "$VERSION_FILE"
    else
        PROJECT_VERSION="0.0.0"
    fi
}

# Salvar versão
save_version() {
    local version=$1
    local description=$2
    local date=$(date +%Y-%m-%d)
    
    cat > "$VERSION_FILE" << EOF
# Versão atual do projeto TCC
# Este arquivo é usado pelos scripts de automação para versionamento dos resultados
PROJECT_VERSION=$version

# Descrição da versão
VERSION_DESCRIPTION="$description"

# Data de criação
VERSION_DATE="$date"
EOF
    
    echo -e "${GREEN}✅ Versão atualizada para: $version${NC}"
}

# Mostrar versão atual
show_version() {
    load_version
    echo -e "${BLUE}📦 Versão atual do projeto:${NC} ${GREEN}$PROJECT_VERSION${NC}"
    if [[ -n "$VERSION_DESCRIPTION" ]]; then
        echo -e "${BLUE}📝 Descrição:${NC} $VERSION_DESCRIPTION"
    fi
    if [[ -n "$VERSION_DATE" ]]; then
        echo -e "${BLUE}📅 Data:${NC} $VERSION_DATE"
    fi
}

# Incrementar versão
bump_version() {
    load_version
    local bump_type=${1:-patch}
    
    # Extrair partes da versão
    IFS='.' read -r major minor patch <<< "$PROJECT_VERSION"
    
    case $bump_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            echo -e "${RED}❌ Tipo inválido: $bump_type. Use: major, minor ou patch${NC}"
            exit 1
            ;;
    esac
    
    local new_version="$major.$minor.$patch"
    echo -e "${YELLOW}🔄 Atualizando versão: $PROJECT_VERSION → $new_version${NC}"
    
    read -p "Digite uma descrição para esta versão: " description
    save_version "$new_version" "$description"
    
    # Atualizar POMs
    update_poms "$new_version"
}

# Atualizar POMs
update_poms() {
    local version=$1
    
    echo -e "${BLUE}📝 Atualizando POMs para versão $version...${NC}"
    
    # Payment Service V1
    sed -i '' "s|<version>[0-9]\+\.[0-9]\+\.[0-9]\+</version>|<version>$version</version>|" \
        "$PROJECT_ROOT/services/payment-service-v1/pom.xml" 2>/dev/null || true
    
    # Payment Service V2
    sed -i '' "s|<version>[0-9]\+\.[0-9]\+\.[0-9]\+</version>|<version>$version</version>|" \
        "$PROJECT_ROOT/services/payment-service-v2/pom.xml" 2>/dev/null || true
    
    # Acquirer Service
    sed -i '' "s|<version>[0-9]\+\.[0-9]\+\.[0-9]\+</version>|<version>$version</version>|" \
        "$PROJECT_ROOT/services/acquirer-service/pom.xml" 2>/dev/null || true
    
    echo -e "${GREEN}✅ POMs atualizados${NC}"
}

# Arquivar resultados atuais
archive_results() {
    load_version
    local archive_path="$ARCHIVE_DIR/v$PROJECT_VERSION"
    
    echo -e "${BLUE}📦 Arquivando resultados da versão $PROJECT_VERSION...${NC}"
    
    # Criar diretório de arquivo
    mkdir -p "$archive_path"
    
    # Copiar resultados K6
    if [[ -d "$K6_RESULTS" ]] && [[ "$(ls -A $K6_RESULTS 2>/dev/null)" ]]; then
        cp -r "$K6_RESULTS" "$archive_path/"
        echo -e "${GREEN}  ✓ Resultados K6 arquivados${NC}"
    else
        echo -e "${YELLOW}  ⚠ Nenhum resultado K6 encontrado${NC}"
    fi
    
    # Copiar resultados de análise
    if [[ -d "$ANALYSIS_RESULTS" ]] && [[ "$(ls -A $ANALYSIS_RESULTS 2>/dev/null)" ]]; then
        cp -r "$ANALYSIS_RESULTS" "$archive_path/"
        echo -e "${GREEN}  ✓ Resultados de análise arquivados${NC}"
    else
        echo -e "${YELLOW}  ⚠ Nenhum resultado de análise encontrado${NC}"
    fi
    
    # Copiar VERSION file
    cp "$VERSION_FILE" "$archive_path/"
    
    # Criar README do arquivo
    cat > "$archive_path/README.md" << EOF
# Resultados - Versão $PROJECT_VERSION

**Data do arquivamento:** $(date +%Y-%m-%d\ %H:%M:%S)
**Descrição:** $VERSION_DESCRIPTION

## Conteúdo

- \`results/\` - Resultados brutos do K6 (JSON)
- \`analysis_results/\` - Gráficos, CSVs e relatórios HTML

## Como reproduzir

\`\`\`bash
git checkout v$PROJECT_VERSION
./run-experiments.sh
\`\`\`
EOF
    
    echo -e "${GREEN}✅ Resultados arquivados em: $archive_path${NC}"
}

# Preparar para nova execução
prepare_new_run() {
    load_version
    
    echo -e "${BLUE}🧹 Preparando pastas para nova execução (v$PROJECT_VERSION)...${NC}"
    
    # Limpar resultados K6 (manter estrutura)
    if [[ -d "$K6_RESULTS" ]]; then
        find "$K6_RESULTS" -name "*.json" -type f -delete 2>/dev/null || true
        echo -e "${GREEN}  ✓ Resultados K6 limpos${NC}"
    fi
    
    # Limpar resultados de análise (manter estrutura)
    if [[ -d "$ANALYSIS_RESULTS" ]]; then
        find "$ANALYSIS_RESULTS" -name "*.png" -type f -delete 2>/dev/null || true
        find "$ANALYSIS_RESULTS" -name "*.csv" -type f -delete 2>/dev/null || true
        find "$ANALYSIS_RESULTS" -name "*.html" -type f -delete 2>/dev/null || true
        find "$ANALYSIS_RESULTS" -name "*.tex" -type f -delete 2>/dev/null || true
        echo -e "${GREEN}  ✓ Resultados de análise limpos${NC}"
    fi
    
    echo -e "${GREEN}✅ Pronto para nova execução!${NC}"
}

# Listar versões arquivadas
list_versions() {
    echo -e "${BLUE}📚 Versões arquivadas:${NC}\n"
    
    if [[ -d "$ARCHIVE_DIR" ]]; then
        for dir in "$ARCHIVE_DIR"/v*; do
            if [[ -d "$dir" ]]; then
                local version=$(basename "$dir")
                local date=""
                local desc=""
                
                if [[ -f "$dir/VERSION" ]]; then
                    source "$dir/VERSION"
                    date="$VERSION_DATE"
                    desc="$VERSION_DESCRIPTION"
                fi
                
                echo -e "${GREEN}$version${NC}"
                [[ -n "$date" ]] && echo -e "  📅 Data: $date"
                [[ -n "$desc" ]] && echo -e "  📝 $desc"
                
                # Contar arquivos
                local k6_count=$(find "$dir/results" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
                local charts_count=$(find "$dir/analysis_results" -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
                echo -e "  📊 $k6_count resultados K6, $charts_count gráficos"
                echo ""
            fi
        done
    else
        echo -e "${YELLOW}Nenhuma versão arquivada encontrada${NC}"
    fi
}

# Menu principal
case "${1:-show}" in
    show)
        show_version
        ;;
    bump)
        bump_version "${2:-patch}"
        ;;
    archive)
        archive_results
        ;;
    prepare)
        prepare_new_run
        ;;
    list)
        list_versions
        ;;
    help|--help|-h)
        echo "Uso: $0 [comando] [argumentos]"
        echo ""
        echo "Comandos:"
        echo "  show              - Mostra a versão atual"
        echo "  bump [type]       - Incrementa versão (major|minor|patch)"
        echo "  archive           - Arquiva os resultados atuais"
        echo "  prepare           - Limpa pastas para nova execução"
        echo "  list              - Lista versões arquivadas"
        echo "  help              - Mostra esta ajuda"
        ;;
    *)
        echo -e "${RED}Comando desconhecido: $1${NC}"
        echo "Use '$0 help' para ver os comandos disponíveis"
        exit 1
        ;;
esac
