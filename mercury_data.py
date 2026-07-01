"""
mercury_data.py — Mercury Wealth Management
============================================
Fonte de dados: Excel exportado pela API do Quantum Axis.
Formato esperado: aba "Quantum Axis" com colunas
  [Nome do Ativo | Data | Cota/Preço de Fechamento Ajustados]

Atualização: mensal/trimestral via API Quantum → atualiza QUANTUM_FILE.
"""

import math
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import openpyxl
import pandas as pd

# ─── Caminho do arquivo Quantum ───────────────────────────────────────────────
# Pode ser sobrescrito via variável de ambiente QUANTUM_FILE
QUANTUM_FILE = Path(os.environ.get(
    "QUANTUM_FILE",
    Path(__file__).parent / "data" / "quantum.xlsx"
))


# ─── Leitura e cache ──────────────────────────────────────────────────────────

_cache: dict = {}

def _load_series(filepath: Path = QUANTUM_FILE) -> dict[str, list[tuple[date, float]]]:
    """Lê o Excel da Quantum e retorna dict nome → [(data, cota), ...]."""
    key = str(filepath)
    if key in _cache:
        return _cache[key]

    wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
    ws = wb.active  # primeira aba ou "Quantum Axis"
    for s in wb.sheetnames:
        if "quantum" in s.lower():
            ws = wb[s]
            break

    series: dict[str, list] = defaultdict(list)
    for row in ws.iter_rows(min_row=2, values_only=True):
        nome, data_val, cota = row[0], row[1], row[2]
        if not (nome and data_val and isinstance(cota, (int, float))):
            continue
        if isinstance(data_val, datetime):
            data_val = data_val.date()
        elif isinstance(data_val, date):
            pass
        else:
            continue
        series[str(nome).strip()].append((data_val, float(cota)))

    # Ordenar cada série por data
    for nome in series:
        series[nome].sort(key=lambda x: x[0])

    wb.close()
    _cache[key] = dict(series)
    return _cache[key]


# ─── Funções de cálculo ───────────────────────────────────────────────────────

def _find_closest(dados: list[tuple[date, float]], alvo: date) -> tuple[date, float] | None:
    """Retorna o ponto mais próximo da data alvo (tolerância 45 dias)."""
    if not dados:
        return None
    closest = min(dados, key=lambda x: abs((x[0] - alvo).days))
    if abs((closest[0] - alvo).days) > 45:
        return None
    return closest


def _retorno_meses(dados: list, meses: int) -> float | None:
    """Retorno acumulado nos últimos N meses."""
    if not dados:
        return None
    ultima_data, ultima_cota = dados[-1]
    m = ultima_data.month - (meses % 12)
    y = ultima_data.year - (meses // 12)
    if m <= 0:
        m += 12
        y -= 1
    try:
        alvo = date(y, m, ultima_data.day)
    except ValueError:
        import calendar
        alvo = date(y, m, calendar.monthrange(y, m)[1])
    ref = _find_closest(dados, alvo)
    if ref is None:
        return None
    return (ultima_cota / ref[1]) - 1


def _retorno_ytd(dados: list) -> float | None:
    """Retorno desde 31/dez do ano anterior."""
    if not dados:
        return None
    ultima_data, ultima_cota = dados[-1]
    alvo = date(ultima_data.year - 1, 12, 31)
    ref = _find_closest(dados, alvo)
    if ref is None or abs((ref[0] - alvo).days) > 10:
        return None
    return (ultima_cota / ref[1]) - 1


def _volatilidade_anual(dados: list, meses: int = 12) -> float | None:
    """Volatilidade anualizada (252 dias úteis) dos últimos N meses."""
    if not dados or len(dados) < 30:
        return None
    ultima_data = dados[-1][0]
    m = ultima_data.month - (meses % 12)
    y = ultima_data.year - (meses // 12)
    if m <= 0:
        m += 12
        y -= 1
    corte = date(y, m, 1)
    recente = [(d, c) for d, c in dados if d >= corte]
    if len(recente) < 20:
        return None
    rets = [(recente[i][1] / recente[i - 1][1]) - 1 for i in range(1, len(recente))]
    media = sum(rets) / len(rets)
    var = sum((r - media) ** 2 for r in rets) / len(rets)
    return math.sqrt(var * 252)


def _pct_cdi(retorno_fundo: float | None, retorno_cdi: float | None) -> float | None:
    if retorno_fundo is None or not retorno_cdi:
        return None
    return retorno_fundo / retorno_cdi


# ─── API pública ──────────────────────────────────────────────────────────────

def calcular_metricas(filepath: Path = QUANTUM_FILE) -> dict[str, dict]:
    """
    Retorna dict nome_fundo → métricas calculadas.
    Inclui benchmarks: CDI, IMA-B, IPCA, Ibovespa.
    """
    series = _load_series(filepath)

    cdi_dados = series.get("CDI", [])
    cdi_12m   = _retorno_meses(cdi_dados, 12)

    resultado = {}
    for nome, dados in series.items():
        # Filtrar linhas de disclaimer que caem como "nome"
        if len(nome) > 120 or nome.lower().startswith(("fonte:", "as info", "os val",
                                                         "fundos de", "para seus",
                                                         "qualquer", "passado")):
            continue

        r12  = _retorno_meses(dados, 12)
        r24  = _retorno_meses(dados, 24)
        r36  = _retorno_meses(dados, 36)
        ytd  = _retorno_ytd(dados)
        vol  = _volatilidade_anual(dados)
        pct  = _pct_cdi(r12, cdi_12m)

        resultado[nome] = {
            "ret_12m":   r12,
            "ret_24m":   r24,
            "ret_36m":   r36,
            "ytd":       ytd,
            "vol_12m":   vol,
            "pct_cdi":   pct,
            "data_inicio": dados[0][0] if dados else None,
            "data_fim":    dados[-1][0] if dados else None,
            "n_pontos":  len(dados),
        }

    return resultado


def metricas_fundo(nome: str, filepath: Path = QUANTUM_FILE) -> dict | None:
    """Retorna métricas de um fundo específico pelo nome exato."""
    return calcular_metricas(filepath).get(nome)


def ultima_data_atualizacao(filepath: Path = QUANTUM_FILE) -> date | None:
    """Retorna a data mais recente presente no arquivo."""
    series = _load_series(filepath)
    datas = [dados[-1][0] for dados in series.values() if dados]
    return max(datas) if datas else None


def cdi_acumulado(meses: int, filepath: Path = QUANTUM_FILE) -> float | None:
    """CDI acumulado nos últimos N meses."""
    series = _load_series(filepath)
    return _retorno_meses(series.get("CDI", []), meses)


# ─── Teste rápido ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    fp = Path(sys.argv[1]) if len(sys.argv) > 1 else QUANTUM_FILE

    if not fp.exists():
        print(f"Arquivo não encontrado: {fp}")
        print("Uso: python mercury_data.py /caminho/para/quantum.xlsx")
        sys.exit(1)

    print(f"Carregando: {fp}")
    print(f"Última atualização: {ultima_data_atualizacao(fp)}\n")

    cdi_ref = cdi_acumulado(12, fp)
    print(f"{'Fundo':<50} {'12m':>7} {'YTD':>7} {'%CDI':>7} {'Vol':>7}")
    print("-" * 80)
    for nome, m in sorted(calcular_metricas(fp).items()):
        if m["ret_12m"] is None:
            continue
        def fmt(v): return f"{v*100:.1f}%" if v is not None else "  N/D"
        print(f"{nome[:50]:<50} {fmt(m['ret_12m']):>7} {fmt(m['ytd']):>7} "
              f"{fmt(m['pct_cdi']):>7} {fmt(m['vol_12m']):>7}")
