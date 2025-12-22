#!/usr/bin/env python3

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except Exception:
    HAS_PYARROW = False


# Observação: não usamos \b (word-boundary) porque '_' conta como caractere de palavra.
# Precisamos reconhecer nomes como "V1_Completo.json".
VERSION_RE = re.compile(r"(?i)(?:^|[^A-Za-z0-9])V(?P<num>[123])(?:[^A-Za-z0-9]|$)")
SCENARIO_RE = re.compile(r"^(?P<scenario>[a-zA-Z0-9_-]+)_V(?P<num>[123])", re.IGNORECASE)


@dataclass(frozen=True)
class FileStat:
    path: Path
    kind: str
    size_bytes: int
    version: Optional[str] = None
    scenario: Optional[str] = None
    ndjson_total_lines: Optional[int] = None
    ndjson_point_lines: Optional[int] = None
    parquet_rows: Optional[int] = None
    parquet_columns: Optional[int] = None


def _human_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    units = ["KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        size /= 1024.0
        if size < 1024.0:
            return f"{size:.2f} {unit}"
    return f"{size:.2f} PB"


def _detect_k6_results_dir(project_root: Path) -> Path:
    # Mantém a mesma lógica dos scripts .sh
    if (project_root / "k6-results").is_dir():
        return project_root / "k6-results"
    return project_root / "k6" / "results"


def _infer_version_and_scenario(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    name = file_path.name

    m_s = SCENARIO_RE.match(name)
    if m_s:
        return f"V{m_s.group('num')}", m_s.group("scenario")

    m_v = VERSION_RE.search(name)
    if m_v:
        return f"V{m_v.group('num')}".upper(), None

    return None, None


def _iter_files(base_dir: Path, patterns: Iterable[str]) -> Iterable[Path]:
    for pattern in patterns:
        yield from base_dir.rglob(pattern)


def _count_ndjson_lines(path: Path, count_point_lines: bool = True) -> Tuple[int, Optional[int]]:
    total = 0
    points = 0
    needle = b'"type":"Point"'

    with path.open("rb") as f:
        for line in f:
            total += 1
            if count_point_lines and needle in line:
                points += 1

    return total, (points if count_point_lines else None)


def _parquet_metadata(path: Path) -> Tuple[Optional[int], Optional[int]]:
    if not HAS_PYARROW:
        return None, None

    try:
        pf = pq.ParquetFile(str(path))
        meta = pf.metadata
        if meta is None:
            return None, None
        return int(meta.num_rows), int(meta.num_columns)
    except Exception:
        return None, None


def _load_summary_metrics(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_http_reqs(summary: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    metrics = summary.get("metrics", {})
    http_reqs = metrics.get("http_reqs", {})
    count = http_reqs.get("count")
    rate = http_reqs.get("rate")
    try:
        count_f = float(count) if count is not None else None
    except Exception:
        count_f = None
    try:
        rate_f = float(rate) if rate is not None else None
    except Exception:
        rate_f = None
    return count_f, rate_f


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def generate_report(project_root: Path, k6_results_dir: Path, analysis_results_dir: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Arquivos relevantes
    ndjson_files = sorted(
        [p for p in _iter_files(k6_results_dir, ["*.json"]) if p.name.endswith(".json") and not p.name.endswith("_summary.json")]
    )
    summary_files = sorted(list(_iter_files(k6_results_dir, ["*_summary.json"])))

    # Caches Parquet: tanto do cenário completo quanto dos cenários
    parquet_files = []
    for cache_dir in [k6_results_dir / ".cache", k6_results_dir / "scenarios" / ".cache"]:
        if cache_dir.is_dir():
            parquet_files.extend(sorted(cache_dir.glob("*.parquet")))

    # Estatísticas detalhadas (mas mantendo o relatório legível)
    file_stats: List[FileStat] = []

    for p in ndjson_files:
        version, scenario = _infer_version_and_scenario(p)
        size_bytes = p.stat().st_size
        total_lines, point_lines = _count_ndjson_lines(p, count_point_lines=True)
        file_stats.append(
            FileStat(
                path=p,
                kind="ndjson",
                size_bytes=size_bytes,
                version=version,
                scenario=scenario,
                ndjson_total_lines=total_lines,
                ndjson_point_lines=point_lines,
            )
        )

    for p in summary_files:
        version, scenario = _infer_version_and_scenario(p)
        size_bytes = p.stat().st_size
        file_stats.append(
            FileStat(
                path=p,
                kind="summary_json",
                size_bytes=size_bytes,
                version=version,
                scenario=scenario,
            )
        )

    for p in parquet_files:
        version, scenario = _infer_version_and_scenario(p)
        size_bytes = p.stat().st_size
        rows, cols = _parquet_metadata(p)
        file_stats.append(
            FileStat(
                path=p,
                kind="parquet_cache",
                size_bytes=size_bytes,
                version=version,
                scenario=scenario,
                parquet_rows=rows,
                parquet_columns=cols,
            )
        )

    # Totais
    def sum_bytes(kind: str) -> int:
        return sum(s.size_bytes for s in file_stats if s.kind == kind)

    total_ndjson_bytes = sum_bytes("ndjson")
    total_summary_bytes = sum_bytes("summary_json")
    total_parquet_bytes = sum_bytes("parquet_cache")

    # Tabelas
    # 1) Resumo por tipo
    resumo_rows = [
        ["NDJSON (k6 --out json)", str(len([s for s in file_stats if s.kind == 'ndjson'])), _human_bytes(total_ndjson_bytes)],
        ["Summary JSON (k6 --summary-export)", str(len([s for s in file_stats if s.kind == 'summary_json'])), _human_bytes(total_summary_bytes)],
        ["Cache Parquet (FastK6Loader)", str(len([s for s in file_stats if s.kind == 'parquet_cache'])), _human_bytes(total_parquet_bytes)],
    ]

    # 2) Cenário completo por versão (V1/V2/V3)
    complete_rows: List[List[str]] = []
    for version in ["V1", "V2", "V3"]:
        nd = next((s for s in file_stats if s.kind == "ndjson" and s.version == version and s.scenario is None and s.path.name.endswith("_Completo.json")), None)
        sm = next((s for s in file_stats if s.kind == "summary_json" and s.version == version and s.scenario is None and s.path.name.endswith("_Completo_summary.json")), None)
        pqf = next((s for s in file_stats if s.kind == "parquet_cache" and s.version == version and s.scenario is None), None)

        http_reqs_count = None
        http_reqs_rate = None
        duration_s = None
        if sm is not None:
            try:
                summary = _load_summary_metrics(sm.path)
                http_reqs_count, http_reqs_rate = _extract_http_reqs(summary)
                duration_s = _safe_div(http_reqs_count, http_reqs_rate)
            except Exception:
                pass

        parquet_ratio = None
        if nd is not None and pqf is not None and nd.size_bytes > 0:
            parquet_ratio = pqf.size_bytes / nd.size_bytes

        complete_rows.append(
            [
                version,
                _human_bytes(nd.size_bytes) if nd else "—",
                f"{nd.ndjson_point_lines:,}" if nd and nd.ndjson_point_lines is not None else "—",
                _human_bytes(pqf.size_bytes) if pqf else "—",
                f"{pqf.parquet_rows:,}" if pqf and pqf.parquet_rows is not None else "—",
                (f"{parquet_ratio*100:.1f}%" if parquet_ratio is not None else "—"),
                (f"{int(http_reqs_count):,}" if http_reqs_count is not None else "—"),
                (f"{http_reqs_rate:.2f}/s" if http_reqs_rate is not None else "—"),
                (f"{duration_s/60:.1f} min" if duration_s is not None else "—"),
            ]
        )

    # 3) Cenários críticos (agregado por cenário + versão)
    scenario_rows: List[List[str]] = []
    scenarios = sorted(
        {s.scenario for s in file_stats if s.scenario is not None and s.kind == "summary_json"}
    )

    for scenario in scenarios:
        for version in ["V1", "V2", "V3"]:
            sm = next((s for s in file_stats if s.kind == "summary_json" and s.version == version and s.scenario == scenario), None)
            nd = next((s for s in file_stats if s.kind == "ndjson" and s.version == version and s.scenario == scenario), None)
            pqf = next((s for s in file_stats if s.kind == "parquet_cache" and s.version == version and s.scenario == scenario), None)

            http_reqs_count = None
            http_reqs_rate = None
            duration_s = None
            if sm is not None:
                try:
                    summary = _load_summary_metrics(sm.path)
                    http_reqs_count, http_reqs_rate = _extract_http_reqs(summary)
                    duration_s = _safe_div(http_reqs_count, http_reqs_rate)
                except Exception:
                    pass

            scenario_rows.append(
                [
                    scenario,
                    version,
                    _human_bytes(nd.size_bytes) if nd else "—",
                    (f"{nd.ndjson_point_lines:,}" if nd and nd.ndjson_point_lines is not None else "—"),
                    (_human_bytes(pqf.size_bytes) if pqf else "—"),
                    (f"{pqf.parquet_rows:,}" if pqf and pqf.parquet_rows is not None else "—"),
                    (f"{int(http_reqs_count):,}" if http_reqs_count is not None else "—"),
                    (f"{duration_s/60:.1f} min" if duration_s is not None else "—"),
                ]
            )

    # Markdown
    rel = []
    rel.append("# 📦 Relatório de Volume de Dados (k6 + pós-processamento)\n")
    rel.append(f"> Gerado em: **{now}**")
    rel.append(f"> Projeto: **{project_root.name}**")
    rel.append(f"> k6 results dir: `{k6_results_dir}`")
    rel.append(f"> analysis_results dir: `{analysis_results_dir}`\n")

    rel.append("## ✅ Resumo\n")
    rel.append(_md_table(["Categoria", "Arquivos", "Tamanho total"], resumo_rows))

    if not HAS_PYARROW:
        rel.append("\n> ⚠️ `pyarrow` não está disponível: metadados do Parquet (rows/cols) aparecem como ‘—’.\n")

    rel.append("\n## 🧪 Cenário completo (V1/V2/V3)\n")
    rel.append(
        _md_table(
            [
                "Versão",
                "NDJSON size",
                "NDJSON points (linhas Point)",
                "Parquet cache size",
                "Parquet rows",
                "Parquet/NDJSON",
                "http_reqs (summary)",
                "http_reqs rate",
                "Duração estimada",
            ],
            complete_rows,
        )
    )

    rel.append("\n## 🧨 Cenários críticos (por cenário + versão)\n")
    rel.append(
        _md_table(
            [
                "Cenário",
                "Versão",
                "NDJSON size",
                "NDJSON points",
                "Parquet cache size",
                "Parquet rows",
                "http_reqs (summary)",
                "Duração estimada",
            ],
            scenario_rows,
        )
    )

    rel.append("\n## ℹ️ Notas de interpretação\n")
    rel.append(
        "- **NDJSON points**: conta quantas linhas contêm `\"type\":\"Point\"` (métricas do k6).\n"
        "- **Parquet cache**: é um *cache de leitura* gerado pelo `FastK6Loader` para acelerar execuções subsequentes.\n"
        "- **Parquet/NDJSON**: razão de tamanho (quanto menor, melhor). Isso varia com compressão e distribuição de dados.\n"
        "- **Duração estimada**: calculada como `http_reqs.count / http_reqs.rate` a partir do summary do k6.\n"
    )

    return "\n".join(rel) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera um relatório Markdown com volume de dados (tamanho/linhas/rows/requests) do pipeline k6 + análise."
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Raiz do projeto (default: detectado a partir do script)",
    )
    parser.add_argument(
        "--k6-results-dir",
        default=None,
        help="Diretório de resultados do k6 (default: k6-results/ ou k6/results/)",
    )
    parser.add_argument(
        "--analysis-results-dir",
        default=None,
        help="Diretório analysis_results (default: ./analysis_results)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Arquivo Markdown de saída (default: analysis_results/markdown/RELATORIO_VOLUME_DADOS.md)",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    k6_results_dir = Path(args.k6_results_dir).resolve() if args.k6_results_dir else _detect_k6_results_dir(project_root)
    analysis_results_dir = (
        Path(args.analysis_results_dir).resolve() if args.analysis_results_dir else (project_root / "analysis_results")
    )

    output_path = (
        Path(args.output).resolve()
        if args.output
        else (analysis_results_dir / "markdown" / "RELATORIO_VOLUME_DADOS.md")
    )

    try:
        analysis_results_dir.mkdir(parents=True, exist_ok=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_md = generate_report(project_root, k6_results_dir, analysis_results_dir)
        output_path.write_text(report_md, encoding="utf-8")

        print(f"OK: relatório gerado em {output_path}")
        return 0
    except Exception as e:
        # Não queremos quebrar pipelines; melhor gerar diagnóstico e sair 0 se rodar em batch.
        print(f"WARN: não foi possível gerar relatório: {e}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
