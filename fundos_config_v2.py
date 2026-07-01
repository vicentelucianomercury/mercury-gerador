"""
fundos_config.py — Mercury Wealth Management
=============================================
Fonte: Cópia_de_Matriz_atual_v2.xlsx, aba "MATRIZ"
Coluna utilizada: "Tática" (coluna Base na planilha) — posição atual da Mercury.

Estrutura de classes conforme a matriz:
  CDI | Renda Fixa | Multimercados | Ações
"""

# ─── TÁTICA: alocação central por perfil (coluna "Tática" da matriz) ─────────
PERFIS_TATICA = {
    "Conservador": {
        "CDI":          0.30,
        "Renda Fixa":   0.50,
        "Multimercados":0.20,
        "Ações":        0.00,
    },
    "Moderado": {
        "CDI":          0.15,
        "Renda Fixa":   0.55,
        "Multimercados":0.25,
        "Ações":        0.05,
    },
    "Balanceado": {
        "CDI":          0.05,
        "Renda Fixa":   0.55,
        "Multimercados":0.30,
        "Ações":        0.10,
    },
    "Crescimento": {
        "CDI":          0.00,
        "Renda Fixa":   0.50,
        "Multimercados":0.35,
        "Ações":        0.15,
    },
    "Sofisticado": {
        "CDI":          0.00,
        "Renda Fixa":   0.35,
        "Multimercados":0.40,
        "Ações":        0.25,
    },
}

# ─── BANDAS min / max por perfil ─────────────────────────────────────────────
# NOTA: Balanceado / Renda Fixa tem min=65% enquanto a tática é 55%.
# Provável inconsistência na planilha — confirmar com o time Mercury.
PERFIS_BANDAS = {
    "Conservador": {
        "CDI":          {"min": 0.00, "max": 0.50},
        "Renda Fixa":   {"min": 0.45, "max": 0.65},
        "Multimercados":{"min": 0.10, "max": 0.40},
        "Ações":        {"min": 0.00, "max": 0.02},
    },
    "Moderado": {
        "CDI":          {"min": 0.00, "max": 0.30},
        "Renda Fixa":   {"min": 0.45, "max": 0.65},
        "Multimercados":{"min": 0.10, "max": 0.40},
        "Ações":        {"min": 0.03, "max": 0.07},
    },
    "Balanceado": {
        "CDI":          {"min": 0.00, "max": 0.30},
        "Renda Fixa":   {"min": 0.65, "max": 0.70},  # ← ATENÇÃO: min > tática (55%)
        "Multimercados":{"min": 0.05, "max": 0.55},
        "Ações":        {"min": 0.05, "max": 0.15},
    },
    "Crescimento": {
        "CDI":          {"min": 0.00, "max": 0.25},
        "Renda Fixa":   {"min": 0.35, "max": 0.65},
        "Multimercados":{"min": 0.15, "max": 0.55},
        "Ações":        {"min": 0.10, "max": 0.20},
    },
    "Sofisticado": {
        "CDI":          {"min": 0.00, "max": 0.15},
        "Renda Fixa":   {"min": 0.25, "max": 0.45},
        "Multimercados":{"min": 0.30, "max": 0.50},
        "Ações":        {"min": 0.20, "max": 0.30},
    },
}

# ─── METAS DE DESEMPENHO (seção "Estatísticas" da matriz) ────────────────────
PERFIS_METAS = {
    "Conservador": {"retorno_pct_cdi": 1.07, "vol":  0.020, "p90": 1.30, "p10": 0.85},
    "Moderado":    {"retorno_pct_cdi": 1.10, "vol":  0.025, "p90": 1.43, "p10": 0.76},
    "Balanceado":  {"retorno_pct_cdi": 1.12, "vol":  0.035, "p90": 1.56, "p10": 0.65},
    "Crescimento": {"retorno_pct_cdi": 1.14, "vol":  0.050, "p90": 1.60, "p10": 0.59},
    "Sofisticado": {"retorno_pct_cdi": 1.16, "vol":  0.070, "p90": 1.80, "p10": 0.41},
}

CLASSES_ORDEM = ["CDI", "Renda Fixa", "Multimercados", "Ações"]
PERFIS_LISTA  = ["Conservador", "Moderado", "Balanceado", "Crescimento", "Sofisticado"]

# ─── FUNDOS POR CLASSE ────────────────────────────────────────────────────────
# PENDENTE: lista oficial de fundos da Mercury por classe.
# Os fundos abaixo são referência da carteira Lauro Eduardo — substituir.
FUNDOS_POR_CLASSE = {
    "CDI": [
        {"cnpj": "30.509.221/0001-50", "nome": "V8 Cash FIC FIRF",          "tipo": "fundo_cvm"},
        {"cnpj": "46.098.897/0001-39", "nome": "Occam Liquidez FIC FIF RF", "tipo": "fundo_cvm"},
    ],
    "Renda Fixa": [
        {"cnpj": "53.095.152/0001-81", "nome": "XP Juros Ativos CDI Deb. Incentivadas FI Infra RF", "tipo": "fundo_cvm"},
        {"cnpj": "19.418.031/0001-95", "nome": "Icatu Vanguarda Pré-Fixado FIF CI RF",              "tipo": "fundo_cvm"},
        {"cnpj": "22.003.930/0001-31", "nome": "XP Crédito Estruturado 120 FIC FIM CP",             "tipo": "fundo_cvm"},
        {"cnpj": "50.716.952/0001-84", "nome": "M8 Credit Advanced FIC FIDC",
         "tipo": "fidc", "benchmark_ref": "CDI", "benchmark_pct": 1.14},
    ],
    "Multimercados": [
        {"cnpj": "48.997.077/0001-04", "nome": "Genoa Capital Sagres I FIF CIC Multimercado", "tipo": "fundo_cvm"},
        {"cnpj": "32.240.069/0001-89", "nome": "AZ Quest Advisory Total Return FIC FIF MM",   "tipo": "fundo_cvm"},
    ],
    "Ações": [
        # PENDENTE: fundos de ações Mercury
    ],
}
