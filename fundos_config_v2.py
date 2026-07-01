"""
fundos_config.py — Mercury Wealth Management
============================================
Fonte da lista: aba "Lista de Fundos Aprovados" (01/07/2026)
Fonte dos dados: API Quantum Axis → quantum.xlsx (atualização mensal/trimestral)

NOME_QUANTUM: nome exato como aparece no Excel da Quantum (chave de join)
CLASSE_GRANULAR: classe conforme a lista aprovada da Mercury
MACRO_CLASSE: mapeamento → 4 classes da matriz de alocação
  CDI | Renda Fixa | Multimercados | Ações
"""

# ─── FUNDOS APROVADOS ────────────────────────────────────────────────────────
# Mapeamento macro_classe é proposta — confirmar com o comitê Mercury.

FUNDOS = [
    {
        "nome_quantum":  "BTG PACTUAL DIGITAL TESOURO SELIC FIF RENDA FIXA SIMPLES",
        "cnpj":          "29.562.673/0001-17",
        "classe_granular": "Caixa",
        "macro_classe":  "CDI",
    },
    {
        "nome_quantum":  "CAPITÂNIA REIT MASTER RESP LIMITADA FIF CIC MULTIMERCADO",
        "cnpj":          "18.447.898/0001-06",
        "classe_granular": "Imobiliários",
        "macro_classe":  "Multimercados",   # ← confirmar: Multimercados ou classe própria?
    },
    {
        "nome_quantum":  "GAMA PEARL DIVER GLOBAL FLOATING INCOME BRL INVESTIMENTO NO EXTERIOR RESP LIMITADA FIF CIC",
        "cnpj":          "51.835.937/0001-18",
        "classe_granular": "Offshore BRL",
        "macro_classe":  "Multimercados",   # ← confirmar
    },
    {
        "nome_quantum":  "GAMA SCHRODER GAIA CONTOUR TECH EQUITY LONG & SHORT BRL INVESTIMENTO NO EXTERIOR RESP LIMITADA FIF CIC MULTIMERCADO",
        "cnpj":          "35.744.790/0001-02",
        "classe_granular": "Offshore BRL",
        "macro_classe":  "Multimercados",   # ← confirmar
    },
    {
        "nome_quantum":  "ITAÚ DEBÊNTURES INCENTIVADAS CDI DIST RESP LIMITADA FIF CIC FI INFRA RENDA FIXA CRÉDITO PRIVADO",
        "cnpj":          "45.512.145/0001-00",
        "classe_granular": "Crédito Corporativo",
        "macro_classe":  "Renda Fixa",
    },
    {
        "nome_quantum":  "M MACRO FIF CIC MULTIMERCADO",
        "cnpj":          "14.796.095/0001-06",
        "classe_granular": "Multimercados",
        "macro_classe":  "Multimercados",
    },
    {
        "nome_quantum":  "MCA II RESP LIMITADA FICFIDC 1",
        "cnpj":          "23.711.364/0001-85",
        "classe_granular": "Crédito Estruturado",
        "macro_classe":  "Renda Fixa",
    },
    {
        "nome_quantum":  "MHX FICFIDC 1",
        "cnpj":          "37.970.369/0001-37",
        "classe_granular": "Crédito Estruturado",
        "macro_classe":  "Renda Fixa",
    },
    {
        "nome_quantum":  "MORE CRÉDITO RESP LIMITADA FICFIDC 1",
        "cnpj":          "15.585.932/0001-10",
        "classe_granular": "Crédito Estruturado",
        "macro_classe":  "Renda Fixa",
    },
    {
        "nome_quantum":  "NEST IBOVESPA ENHANCED RESP LIMITADA FIF AÇÕES",
        "cnpj":          "41.215.368/0001-54",
        "classe_granular": "Renda Variável",
        "macro_classe":  "Ações",
    },
    {
        "nome_quantum":  "SPARTA DEBÊNTURES INCENTIVADAS INFLAÇÃO RESP LIMITADA FIF CIC FI INFRA RENDA FIXA",
        "cnpj":          "39.959.025/0001-52",
        "classe_granular": "Renda Fixa Inflação",
        "macro_classe":  "Renda Fixa",
    },
    {
        "nome_quantum":  "M BRZ RESP LIMITADA FICFIDC 1",
        "cnpj":          "57.391.121/0001-29",
        "classe_granular": "Crédito Estruturado",
        "macro_classe":  "Renda Fixa",
    },
    {
        "nome_quantum":  "M8 CREDIT OPPORTUNITIES FICFIDC 1",
        "cnpj":          "26.841.302/0001-86",
        "classe_granular": "Crédito Estruturado",
        "macro_classe":  "Renda Fixa",
    },
]

# ─── Helpers ──────────────────────────────────────────────────────────────────
def fundos_por_macro(macro_classe: str) -> list[dict]:
    return [f for f in FUNDOS if f["macro_classe"] == macro_classe]

def fundo_por_nome_quantum(nome: str) -> dict | None:
    return next((f for f in FUNDOS if f["nome_quantum"] == nome), None)

CLASSES_MACRO   = ["CDI", "Renda Fixa", "Multimercados", "Ações"]
CLASSES_GRANULARES = sorted(set(f["classe_granular"] for f in FUNDOS))


# ─── PERFIS (coluna Tática da Matriz) ────────────────────────────────────────
PERFIS_TATICA = {
    "Conservador": {"CDI": 0.30, "Renda Fixa": 0.50, "Multimercados": 0.20, "Ações": 0.00},
    "Moderado":    {"CDI": 0.15, "Renda Fixa": 0.55, "Multimercados": 0.25, "Ações": 0.05},
    "Balanceado":  {"CDI": 0.05, "Renda Fixa": 0.55, "Multimercados": 0.30, "Ações": 0.10},
    "Crescimento": {"CDI": 0.00, "Renda Fixa": 0.50, "Multimercados": 0.35, "Ações": 0.15},
    "Sofisticado": {"CDI": 0.00, "Renda Fixa": 0.35, "Multimercados": 0.40, "Ações": 0.25},
}

PERFIS_BANDAS = {
    "Conservador": {"CDI": (0.00, 0.50), "Renda Fixa": (0.45, 0.65), "Multimercados": (0.10, 0.40), "Ações": (0.00, 0.02)},
    "Moderado":    {"CDI": (0.00, 0.30), "Renda Fixa": (0.45, 0.65), "Multimercados": (0.10, 0.40), "Ações": (0.03, 0.07)},
    "Balanceado":  {"CDI": (0.00, 0.30), "Renda Fixa": (0.65, 0.70), "Multimercados": (0.05, 0.55), "Ações": (0.05, 0.15)},
    "Crescimento": {"CDI": (0.00, 0.25), "Renda Fixa": (0.35, 0.65), "Multimercados": (0.15, 0.55), "Ações": (0.10, 0.20)},
    "Sofisticado": {"CDI": (0.00, 0.15), "Renda Fixa": (0.25, 0.45), "Multimercados": (0.30, 0.50), "Ações": (0.20, 0.30)},
}

PERFIS_METAS = {
    "Conservador": {"retorno_pct_cdi": 1.07, "vol": 0.020, "p90": 1.30, "p10": 0.85},
    "Moderado":    {"retorno_pct_cdi": 1.10, "vol": 0.025, "p90": 1.43, "p10": 0.76},
    "Balanceado":  {"retorno_pct_cdi": 1.12, "vol": 0.035, "p90": 1.56, "p10": 0.65},
    "Crescimento": {"retorno_pct_cdi": 1.14, "vol": 0.050, "p90": 1.60, "p10": 0.59},
    "Sofisticado": {"retorno_pct_cdi": 1.16, "vol": 0.070, "p90": 1.80, "p10": 0.41},
}
