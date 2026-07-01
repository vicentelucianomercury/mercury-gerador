"""
fundos_config_v2.py — Mercury Wealth Management
================================================
Fonte: Matriz Editavel + Lista de Fundos Aprovados
Classes: 10 granulares (conforme Matriz Editavel)
"""

# ─── CLASSES (ordem de exibição) ─────────────────────────────────────────────
# Agrupamento visual "Renda Fixa" = Caixa + Cred Corp + Cred Est + RF Inflação/Pré
CLASSES = [
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

# Classes que compõem o bloco "Renda Fixa" (só para agrupamento visual)
CLASSES_RF = ["Caixa", "Crédito Corporativo", "Crédito Estruturado", "Renda Fixa Inflação/Pré"]

# ─── FUNDOS APROVADOS ────────────────────────────────────────────────────────
FUNDOS = [
    {"nome_quantum": "BTG PACTUAL DIGITAL TESOURO SELIC FIF RENDA FIXA SIMPLES",
     "cnpj": "29.562.673/0001-17", "classe": "Caixa"},
    {"nome_quantum": "CAPITÂNIA REIT MASTER RESP LIMITADA FIF CIC MULTIMERCADO",
     "cnpj": "18.447.898/0001-06", "classe": "Imobiliários"},
    {"nome_quantum": "GAMA PEARL DIVER GLOBAL FLOATING INCOME BRL INVESTIMENTO NO EXTERIOR RESP LIMITADA FIF CIC",
     "cnpj": "51.835.937/0001-18", "classe": "Offshore BRL"},
    {"nome_quantum": "GAMA SCHRODER GAIA CONTOUR TECH EQUITY LONG & SHORT BRL INVESTIMENTO NO EXTERIOR RESP LIMITADA FIF CIC MULTIMERCADO",
     "cnpj": "35.744.790/0001-02", "classe": "Offshore BRL"},
    {"nome_quantum": "ITAÚ DEBÊNTURES INCENTIVADAS CDI DIST RESP LIMITADA FIF CIC FI INFRA RENDA FIXA CRÉDITO PRIVADO",
     "cnpj": "45.512.145/0001-00", "classe": "Crédito Corporativo"},
    {"nome_quantum": "M MACRO FIF CIC MULTIMERCADO",
     "cnpj": "14.796.095/0001-06", "classe": "Multimercado"},
    {"nome_quantum": "MCA II RESP LIMITADA FICFIDC 1",
     "cnpj": "23.711.364/0001-85", "classe": "Crédito Estruturado"},
    {"nome_quantum": "MHX FICFIDC 1",
     "cnpj": "37.970.369/0001-37", "classe": "Crédito Estruturado"},
    {"nome_quantum": "MORE CRÉDITO RESP LIMITADA FICFIDC 1",
     "cnpj": "15.585.932/0001-10", "classe": "Crédito Estruturado"},
    {"nome_quantum": "NEST IBOVESPA ENHANCED RESP LIMITADA FIF AÇÕES",
     "cnpj": "41.215.368/0001-54", "classe": "Renda Variável"},
    {"nome_quantum": "SPARTA DEBÊNTURES INCENTIVADAS INFLAÇÃO RESP LIMITADA FIF CIC FI INFRA RENDA FIXA",
     "cnpj": "39.959.025/0001-52", "classe": "Renda Fixa Inflação/Pré"},
    {"nome_quantum": "M BRZ RESP LIMITADA FICFIDC 1",
     "cnpj": "57.391.121/0001-29", "classe": "Crédito Estruturado"},
    {"nome_quantum": "M8 CREDIT OPPORTUNITIES FICFIDC 1",
     "cnpj": "26.841.302/0001-86", "classe": "Crédito Estruturado"},
]

def fundos_por_classe(classe: str) -> list[dict]:
    return [f for f in FUNDOS if f["classe"] == classe]

# ─── TÁTICA (coluna Tática da Matriz Editavel) ───────────────────────────────
PERFIS_TATICA = {
    "Conservador": {
        "Caixa":                  0.185,
        "Crédito Corporativo":    0.150,
        "Crédito Estruturado":    0.350,
        "Renda Fixa Inflação/Pré":0.150,
        "Multimercado":           0.150,
        "Offshore USD":           0.000,
        "Offshore BRL":           0.000,
        "Renda Variável":         0.000,
        "Imobiliários":           0.015,
        "Private Equity/VC":      0.000,
    },
    "Moderado": {
        "Caixa":                  0.060,
        "Crédito Corporativo":    0.125,
        "Crédito Estruturado":    0.350,
        "Renda Fixa Inflação/Pré":0.175,
        "Multimercado":           0.175,
        "Offshore USD":           0.000,
        "Offshore BRL":           0.025,
        "Renda Variável":         0.075,
        "Imobiliários":           0.015,
        "Private Equity/VC":      0.000,
    },
    "Balanceado": {
        "Caixa":                  0.050,
        "Crédito Corporativo":    0.000,
        "Crédito Estruturado":    0.350,
        "Renda Fixa Inflação/Pré":0.175,
        "Multimercado":           0.200,
        "Offshore USD":           0.000,
        "Offshore BRL":           0.050,
        "Renda Variável":         0.150,
        "Imobiliários":           0.025,
        "Private Equity/VC":      0.000,
    },
    "Crescimento": {
        "Caixa":                  0.020,
        "Crédito Corporativo":    0.000,
        "Crédito Estruturado":    0.250,
        "Renda Fixa Inflação/Pré":0.200,
        "Multimercado":           0.150,
        "Offshore USD":           0.000,
        "Offshore BRL":           0.100,
        "Renda Variável":         0.200,
        "Imobiliários":           0.050,
        "Private Equity/VC":      0.030,
    },
    "Sofisticado": {
        "Caixa":                  0.000,
        "Crédito Corporativo":    0.000,
        "Crédito Estruturado":    0.195,
        "Renda Fixa Inflação/Pré":0.250,
        "Multimercado":           0.100,
        "Offshore USD":           0.000,
        "Offshore BRL":           0.080,
        "Renda Variável":         0.250,
        "Imobiliários":           0.075,
        "Private Equity/VC":      0.050,
    },
}

# ─── BANDAS min/max (da Matriz Editavel) ─────────────────────────────────────
PERFIS_BANDAS = {
    "Conservador": {
        "Caixa":                  (0.10, 0.50),
        "Crédito Corporativo":    (0.10, 0.25),
        "Crédito Estruturado":    (0.10, 0.35),
        "Renda Fixa Inflação/Pré":(0.10, 0.25),
        "Multimercado":           (0.15, 0.25),
        "Offshore USD":           (0.00, 0.00),
        "Offshore BRL":           (0.00, 0.00),
        "Renda Variável":         (0.00, 0.00),
        "Imobiliários":           (0.00, 0.05),
        "Private Equity/VC":      (0.00, 0.00),
    },
    "Moderado": {
        "Caixa":                  (0.05, 0.35),
        "Crédito Corporativo":    (0.10, 0.25),
        "Crédito Estruturado":    (0.10, 0.35),
        "Renda Fixa Inflação/Pré":(0.10, 0.25),
        "Multimercado":           (0.20, 0.30),
        "Offshore USD":           (0.00, 0.05),
        "Offshore BRL":           (0.00, 0.02),
        "Renda Variável":         (0.00, 0.10),
        "Imobiliários":           (0.00, 0.10),
        "Private Equity/VC":      (0.00, 0.00),
    },
    "Balanceado": {
        "Caixa":                  (0.00, 0.25),
        "Crédito Corporativo":    (0.10, 0.25),
        "Crédito Estruturado":    (0.10, 0.35),
        "Renda Fixa Inflação/Pré":(0.10, 0.25),
        "Multimercado":           (0.20, 0.35),
        "Offshore USD":           (0.025, 0.10),
        "Offshore BRL":           (0.00, 0.075),
        "Renda Variável":         (0.05, 0.20),
        "Imobiliários":           (0.00, 0.10),
        "Private Equity/VC":      (0.00, 0.00),
    },
    "Crescimento": {
        "Caixa":                  (0.00, 0.20),
        "Crédito Corporativo":    (0.05, 0.25),
        "Crédito Estruturado":    (0.10, 0.25),
        "Renda Fixa Inflação/Pré":(0.10, 0.25),
        "Multimercado":           (0.25, 0.40),
        "Offshore USD":           (0.025, 0.15),
        "Offshore BRL":           (0.00, 0.10),
        "Renda Variável":         (0.05, 0.30),
        "Imobiliários":           (0.025, 0.125),
        "Private Equity/VC":      (0.00, 0.03),
    },
    "Sofisticado": {
        "Caixa":                  (0.00, 0.15),
        "Crédito Corporativo":    (0.00, 0.15),
        "Crédito Estruturado":    (0.10, 0.35),
        "Renda Fixa Inflação/Pré":(0.05, 0.30),
        "Multimercado":           (0.25, 0.40),
        "Offshore USD":           (0.05, 0.20),
        "Offshore BRL":           (0.00, 0.15),
        "Renda Variável":         (0.10, 0.40),
        "Imobiliários":           (0.05, 0.15),
        "Private Equity/VC":      (0.00, 0.05),
    },
}

PERFIS_METAS = {
    "Conservador": {"objetivo": "CDI + 2%", "vol": 0.02},
    "Moderado":    {"objetivo": "CDI + 2%", "vol": 0.02},
    "Balanceado":  {"objetivo": "CDI + 3%", "vol": 0.03},
    "Crescimento": {"objetivo": "CDI + 5%", "vol": 0.05},
    "Sofisticado": {"objetivo": "CDI + 6%", "vol": 0.06},
}
