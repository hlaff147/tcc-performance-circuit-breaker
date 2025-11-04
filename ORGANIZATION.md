# Convenções e Organização do Projeto

Este documento descreve as convenções e a organização do projeto de análise do Circuit Breaker.

## Estrutura de Diretórios

```
tcc-performance-circuit-breaker/
├── docs/                      # Documentação
│   ├── images/               # Imagens dos diagramas e screenshots
│   ├── diagramas/            # Arquivos fonte dos diagramas PlantUML
│   └── chapters/             # Capítulos do TCC em Markdown
├── k6/                       # Testes de carga
│   ├── scripts/             # Scripts de teste k6
│   └── results/             # Resultados dos testes
├── monitoring/              # Configurações de monitoramento
│   ├── grafana/            # Dashboards e configurações do Grafana
│   └── prometheus/         # Configurações do Prometheus
├── services/               # Microsserviços
│   ├── payment-service/    # Serviço de Pagamento (V1 e V2)
│   └── acquirer-service/   # Serviço Adquirente
└── analysis/              # Scripts e resultados de análise
    ├── scripts/           # Scripts Python de análise
    ├── data/             # Dados processados (CSV)
    └── reports/          # Relatórios gerados
```

## Convenções de Nomenclatura

### Arquivos e Diretórios

- Use kebab-case para nomes de diretórios e arquivos
- Sufixe arquivos de teste com `-test` ou `.test`
- Use extensões apropriadas (.md, .puml, .js, .java, .py)

### Código

- Java: Use convenções padrão do Java (CamelCase)
- JavaScript (k6): Use camelCase para variáveis e funções
- Python: Use snake_case para variáveis e funções
- PlantUML: Use PascalCase para componentes e snake_case para relações

### Commits

- Use commits atômicos e mensagens descritivas
- Prefixe commits com o tipo: feat:, fix:, docs:, etc.
- Referencie issues quando aplicável

### Documentação

- Use Markdown para documentação
- Inclua diagramas quando necessário
- Mantenha a documentação atualizada com o código

## Fluxo de Trabalho

1. Documentação
   - Mantenha os diagramas em `docs/diagramas/`
   - Gere imagens em `docs/images/`
   - Atualize a documentação em `docs/chapters/`

2. Desenvolvimento
   - Implemente mudanças em `services/`
   - Atualize testes em `k6/scripts/`
   - Configure monitoramento em `monitoring/`

3. Testes e Análise
   - Execute testes via k6
   - Colete resultados em `k6/results/`
   - Analise com scripts em `analysis/scripts/`
   - Gere relatórios em `analysis/reports/`

## Versionamento

- Mantenha as versões V1 e V2 do serviço de pagamento separadas
- Use tags para marcar versões estáveis
- Documente mudanças no CHANGELOG.md

## Integração e Deployment

- Use Docker para todos os serviços
- Mantenha o docker-compose.yml atualizado
- Documente variáveis de ambiente e configurações