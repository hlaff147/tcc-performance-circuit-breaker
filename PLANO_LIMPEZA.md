# 🗂️ PLANO DE LIMPEZA - Reorganização de Arquivos .md

> **INSTRUÇÕES PARA CODEX/CLAUDE:**  
> Execute as tarefas abaixo em ordem. Use ferramentas de criação/edição/deleção de arquivos.
> Confirme cada etapa antes de prosseguir para a próxima.

---

## 🎯 OBJETIVO

Reduzir de **31 arquivos .md** para **9 arquivos .md** (-71%), eliminando redundâncias e organizando documentação.

---

## 📋 TAREFAS

### ETAPA 1: CONSOLIDAR 3 ARQUIVOS → 1 NOVO

**Ação:** Criar `GUIA_EXECUCAO.md` consolidando conteúdo de:

| Arquivo Original | Seção no Novo Arquivo | Conteúdo a Extrair |
|------------------|----------------------|-------------------|
| `GUIA_RAPIDO.md` | "🚀 Guia Rápido de Execução" | Comandos principais, workflow básico |
| `METRICAS_CIRCUIT_BREAKER.md` | "📊 Métricas do Circuit Breaker" | Explicação das métricas coletadas |
| `OTIMIZACAO_ALTA_DISPONIBILIDADE.md` | "⚙️ Configuração Otimizada" | Estratégia de otimização, configuração de alta disponibilidade |

**Estrutura do novo arquivo:**

```markdown
# 🚀 Guia de Execução - Circuit Breaker TCC

## 🚀 Guia Rápido de Execução
[Conteúdo de GUIA_RAPIDO.md]

## 📊 Métricas do Circuit Breaker
[Conteúdo de METRICAS_CIRCUIT_BREAKER.md]

## ⚙️ Configuração Otimizada (Alta Disponibilidade)
[Conteúdo de OTIMIZACAO_ALTA_DISPONIBILIDADE.md]

## 🔄 Workflows Comuns
- Executar todos os testes
- Trocar perfil do CB
- Analisar resultados
- Regenerar relatórios
```

---

### ETAPA 2: DELETAR ARQUIVOS OBSOLETOS

**Ação:** Deletar os seguintes arquivos (usar `rm` ou ferramenta de deleção):

#### 📁 Raiz do Projeto (9 arquivos):

```bash
# Documentos Históricos/Temporários
INSTRUCOES.md                    # Procedimentos antigos (substituído por scripts)
MUDANCA_CENARIO_UNICO.md         # Histórico de mudança já implementada
SOLUCAO_EXIT99.md                # Bug já corrigido
RESUMO_CORRECOES.md              # Correções já aplicadas
ORGANIZATION.md                  # Organização antiga (obsoleta)

# Documentos Redundantes
APRESENTACAO_TCC.md              # Conteúdo obsoleto
COMPARACAO_ESPERADA.md           # Substituído por ANALISE_FINAL_TCC.md
SUMARIO_EXECUTIVO_ATUALIZADO.md  # Redundante com docs/SUMARIO_EXECUTIVO.md
GUIA_CENARIOS_CRITICOS.md        # Info já nos scripts e análise final

# Documentos Consolidados (deletar após criar GUIA_EXECUCAO.md)
GUIA_RAPIDO.md
METRICAS_CIRCUIT_BREAKER.md
OTIMIZACAO_ALTA_DISPONIBILIDADE.md
```

#### 📁 Pasta docs/ (5 arquivos):

```bash
docs/ACOES_PRIORITARIAS.md       # Ações já concluídas
docs/ANALISE_INCONGRUENCIAS.md   # Análise antiga
docs/GUIA_ORGANIZACAO_TCC.md     # Redundante com README.md
docs/INDICE_MESTRE.md            # Redundante com docs/README.md
docs/SUMARIO_EXECUTIVO.md        # Info já nos chapters/
```

**Total a deletar:** 14 arquivos

---

### ETAPA 3: ATUALIZAR REFERÊNCIAS

**Ação:** Atualizar arquivos que referenciam documentos deletados:

#### 3.1. README.md (raiz)

**Localizar e atualizar seção de documentação:**

```markdown
## 📚 Documentação

- **[GUIA_EXECUCAO.md](GUIA_EXECUCAO.md)** - Guia rápido de execução e métricas
- **[ANALISE_FINAL_TCC.md](ANALISE_FINAL_TCC.md)** - Análise consolidada final
- **[CB_PERFIS_CONFIGURACAO.md](CB_PERFIS_CONFIGURACAO.md)** - Perfis de configuração do CB
- **[ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md)** - Estrutura completa do projeto
- **[docs/](docs/)** - Documentação acadêmica do TCC
```

#### 3.2. docs/README.md

**Atualizar índice removendo referências aos arquivos deletados:**

```markdown
## 📑 Índice

### Capítulos Principais
- [01 - Introdução e Justificativa](chapters/01-introducao-e-justificativa.md)
- [02 - Metodologia e Design do Experimento](chapters/02-metodologia-e-design-experimento.md)
- [03 - Resultados e Discussão](chapters/03-resultados-e-discussao.md)
- [04 - Conclusão](chapters/04-conclusao.md)

### Recursos Adicionais
- [Diagramas](diagramas/) - Diagramas PlantUML e imagens
```

---

### ETAPA 4: ATUALIZAR ESTRUTURA_PROJETO.md

**Ação:** Atualizar seção de arquivos .md para refletir nova estrutura:

**Localizar seção "📄 Arquivos .md na Raiz" e substituir por:**

```markdown
## 📄 Arquivos .md na Raiz (Documentação Operacional)

### ✅ Documentação Essencial

| Arquivo | Descrição | Quando Usar |
|---------|-----------|-------------|
| **README.md** | Documentação principal do projeto | Primeiro acesso ao projeto |
| **GUIA_EXECUCAO.md** | Guia de execução, métricas e configuração | Executar testes e configurar CB |
| **ANALISE_FINAL_TCC.md** | Análise consolidada dos 3 cenários | Resultados finais para o TCC |
| **CB_PERFIS_CONFIGURACAO.md** | Perfis de configuração do CB | Referência de configurações |
| **ESTRUTURA_PROJETO.md** | Estrutura completa do projeto | Navegar e entender organização |
| **PLANO_LIMPEZA.md** | Plano de reorganização de arquivos | Referência de limpeza (este arquivo) |
```

---

### ETAPA 5: VALIDAÇÃO FINAL

**Ação:** Executar checklist de validação:

```bash
# 1. Verificar arquivos .md restantes na raiz
ls -1 *.md

# 2. Verificar arquivos .md em docs/
ls -1 docs/*.md
ls -1 docs/chapters/*.md

# 3. Confirmar criação do novo arquivo
test -f GUIA_EXECUCAO.md && echo "✅ GUIA_EXECUCAO.md criado" || echo "❌ GUIA_EXECUCAO.md faltando"

# 4. Confirmar deleção dos obsoletos
! test -f INSTRUCOES.md && echo "✅ INSTRUCOES.md deletado" || echo "❌ INSTRUCOES.md ainda existe"
! test -f COMPARACAO_ESPERADA.md && echo "✅ COMPARACAO_ESPERADA.md deletado" || echo "❌ ainda existe"
```

**Resultado esperado:**

```
Raiz (6 arquivos .md):
✅ README.md
✅ GUIA_EXECUCAO.md (NOVO)
✅ ANALISE_FINAL_TCC.md
✅ CB_PERFIS_CONFIGURACAO.md
✅ ESTRUTURA_PROJETO.md
✅ PLANO_LIMPEZA.md

docs/ (1 arquivo):
✅ docs/README.md

docs/chapters/ (4 arquivos):
✅ docs/chapters/01-introducao-e-justificativa.md
✅ docs/chapters/02-metodologia-e-design-experimento.md
✅ docs/chapters/03-resultados-e-discussao.md
✅ docs/chapters/04-conclusao.md

TOTAL: 11 arquivos .md (-64% de redução)
```

---

## ✅ BENEFÍCIOS DA REORGANIZAÇÃO

1. ✅ **Menos confusão** - Eliminação de 64% dos arquivos .md
2. ✅ **Zero redundância** - Cada informação em um único lugar
3. ✅ **Navegação clara** - Estrutura organizada e lógica
4. ✅ **Atualizado** - Apenas documentos refletindo estado atual
5. ✅ **Separação lógica** - Guias operacionais vs TCC acadêmico

---

## 🔄 RESUMO DAS MUDANÇAS

### Arquivos Criados (1):
- `GUIA_EXECUCAO.md` - Consolidação de 3 arquivos

### Arquivos Deletados (14):
- **Raiz:** 9 arquivos (históricos + redundantes + consolidados)
- **docs/:** 5 arquivos (redundantes + obsoletos)

### Arquivos Atualizados (3):
- `README.md` - Links atualizados
- `docs/README.md` - Índice atualizado
- `ESTRUTURA_PROJETO.md` - Lista de arquivos .md atualizada

### Arquivos Mantidos Intactos (7):
- `ANALISE_FINAL_TCC.md`
- `CB_PERFIS_CONFIGURACAO.md`
- `ESTRUTURA_PROJETO.md`
- `docs/chapters/01-introducao-e-justificativa.md`
- `docs/chapters/02-metodologia-e-design-experimento.md`
- `docs/chapters/03-resultados-e-discussao.md`
- `docs/chapters/04-conclusao.md`

---

## 🚀 EXECUÇÃO

**Para Codex/Claude Code:**

Execute as etapas na ordem:
1. Criar `GUIA_EXECUCAO.md` consolidando os 3 arquivos
2. Deletar 14 arquivos obsoletos
3. Atualizar referências em README.md e docs/README.md
4. Atualizar ESTRUTURA_PROJETO.md
5. Executar validação final

**Confirmação antes de cada etapa:** Perguntar ao usuário se deve prosseguir após cada etapa.

---

## ⚠️ NOTAS IMPORTANTES

- **Não deletar:** README.md, ANALISE_FINAL_TCC.md, CB_PERFIS_CONFIGURACAO.md, ESTRUTURA_PROJETO.md
- **Backup:** Se incerto, criar backup antes de deletar
- **Git:** Arquivos deletados devem ser commitados com mensagem clara
- **Validação:** Sempre executar ETAPA 5 ao final
