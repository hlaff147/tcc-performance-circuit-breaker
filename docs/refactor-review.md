# Revisão da Refatoração de Estrutura

## 1. Estrutura de Diretórios
- **Clareza e Intuitividade:** A hierarquia proposta separa corretamente documentação (`docs/`), testes de carga (`k6/`), monitoramento (`monitoring/`), microsserviços (`services/`) e análise (`analysis/`). Essa divisão reflete claramente o fluxo de trabalho do experimento e facilita localizar recursos específicos.
- **Responsabilidades:** Cada diretório agrupa responsabilidades específicas sem sobreposição. Os subdiretórios `services/payment-service-v1` e `services/payment-service-v2` permitem comparar implementações lado a lado, enquanto `analysis/` centraliza scripts e saídas dos estudos.
- **Nomenclatura:** Pastas usam nomes descritivos em inglês, com hífens para separar palavras. O README já menciona explicitamente `payment-service-v1` e `payment-service-v2`, mantendo a consistência com a estrutura real.
- **Redundâncias/Ambiguidades:** Não foram identificadas redundâncias. Apenas atenção para manter consistência nos comandos que fazem referência ao mapeamento de volumes do `k6` (ver seção 4).

## 2. Movimentação de Arquivos
- Documentação, diagramas e capítulos foram consolidados corretamente em `docs/`. Os caminhos usados nas imagens do README apontam para `docs/images/`, confirmando a atualização.
- Scripts e resultados do k6 encontram-se em `k6/scripts/` e `k6/results/`, alinhados com o `docker-compose.yml`.
- Configurações de monitoramento residem em `monitoring/grafana/datasources` e `monitoring/prometheus/prometheus.yml`, refletindo o mapeamento do Compose.
- Serviços foram distribuídos entre `services/acquirer-service`, `services/payment-service-v1` e `services/payment-service-v2`, permitindo builds independentes.
- Scripts de análise, dados e relatórios foram movidos para `analysis/scripts`, `analysis/data` e `analysis/reports`.

## 3. Docker Compose
- O arquivo `docker-compose.yml` referencia corretamente os novos caminhos para build dos serviços e volumes do Prometheus/Grafana.
- O serviço `k6-tester` monta `./k6/scripts` em `/k6/scripts` e `./k6/results` em `/k6/results`, mantendo consistência com os comandos descritos no README.
- Todos os serviços compartilham a rede `tcc-network`, garantindo comunicação consistente após a refatoração.

## 4. Documentação
- O README reflete a nova organização, descrevendo separadamente os serviços `payment-service-v1` e `payment-service-v2`.
- O título da stack de monitoramento foi ajustado para "## 🧰 Stack de Monitoramento", eliminando o caractere inválido.
- A seção de contribuições instrui o fluxo de colaboração mesmo sem um `CONTRIBUTING.md`, reduzindo referências quebradas.

## 5. Boas Práticas
- A estrutura está alinhada com SRP e separação de conceitos, isolando documentação, infraestrutura de testes e código de serviço.
- A nomenclatura consistente facilita automação e scripts de CI/CD.
- A documentação visual (imagens/diagramas) está centralizada, melhorando a manutenção.

## 6. Sugestões de Melhoria
1. **Adicionar checklist operacional:** incluir na documentação um roteiro de verificação (ex.: scripts de análise, dashboards) para facilitar futuras revisões.
2. **Automatizar testes:** considerar scripts shell/Makefile para subir a stack, rodar testes e coletar métricas de forma reproduzível.

## 7. Validação de Integridade
- **Paths do Compose:** verificações concluídas para builds (`services/...`) e volumes (`monitoring/...`, `k6/...`).
- **Referências em Documentação:** imagens apontam para `docs/images`. A atualização do README garantiu que a árvore de diretórios e os comandos estejam sincronizados com a estrutura atual.
- **Scripts de Análise:** arquivos permanecem em `analysis/scripts`, mas recomenda-se executar os notebooks/scripts após a refatoração para garantir que paths relativos continuem válidos.
- **Monitoramento:** configurações de Prometheus e Grafana estão no local esperado; validar se provisionamentos adicionais (dashboards) precisam ser movidos.

## 8. Checklist de Validação
- [x] Estrutura de diretórios coerente com responsabilidades
- [x] Paths do `docker-compose.yml` atualizados
- [x] Documentação reorganizada em `docs/`
- [x] Serviços separados em V1/V2
- [x] README atualizado com novos paths e correções
- [ ] Verificação executando scripts pós-refatoração (recomendada)

## 9. Recomendação Final
A branch `refactor-folder-readme` mantém a funcionalidade esperada, com caminhos ajustados para a nova hierarquia. As correções remanescentes concentram-se na documentação (README e referência ao `k6`). Após esses ajustes, a refatoração oferece uma base mais organizada para evolução do experimento.
