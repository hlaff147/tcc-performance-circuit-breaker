#!/usr/bin/env python3
"""
Fast K6 Results Loader - Optimized for Large Files

Este módulo fornece carregamento otimizado de resultados k6 para arquivos grandes.
Usa orjson para parsing rápido, multiprocessing para paralelização,
e cache Parquet para reutilização instantânea.

Performance esperada:
- Carregamento inicial: ~5x mais rápido que json padrão
- Execuções subsequentes: instantâneo (cache Parquet)
"""

import os
import gc
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import warnings

warnings.filterwarnings('ignore')

# Imports com fallback para compatibilidade
try:
    import orjson
    USE_ORJSON = True
except ImportError:
    import json
    USE_ORJSON = False
    print("⚠️  orjson não instalado. Usando json padrão (mais lento).")
    print("   Instale com: pip install orjson")

import numpy as np
import pandas as pd

try:
    import pyarrow.parquet as pq
    USE_PARQUET = True
except ImportError:
    USE_PARQUET = False
    print("⚠️  pyarrow não instalado. Cache Parquet desabilitado.")
    print("   Instale com: pip install pyarrow")

try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False


def _parse_line(line: str) -> Optional[dict]:
    """Parse uma linha JSON de forma otimizada."""
    if '"type":"Point"' not in line:
        return None
    try:
        if USE_ORJSON:
            m = orjson.loads(line)
        else:
            import json
            m = json.loads(line)
        point_data = m['data']
        point_data['metric'] = m['metric']
        return point_data
    except (KeyError, ValueError, TypeError):
        return None


def _process_chunk(chunk: List[str]) -> List[dict]:
    """Processa um chunk de linhas em paralelo."""
    results = []
    for line in chunk:
        parsed = _parse_line(line)
        if parsed:
            results.append(parsed)
    return results


def _count_lines_fast(file_path: str) -> int:
    """Conta linhas de arquivo de forma rápida."""
    count = 0
    with open(file_path, 'rb') as f:
        for _ in f:
            count += 1
    return count


class FastK6Loader:
    """
    Carregador otimizado para resultados k6 de arquivos grandes.
    
    Features:
    - Parsing paralelo com multiprocessing
    - orjson para parsing JSON 3-10x mais rápido
    - Cache em Parquet para reutilização instantânea
    - Amostragem reservoir para arquivos muito grandes
    - Progress bar com tqdm
    """
    
    def __init__(
        self,
        results_dir: str,
        cache_dir: Optional[str] = None,
        max_workers: int = None,
        use_cache: bool = True
    ):
        """
        Args:
            results_dir: Diretório com arquivos JSON do k6
            cache_dir: Diretório para cache Parquet (default: results_dir/.cache)
            max_workers: Número de workers para processamento paralelo
            use_cache: Se True, usa/cria cache Parquet
        """
        self.results_dir = Path(results_dir)
        self.cache_dir = Path(cache_dir) if cache_dir else self.results_dir / '.cache'
        self.max_workers = max_workers or min(os.cpu_count() or 4, 8)
        self.use_cache = use_cache and USE_PARQUET
        
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, file_name: str) -> Path:
        """Retorna caminho do arquivo de cache para um dado arquivo JSON."""
        return self.cache_dir / f"{Path(file_name).stem}.parquet"
    
    def _is_cache_valid(self, json_path: Path, cache_path: Path) -> bool:
        """Verifica se cache é válido (existe e mais recente que JSON)."""
        if not cache_path.exists():
            return False
        return cache_path.stat().st_mtime > json_path.stat().st_mtime
    
    def _save_to_cache(self, df: pd.DataFrame, cache_path: Path):
        """Salva DataFrame em cache Parquet."""
        if not self.use_cache:
            return
        try:
            # Converter colunas problemáticas para tipos serializáveis
            df_cache = df.copy()
            for col in df_cache.columns:
                if df_cache[col].dtype == object:
                    # Converter dicts/lists para strings JSON
                    df_cache[col] = df_cache[col].apply(
                        lambda x: orjson.dumps(x).decode() if isinstance(x, (dict, list)) else x
                    ) if USE_ORJSON else df_cache[col].astype(str)
            df_cache.to_parquet(cache_path, engine='pyarrow', compression='snappy')
            print(f"  💾 Cache salvo: {cache_path.name}")
        except Exception as e:
            print(f"  ⚠️  Erro ao salvar cache: {e}")
    
    def _load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """Carrega DataFrame do cache Parquet."""
        if not self.use_cache or not cache_path.exists():
            return None
        try:
            df = pd.read_parquet(cache_path, engine='pyarrow')
            # Reconverter strings JSON de volta para dicts
            if 'tags' in df.columns:
                df['tags'] = df['tags'].apply(
                    lambda x: orjson.loads(x) if isinstance(x, str) and x.startswith('{') else x
                ) if USE_ORJSON else df['tags']
            return df
        except Exception as e:
            print(f"  ⚠️  Erro ao ler cache: {e}")
            return None
    
    def load_file(
        self,
        file_path: str,
        max_sample_size: int = 500000,
        chunk_size: int = 50000
    ) -> Optional[pd.DataFrame]:
        """
        Carrega um arquivo JSON do k6 de forma otimizada.
        
        Args:
            file_path: Caminho para o arquivo JSON
            max_sample_size: Máximo de pontos a carregar (reservoir sampling)
            chunk_size: Tamanho do chunk para processamento paralelo
        
        Returns:
            DataFrame com os dados processados ou None se arquivo não existe
        """
        path = Path(file_path)
        if not path.exists():
            return None
        
        cache_path = self._get_cache_path(path.name)
        
        # Tenta carregar do cache
        if self._is_cache_valid(path, cache_path):
            print(f"  ⚡ Carregando do cache: {cache_path.name}")
            df = self._load_from_cache(cache_path)
            if df is not None:
                print(f"  ✅ {len(df):,} pontos carregados do cache")
                return df
        
        # Carrega do JSON
        file_size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  📂 Processando: {path.name} ({file_size_mb:.1f} MB)")
        
        all_points = []
        use_sampling = file_size_mb > 100
        
        if use_sampling:
            print(f"  🎲 Usando reservoir sampling (máx. {max_sample_size:,} pontos)")
            all_points = self._load_with_sampling(path, max_sample_size)
        else:
            all_points = self._load_parallel(path, chunk_size)
        
        if not all_points:
            return None
        
        df = pd.DataFrame(all_points)
        print(f"  ✅ {len(df):,} pontos carregados")
        
        # Salva no cache
        self._save_to_cache(df, cache_path)
        
        # Libera memória
        del all_points
        gc.collect()
        
        return df
    
    def _load_with_sampling(
        self,
        file_path: Path,
        max_sample_size: int
    ) -> List[dict]:
        """Carrega arquivo grande com reservoir sampling."""
        all_points = []
        line_count = 0
        
        # Usa iterador para arquivo grande
        iterator = open(file_path, 'r')
        if USE_TQDM:
            iterator = tqdm(iterator, desc="  Lendo", unit=" linhas", leave=False)
        
        try:
            for line in iterator:
                parsed = _parse_line(line)
                if parsed:
                    line_count += 1
                    # Reservoir sampling
                    if len(all_points) < max_sample_size:
                        all_points.append(parsed)
                    else:
                        j = random.randint(0, line_count - 1)
                        if j < max_sample_size:
                            all_points[j] = parsed
        finally:
            if hasattr(iterator, 'close'):
                iterator.close()
        
        print(f"  📊 Processadas {line_count:,} linhas, amostradas {len(all_points):,}")
        return all_points
    
    def _load_parallel(
        self,
        file_path: Path,
        chunk_size: int
    ) -> List[dict]:
        """Carrega arquivo com processamento paralelo."""
        all_points = []
        
        # Lê arquivo em chunks e processa em paralelo
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Divide em chunks
        chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
        
        # Processa em paralelo com ThreadPoolExecutor (mais leve que Process para I/O)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(_process_chunk, chunks))
        
        # Concatena resultados
        for chunk_result in results:
            all_points.extend(chunk_result)
        
        return all_points
    
    def load_all_versions(
        self,
        pattern: str = "{version}_Completo.json",
        versions: List[str] = None,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Carrega dados de múltiplas versões em paralelo.
        
        Args:
            pattern: Padrão do nome do arquivo (use {version} como placeholder)
            versions: Lista de versões a carregar (default: V1, V2, V3)
            **kwargs: Argumentos passados para load_file()
        
        Returns:
            Dict mapeando versão -> DataFrame
        """
        versions = versions or ["V1", "V2", "V3"]
        data = {}
        
        print(f"\n🚀 Carregando {len(versions)} versões em paralelo...")
        
        for version in versions:
            file_name = pattern.format(version=version)
            file_path = self.results_dir / file_name
            
            print(f"\n📦 {version}:")
            df = self.load_file(str(file_path), **kwargs)
            
            if df is not None:
                data[version] = df
            else:
                print(f"  ⚠️  Arquivo não encontrado: {file_path}")
        
        print(f"\n✅ Carregadas {len(data)} versões com sucesso")
        return data
    
    def load_scenario(
        self,
        scenario_name: str,
        versions: List[str] = None,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Carrega dados de um cenário específico.
        
        Args:
            scenario_name: Nome do cenário (ex: 'catastrofe', 'degradacao')
            versions: Lista de versões (default: V1, V2, V3)
            **kwargs: Argumentos passados para load_file()
        
        Returns:
            Dict mapeando versão -> DataFrame
        """
        versions = versions or ["V1", "V2", "V3"]
        data = {}
        
        print(f"\n📂 Carregando cenário: {scenario_name}")
        
        for version in versions:
            file_name = f"{scenario_name}_{version}.json"
            file_path = self.results_dir / file_name
            
            if not file_path.exists():
                # Tenta no subdiretório scenarios
                file_path = self.results_dir / "scenarios" / file_name
            
            df = self.load_file(str(file_path), **kwargs)
            
            if df is not None:
                data[version] = df
                print(f"  ✅ {version}: {len(df):,} pontos")
        
        return data
    
    def clear_cache(self):
        """Limpa todos os arquivos de cache."""
        if not self.cache_dir.exists():
            return
        
        count = 0
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()
            count += 1
        
        print(f"🗑️  Cache limpo: {count} arquivos removidos")


# Funções otimizadas para estatísticas
def fast_bootstrap_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 10000,
    ci: float = 0.95,
    seed: int = 42
) -> Tuple[float, float]:
    """
    Calcula intervalo de confiança bootstrap de forma vetorizada.
    
    Usa operações NumPy vetorizadas para ~10x speedup vs loop Python.
    """
    np.random.seed(seed)
    
    # Pré-aloca arrays para amostras
    n_x, n_y = len(x), len(y)
    
    # Gera todos os índices de uma vez
    x_indices = np.random.randint(0, n_x, size=(n_bootstrap, n_x))
    y_indices = np.random.randint(0, n_y, size=(n_bootstrap, n_y))
    
    # Calcula médias de forma vetorizada
    x_means = x[x_indices].mean(axis=1)
    y_means = y[y_indices].mean(axis=1)
    
    # Diferenças
    diff_means = x_means - y_means
    
    # Percentis
    alpha = 1 - ci
    lower = np.percentile(diff_means, alpha / 2 * 100)
    upper = np.percentile(diff_means, (1 - alpha / 2) * 100)
    
    return lower, upper


def fast_cliffs_delta(x: np.ndarray, y: np.ndarray, max_sample: int = 10000) -> float:
    """
    Calcula Cliff's Delta de forma otimizada.
    
    Para amostras muito grandes, usa amostragem para evitar explosão de memória.
    """
    # Amostra se arrays forem muito grandes (evita O(n*m) memória)
    if len(x) > max_sample:
        x = np.random.choice(x, max_sample, replace=False)
    if len(y) > max_sample:
        y = np.random.choice(y, max_sample, replace=False)
    
    # Usa broadcasting para comparação vetorizada
    # Conta quantas vezes x[i] > y[j] e x[i] < y[j]
    diff = x[:, np.newaxis] - y[np.newaxis, :]
    
    n_greater = (diff > 0).sum()
    n_less = (diff < 0).sum()
    n_total = len(x) * len(y)
    
    return (n_greater - n_less) / n_total


if __name__ == "__main__":
    # Exemplo de uso
    import time
    
    print("=" * 60)
    print("  FAST K6 LOADER - Teste de Performance")
    print("=" * 60)
    
    loader = FastK6Loader(
        results_dir="k6/results",
        use_cache=True
    )
    
    start = time.time()
    data = loader.load_all_versions()
    elapsed = time.time() - start
    
    print(f"\n⏱️  Tempo total: {elapsed:.2f}s")
    
    for version, df in data.items():
        print(f"   {version}: {len(df):,} pontos")
