"""
gerar_pdf.py — Mercury · Relatório de Proposta (formato BTG, 13 páginas)
=========================================================================
Páginas:
 1. Capa            2. Índice           3. Resumo
 4-5. Composição    6. Rentabilidade    7. Rent. mês a mês
 8. Rent. por classe 9. Estatísticas    10. Volatilidade
 11. Liquidez       12. Sobre este material  13. Fale conosco
"""
import io
import math
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, HRFlowable, NextPageTemplate)

# ─── Paleta Mercury ───────────────────────────────────────────────────────────
AZUL_ESCURO = colors.HexColor("#12365c")
AZUL_MEDIO  = colors.HexColor("#1e63b4")
AZUL_CLARO  = colors.HexColor("#5a9cf8")
AZUL_BEBE   = colors.HexColor("#8ab6f9")
CINZA_TXT   = colors.HexColor("#555555")
CINZA_CLARO = colors.HexColor("#f5f6f8")
CINZA_LINHA = colors.HexColor("#dddddd")
VERDE       = colors.HexColor("#1b7e3c")
VERMELHO    = colors.HexColor("#c62828")

MPL_AZUL   = "#1e63b4"
MPL_AMARELO= "#f0b429"
PIE_CORES  = ["#f0b429", "#d1478c", "#4a5fdb", "#6cbd45", "#e8632a",
              "#42a5f5", "#8e24aa", "#26a69a", "#ef5350", "#795548"]

def _fmt_pct(v, dec=2):
    if v is None: return "—"
    return f"{v*100:.{dec}f}%".replace(".", ",")

def _fmt_brl(v, dec=2):
    if v is None: return "—"
    s = f"{v:,.{dec}f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

MESES_PT = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]


# ─── Template com header/footer ───────────────────────────────────────────────
class RelatorioTemplate(BaseDocTemplate):
    def __init__(self, buf, periodo_txt, gerado_txt, **kw):
        super().__init__(buf, pagesize=A4,
                         leftMargin=1.6*cm, rightMargin=1.6*cm,
                         topMargin=2.2*cm, bottomMargin=1.8*cm, **kw)
        self.periodo_txt = periodo_txt
        self.gerado_txt  = gerado_txt

        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="main")
        capa_frame = Frame(self.leftMargin, self.bottomMargin,
                           self.width, self.height, id="capa")

        self.addPageTemplates([
            PageTemplate(id="capa", frames=[capa_frame],
                         onPage=self._pagina_capa),
            PageTemplate(id="normal", frames=[frame],
                         onPage=self._pagina_normal),
        ])

    def _pagina_capa(self, canvas, doc):
        w, h = A4
        canvas.saveState()
        # Faixas azuis à direita
        canvas.setFillColor(AZUL_BEBE)
        canvas.rect(w-2.2*cm, h-5.5*cm, 2.2*cm, 5.5*cm, stroke=0, fill=1)
        canvas.setFillColor(AZUL_CLARO)
        canvas.rect(w-2.2*cm, h-12.5*cm, 2.2*cm, 7*cm, stroke=0, fill=1)
        canvas.setFillColor(AZUL_MEDIO)
        canvas.rect(w-2.2*cm, h-18*cm, 2.2*cm, 5.5*cm, stroke=0, fill=1)
        canvas.setFillColor(AZUL_ESCURO)
        canvas.rect(w-2.2*cm, 0, 2.2*cm, h-18*cm+0.5*cm, stroke=0, fill=1)
        canvas.setFillColor(AZUL_ESCURO)
        canvas.rect(0, 0, w-2.2*cm, 0.9*cm, stroke=0, fill=1)
        # Logo (texto)
        canvas.setFillColor(AZUL_ESCURO)
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawString(1.8*cm, h-2.8*cm, "MERCURY")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(AZUL_MEDIO)
        canvas.drawString(1.85*cm, h-3.2*cm, "W E A L T H   M A N A G E M E N T")
        canvas.restoreState()

    def _pagina_normal(self, canvas, doc):
        w, h = A4
        canvas.saveState()
        # Header
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(CINZA_TXT)
        canvas.drawString(1.6*cm, h-1.2*cm, self.periodo_txt)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.setFillColor(AZUL_ESCURO)
        canvas.drawRightString(w-1.6*cm, h-1.3*cm, "MERCURY")
        canvas.setFont("Helvetica", 5)
        canvas.setFillColor(AZUL_MEDIO)
        canvas.drawRightString(w-1.6*cm, h-1.55*cm, "WEALTH MANAGEMENT")
        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(CINZA_TXT)
        canvas.drawString(1.6*cm, 1.1*cm, self.gerado_txt)
        canvas.drawRightString(w-1.6*cm, 1.1*cm, f"Página {doc.page}")
        canvas.restoreState()


# ─── Gráficos matplotlib → Image flowable ─────────────────────────────────────
def _fig_to_image(fig, width_cm=17.5):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth  = width_cm * cm
    img.drawHeight = width_cm * ratio * cm
    return img


def _grafico_linha_acumulada(port_rets, cdi_rets):
    """Linha: retorno acumulado Portfolio vs CDI."""
    meses = sorted(port_rets.keys())
    if not meses: return None
    x_labels, port_acum, cdi_acum = [], [], []
    pa, ca = 1.0, 1.0
    for m in meses:
        pa *= (1 + port_rets[m])
        ca *= (1 + cdi_rets.get(m, 0))
        x_labels.append(f"{MESES_PT[m[1]-1]}\n{str(m[0])[2:]}")
        port_acum.append((pa-1)*100)
        cdi_acum.append((ca-1)*100)

    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(range(len(meses)), port_acum, color=MPL_AZUL, lw=1.6,
            marker="o", ms=2.5, label="Portfolio")
    ax.plot(range(len(meses)), cdi_acum, color=MPL_AMARELO, lw=1.3,
            ls="--", label="CDI")
    ax.set_xticks(range(len(meses)))
    ax.set_xticklabels(x_labels, fontsize=6)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}%"))
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="y", color="#eeeeee", lw=0.6)
    for spine in ["top","right"]:
        ax.spines[spine].set_visible(False)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    return _fig_to_image(fig)


def _grafico_donut(labels_vals, titulo=""):
    labels = [l for l, v in labels_vals]
    vals   = [v for l, v in labels_vals]
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    wedges, _ = ax.pie(vals, colors=PIE_CORES[:len(vals)],
                       startangle=180, counterclock=False,
                       wedgeprops=dict(width=0.42))
    # semicírculo estilo BTG: manter círculo completo é mais simples e claro
    ax.legend(wedges,
              [f"{l} | {v*100:.2f}%".replace(".",",") for l, v in labels_vals],
              loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=7,
              frameon=False)
    if titulo:
        ax.set_title(titulo, fontsize=9)
    fig.tight_layout()
    return _fig_to_image(fig, width_cm=15)


def _grafico_barras_classe(classe_rets):
    labels = [c for c, v in classe_rets]
    vals   = [v*100 for c, v in classe_rets]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    bars = ax.bar(range(len(vals)), vals, color=MPL_AZUL, width=0.45)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v + (0.15 if v>=0 else -0.4),
                f"{v:.2f}%".replace(".",","), ha="center", fontsize=7,
                fontweight="bold", color="#333")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}%"))
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="y", color="#eeeeee", lw=0.6)
    for spine in ["top","right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return _fig_to_image(fig)


def _grafico_vol_movel(port_rets, cdi_rets, janela=6):
    """Vol móvel anualizada (janela em meses)."""
    meses = sorted(port_rets.keys())
    if len(meses) < janela+1: return None
    import statistics
    xs, vols_p, vols_c = [], [], []
    for i in range(janela, len(meses)):
        window = [port_rets[m] for m in meses[i-janela:i+1]]
        vols_p.append(statistics.pstdev(window)*math.sqrt(12)*100)
        wc = [cdi_rets.get(m, 0) for m in meses[i-janela:i+1]]
        vols_c.append(statistics.pstdev(wc)*math.sqrt(12)*100)
        m = meses[i]
        xs.append(f"{MESES_PT[m[1]-1]}\n{str(m[0])[2:]}")
    fig, ax = plt.subplots(figsize=(9, 3.0))
    ax.plot(range(len(xs)), vols_p, color=MPL_AZUL, lw=1.6, label="Portfolio")
    ax.plot(range(len(xs)), vols_c, color=MPL_AMARELO, lw=1.3, ls="--", label="CDI")
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, fontsize=6)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}%"))
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="y", color="#eeeeee", lw=0.6)
    for spine in ["top","right"]:
        ax.spines[spine].set_visible(False)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    return _fig_to_image(fig)


# ─── Estilos ──────────────────────────────────────────────────────────────────
def _estilos():
    base = getSampleStyleSheet()["Normal"]
    mk = lambda name, **kw: ParagraphStyle(name, parent=base, **kw)
    return {
        "h1":       mk("h1", fontSize=17, textColor=colors.HexColor("#222"),
                        fontName="Helvetica", spaceAfter=2),
        "h1_sub":   mk("h1s", fontSize=9, textColor=CINZA_TXT, spaceAfter=8),
        "capa_tit": mk("ct", fontSize=34, textColor=AZUL_ESCURO,
                        fontName="Helvetica", leading=40),
        "capa_sub": mk("cs", fontSize=12, textColor=AZUL_ESCURO, leading=16),
        "cell":     mk("cell", fontSize=7.5, leading=9),
        "cell_b":   mk("cellb", fontSize=7.5, leading=9,
                        fontName="Helvetica-Bold"),
        "nota":     mk("nota", fontSize=7, textColor=CINZA_TXT, leading=9),
        "idx":      mk("idx", fontSize=10, textColor=colors.HexColor("#333"),
                        leading=22),
        "disc":     mk("disc", fontSize=7.5, textColor=colors.HexColor("#444"),
                        leading=10.5, alignment=4),  # justify
        "contato_t":mk("cont", fontSize=10, fontName="Helvetica-Bold",
                        textColor=colors.HexColor("#222"), spaceAfter=2),
        "contato":  mk("contv", fontSize=9, textColor=CINZA_TXT, leading=13),
    }

def _header_tabela():
    return [
        ("BACKGROUND", (0,0), (-1,0), AZUL_MEDIO),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("GRID",       (0,0), (-1,-1), 0.4, CINZA_LINHA),
        ("TOPPADDING", (0,0), (-1,-1), 3.5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3.5),
        ("LEFTPADDING",(0,0), (-1,-1), 5),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]


# ─── GERADOR PRINCIPAL ────────────────────────────────────────────────────────
def gerar_pdf_proposta(cliente, valor, perfil, aloc_cl, aloc_fd, metricas,
                       quantum_file=None):
    from fundos_config_v2 import CLASSES, fundos_por_classe, LIQUIDEZ_DIAS
    from mercury_data import calcular_portfolio, QUANTUM_FILE
    from pathlib import Path

    fp = Path(quantum_file) if quantum_file else QUANTUM_FILE

    # Pesos por fundo (% do total)
    pesos = {nq: p/100 for nq, p in aloc_fd.items() if p > 0}
    port  = calcular_portfolio(pesos, fp) if pesos else {}

    port_rets = port.get("retornos_mensais", {})
    cdi_rets  = port.get("cdi_mensais", {})

    # Limitar aos últimos 12 meses (padrão do relatório)
    todos_meses = sorted(port_rets.keys())
    if len(todos_meses) > 12:
        ult12 = todos_meses[-12:]
        port_rets = {m: port_rets[m] for m in ult12}
        # Recalcular estatísticas sobre a janela de 12 meses
        import statistics as _st
        rets_lst = [port_rets[m] for m in ult12]
        acum = 1.0
        for r in rets_lst: acum *= (1+r)
        cdi_ac = 1.0
        n_cdi = 0
        for m in ult12:
            if m in cdi_rets:
                cdi_ac *= (1+cdi_rets[m]); n_cdi += 1
        vol_m = _st.pstdev(rets_lst) if len(rets_lst) > 2 else None
        vol_a = vol_m*math.sqrt(12) if vol_m else None
        ret_a = acum**(12/len(ult12)) - 1
        cdi_a = cdi_ac**(12/n_cdi) - 1 if n_cdi >= 6 else None
        port = dict(port)
        port.update({
            "ret_total": acum-1,
            "ret_anualizado": ret_a,
            "vol_anualizada": vol_a,
            "cdi_total": cdi_ac-1 if n_cdi else None,
            "pct_cdi": (acum-1)/(cdi_ac-1) if cdi_ac != 1 else None,
            "sharpe": ((ret_a-cdi_a)/vol_a) if (cdi_a is not None and vol_a) else None,
            "meses_positivos": sum(1 for r in rets_lst if r > 0),
            "meses_negativos": sum(1 for r in rets_lst if r < 0),
            "maior_retorno": max(rets_lst),
            "menor_retorno": min(rets_lst),
            "acima_cdi": sum(1 for m in ult12
                             if m in cdi_rets and port_rets[m] > cdi_rets[m]),
            "abaixo_cdi": sum(1 for m in ult12
                              if m in cdi_rets and port_rets[m] <= cdi_rets[m]),
            "n_meses": len(ult12),
        })

    meses_ord = sorted(port_rets.keys())

    # Período do relatório
    if meses_ord:
        m0, m1 = meses_ord[0], meses_ord[-1]
        periodo_txt = (f"Período da comparação: 01/{m0[1]:02d}/{m0[0]} "
                       f"a 01/{m1[1]:02d}/{m1[0]}")
        periodo_capa = f"01/{m0[1]:02d}/{m0[0]} - 01/{m1[1]:02d}/{m1[0]}"
    else:
        periodo_txt  = "Período da comparação: —"
        periodo_capa = "—"
    gerado_txt = f"Relatório gerado em {date.today().strftime('%d/%m/%Y')}"

    S = _estilos()
    buf = io.BytesIO()
    doc = RelatorioTemplate(buf, periodo_txt, gerado_txt)
    story = []

    # ══ 1. CAPA ═══════════════════════════════════════════════════════════════
    story.append(NextPageTemplate("normal"))
    story.append(Spacer(1, 7*cm))
    story.append(Paragraph("Relatório da<br/>proposta", S["capa_tit"]))
    story.append(Spacer(1, 2.2*cm))
    story.append(Paragraph("Informações detalhadas sobre<br/>portfólios de produtos",
                           S["capa_sub"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Período: {periodo_capa}", S["capa_sub"]))
    story.append(Paragraph(f"Gerado em {date.today().strftime('%d/%m/%Y')}",
                           S["capa_sub"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"<b>Cliente:</b> {cliente} &nbsp;·&nbsp; "
                           f"<b>Perfil:</b> {perfil} &nbsp;·&nbsp; "
                           f"<b>Valor:</b> {_fmt_brl(valor, 2)}", S["capa_sub"]))
    story.append(PageBreak())

    # ══ 2. ÍNDICE ═════════════════════════════════════════════════════════════
    story.append(Paragraph("Índice", S["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=14))
    indice = [("Resumo",3),("Composição da carteira",4),("Rentabilidade",6),
              ("Rentabilidade mês a mês",7),("Rentabilidade por classe de ativo",8),
              ("Estatísticas",9),("Volatilidade",10),("Liquidez",11),
              ("Sobre este material",12),("Fale conosco",13)]
    rows_idx = [[Paragraph(t, S["idx"]),
                 Paragraph(f'<font color="#1e63b4">{p}</font>', S["idx"])]
                for t, p in indice]
    tbl = Table(rows_idx, colWidths=[15*cm, 2*cm])
    tbl.setStyle(TableStyle([
        ("LINEBELOW", (0,0), (-1,-1), 0.5, CINZA_LINHA),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ══ 3. RESUMO ═════════════════════════════════════════════════════════════
    story.append(Paragraph("Resumo", S["h1"]))
    story.append(Paragraph("Este é o resumo das carteiras no período selecionado.",
                           S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=14))

    patrimonio_acum = valor * (1 + port.get("ret_total", 0)) if port else None
    rows_r = [
        ["", "Portfolio"],
        ["Rentabilidade anualizada estimada", _fmt_pct(port.get("ret_anualizado"))],
        ["Volatilidade anualizada estimada",  _fmt_pct(port.get("vol_anualizada"))],
        ["Valor da carteira",                 _fmt_brl(valor, 2)],
        ["Patrimônio acumulado",              _fmt_brl(patrimonio_acum, 2)],
        ["Sharpe", f"{port['sharpe']:.2f}".replace(".",",") if port.get("sharpe") is not None else "—"],
        ["% CDI",  _fmt_pct(port.get("pct_cdi"))],
    ]
    tbl = Table(rows_r, colWidths=[9*cm, 8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (1,0), (1,0), AZUL_MEDIO),
        ("TEXTCOLOR",  (1,0), (1,0), colors.white),
        ("FONTNAME",   (1,0), (1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ALIGN",      (1,0), (1,-1), "CENTER"),
        ("ALIGN",      (1,1), (1,-1), "RIGHT"),
        ("LINEBELOW",  (0,1), (-1,-1), 0.5, CINZA_LINHA),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("RIGHTPADDING",(1,0),(1,-1), 10),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ══ 4-5. COMPOSIÇÃO ═══════════════════════════════════════════════════════
    story.append(Paragraph("Composição da carteira", S["h1"]))
    story.append(Paragraph("É a distribuição estratégica dos recursos entre "
                           "diferentes classes de ativos.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=10))

    classes_ativas = [(c, aloc_cl.get(c,0)) for c in CLASSES if aloc_cl.get(c,0) > 0]
    donut = _grafico_donut(classes_ativas)
    if donut: story.append(donut)
    story.append(Spacer(1, 0.3*cm))

    rows_comp = [["Classe", "Portfolio %", "Volume financeiro (R$)"]]
    for c, p in classes_ativas:
        rows_comp.append([c, _fmt_pct(p), _fmt_brl(p*valor, 2)])
    rows_comp.append(["Total", "100%", _fmt_brl(valor, 2)])
    tbl = Table(rows_comp, colWidths=[8*cm, 3.5*cm, 5.5*cm])
    st = _header_tabela() + [
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, CINZA_CLARO]),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND", (0,-1), (-1,-1), CINZA_CLARO),
    ]
    tbl.setStyle(TableStyle(st))
    story.append(tbl)
    story.append(PageBreak())

    # Detalhe por classe (página 5)
    for c, pct_c in classes_ativas:
        fundos_c = [f for f in fundos_por_classe(c)
                    if aloc_fd.get(f["nome_quantum"], 0) > 0]
        if not fundos_c:
            continue
        val_c = pct_c * valor
        story.append(Paragraph(
            f'<font color="#1e63b4"><b>Portfolio</b></font> &nbsp;&nbsp;'
            f'<b>{c}</b> &nbsp;&nbsp; {_fmt_pct(pct_c)} do total &nbsp;&nbsp; '
            f'{_fmt_brl(val_c,2)}', 
            ParagraphStyle("cls", fontSize=10, leading=13, spaceAfter=5,
                           spaceBefore=8)))
        rows_f = [["Produto", "Rent. 12m", "%CDI 12m", "Vol. 12m", "Resgate", "Valor total"]]
        for f in fundos_c:
            nq = f["nome_quantum"]
            m  = metricas.get(nq, {})
            val_f = (aloc_fd.get(nq,0)/100) * valor
            dmais = LIQUIDEZ_DIAS.get(nq)
            rows_f.append([
                Paragraph(nq[:65], S["cell"]),
                _fmt_pct(m.get("ret_12m")),
                _fmt_pct(m.get("pct_cdi")),
                _fmt_pct(m.get("vol_12m")),
                f"D+{dmais}" if dmais is not None else "—",
                _fmt_brl(val_f, 2),
            ])
        tbl = Table(rows_f, colWidths=[6.4*cm, 2.1*cm, 2.1*cm, 2.1*cm, 1.7*cm, 2.8*cm])
        st = _header_tabela() + [
            ("ALIGN", (1,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, CINZA_CLARO]),
        ]
        tbl.setStyle(TableStyle(st))
        story.append(tbl)
        story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(
        "Nota: D+ de resgate são estimativas e devem ser confirmados nos "
        "regulamentos dos fundos.", S["nota"]))
    story.append(PageBreak())

    # ══ 6. RENTABILIDADE ══════════════════════════════════════════════════════
    story.append(Paragraph("Rentabilidade", S["h1"]))
    story.append(Paragraph(
        "É o ganho ou perda financeira que a carteira apresenta ao longo do "
        "tempo. Essa medida é calculada com base no retorno dos ativos que "
        "compõem a carteira.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=10))

    g = _grafico_linha_acumulada(port_rets, cdi_rets)
    if g: story.append(g)
    story.append(Spacer(1, 0.3*cm))

    # Tabela: CDI, Portfolio + cada fundo (Mês/Ano/12M/Período)
    def _ret_stats(rets_dict):
        """(mes, ano_ytd, 12m, período) a partir de dict {(a,m): r}"""
        ms = sorted(rets_dict.keys())
        if not ms: return "—","—","—","—"
        ult = ms[-1]
        r_mes = rets_dict[ult]
        # YTD
        acum_ytd = 1.0
        for m in ms:
            if m[0] == ult[0]:
                acum_ytd *= (1+rets_dict[m])
        # 12m
        ult12 = ms[-12:] if len(ms)>=12 else ms
        acum12 = 1.0
        for m in ult12: acum12 *= (1+rets_dict[m])
        # período
        acum_p = 1.0
        for m in ms: acum_p *= (1+rets_dict[m])
        return (_fmt_pct(r_mes), _fmt_pct(acum_ytd-1),
                _fmt_pct(acum12-1), _fmt_pct(acum_p-1))

    from mercury_data import retornos_mensais_ativo
    rows_rent = [["Rentabilidade", "Mês", "Ano", "12 Meses", "Período"]]
    cdi_row = _ret_stats({m: r for m, r in cdi_rets.items() if m in port_rets})
    rows_rent.append(["CDI", *cdi_row])
    port_row = _ret_stats(port_rets)
    rows_rent.append([Paragraph("<b>Portfolio</b>", S["cell_b"]), *port_row])

    fundos_ativos = [(nq, p) for nq, p in aloc_fd.items() if p > 0]
    for nq, _ in fundos_ativos:
        rets_f = retornos_mensais_ativo(nq, fp)
        rets_f = {m: r for m, r in rets_f.items() if m in port_rets}
        rows_rent.append([Paragraph(nq[:60], S["cell"]), *_ret_stats(rets_f)])

    if port.get("pct_cdi") is not None:
        cdi_periodo = port.get("cdi_total")
        # % CDI por coluna: simplificação — só período/12m
        rows_rent.append([Paragraph("<b>% CDI Portfolio</b>", S["cell_b"]),
                          "—", "—", _fmt_pct(port.get("pct_cdi")),
                          _fmt_pct(port.get("pct_cdi"))])

    tbl = Table(rows_rent, colWidths=[7.4*cm, 2.4*cm, 2.4*cm, 2.4*cm, 2.4*cm])
    st = _header_tabela() + [
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, CINZA_CLARO]),
    ]
    tbl.setStyle(TableStyle(st))
    story.append(tbl)
    story.append(PageBreak())

    # ══ 7. RENTABILIDADE MÊS A MÊS ════════════════════════════════════════════
    story.append(Paragraph("Rentabilidade mês a mês", S["h1"]))
    story.append(Paragraph("Confira a rentabilidade da carteira em cada mês e "
                           "compare com o desempenho do benchmark.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=10))

    anos = sorted(set(m[0] for m in meses_ord))
    header_m = [""] + MESES_PT + ["Total"]
    rows_m = [header_m]
    span_rows = []
    for ano in anos:
        rows_m.append([str(ano)] + [""]*13)
        span_rows.append(len(rows_m)-1)
        linha_cdi  = ["CDI"]
        linha_port = ["Portfolio"]
        linha_pct  = ["% CDI"]
        cdi_ac, port_ac = 1.0, 1.0
        for mes in range(1, 13):
            k = (ano, mes)
            rc = cdi_rets.get(k) if k in port_rets else None
            rp = port_rets.get(k)
            if rp is not None:
                port_ac *= (1+rp)
                linha_port.append(_fmt_pct(rp))
            else:
                linha_port.append("-")
            if rc is not None:
                cdi_ac *= (1+rc)
                linha_cdi.append(_fmt_pct(rc))
            else:
                linha_cdi.append("-")
            if rp is not None and rc not in (None, 0):
                linha_pct.append(_fmt_pct(rp/rc, 1))
            else:
                linha_pct.append("-")
        linha_cdi.append(_fmt_pct(cdi_ac-1))
        linha_port.append(_fmt_pct(port_ac-1))
        linha_pct.append(_fmt_pct((port_ac-1)/(cdi_ac-1),1) if cdi_ac!=1 else "-")
        rows_m += [linha_cdi, linha_port, linha_pct]

    col_w_m = [1.7*cm] + [1.18*cm]*12 + [1.35*cm]
    tbl = Table(rows_m, colWidths=col_w_m)
    st = [
        ("BACKGROUND", (0,0), (-1,0), AZUL_MEDIO),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 6),
        ("GRID",       (0,0), (-1,-1), 0.4, CINZA_LINHA),
        ("ALIGN",      (1,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]
    for r in span_rows:
        st += [("SPAN", (0,r), (-1,r)),
               ("BACKGROUND", (0,r), (-1,r), colors.HexColor("#dce8fb")),
               ("FONTNAME", (0,r), (-1,r), "Helvetica-Bold")]
    tbl.setStyle(TableStyle(st))
    story.append(tbl)
    story.append(PageBreak())

    # ══ 8. RENTABILIDADE POR CLASSE ═══════════════════════════════════════════
    story.append(Paragraph("Rentabilidade por classe de ativo", S["h1"]))
    story.append(Paragraph("Esta é a rentabilidade das carteiras por classe de "
                           "ativos.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=10))

    classe_rets = []
    for c, pct_c in classes_ativas:
        fundos_c = [f for f in fundos_por_classe(c)
                    if aloc_fd.get(f["nome_quantum"],0) > 0]
        if not fundos_c: continue
        pesos_classe = {f["nome_quantum"]: aloc_fd[f["nome_quantum"]]/100
                        for f in fundos_c}
        port_c = calcular_portfolio(pesos_classe, fp)
        # contribuição = retorno da classe * peso da classe
        if port_c.get("ret_total") is not None:
            classe_rets.append((c, port_c["ret_total"] * pct_c))

    g = _grafico_barras_classe(classe_rets)
    if g: story.append(g)
    story.append(Paragraph(
        "Contribuição de cada classe para o retorno total do período "
        "(retorno da classe × peso na carteira).", S["nota"]))
    story.append(PageBreak())

    # ══ 9. ESTATÍSTICAS ═══════════════════════════════════════════════════════
    story.append(Paragraph("Estatísticas", S["h1"]))
    story.append(Paragraph("As estatísticas oferecem um resumo valioso sobre o "
                           "desempenho da carteira ao longo do período.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=14))

    rows_e = [["Carteira","Meses positivos","Meses negativos","Maior retorno",
               "Menor retorno","Acima do CDI\n(meses)","Abaixo do CDI\n(meses)"],
              ["Portfolio",
               str(port.get("meses_positivos","—")),
               str(port.get("meses_negativos","—")),
               _fmt_pct(port.get("maior_retorno")),
               _fmt_pct(port.get("menor_retorno")),
               str(port.get("acima_cdi","—")),
               str(port.get("abaixo_cdi","—"))]]
    tbl = Table(rows_e, colWidths=[2.6*cm]+[2.45*cm]*6)
    st = _header_tabela() + [
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("TEXTCOLOR", (3,1), (3,1), VERDE),
        ("TEXTCOLOR", (4,1), (4,1), VERMELHO),
    ]
    tbl.setStyle(TableStyle(st))
    story.append(tbl)
    story.append(PageBreak())

    # ══ 10. VOLATILIDADE ══════════════════════════════════════════════════════
    story.append(Paragraph("Volatilidade", S["h1"]))
    story.append(Paragraph(
        "A volatilidade refere-se à variabilidade ou instabilidade nos preços "
        "de ativos durante um período determinado. Essa medida é utilizada para "
        "avaliar a imprevisibilidade e as flutuações nos valores desses ativos "
        "ao longo do tempo.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=10))

    g = _grafico_vol_movel(port_rets, cdi_rets)
    if g: story.append(g)
    story.append(Spacer(1, 0.3*cm))

    rows_v = [["Volatilidade", "12 Meses (a.a.)"]]
    rows_v.append([Paragraph("<b>Portfolio</b>", S["cell_b"]),
                   _fmt_pct(port.get("vol_anualizada"))])
    for nq, _ in fundos_ativos:
        m = metricas.get(nq, {})
        rows_v.append([Paragraph(nq[:65], S["cell"]),
                       _fmt_pct(m.get("vol_12m"))])
    tbl = Table(rows_v, colWidths=[12*cm, 5*cm])
    st = _header_tabela() + [
        ("ALIGN", (1,0), (1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, CINZA_CLARO]),
    ]
    tbl.setStyle(TableStyle(st))
    story.append(tbl)
    story.append(PageBreak())

    # ══ 11. LIQUIDEZ ══════════════════════════════════════════════════════════
    story.append(Paragraph("Liquidez", S["h1"]))
    story.append(Paragraph("Refere-se a rapidez e eficiência com que um investidor "
                           "pode converter um ativo em dinheiro.", S["h1_sub"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=10))

    # Donut por faixa de liquidez
    faixas = {"D+0 a D+5": 0.0, "De 6 até 30 dias": 0.0,
              "De 31 até 60 dias": 0.0, "Acima de 60 dias": 0.0}
    detalhe = {k: [] for k in faixas}
    for nq, p in fundos_ativos:
        d = LIQUIDEZ_DIAS.get(nq)
        val_f = (p/100)*valor
        if d is None: continue
        if d <= 5:    k = "D+0 a D+5"
        elif d <= 30: k = "De 6 até 30 dias"
        elif d <= 60: k = "De 31 até 60 dias"
        else:         k = "Acima de 60 dias"
        faixas[k] += (p/100)
        detalhe[k].append((nq, val_f, d))

    faixas_ativas = [(k, v) for k, v in faixas.items() if v > 0]
    g = _grafico_donut(faixas_ativas)
    if g: story.append(g)
    story.append(Spacer(1, 0.3*cm))

    rows_l = [["", "Produto", "Valor", "Liquidez (Dias)"]]
    merge_info = []
    for k, _ in faixas_ativas:
        start = len(rows_l)
        for nq, val_f, d in detalhe[k]:
            rows_l.append(["", Paragraph(nq[:60], S["cell"]),
                           _fmt_brl(val_f, 2), f"D+{d}"])
        end = len(rows_l)-1
        if end >= start:
            rows_l[start][0] = k
            merge_info.append((start, end))

    tbl = Table(rows_l, colWidths=[3.2*cm, 8*cm, 3.4*cm, 2.4*cm])
    st = _header_tabela() + [
        ("ALIGN", (2,0), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,1), (0,-1), 7),
        ("VALIGN", (0,1), (0,-1), "MIDDLE"),
    ]
    for s, e in merge_info:
        if e > s:
            st.append(("SPAN", (0,s), (0,e)))
    tbl.setStyle(TableStyle(st))
    story.append(tbl)
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Nota: prazos de resgate estimados — confirmar nos regulamentos.",
        S["nota"]))
    story.append(PageBreak())

    # ══ 12. SOBRE ESTE MATERIAL ═══════════════════════════════════════════════
    story.append(Paragraph("Sobre este material", S["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=14))
    disclaimer = (
        "Esse material é um breve resumo de cunho meramente informativo, preparado e "
        "distribuído pela Mercury Wealth Management (\"Mercury\"), não configurando "
        "análise de valores mobiliários e não tendo como objetivo a oferta, solicitação "
        "de oferta, ou recomendação para a compra ou venda de qualquer investimento ou "
        "produto específico. Essa é uma ferramenta de simulação com utilização de "
        "algoritmos, não configurando compromisso ou garantia por parte da Mercury. "
        "Embora as informações e opiniões expressas neste documento tenham sido obtidas "
        "de fontes confiáveis e fidedignas, nenhuma garantia ou responsabilidade, "
        "expressa ou implícita, é feita a respeito da exatidão, fidelidade e/ou "
        "totalidade das informações. Todas as informações, opiniões e valores "
        "eventualmente indicados estão sujeitos à alteração sem prévio aviso. "
        "<b>RENTABILIDADE PASSADA NÃO REPRESENTA GARANTIA DE RENTABILIDADE FUTURA. "
        "LEIA O FORMULÁRIO DE INFORMAÇÕES COMPLEMENTARES, LÂMINA DE INFORMAÇÕES "
        "ESSENCIAIS E O REGULAMENTO ANTES DE INVESTIR. FUNDOS DE INVESTIMENTO NÃO "
        "CONTAM COM GARANTIA DO ADMINISTRADOR, DO GESTOR, DE QUALQUER MECANISMO DE "
        "SEGURO OU FUNDO GARANTIDOR DE CRÉDITO — FGC.</b> Esse material não deve servir "
        "como única fonte de informações no processo decisório do investidor, que, "
        "antes de tomar qualquer decisão, deverá realizar uma avaliação minuciosa do "
        "produto e respectivos riscos, face aos seus objetivos pessoais e ao seu perfil "
        "de risco (\"Suitability\"). A rentabilidade divulgada não é líquida de "
        "impostos. Os cenários de investimento aqui previstos levam em conta projeções "
        "calculadas com base em metodologia interna que considera, dentre outras "
        "variáveis, a rentabilidade histórica dos produtos, não constituindo promessa "
        "ou garantia de rentabilidade. Há riscos inerentes aos diversos mercados, "
        "podendo ocorrer variações do patrimônio investido, inclusive perda total. "
        "Este material não deve ser reproduzido ou ter suas cópias circuladas sem "
        "prévia autorização da Mercury."
    )
    story.append(Paragraph(disclaimer, S["disc"]))
    story.append(PageBreak())

    # ══ 13. FALE CONOSCO ══════════════════════════════════════════════════════
    story.append(Paragraph("Fale conosco", S["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=CINZA_LINHA,
                            spaceAfter=14))
    contato_tbl = Table([
        [Paragraph("Mercury Wealth Management", S["contato_t"]),
         Paragraph("Atendimento", S["contato_t"])],
        [Paragraph("contato@mercurywm.com.br<br/>www.mercurywm.com.br",
                   S["contato"]),
         Paragraph("De segunda a sexta, das 9h às 18h<br/>(exceto feriados)",
                   S["contato"])],
    ], colWidths=[8.5*cm, 8.5*cm])
    contato_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(contato_tbl)
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "⚠ Substituir pelos contatos oficiais da Mercury antes do uso com clientes.",
        S["nota"]))

    doc.build(story)
    return buf.getvalue()
