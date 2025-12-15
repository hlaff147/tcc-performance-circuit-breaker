# 📦 Arquivo de Resultados - TCC Circuit Breaker

Esta pasta contém os resultados históricos de todas as execuções dos experimentos, organizados por versão do projeto.

## 📂 Estrutura

```
results_archive/
├── v0.0.1-SNAPSHOT/     # Versão inicial
│   ├── results/          # Resultados brutos do K6
│   ├── analysis_results/ # Gráficos e análises
│   ├── VERSION           # Metadados da versão
│   └── README.md         # Descrição do experimento
├── v1.0.0/              # Versão refatorada
│   └── ...
└── README.md            # Este arquivo
```

## 🔄 Como usar

### Listar versões arquivadas
```bash
./version-manager.sh list
```

### Arquivar resultados atuais
```bash
./version-manager.sh archive
```

### Preparar para nova execução (limpar resultados)
```bash
./version-manager.sh prepare
```

### Incrementar versão
```bash
./version-manager.sh bump patch  # 1.0.0 → 1.0.1
./version-manager.sh bump minor  # 1.0.0 → 1.1.0
./version-manager.sh bump major  # 1.0.0 → 2.0.0
```

## 📊 Versões Disponíveis

| Versão | Data | Descrição |
|--------|------|-----------|
| v0.0.1-SNAPSHOT | 2024-12-06 | Versão inicial - Experimentos originais |
| v1.0.0 | 2024-12-06 | Refatoração completa com camada de serviço, testes e métricas padronizadas |

## ⚠️ Notas

- Os arquivos JSON brutos do K6 são **muito grandes** (podem chegar a 1.4GB+)
- Apenas os arquivos `*_summary.json` são versionados no Git
- Os gráficos e CSVs são incluídos no versionamento para referência rápida
