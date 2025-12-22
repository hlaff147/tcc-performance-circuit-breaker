# 📦 Relatório de Volume de Dados (k6 + pós-processamento)

> Gerado em: **2025-12-21 23:56:20**
> Projeto: **tcc-performance-circuit-breaker**
> k6 results dir: `/Users/hlaff/tcc-performance-circuit-breaker/k6/results`
> analysis_results dir: `/Users/hlaff/tcc-performance-circuit-breaker/analysis_results`

## ✅ Resumo

| Categoria | Arquivos | Tamanho total |
|---|---|---|
| NDJSON (k6 --out json) | 18 | 11.01 GB |
| Summary JSON (k6 --summary-export) | 18 | 95.60 KB |
| Cache Parquet (FastK6Loader) | 18 | 123.80 MB |

> ⚠️ `pyarrow` não está disponível: metadados do Parquet (rows/cols) aparecem como ‘—’.


## 🧪 Cenário completo (V1/V2/V3)

| Versão | NDJSON size | NDJSON points (linhas Point) | Parquet cache size | Parquet rows | Parquet/NDJSON | http_reqs (summary) | http_reqs rate | Duração estimada |
|---|---|---|---|---|---|---|---|---|
| V1 | 2.10 GB | 8,885,464 | 8.88 MB | — | 0.4% | 403,721 | 224.11/s | 30.0 min |
| V2 | 2.39 GB | 10,136,740 | 8.88 MB | — | 0.4% | 460,597 | 255.38/s | 30.1 min |
| V3 | 1.87 GB | 7,926,884 | 8.91 MB | — | 0.5% | 360,149 | 199.75/s | 30.1 min |

## 🧨 Cenários críticos (por cenário + versão)

| Cenário | Versão | NDJSON size | NDJSON points | Parquet cache size | Parquet rows | http_reqs (summary) | Duração estimada |
|---|---|---|---|---|---|---|---|
| catastrofe | V1 | 354.51 MB | 1,381,184 | 7.51 MB | — | 62,710 | 13.0 min |
| catastrofe | V2 | 355.08 MB | 1,410,638 | 7.51 MB | — | 64,049 | 13.0 min |
| catastrofe | V3 | 213.01 MB | 833,360 | 6.52 MB | — | 37,809 | 13.0 min |
| degradacao | V1 | 319.35 MB | 1,256,004 | 7.43 MB | — | 57,020 | 13.0 min |
| degradacao | V2 | 450.42 MB | 1,784,442 | 7.90 MB | — | 81,040 | 13.0 min |
| degradacao | V3 | 268.17 MB | 1,054,726 | 7.13 MB | — | 47,871 | 13.0 min |
| indisponibilidade | V1 | 412.37 MB | 1,557,144 | 7.61 MB | — | 70,730 | 9.0 min |
| indisponibilidade | V2 | 449.42 MB | 1,747,312 | 7.55 MB | — | 79,374 | 9.0 min |
| indisponibilidade | V3 | 191.70 MB | 724,750 | 5.96 MB | — | 32,894 | 9.0 min |
| normal | V1 | 102.07 MB | 391,493 | 2.69 MB | — | 19,545 | 5.0 min |
| normal | V2 | 102.09 MB | 391,573 | 2.68 MB | — | 19,549 | 5.0 min |
| normal | V3 | 102.10 MB | 391,633 | 2.67 MB | — | 19,552 | 5.0 min |
| rajadas | V1 | 518.74 MB | 2,037,446 | 8.02 MB | — | 92,540 | 13.1 min |
| rajadas | V2 | 515.27 MB | 2,046,444 | 8.08 MB | — | 92,949 | 13.1 min |
| rajadas | V3 | 394.64 MB | 1,555,602 | 7.88 MB | — | 70,638 | 13.1 min |

## ℹ️ Notas de interpretação

- **NDJSON points**: conta quantas linhas contêm `"type":"Point"` (métricas do k6).
- **Parquet cache**: é um *cache de leitura* gerado pelo `FastK6Loader` para acelerar execuções subsequentes.
- **Parquet/NDJSON**: razão de tamanho (quanto menor, melhor). Isso varia com compressão e distribuição de dados.
- **Duração estimada**: calculada como `http_reqs.count / http_reqs.rate` a partir do summary do k6.

