"""
gerar_pdf.py — Mercury · Gerador de Propostas
"""
from io import BytesIO
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

AZUL  = colors.HexColor("#0a2744")
CINZA = colors.HexColor("#f5f5f2")
CINZA2= colors.HexColor("#e8e8e4")
VERDE = colors.HexColor("#1b5e20")

def _fmt_pct(v): return f"{v*100:.1f}%" if v is not None else "—"
def _fmt_brl(v):
    if v is None: return "—"
    return "R$ {:,.0f}".format(v).replace(",","X").replace(".",",").replace("X",".")

def gerar_pdf_proposta(cliente, valor, perfil, aloc_cl, aloc_fd, metricas):
    from fundos_config_v2 import CLASSES, fundos_por_classe

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    titulo  = ParagraphStyle("titulo",  parent=styles["Normal"],
                             fontSize=20, textColor=AZUL, spaceAfter=4,
                             fontName="Helvetica-Bold")
    subtit  = ParagraphStyle("subtit",  parent=styles["Normal"],
                             fontSize=12, textColor=AZUL, spaceAfter=2,
                             fontName="Helvetica-Bold")
    meta_s  = ParagraphStyle("meta",    parent=styles["Normal"],
                             fontSize=10, textColor=colors.HexColor("#555"),
                             spaceAfter=12)
    small   = ParagraphStyle("small",   parent=styles["Normal"],
                             fontSize=7, textColor=colors.HexColor("#888"),
                             spaceAfter=4)
    cell_s  = ParagraphStyle("cell",    parent=styles["Normal"],
                             fontSize=8, leading=10)

    story = []

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Mercury Wealth Management", subtit))
    story.append(Paragraph("Proposta de Carteira", titulo))
    story.append(Paragraph(
        f"<b>{cliente}</b> &nbsp;|&nbsp; Perfil: {perfil} "
        f"&nbsp;|&nbsp; {_fmt_brl(valor)} "
        f"&nbsp;|&nbsp; {date.today().strftime('%d/%m/%Y')}", meta_s))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL, spaceAfter=10))

    # ── Tabela de classes ──────────────────────────────────────────────────────
    story.append(Paragraph("Alocação por classe de ativo", subtit))

    rows_c = [["Classe de Ativo", "% Carteira", "Valor"]]
    for c in CLASSES:
        pct = aloc_cl.get(c, 0)
        if pct == 0: continue
        rows_c.append([c, _fmt_pct(pct), _fmt_brl(pct*valor)])
    rows_c.append(["TOTAL", "100,0%", _fmt_brl(valor)])

    tbl_c = Table(rows_c, colWidths=[8*cm, 3*cm, 4*cm])
    tbl_c.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  AZUL),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ALIGN",       (1,0), (-1,-1), "CENTER"),
        ("ALIGN",       (0,0), (0,-1),  "LEFT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-2),[CINZA, colors.white]),
        ("BACKGROUND",  (0,-1),(-1,-1), CINZA2),
        ("FONTNAME",    (0,-1),(-1,-1), "Helvetica-Bold"),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#ddd")),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tbl_c)
    story.append(Spacer(1, 0.4*cm))

    # ── Tabela de fundos ───────────────────────────────────────────────────────
    story.append(Paragraph("Fundos da carteira", subtit))

    hdrs = ["Fundo", "Classe", "% Total", "Valor", "Ret 6m", "Ret 12m", "Ret 24m", "YTD", "Vol 12m"]
    rows_f = [hdrs]
    for c in CLASSES:
        pct_c = aloc_cl.get(c, 0)
        if pct_c == 0: continue
        for f in fundos_por_classe(c):
            nq     = f["nome_quantum"]
            p_tot  = aloc_fd.get(nq, 0) / 100
            val_f  = p_tot * valor
            if val_f == 0: continue
            m = metricas.get(nq, {})
            rows_f.append([
                Paragraph(nq[:60], cell_s), c,
                _fmt_pct(p_tot), _fmt_brl(val_f),
                _fmt_pct(m.get("ret_6m")),
                _fmt_pct(m.get("ret_12m")),
                _fmt_pct(m.get("ret_24m")),
                _fmt_pct(m.get("ytd")),
                _fmt_pct(m.get("vol_12m")),
            ])

    col_w = [7.5*cm, 3.5*cm, 1.8*cm, 2.8*cm, 1.7*cm, 1.8*cm, 1.8*cm, 1.7*cm, 1.8*cm]
    tbl_f = Table(rows_f, colWidths=col_w)
    tbl_f.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),  (-1,0),  AZUL),
        ("TEXTCOLOR",    (0,0),  (-1,0),  colors.white),
        ("FONTNAME",     (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),  (-1,-1), 8),
        ("ALIGN",        (2,0),  (-1,-1), "CENTER"),
        ("ALIGN",        (0,0),  (1,-1),  "LEFT"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [CINZA, colors.white]),
        ("GRID",         (0,0),  (-1,-1), 0.3, colors.HexColor("#ddd")),
        ("TOPPADDING",   (0,0),  (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),  (-1,-1), 3),
        ("LEFTPADDING",  (0,0),  (-1,-1), 5),
        ("VALIGN",       (0,0),  (-1,-1), "MIDDLE"),
    ]))
    story.append(tbl_f)
    story.append(Spacer(1, 0.5*cm))

    # disclaimer
    story.append(Paragraph(
        "Este documento é de uso exclusivo da Mercury Wealth Management e do cliente indicado. "
        "Rentabilidades passadas não garantem rentabilidades futuras. "
        "Fundos de investimento não contam com garantia do FGC.",
        small))

    doc.build(story)
    return buf.getvalue()
