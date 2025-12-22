# 📚 Pós-processamento, Parquet e Paralelismo (Execução + Análise)

> **Última atualização:** 21 de dezembro de 2025  
> **Objetivo:** Documentar como o projeto faz pós-processamento dos resultados do k6, como o **NDJSON/JSON vira Parquet (cache)**, como a análise é executada e como a paralelização (threads + k6 em paralelo + ambientes isolados) acelera a execução.

---

## 🎯 Visão geral do pipeline

A execução ponta-a-ponta segue este fluxo:

1. **Testes de carga (k6)** geram:
   - **NDJSON** (`--out json=...`): arquivos grandes com eventos “Point” de métricas
   - **Summary JSON** (`--summary-export ...`): resumo agregado (contagens, rates, percentis)
2. **Pós-processamento em Python** lê NDJSON e aplica:
   - parsing otimizado (orjson quando disponível)
   - **paralelização (threads)** no parsing de chunks
   - **cache em Parquet** para acelerar reexecuções
3. **Análises** geram artefatos em `analysis_results/`:
   - relatórios HTML
   - tabelas CSV e tabelas Markdown
   - gráficos (PNG)

O orquestrador padrão do pipeline é:
- [run_everything.sh](run_everything.sh)

---

## 📦 Formatos e convenções de arquivos

### 1) NDJSON do k6 (entrada principal)

Arquivos (cenário completo):
- `k6/results/V1_Completo.json`
- `k6/results/V2_Completo.json`
- `k6/results/V3_Completo.json`

Arquivos (cenários críticos):
- `k6/results/scenarios/<cenario>_V1.json`
- `k6/results/scenarios/<cenario>_V2.json`
- `k6/results/scenarios/<cenario>_V3.json`

Observação importante: esses arquivos são “NDJSON” na prática (1 JSON por linha), e os scripts de análise filtram linhas que contêm `"type":"Point"`.

### 2) Summary JSON do k6 (quantificação confiável)

Arquivos (cenário completo):
- `k6/results/V1_Completo_summary.json` (e V2/V3)

Arquivos (cenários críticos):
- `k6/results/scenarios/<cenario>_V1_summary.json` (e V2/V3)

Esse formato é excelente para **quantificar** volume de requests e duração via:
- `metrics.http_reqs.count`
- `metrics.http_reqs.rate`

### 3) Cache Parquet (pós-processamento)

O Parquet é usado como **cache de leitura** gerado pelo loader em Python:
- `k6/results/.cache/*.parquet`
- `k6/results/scenarios/.cache/*.parquet`

Esse cache acelera execuções subsequentes porque evita reparsear NDJSON gigante.

---

## 🧱 Como o JSON vira Parquet (cache)

A conversão acontece no loader otimizado [analysis/scripts/fast_loader.py](analysis/scripts/fast_loader.py).

### Quando o cache é usado

- Se existir `*.parquet` correspondente e ele for **mais novo** que o JSON de origem, o loader lê direto do Parquet.
- Caso contrário, ele faz o parsing do NDJSON e salva o cache Parquet.

### Escrita do Parquet (compressão)

O cache é salvo com `pyarrow` e compressão `snappy`:

```python
df_cache.to_parquet(cache_path, engine='pyarrow', compression='snappy')
```

### Tratamento de colunas complexas (`tags`)

Como `tags` pode ser dict/list, o loader converte para string JSON na gravação e tenta reidratar ao ler:

```python
# grava
lambda x: orjson.dumps(x).decode() if isinstance(x, (dict, list)) else x

# leitura
lambda x: orjson.loads(x) if isinstance(x, str) and x.startswith('{') else x
```

---

## 🧮 Como a análise de dados é feita

### 1) Cenário completo (V1/V2/V3)

O script principal é [analysis/scripts/analyzer.py](analysis/scripts/analyzer.py).

- Entrada: `k6/results/V*_Completo.json` (via FastK6Loader)
- Saídas: `analysis_results/` (HTML, CSV, Markdown, plots)

Exemplos do que ele calcula:
- `Total Requests` (via métrica `http_reqs` dentro do NDJSON)
- latência (métrica `http_req_duration`) com `Avg`, `P95`, etc
- taxas por status (`200`, `202`, `500`, `503`)

### 2) Cenários críticos (catástrofe, degradação, rajadas, indisponibilidade, normal)

O script principal é [analysis/scripts/scenario_analyzer.py](analysis/scripts/scenario_analyzer.py).

- Entrada: `k6/results/scenarios/<cenario>_V*.json` e `*_summary.json`
- Saídas: `analysis_results/scenarios/` (HTML, CSV, plots)

Um detalhe importante: o `scenario_analyzer.py` também tenta inferir a duração do teste a partir do summary (`count/rate`) e usa uma duração estimada quando necessário.

### 3) Consolidação e gráficos finais

- [analysis/scripts/generate_final_charts.py](analysis/scripts/generate_final_charts.py) consolida CSVs e gera gráficos finais.
- [analysis/scripts/generate_comparison_charts.py](analysis/scripts/generate_comparison_charts.py) gera comparativos focados.
- [analysis/scripts/statistical_analysis.py](analysis/scripts/statistical_analysis.py) e [analysis/scripts/generate_academic_charts.py](analysis/scripts/generate_academic_charts.py) produzem estatística e gráficos “acadêmicos”.

---

## 📏 Quantificação: quantos dados foram analisados (tamanho/quantidade)

Para evitar “chutar números” e manter o relatório sempre reprodutível, este projeto inclui um gerador de quantificação:

- Script: [analysis/scripts/data_volume_report.py](analysis/scripts/data_volume_report.py)
- Saída (Markdown): `analysis_results/markdown/RELATORIO_VOLUME_DADOS.md`

### Como gerar

```bash
python3 analysis/scripts/data_volume_report.py
```

### O que o relatório mede

- **Quantidade de arquivos** NDJSON / summary / Parquet
- **Tamanho total** por categoria
- **NDJSON points**: número de linhas que contêm `"type":"Point"` (métricas)
- **Total de requests** e **duração estimada** via `*_summary.json` (`http_reqs.count / http_reqs.rate`)
- **Razão Parquet/NDJSON** (quanto o cache Parquet reduz de tamanho, em %)

Relatório gerado em:
- [analysis_results/markdown/RELATORIO_VOLUME_DADOS.md](analysis_results/markdown/RELATORIO_VOLUME_DADOS.md)

---

## 🧵 Multiprocessing/threads no pós-processamento

### Parsing paralelo (ThreadPoolExecutor)

O parsing do NDJSON, quando o arquivo não é “grande demais”, é dividido em chunks e processado em **threads** (mais leve para I/O + parsing):

```python
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    results = list(executor.map(_process_chunk, chunks))
```

Isso está implementado em [analysis/scripts/fast_loader.py](analysis/scripts/fast_loader.py).

### Reservoir sampling para arquivos muito grandes

Quando o arquivo passa de um limiar (ex.: > 100 MB), o loader ativa reservoir sampling:

```python
use_sampling = file_size_mb > 100
```

Isso mantém o pós-processamento executável mesmo com arquivos enormes, limitando o número máximo de pontos carregados.

---

## ⚡ k6 em paralelo + ambientes isolados (sem interferência)

### Execução paralela

O script [run_all_tests_parallel.sh](run_all_tests_parallel.sh) sobe todos os ambientes e executa V1/V2/V3 **simultaneamente** (processos em background), com logs por versão em `.parallel_logs/`.

Trecho essencial:

```bash
run_k6_for_version "v1" &
run_k6_for_version "v2" &
run_k6_for_version "v3" &
wait
```

### Ambientes 100% isolados

O arquivo [docker-compose-parallel.yml](docker-compose-parallel.yml) define um conjunto *dedicado* de containers por versão:

- `servico-pagamento-v1` ↔ `servico-adquirente-v1`
- `servico-pagamento-v2` ↔ `servico-adquirente-v2`
- `servico-pagamento-v3` ↔ `servico-adquirente-v3`

E cada versão expõe portas distintas no host (evita colisão e evita “misturar tráfego”):
- V1: `8080` / `8091`
- V2: `8082` / `8092`
- V3: `8083` / `8093`

No script paralelo, o k6 aponta para o container específico via rede Docker:

```bash
-e "PAYMENT_BASE_URL=http://${container}:8080"
```

### Ganho de tempo (observado)

O repositório documenta a economia de tempo como **~60%** no modo paralelo:
- [run_all_tests_parallel.sh](run_all_tests_parallel.sh)
- [run_everything.sh](run_everything.sh)

Sugestão para “fechar” isso com números exatos na escrita do TCC: use timestamps de início/fim do pipeline (ou logs) e compare execução sequencial vs paralela.

---

## ✅ Como rodar tudo (incluindo análise)

- Pipeline completo (sequencial):

```bash
./run_everything.sh
```

- Pipeline completo (paralelo V1/V2/V3):

```bash
./run_everything.sh --parallel
```

Depois, para (re)gerar a quantificação em Markdown:

```bash
python3 analysis/scripts/data_volume_report.py
```
