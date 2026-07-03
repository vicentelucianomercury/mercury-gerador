"""
fundos_config_v2.py — Mercury Wealth Management
================================================
Fontes:
- Lista de Fundos Aprovados (Classe + Subclasse) — enviada 02/07/2026
- Cadastro Quantum (COMPARACAO 02/07/2026): D+ resgate, taxa adm
- Matriz Editavel: táticas e bandas por subclasse

Estrutura de 2 níveis:
  CLASSE (agrupamento do relatório) → SUBCLASSE (alocação granular)
"""

# ─── SUBCLASSES (nível de alocação — 10, conforme Matriz Editavel) ───────────
SUBCLASSES = [
    "Caixa",
    "Crédito Corporativo",
    "Crédito Estruturado",
    "Renda Fixa Inflação/Pré",
    "Multimercado",
    "Offshore USD",
    "Offshore BRL",
    "Renda Variável",
    "Imobiliários",
    "Private Equity/VC",
]
# Compatibilidade com código existente
CLASSES = SUBCLASSES
CLASSES_RF = ["Caixa", "Crédito Corporativo", "Crédito Estruturado",
              "Renda Fixa Inflação/Pré"]

# ─── CLASSE de relatório (agrupamento, conforme Lista de Fundos Aprovados) ───
SUBCLASSE_PARA_CLASSE = {
    "Caixa":                   "Caixa",
    "Crédito Corporativo":     "Renda Fixa",
    "Crédito Estruturado":     "Renda Fixa",
    "Renda Fixa Inflação/Pré": "Renda Fixa",
    "Multimercado":            "Multimercados",
    "Offshore USD":            "Offshore USD",
    "Offshore BRL":            "Offshore BRL",
    "Renda Variável":          "Renda Variável",
    "Imobiliários":            "Imobiliários",
    "Private Equity/VC":       "Private Equity/VC",
}
# Ordem de exibição das classes no relatório
CLASSES_RELATORIO = ["Caixa", "Renda Fixa", "Multimercados", "Offshore BRL",
                     "Offshore USD", "Renda Variável", "Imobiliários",
                     "Private Equity/VC"]

# ─── FUNDOS APROVADOS ────────────────────────────────────────────────────────
# liquidez: prazos do cadastro Quantum (COMPARACAO 02/07/2026)
#   conversao      = Conversão para Resgate
#   disponibilizacao = Disponibilização do Resgate (o dinheiro cai)
#   dias_liq       = número p/ agrupamento de liquidez (disponibilização;
#                    'du' tratado como dias úteis, usado o número)
#   None = NÃO INFORMADO no cadastro — confirmar com a gestora
FUNDOS = [
    {"nome_quantum": "BTG PACTUAL DIGITAL TESOURO SELIC FIF RENDA FIXA SIMPLES",
     "cnpj": "29.562.673/0001-17", "classe": "Caixa",
     "conversao": "D+0", "disponibilizacao": "D+0", "dias_liq": 0,
     "taxa_adm": 0.00},
    {"nome_quantum": "CAPITÂNIA REIT MASTER RESP LIMITADA FIF CIC MULTIMERCADO",
     "cnpj": "18.447.898/0001-06", "classe": "Imobiliários",
     "conversao": "D+0", "disponibilizacao": "D+2 du", "dias_liq": 2,
     "taxa_adm": 0.00},
    {"nome_quantum": "GAMA PEARL DIVER GLOBAL FLOATING INCOME BRL INVESTIMENTO NO EXTERIOR RESP LIMITADA FIF CIC",
     "cnpj": "51.835.937/0001-18", "classe": "Offshore BRL",
     "conversao": "D+30", "disponibilizacao": "D+37", "dias_liq": 37,
     "taxa_adm": 0.65},
    {"nome_quantum": "GAMA SCHRODER GAIA CONTOUR TECH EQUITY LONG & SHORT BRL INVESTIMENTO NO EXTERIOR RESP LIMITADA FIF CIC MULTIMERCADO",
     "cnpj": "35.744.790/0001-02", "classe": "Offshore BRL",
     "conversao": "D+2 du", "disponibilizacao": "D+5 du", "dias_liq": 5,
     "taxa_adm": 0.75},
    {"nome_quantum": "ITAÚ DEBÊNTURES INCENTIVADAS CDI DIST RESP LIMITADA FIF CIC FI INFRA RENDA FIXA CRÉDITO PRIVADO",
     "cnpj": "45.512.145/0001-00", "classe": "Crédito Corporativo",
     "conversao": "D+21 du", "disponibilizacao": "D+22 du", "dias_liq": 22,
     "taxa_adm": 0.55},
    {"nome_quantum": "M MACRO FIF CIC MULTIMERCADO",
     "cnpj": "14.796.095/0001-06", "classe": "Multimercado",
     "conversao": "D+30", "disponibilizacao": "D+31", "dias_liq": 31,
     "taxa_adm": 0.67},
    {"nome_quantum": "MCA II RESP LIMITADA FICFIDC 1",
     "cnpj": "23.711.364/0001-85", "classe": "Crédito Estruturado",
     "conversao": None, "disponibilizacao": None, "dias_liq": None,
     "taxa_adm": 1.02},
    {"nome_quantum": "MHX FICFIDC 1",
     "cnpj": "37.970.369/0001-37", "classe": "Crédito Estruturado",
     "conversao": None, "disponibilizacao": None, "dias_liq": None,
     "taxa_adm": 1.15},
    {"nome_quantum": "MORE CRÉDITO RESP LIMITADA FICFIDC 1",
     "cnpj": "15.585.932/0001-10", "classe": "Crédito Estruturado",
     "conversao": None, "disponibilizacao": None, "dias_liq": None,
     "taxa_adm": 1.22},
    {"nome_quantum": "NEST IBOVESPA ENHANCED RESP LIMITADA FIF AÇÕES",
     "cnpj": "41.215.368/0001-54", "classe": "Renda Variável",
     "conversao": "D+1 du", "disponibilizacao": "D+3 du", "dias_liq": 3,
     "taxa_adm": 0.75},
    {"nome_quantum": "SPARTA DEBÊNTURES INCENTIVADAS INFLAÇÃO RESP LIMITADA FIF CIC FI INFRA RENDA FIXA",
     "cnpj": "39.959.025/0001-52", "classe": "Renda Fixa Inflação/Pré",
     "conversao": "D+30", "disponibilizacao": "D+32", "dias_liq": 32,
     "taxa_adm": 0.04},
    {"nome_quantum": "M BRZ RESP LIMITADA FICFIDC 1",
     "cnpj": "57.391.121/0001-29", "classe": "Crédito Estruturado",
     "conversao": None, "disponibilizacao": None, "dias_liq": None,
     "taxa_adm": None},
    {"nome_quantum": "M8 CREDIT OPPORTUNITIES FICFIDC 1",
     "cnpj": "26.841.302/0001-86", "classe": "Crédito Estruturado",
     "conversao": None, "disponibilizacao": None, "dias_liq": None,
     "taxa_adm": 0.97},
]

def fundos_por_classe(subclasse: str) -> list[dict]:
    """Fundos de uma subclasse (nome mantido por compatibilidade)."""
    return [f for f in FUNDOS if f["classe"] == subclasse]

def fundos_por_classe_relatorio(classe: str) -> list[dict]:
    """Fundos de uma CLASSE de relatório (agrupa subclasses)."""
    return [f for f in FUNDOS
            if SUBCLASSE_PARA_CLASSE.get(f["classe"]) == classe]

def subclasses_da_classe(classe: str) -> list[str]:
    return [s for s in SUBCLASSES if SUBCLASSE_PARA_CLASSE.get(s) == classe]

# Compat: LIQUIDEZ_DIAS (agora derivado do cadastro real)
LIQUIDEZ_DIAS = {f["nome_quantum"]: f["dias_liq"] for f in FUNDOS}

# ─── TÁTICA por subclasse (Matriz Editavel) ──────────────────────────────────
PERFIS_TATICA = {
    "Conservador": {
        "Caixa": 0.185, "Crédito Corporativo": 0.150, "Crédito Estruturado": 0.350,
        "Renda Fixa Inflação/Pré": 0.150, "Multimercado": 0.150,
        "Offshore USD": 0.000, "Offshore BRL": 0.000, "Renda Variável": 0.000,
        "Imobiliários": 0.015, "Private Equity/VC": 0.000},
    "Moderado": {
        "Caixa": 0.060, "Crédito Corporativo": 0.125, "Crédito Estruturado": 0.350,
        "Renda Fixa Inflação/Pré": 0.175, "Multimercado": 0.175,
        "Offshore USD": 0.000, "Offshore BRL": 0.025, "Renda Variável": 0.075,
        "Imobiliários": 0.015, "Private Equity/VC": 0.000},
    "Balanceado": {
        "Caixa": 0.050, "Crédito Corporativo": 0.000, "Crédito Estruturado": 0.350,
        "Renda Fixa Inflação/Pré": 0.175, "Multimercado": 0.200,
        "Offshore USD": 0.000, "Offshore BRL": 0.050, "Renda Variável": 0.150,
        "Imobiliários": 0.025, "Private Equity/VC": 0.000},
    "Crescimento": {
        "Caixa": 0.020, "Crédito Corporativo": 0.000, "Crédito Estruturado": 0.250,
        "Renda Fixa Inflação/Pré": 0.200, "Multimercado": 0.150,
        "Offshore USD": 0.000, "Offshore BRL": 0.100, "Renda Variável": 0.200,
        "Imobiliários": 0.050, "Private Equity/VC": 0.030},
    "Sofisticado": {
        "Caixa": 0.000, "Crédito Corporativo": 0.000, "Crédito Estruturado": 0.195,
        "Renda Fixa Inflação/Pré": 0.250, "Multimercado": 0.100,
        "Offshore USD": 0.000, "Offshore BRL": 0.080, "Renda Variável": 0.250,
        "Imobiliários": 0.075, "Private Equity/VC": 0.050},
}

PERFIS_BANDAS = {
    "Conservador": {
        "Caixa": (0.10,0.50), "Crédito Corporativo": (0.10,0.25),
        "Crédito Estruturado": (0.10,0.35), "Renda Fixa Inflação/Pré": (0.10,0.25),
        "Multimercado": (0.15,0.25), "Offshore USD": (0.0,0.0),
        "Offshore BRL": (0.0,0.0), "Renda Variável": (0.0,0.0),
        "Imobiliários": (0.0,0.05), "Private Equity/VC": (0.0,0.0)},
    "Moderado": {
        "Caixa": (0.05,0.35), "Crédito Corporativo": (0.10,0.25),
        "Crédito Estruturado": (0.10,0.35), "Renda Fixa Inflação/Pré": (0.10,0.25),
        "Multimercado": (0.20,0.30), "Offshore USD": (0.0,0.05),
        "Offshore BRL": (0.0,0.02), "Renda Variável": (0.0,0.10),
        "Imobiliários": (0.0,0.10), "Private Equity/VC": (0.0,0.0)},
    "Balanceado": {
        "Caixa": (0.0,0.25), "Crédito Corporativo": (0.10,0.25),
        "Crédito Estruturado": (0.10,0.35), "Renda Fixa Inflação/Pré": (0.10,0.25),
        "Multimercado": (0.20,0.35), "Offshore USD": (0.025,0.10),
        "Offshore BRL": (0.0,0.075), "Renda Variável": (0.05,0.20),
        "Imobiliários": (0.0,0.10), "Private Equity/VC": (0.0,0.0)},
    "Crescimento": {
        "Caixa": (0.0,0.20), "Crédito Corporativo": (0.05,0.25),
        "Crédito Estruturado": (0.10,0.25), "Renda Fixa Inflação/Pré": (0.10,0.25),
        "Multimercado": (0.25,0.40), "Offshore USD": (0.025,0.15),
        "Offshore BRL": (0.0,0.10), "Renda Variável": (0.05,0.30),
        "Imobiliários": (0.025,0.125), "Private Equity/VC": (0.0,0.03)},
    "Sofisticado": {
        "Caixa": (0.0,0.15), "Crédito Corporativo": (0.0,0.15),
        "Crédito Estruturado": (0.10,0.35), "Renda Fixa Inflação/Pré": (0.05,0.30),
        "Multimercado": (0.25,0.40), "Offshore USD": (0.05,0.20),
        "Offshore BRL": (0.0,0.15), "Renda Variável": (0.10,0.40),
        "Imobiliários": (0.05,0.15), "Private Equity/VC": (0.0,0.05)},
}

PERFIS_METAS = {
    "Conservador": {"objetivo": "CDI + 2%", "vol": 0.02},
    "Moderado":    {"objetivo": "CDI + 2%", "vol": 0.02},
    "Balanceado":  {"objetivo": "CDI + 3%", "vol": 0.03},
    "Crescimento": {"objetivo": "CDI + 5%", "vol": 0.05},
    "Sofisticado": {"objetivo": "CDI + 6%", "vol": 0.06},
}

# ─── IDENTIDADE VISUAL MERCURY ───────────────────────────────────────────────
MERCURY_GRAFITE   = "#231f20"
MERCURY_TEAL      = "#1d7490"
MERCURY_CINZA     = "#6d6e71"
MERCURY_CINZA_CLARO = "#bcbdc0"


# ─── Override em tempo de execução (matriz vinda do Excel) ───────────────────
# O app chama aplicar_matriz(cfg) quando o usuário sobe e CONFIRMA a planilha
# da matriz (matriz_loader.MatrizConfig). Os geradores (gerar_pdf/gerar_ppt)
# importam FUNDOS / fundos_por_classe / LIQUIDEZ_DIAS deste módulo em tempo de
# chamada; a mutação in-place garante que todos enxerguem a matriz ativa.
# Sem planilha, valem os valores padrão acima (fallback).
#
# Divisão de responsabilidade (decisão do comitê, jul/2026):
#   - Da PLANILHA: quais fundos existem, CNPJ, classe, táticas, bandas, metas.
#   - Do CÓDIGO  : dados cadastrais/técnicos (D+ de resgate, conversão,
#     disponibilização, taxa adm) — mesclados por CNPJ (fallback: nome).
#     Fundo novo sem cadastro fica com None (o PDF exibe "a confirmar").

import re as _re
import unicodedata as _ud

_CAMPOS_CADASTRAIS = ("conversao", "disponibilizacao", "dias_liq", "taxa_adm")

_DEFAULTS = {
    "FUNDOS": [dict(f) for f in FUNDOS],
    "PERFIS_TATICA": {p: dict(v) for p, v in PERFIS_TATICA.items()},
    "PERFIS_BANDAS": {p: dict(v) for p, v in PERFIS_BANDAS.items()},
    "PERFIS_METAS":  {p: dict(v) for p, v in PERFIS_METAS.items()},
}

FONTE_MATRIZ = "padrão do sistema"


def _norm_nome(s):
    s = _ud.normalize("NFKD", str(s or ""))
    s = "".join(ch for ch in s if not _ud.combining(ch))
    return _re.sub(r"\s+", " ", s).strip().upper()


def _so_digitos(s):
    return _re.sub(r"\D", "", str(s or ""))


def _cadastro_do_fundo(nome, cnpj):
    """Localiza o cadastro técnico no padrão do código (CNPJ; senão nome
    normalizado por prefixo, p/ nomes truncados)."""
    cd = _so_digitos(cnpj)
    if cd:
        for f in _DEFAULTS["FUNDOS"]:
            if _so_digitos(f.get("cnpj")) == cd:
                return f
    n = _norm_nome(nome)
    if len(n) >= 5:
        cands = [f for f in _DEFAULTS["FUNDOS"]
                 if _norm_nome(f["nome_quantum"]).startswith(n)
                 or n.startswith(_norm_nome(f["nome_quantum"]))]
        if len(cands) == 1:
            return cands[0]
    return None


def _recalcular_liquidez():
    LIQUIDEZ_DIAS.clear()
    LIQUIDEZ_DIAS.update({f["nome_quantum"]: f.get("dias_liq") for f in FUNDOS})


def aplicar_matriz(cfg) -> None:
    """Ativa a configuração lida da planilha. Metas com campo vazio caem no
    padrão do código, campo a campo."""
    global FONTE_MATRIZ
    novos = []
    for f in cfg.fundos:
        item = dict(f)
        cad = _cadastro_do_fundo(f.get("nome_quantum"), f.get("cnpj"))
        for campo in _CAMPOS_CADASTRAIS:
            item.setdefault(campo, cad.get(campo) if cad else None)
        novos.append(item)
    FUNDOS[:] = novos
    _recalcular_liquidez()

    PERFIS_TATICA.clear(); PERFIS_TATICA.update(cfg.tatica)
    PERFIS_BANDAS.clear(); PERFIS_BANDAS.update(cfg.bandas)
    PERFIS_METAS.clear()
    for p in cfg.tatica:
        meta = dict(cfg.metas.get(p) or {})
        padrao = _DEFAULTS["PERFIS_METAS"].get(p, {})
        if not meta.get("objetivo"):
            meta["objetivo"] = padrao.get("objetivo", "—")
        if meta.get("vol") is None:
            meta["vol"] = padrao.get("vol")
        PERFIS_METAS[p] = meta
    FONTE_MATRIZ = f"planilha: {cfg.origem}"


def restaurar_padrao() -> None:
    """Volta aos valores fixos deste módulo."""
    global FONTE_MATRIZ
    FUNDOS[:] = [dict(f) for f in _DEFAULTS["FUNDOS"]]
    _recalcular_liquidez()
    PERFIS_TATICA.clear(); PERFIS_TATICA.update(
        {p: dict(v) for p, v in _DEFAULTS["PERFIS_TATICA"].items()})
    PERFIS_BANDAS.clear(); PERFIS_BANDAS.update(
        {p: dict(v) for p, v in _DEFAULTS["PERFIS_BANDAS"].items()})
    PERFIS_METAS.clear(); PERFIS_METAS.update(
        {p: dict(v) for p, v in _DEFAULTS["PERFIS_METAS"].items()})
    FONTE_MATRIZ = "padrão do sistema"
