"""
gerar_pdf.py — Mercury Wealth Management · Relatório da proposta (design autoral)
=================================================================================
Reescrito em reportlab (Platypus) com a identidade visual da Mercury.
Substitui o layout "formato BTG": paleta teal/ciano própria, tipografia Lato,
logo em imagem, títulos como fluxo (sem sobreposição), gráficos matplotlib
restilizados e tabelas com filete fino (sem cabeçalho azul preenchido).

Assinatura preservada (drop-in com o app):
    gerar_pdf_proposta(cliente, valor, perfil, aloc_cl, aloc_fd, metricas,
                       quantum_file=None) -> bytes

Puro Python (reportlab + matplotlib) — roda no Streamlit Cloud sem browser.
Fontes e logos vêm de assets/ e fonts/ do próprio repo.
"""
from __future__ import annotations

import io
import os
import math
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Image, PageBreak,
                                KeepTogether, FrameBreak, NextPageTemplate,
                                Flowable)

_BASE = Path(__file__).resolve().parent
_FONTS = _BASE / "fonts"
_ASSETS = _BASE / "assets"

# Cache de imagens geradas em runtime. NÃO gravar no diretório do repositório:
# em deploy (ex.: Streamlit Cloud) ele é somente-leitura e o save() falha.
import tempfile as _tempfile
_CACHE_DIR = Path(_tempfile.gettempdir())

# ─── Paleta Mercury ───────────────────────────────────────────────────────────
INK    = HexColor("#231F20")
INK2   = HexColor("#3C3F41")
MUTED  = HexColor("#6D6E71")
LINE   = HexColor("#E4E8EA")
ZEBRA  = HexColor("#F3F6F7")
PAPER  = HexColor("#FBFBFC")
TEAL   = HexColor("#19658E")
DEEP   = HexColor("#002A3A")
CYAN   = HexColor("#00AEEF")
TEAL3  = HexColor("#3E86A8")
TEAL4  = HexColor("#77A9C1")
TEAL5  = HexColor("#B3CCD8")
POS    = HexColor("#127C66")
NEG    = HexColor("#B0524A")
WHITE  = HexColor("#FFFFFF")

# cor por CLASSE de relatório (rampa teal coesa + ciano no motor de retorno)
COR_CLASSE = {
    "Caixa":             HexColor("#8FB8C6"),
    "Renda Fixa":        DEEP,
    "Multimercados":     TEAL,
    "Offshore BRL":      TEAL3,
    "Offshore USD":      HexColor("#5C9EB8"),
    "Renda Variável":    CYAN,
    "Imobiliários":      HexColor("#8FC7BC"),
    "Private Equity/VC": HexColor("#C3D5CE"),
}
_hex = lambda c: "#%02X%02X%02X" % (int(c.red*255), int(c.green*255), int(c.blue*255))

# ─── Fontes ────────────────────────────────────────────────────────────────────
_FONT_OK = False
def _registrar_fontes():
    global _FONT_OK
    if _FONT_OK:
        return
    mapa = {"Lato": "Lato-Regular.ttf", "Lato-Bd": "Lato-Bold.ttf",
            "Lato-Bk": "Lato-Black.ttf", "Lato-Lt": "Lato-Light.ttf"}
    try:
        for nome, arq in mapa.items():
            pdfmetrics.registerFont(TTFont(nome, str(_FONTS / arq)))
        for arq in mapa.values():
            fm.fontManager.addfont(str(_FONTS / arq))
        plt.rcParams["font.family"] = "Lato"
        _FONT_OK = True
    except Exception:
        # fallback: Helvetica (não quebra a geração)
        for a, b in [("Lato", "Helvetica"), ("Lato-Bd", "Helvetica-Bold"),
                     ("Lato-Bk", "Helvetica-Bold"), ("Lato-Lt", "Helvetica")]:
            try: pdfmetrics.registerFontFamily(a, normal=b)
            except Exception: pass
        _FONT_OK = True

def _ff(bold=False, black=False, light=False):
    if not _FONT_OK: return "Helvetica"
    try:
        pdfmetrics.getFont("Lato-Bk")
        return "Lato-Bk" if black else "Lato-Bd" if bold else "Lato-Lt" if light else "Lato"
    except Exception:
        return "Helvetica-Bold" if (bold or black) else "Helvetica"

# ─── Logo reverse (branco + asa ciano) para fundo escuro, gerado on-the-fly ────
_LOGO_LIGHT_CACHE = None
def _logo_light_path():
    global _LOGO_LIGHT_CACHE
    if _LOGO_LIGHT_CACHE and Path(_LOGO_LIGHT_CACHE).exists():
        return _LOGO_LIGHT_CACHE
    try:
        from PIL import Image as PILImage
        im = PILImage.open(_ASSETS / "logo.png").convert("RGBA")
        px = im.load(); w, h = im.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a < 25:
                    continue
                if b > r + 25 and g > r + 5 and b > 80:      # asa teal -> ciano
                    px[x, y] = (0, 174, 239, a)
                else:                                        # resto -> branco
                    px[x, y] = (255, 255, 255, a)
        out = _CACHE_DIR / "mercury_logo_light.png"
        im.save(out)
        _LOGO_LIGHT_CACHE = str(out)
        return _LOGO_LIGHT_CACHE
    except Exception:
        # fallback seguro: o logo colorido existe no repo; evita "Cannot open".
        return str(_ASSETS / "logo.png")

_MARK_LIGHT_CACHE = None
def _mark_light_path():
    """Só o símbolo (sem wordmark) em branco+ciano, para o watermark da capa."""
    global _MARK_LIGHT_CACHE
    if _MARK_LIGHT_CACHE and Path(_MARK_LIGHT_CACHE).exists():
        return _MARK_LIGHT_CACHE
    try:
        from PIL import Image as PILImage
        im = PILImage.open(_logo_light_path()).convert("RGBA")
        w, h = im.size
        mark = im.crop((0, 0, w, int(h*0.58)))
        bbox = mark.getbbox()
        if bbox: mark = mark.crop(bbox)
        out = _CACHE_DIR / "mercury_mark_light.png"; mark.save(out)
        _MARK_LIGHT_CACHE = str(out); return _MARK_LIGHT_CACHE
    except Exception:
        return _logo_light_path()

def _chipbox(color, s=3.0):
    t = Table([[""]], colWidths=[s*mm], rowHeights=[s*mm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),color),
                           ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    return t

def _img(path, w_mm):
    src = path if hasattr(path, "read") else str(path)
    try:
        ir = Image(src)
        ratio = ir.imageHeight / ir.imageWidth
        ir.drawWidth = w_mm * mm
        ir.drawHeight = w_mm * mm * ratio
        return ir
    except Exception:
        # Imagem indisponível (ex.: asset não presente no ambiente de deploy).
        # Degradar sem quebrar a geração do PDF.
        return Spacer(1, 1)

# ─── Formatação ────────────────────────────────────────────────────────────────
def fpct(v, dec=2):
    if v is None: return "—"
    return f"{v*100:.{dec}f}%".replace(".", ",")
def fbrl(v, dec=2):
    if v is None: return "—"
    s = f"{v:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return "R$ " + s

# ─── Estilos de parágrafo ────────────────────────────────────────────────────
def _estilos():
    s = {}
    s["eyebrow"] = ParagraphStyle("eyebrow", fontName=_ff(bold=True), fontSize=8,
        textColor=TEAL, spaceAfter=3, leading=10, tracking=1.6)
    s["h1"] = ParagraphStyle("h1", fontName=_ff(black=True), fontSize=23,
        textColor=INK, leading=25, spaceAfter=0)
    s["desc"] = ParagraphStyle("desc", fontName=_ff(), fontSize=9,
        textColor=MUTED, leading=13, spaceBefore=6)
    s["body"] = ParagraphStyle("body", fontName=_ff(), fontSize=9.2,
        textColor=INK2, leading=14)
    s["kpi_lbl"] = ParagraphStyle("kpi_lbl", fontName=_ff(bold=True), fontSize=7.2,
        textColor=MUTED, leading=9, tracking=0.8)
    s["kpi_val"] = ParagraphStyle("kpi_val", fontName=_ff(black=True), fontSize=19,
        textColor=INK, leading=20)
    s["kpi_sub"] = ParagraphStyle("kpi_sub", fontName=_ff(), fontSize=7.5,
        textColor=MUTED, leading=9, spaceBefore=2)
    s["th"] = ParagraphStyle("th", fontName=_ff(bold=True), fontSize=6.8,
        textColor=MUTED, leading=8, tracking=0.6)
    s["td"] = ParagraphStyle("td", fontName=_ff(), fontSize=7.8, textColor=INK2, leading=9.5)
    s["td_r"] = ParagraphStyle("td_r", parent=s["td"], alignment=TA_RIGHT)
    s["td_b"] = ParagraphStyle("td_b", parent=s["td"], fontName=_ff(bold=True), textColor=INK)
    s["callout"] = ParagraphStyle("callout", fontName=_ff(), fontSize=9, textColor=WHITE,
        leading=14)
    s["callout_h"] = ParagraphStyle("callout_h", fontName=_ff(black=True), fontSize=12,
        textColor=WHITE, leading=14, spaceAfter=4)
    s["legend"] = ParagraphStyle("legend", fontName=_ff(), fontSize=9, textColor=INK2, leading=15)
    s["disc"] = ParagraphStyle("disc", fontName=_ff(), fontSize=7.6, textColor=HexColor("#C2D6DF"),
        leading=11.5, alignment=TA_JUSTIFY)
    s["sec_lbl"] = ParagraphStyle("sec_lbl", fontName=_ff(bold=True), fontSize=9.5,
        textColor=INK, leading=12)
    return s


class HRule(Flowable):
    """Filete fino de largura total do frame."""
    def __init__(self, color=LINE, thickness=1, pad_before=6, pad_after=0):
        super().__init__(); self.color=color; self.t=thickness
        self.pb=pad_before; self.pa=pad_after; self.width=0; self.height=thickness+pad_before+pad_after
    def wrap(self, aw, ah):
        self.width = aw; return aw, self.height
    def draw(self):
        c=self.canv; c.setStrokeColor(self.color); c.setLineWidth(self.t)
        y=self.pa+self.t/2; c.line(0,y,self.width,y)


def _tracked(text, style):
    """Paragraph com tracking via charSpace (reportlab aplica via style.tracking? não;
    usamos espaço fino manual em maiúsculas para eyebrows/labels)."""
    return Paragraph(text, style)


def secao(S, eyebrow, titulo, descricao=None):
    els = [Paragraph(eyebrow.upper(), S["eyebrow"]),
           Paragraph(titulo, S["h1"])]
    if descricao:
        els.append(Paragraph(descricao, S["desc"]))
    els.append(HRule(LINE, 1, pad_before=10, pad_after=0))
    els.append(Spacer(1, 12))
    return els


# ═══════════════════ GRÁFICOS (matplotlib → PNG) ═══════════════════════════════
def _fig_png(fig, dpi=200):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                transparent=True, pad_inches=0.02)
    plt.close(fig); buf.seek(0); return buf

def chart_donut(dados, total_txt):
    """dados: list de (label, valor, cor_hex)."""
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    vals = [d[1] for d in dados]; cols = [d[2] for d in dados]
    ax.pie(vals, colors=cols, startangle=90, counterclock=False,
           wedgeprops=dict(width=0.40, edgecolor="white", linewidth=2))
    ax.text(0, 0.12, "TOTAL", ha="center", va="center",
            fontsize=8, color=_hex(MUTED), fontfamily="Lato")
    _n = len(total_txt)
    _fs = 15 if _n <= 9 else 13 if _n <= 11 else 11 if _n <= 14 else 9.5
    ax.text(0, -0.10, total_txt, ha="center", va="center",
            fontsize=_fs, color=_hex(INK), fontweight="black", fontfamily="Lato")
    ax.set(aspect="equal")
    return _fig_png(fig)

def chart_linha(meses, port_cum, cdi_cum, labels):
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    x = list(range(len(meses)))
    ax.fill_between(x, [v*100 for v in port_cum], 0, color=_hex(TEAL), alpha=0.10, zorder=1)
    ax.plot(x, [v*100 for v in cdi_cum], color=_hex(CYAN), lw=2.2, ls=(0,(4,3)), zorder=2)
    ax.plot(x, [v*100 for v in port_cum], color=_hex(DEEP), lw=2.6, zorder=3)
    ax.scatter([x[-1],x[-1]], [port_cum[-1]*100, cdi_cum[-1]*100],
               color=[_hex(DEEP), _hex(CYAN)], s=22, zorder=4)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5, color=_hex(MUTED))
    ax.tick_params(axis="y", labelsize=7.5, colors=_hex(MUTED))
    ax.yaxis.set_major_formatter(lambda v,_: f"{v:.0f}%")
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(_hex(LINE))
    ax.grid(axis="y", color=_hex(LINE), lw=0.8)
    ax.set_axisbelow(True); ax.margins(x=0.02)
    return _fig_png(fig)

def chart_barras(items, fmt=lambda v: f"+{v*100:.2f} pp".replace(".",",")):
    """items: list de (label, valor, cor_hex) já ordenado desc."""
    n = len(items); fig, ax = plt.subplots(figsize=(7.0, 0.52*n + 0.4))
    y = list(range(n))[::-1]
    ax.barh(y, [i[1]*100 for i in items], color=[i[2] for i in items],
            height=0.55, zorder=2)
    mx = max([i[1]*100 for i in items] + [0.01])
    for yi, it in zip(y, items):
        ax.text(it[1]*100 + mx*0.015, yi, fmt(it[1]), va="center", ha="left",
                fontsize=8.5, color=_hex(INK), fontweight="bold", fontfamily="Lato")
        ax.text(-mx*0.02, yi, it[0], va="center", ha="right",
                fontsize=8.5, color=_hex(INK2), fontfamily="Lato")
    ax.set_xlim(0, mx*1.28); ax.set_yticks([]); ax.set_xticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.margins(y=0.05)
    return _fig_png(fig)

def chart_barras_vol(items):
    n = len(items); fig, ax = plt.subplots(figsize=(7.0, 0.34*n + 0.3))
    y = list(range(n))[::-1]
    mx = max([i[1]*100 for i in items] + [0.01])
    ax.barh(y, [i[1]*100 for i in items], color=[i[2] for i in items],
            height=0.6, zorder=2)
    for yi, it in zip(y, items):
        ax.text(it[1]*100 + mx*0.01, yi, f"{it[1]*100:.2f}%".replace(".",","),
                va="center", ha="left", fontsize=7.5, color=_hex(INK), fontfamily="Lato")
        ax.text(-mx*0.01, yi, it[0][:46], va="center", ha="right",
                fontsize=7.2, color=_hex(INK2), fontfamily="Lato")
    ax.set_xlim(0, mx*1.35); ax.set_yticks([]); ax.set_xticks([])
    for s in ax.spines.values(): s.set_visible(False)
    return _fig_png(fig)


# ═══════════════════ TEMPLATES DE PÁGINA ══════════════════════════════════════
PAGE_W, PAGE_H = A4
MARGIN = 17*mm

def _rgb(c): return (c.red, c.green, c.blue)

def _draw_header_footer(canv, doc):
    canv.saveState()
    # header
    try:
        from PIL import Image as _P  # só p/ medir
    except Exception:
        pass
    logo = str(_ASSETS / "logo.png")
    try:
        ir = pdfmetrics  # noqa
        from reportlab.lib.utils import ImageReader
        img = ImageReader(logo)
        iw, ih = img.getSize(); r = ih/iw
        w = 9*mm; h = w*r
        canv.drawImage(img, MARGIN, PAGE_H-13*mm-h/2+2, width=w, height=h,
                       mask="auto", preserveAspectRatio=True)
        canv.setFont(_ff(bold=True), 6.5); canv.setFillColor(INK2)
        canv.drawString(MARGIN+w+3*mm, PAGE_H-13*mm, "MERCURY")
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN+w+3*mm+ pdfmetrics.stringWidth("MERCURY", _ff(bold=True),6.5)+2*mm,
                        PAGE_H-13*mm, "WEALTH MANAGEMENT")
    except Exception:
        # Sem o PNG do logo: mantém a marca em texto.
        canv.setFont(_ff(bold=True), 6.5); canv.setFillColor(INK2)
        canv.drawString(MARGIN, PAGE_H-13*mm, "MERCURY")
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN + pdfmetrics.stringWidth("MERCURY", _ff(bold=True),6.5)+2*mm,
                        PAGE_H-13*mm, "WEALTH MANAGEMENT")
    canv.setFont(_ff(), 6.5); canv.setFillColor(MUTED)
    canv.drawRightString(PAGE_W-MARGIN, PAGE_H-13*mm,
                         "Período de comparação 01/07/2025 – 30/06/2026")
    canv.setStrokeColor(LINE); canv.setLineWidth(0.8)
    canv.line(MARGIN, PAGE_H-16*mm, PAGE_W-MARGIN, PAGE_H-16*mm)
    # footer
    canv.setStrokeColor(LINE); canv.line(MARGIN, 13*mm, PAGE_W-MARGIN, 13*mm)
    canv.setFont(_ff(), 6.8); canv.setFillColor(MUTED)
    canv.drawString(MARGIN, 10*mm, "Mercury Wealth Management")
    canv.drawRightString(PAGE_W-MARGIN, 10*mm,
        f"Relatório de proposta · gerado em {date.today().strftime('%d/%m/%Y')} · pág. {doc.page}")
    canv.restoreState()

def _draw_cover(canv, doc, meta):
    canv.saveState()
    canv.setFillColor(DEEP); canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # watermark do símbolo
    try:
        from reportlab.lib.utils import ImageReader
        wm = ImageReader(_mark_light_path())
        iw, ih = wm.getSize(); r = ih/iw; w = 115*mm
        canv.saveState(); canv.setFillAlpha(0.06)
        canv.drawImage(wm, PAGE_W-w+18*mm, PAGE_H-w*r-14*mm, width=w, height=w*r,
                       mask="auto"); canv.restoreState()
    except Exception:
        pass
    # logo reverse topo-esquerda
    try:
        from reportlab.lib.utils import ImageReader
        lg = ImageReader(_logo_light_path())
        iw, ih = lg.getSize(); r = ih/iw; w = 30*mm
        canv.drawImage(lg, MARGIN, PAGE_H-24*mm-w*r+6*mm, width=w, height=w*r, mask="auto")
    except Exception:
        # Sem o PNG do logo: wordmark em texto branco/ciano.
        canv.setFillColor(WHITE); canv.setFont(_ff(black=True), 24)
        canv.drawString(MARGIN, PAGE_H-30*mm, "MERCURY")
        canv.setFillColor(CYAN); canv.setFont(_ff(bold=True), 8.5)
        canv.drawString(MARGIN, PAGE_H-35*mm, "W E A L T H   M A N A G E M E N T")
    # eyebrow + título
    canv.setFillColor(CYAN); canv.setFont(_ff(bold=True), 9)
    canv.drawString(MARGIN, PAGE_H-118*mm, "R E L A T Ó R I O   D A   P R O P O S T A")
    canv.setFillColor(WHITE); canv.setFont(_ff(black=True), 52)
    canv.drawString(MARGIN, PAGE_H-138*mm, "Portfólio de")
    canv.setFillColor(CYAN)
    canv.drawString(MARGIN, PAGE_H-153*mm, "produtos")
    canv.setFillColor(HexColor("#C2D6DF")); canv.setFont(_ff(), 10.5)
    canv.drawString(MARGIN, PAGE_H-168*mm,
        "Composição estratégica, rentabilidade e risco da carteira proposta.")
    # faixa de metadados
    y = 30*mm; xs = [MARGIN, MARGIN+62*mm, MARGIN+124*mm]
    labels = [("CLIENTE", meta["cliente"]), ("PERFIL", meta["perfil"]),
              ("VALOR DA CARTEIRA", meta["valor"])]
    canv.setStrokeColor(HexColor("#1C4A5A")); canv.setLineWidth(1)
    canv.line(MARGIN, y+18*mm, PAGE_W-MARGIN, y+18*mm)
    for x,(lb,val) in zip(xs, labels):
        canv.setFillColor(HexColor("#7FA8BC")); canv.setFont(_ff(bold=True), 7)
        canv.drawString(x, y+11*mm, lb)
        canv.setFillColor(CYAN if "VALOR" in lb else WHITE)
        fnt = _ff(black=True); size = 15.0; val = str(val)
        while size > 8.5 and pdfmetrics.stringWidth(val, fnt, size) > 56*mm:
            size -= 0.5
        canv.setFont(fnt, size)
        canv.drawString(x, y+4*mm, val)
    canv.restoreState()

def _draw_closing(canv, doc):
    canv.saveState()
    canv.setFillColor(DEEP); canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    try:
        from reportlab.lib.utils import ImageReader
        lg = ImageReader(_logo_light_path())
        iw, ih = lg.getSize(); r = ih/iw; w = 26*mm
        canv.drawImage(lg, MARGIN, PAGE_H-22*mm-w*r+6*mm, width=w, height=w*r, mask="auto")
    except Exception:
        canv.setFillColor(WHITE); canv.setFont(_ff(black=True), 20)
        canv.drawString(MARGIN, PAGE_H-28*mm, "MERCURY")
        canv.setFillColor(CYAN); canv.setFont(_ff(bold=True), 7.5)
        canv.drawString(MARGIN, PAGE_H-33*mm, "W E A L T H   M A N A G E M E N T")
    canv.restoreState()


# ═══════════════════ TABELAS ══════════════════════════════════════════════════
def _tabela(data, col_widths, header_idx=0, align_right_from=1, zebra=True,
            total_row=False, font_size=7.8, header_font=6.8, lr_pad=6, tb_pad=5):
    ts = [
        ("FONTNAME", (0,0), (-1,-1), _ff()),
        ("FONTSIZE", (0,0), (-1,-1), font_size),
        ("TEXTCOLOR", (0,0), (-1,-1), INK2),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (align_right_from,0), (-1,-1), "RIGHT"),
        ("ALIGN", (0,0), (0,-1), "LEFT"),
        ("TOPPADDING", (0,0), (-1,-1), tb_pad),
        ("BOTTOMPADDING", (0,0), (-1,-1), tb_pad),
        ("LEFTPADDING", (0,0), (-1,-1), lr_pad),
        ("RIGHTPADDING", (0,0), (-1,-1), lr_pad),
        # cabeçalho: só filete inferior grosso, sem preenchimento
        ("FONTNAME", (0,header_idx), (-1,header_idx), _ff(bold=True)),
        ("FONTSIZE", (0,header_idx), (-1,header_idx), header_font),
        ("TEXTCOLOR", (0,header_idx), (-1,header_idx), MUTED),
        ("LINEBELOW", (0,header_idx), (-1,header_idx), 1.2, INK),
        ("LINEBELOW", (0,header_idx+1), (-1,-2), 0.6, LINE),
    ]
    if zebra:
        for r in range(header_idx+1, len(data)):
            if (r-header_idx) % 2 == 0:
                ts.append(("BACKGROUND", (0,r), (-1,r), ZEBRA))
    if total_row:
        ts += [("LINEABOVE", (0,-1), (-1,-1), 1.2, INK),
               ("LINEBELOW", (0,-1), (-1,-1), 0, WHITE),
               ("FONTNAME", (0,-1), (-1,-1), _ff(bold=True)),
               ("TEXTCOLOR", (0,-1), (-1,-1), INK)]
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle(ts))
    return t


# ═══════════════════ FUNÇÃO PRINCIPAL ═════════════════════════════════════════
def gerar_pdf_proposta(cliente, valor, perfil, aloc_cl, aloc_fd, metricas,
                       quantum_file=None):
    _registrar_fontes()
    S = _estilos()

    from fundos_config_v2 import (CLASSES, fundos_por_classe, LIQUIDEZ_DIAS,
                                   SUBCLASSE_PARA_CLASSE, CLASSES_RELATORIO,
                                   subclasses_da_classe, FUNDOS)
    from mercury_data import (calcular_portfolio, retornos_mensais_ativo,
                              QUANTUM_FILE)
    fp = Path(quantum_file) if quantum_file else QUANTUM_FILE
    if not fp or not Path(fp).exists():
        raise FileNotFoundError(
            "Arquivo Quantum não encontrado. Faça o upload no Passo 1 antes de gerar o PDF.")

    # ── Cálculos de portfólio (janela de 12 meses) ────────────────────────────
    pesos = {nq: p/100 for nq, p in aloc_fd.items() if p > 0}
    port = calcular_portfolio(pesos, fp) if pesos else {}
    port_rets = port.get("retornos_mensais", {})
    cdi_rets  = port.get("cdi_mensais", {})
    meses = sorted(port_rets.keys())
    if len(meses) > 12:
        meses = meses[-12:]
    port_rets = {m: port_rets[m] for m in meses}

    def _acum(rets, chaves):
        a = 1.0
        for m in chaves:
            if m in rets: a *= (1 + rets[m])
        return a - 1
    ret_total = _acum(port_rets, meses)
    cdi_total = _acum(cdi_rets, meses)
    import statistics as _st
    rl = [port_rets[m] for m in meses]
    vol_anual = (_st.pstdev(rl) * math.sqrt(12)) if len(rl) > 2 else port.get("vol_anualizada")
    ret_anual = (1+ret_total)**(12/max(len(meses),1)) - 1 if meses else None
    cdi_anual = (1+cdi_total)**(12/max(len(meses),1)) - 1 if meses else None
    pct_cdi = (ret_total/cdi_total) if cdi_total else None
    sharpe = ((ret_anual-cdi_anual)/vol_anual) if (vol_anual and ret_anual is not None
                                                   and cdi_anual is not None) else None
    patrimonio = valor * (1 + ret_total)
    m_pos = sum(1 for r in rl if r > 0); m_neg = sum(1 for r in rl if r < 0)
    maior = max(rl) if rl else None; menor = min(rl) if rl else None
    acima = sum(1 for m in meses if m in cdi_rets and port_rets[m] > cdi_rets[m])
    abaixo = len(meses) - acima

    # ── Peso por CLASSE de relatório ──────────────────────────────────────────
    # Fonte: alocação EFETIVA por fundo (aloc_fd) — não a tática por classe.
    # Assim, classe/subclasse sem produto financiado (ex.: PE/VC sem fundo) NÃO
    # aparece em nenhuma página, e os pesos são rebaseados para 100%. Isso é
    # coerente com o retorno, que já é calculado renormalizando pelos fundos com
    # série. (Regra do comitê: ignorar classe sem produto + rebasear para 100%.)
    _tot_fd = sum(p for p in aloc_fd.values() if p > 0)
    _scale  = (100.0 / _tot_fd) if _tot_fd > 0 else 1.0
    peso_fd = {nq: (p * _scale / 100.0) for nq, p in aloc_fd.items() if p > 0}
    _cls_de = {f["nome_quantum"]: f["classe"] for f in FUNDOS}
    sub_peso = {}
    for nq, w in peso_fd.items():
        sc = _cls_de.get(nq)
        if sc:
            sub_peso[sc] = sub_peso.get(sc, 0) + w
    peso_classe = {}
    for cr in CLASSES_RELATORIO:
        w = sum(sub_peso.get(sc, 0) for sc in CLASSES
                if SUBCLASSE_PARA_CLASSE.get(sc) == cr)
        if w > 1e-9:
            peso_classe[cr] = w
    classes_ativas = [c for c in CLASSES_RELATORIO if c in peso_classe]

    # ── Documento ─────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    meta = {"cliente": cliente, "perfil": perfil, "valor": fbrl(valor, 0)}
    frame = Frame(MARGIN, 15*mm, PAGE_W-2*MARGIN, PAGE_H-33*mm, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_cover = Frame(0, 0, PAGE_W, PAGE_H, id="cover")
    doc = BaseDocTemplate(buf, pagesize=A4, title=f"Proposta — {cliente}",
                          author="Mercury Wealth Management")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame_cover],
                     onPage=lambda c, d: _draw_cover(c, d, meta)),
        PageTemplate(id="content", frames=[frame], onPage=_draw_header_footer),
        PageTemplate(id="closing", frames=[
            Frame(MARGIN, 40*mm, PAGE_W-2*MARGIN, PAGE_H-95*mm, id="cl")],
                     onPage=_draw_closing),
    ])

    story = [NextPageTemplate("content"), PageBreak()]

    # ── RESUMO ────────────────────────────────────────────────────────────────
    story += secao(S, "Visão geral", "Resumo da carteira",
        "Síntese das métricas de desempenho e risco no período. Valores estimados "
        "por simulação — não constituem garantia de rentabilidade futura.")
    def kpi(lbl, val, sub):
        return [[Paragraph(lbl.upper(), S["kpi_lbl"])],
                [Paragraph(val, S["kpi_val"])],
                [Paragraph(sub, S["kpi_sub"])]]
    kpis = [
        ("Rentabilidade anualizada", fpct(ret_anual), "estimada · 12 meses"),
        ("% do CDI", fpct(pct_cdi), "portfólio vs. benchmark"),
        ("Volatilidade anual", fpct(vol_anual), "estimada"),
        ("Índice de Sharpe", (f"{sharpe:.2f}".replace(".",",") if sharpe is not None else "—"),
         "retorno ajustado ao risco"),
        ("Patrimônio acumulado", fbrl(patrimonio, 0), "projeção sobre o período"),
        ("Valor investido", fbrl(valor, 0), f"{len(pesos)} fundos · {len(classes_ativas)} classes"),
    ]
    cw = (PAGE_W-2*MARGIN)/3
    grid = []
    for i in range(0, 6, 3):
        linha = []
        for j in range(3):
            lbl, val, sub = kpis[i+j]
            _fs = 19 if len(val) <= 11 else 16 if len(val) <= 13 else 14
            _vs = ParagraphStyle("kv", parent=S["kpi_val"], fontSize=_fs, leading=_fs+1)
            inner = Table([[Paragraph(lbl.upper(), S["kpi_lbl"])],
                           [Paragraph(val, _vs)],
                           [Paragraph(sub, S["kpi_sub"])]], colWidths=[cw-6*mm])
            inner.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),1),
                                       ("BOTTOMPADDING",(0,0),(-1,-1),1),
                                       ("LEFTPADDING",(0,0),(-1,-1),0),
                                       ("LINEABOVE",(0,0),(-1,0),1.5,INK)]))
            linha.append(inner)
        grid.append(linha)
    gt = Table(grid, colWidths=[cw]*3)
    gt.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),14),
                            ("BOTTOMPADDING",(0,0),(-1,-1),6),
                            ("LEFTPADDING",(0,0),(-1,-1),0),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(gt)
    story.append(Spacer(1, 16))
    # callout
    leitura = (f"A carteira {'supera' if (pct_cdi or 0)>=1 else 'fica abaixo'} do CDI "
               f"({fpct(pct_cdi,0) if pct_cdi else '—'} do CDI) nos 12 meses, com "
               f"volatilidade de {fpct(vol_anual)}. O retorno concentra-se na parcela "
               f"de maior risco da carteira; veja a atribuição por classe adiante.")
    ct = Table([[ _img(_logo_light_path(), 13),
                  [Paragraph("Leitura da proposta", S["callout_h"]),
                   Paragraph(leitura, S["callout"])] ]],
               colWidths=[20*mm, PAGE_W-2*MARGIN-20*mm])
    ct.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DEEP),
                            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                            ("TOPPADDING",(0,0),(-1,-1),16),
                            ("BOTTOMPADDING",(0,0),(-1,-1),16),
                            ("LEFTPADDING",(0,0),(0,-1),14),
                            ("RIGHTPADDING",(0,0),(-1,-1),16)]))
    story.append(ct)

    # ── COMPOSIÇÃO ────────────────────────────────────────────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Alocação", "Composição da carteira",
        "Distribuição estratégica dos recursos entre classes de ativos.")
    donut_dados = [(c, peso_classe[c], _hex(COR_CLASSE.get(c, TEAL))) for c in classes_ativas]
    dimg = _img(chart_donut(donut_dados, fbrl(valor, 0)), 62)
    # legenda
    leg_rows = []
    for c in classes_ativas:
        leg_rows.append([_chipbox(COR_CLASSE.get(c, TEAL)),
                         Paragraph(c, S["legend"]),
                         Paragraph(fpct(peso_classe[c], 2), S["td_b"])])
    leg = Table(leg_rows, colWidths=[6*mm, 46*mm, 24*mm])
    leg.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-2),0.6,LINE),
                             ("ALIGN",(2,0),(2,-1),"RIGHT"),
                             ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                             ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    top = Table([[dimg, leg]], colWidths=[(PAGE_W-2*MARGIN)*0.5]*2)
    top.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                             ("ALIGN",(0,0),(0,0),"CENTER")]))
    story.append(top); story.append(Spacer(1, 14))
    # tabela agrupada classe/subclasse
    data = [[Paragraph("CLASSE / SUBCLASSE", S["th"]),
             Paragraph("PORTFÓLIO %", S["th"]), Paragraph("VOLUME FINANCEIRO", S["th"])]]
    styles_extra = []
    for cr in classes_ativas:
        data.append([Paragraph(f'<b>{cr}</b>', S["td_b"]),
                     Paragraph(fpct(peso_classe[cr]), S["td_r"]),
                     Paragraph(fbrl(peso_classe[cr]*valor), S["td_r"])])
        subs = [sc for sc in subclasses_da_classe(cr) if sub_peso.get(sc,0) > 0]
        if len(subs) > 1 or (subs and subs[0] != cr):
            for sc in subs:
                w = sub_peso.get(sc, 0)
                data.append([Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;{sc}', S["td"]),
                             Paragraph(fpct(w), S["td_r"]),
                             Paragraph(fbrl(w*valor), S["td_r"])])
    tot = sum(peso_classe.values())
    data.append([Paragraph("Total", S["td_b"]), Paragraph(fpct(tot), S["td_r"]),
                 Paragraph(fbrl(tot*valor), S["td_r"])])
    cwid = [(PAGE_W-2*MARGIN)*0.5, (PAGE_W-2*MARGIN)*0.22, (PAGE_W-2*MARGIN)*0.28]
    story.append(_tabela(data, cwid, total_row=True, zebra=False, font_size=8.4))

    # ── PRODUTOS POR CLASSE ───────────────────────────────────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Detalhamento", "Produtos por classe",
        "Rentabilidade, aderência ao CDI, volatilidade, taxa e liquidez de cada "
        "produto. Prazos (D+) do cadastro Quantum — confirmar nos regulamentos.")
    W = PAGE_W-2*MARGIN
    prod_cols = [W*0.26, W*0.12, W*0.085, W*0.085, W*0.085, W*0.065, W*0.10, W*0.20]
    hdr = [Paragraph(x, S["th"]) for x in
           ["PRODUTO","SUBCLASSE","RENT.12M","%CDI","VOL.12M","TX.ADM","RESGATE","VALOR"]]
    def _f(nq, k): return metricas.get(nq, {}).get(k)
    for cr in classes_ativas:
        # título de classe com filete colorido
        story.append(Spacer(1, 6))
        cab = Table([[Paragraph(f'<b>{cr}</b>', S["sec_lbl"]),
                      Paragraph(f'{fpct(peso_classe[cr])} · {fbrl(peso_classe[cr]*valor,0)}',
                                ParagraphStyle("x", parent=S["td_r"], textColor=MUTED))]],
                    colWidths=[W*0.6, W*0.4])
        cab.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-1),1.4,COR_CLASSE.get(cr,TEAL)),
                                 ("BOTTOMPADDING",(0,0),(-1,-1),4),
                                 ("VALIGN",(0,0),(-1,-1),"BOTTOM")]))
        story.append(cab)
        rows = [hdr]
        for sc in subclasses_da_classe(cr):
            for f in fundos_por_classe(sc):
                nq = f["nome_quantum"]
                if aloc_fd.get(nq, 0) <= 0: continue
                dias = f.get("disponibilizacao") or (f"D+{f.get('dias_liq')}"
                        if f.get("dias_liq") is not None else "a confirmar")
                rows.append([
                    Paragraph(nq.title()[:48], S["td"]),
                    Paragraph(sc, S["td"]),
                    Paragraph(fpct(_f(nq,"ret_12m")), S["td_r"]),
                    Paragraph(fpct(_f(nq,"pct_cdi")), S["td_r"]),
                    Paragraph(fpct(_f(nq,"vol_12m")), S["td_r"]),
                    Paragraph((f"{f['taxa_adm']:.2f}%".replace(".",",")
                               if f.get("taxa_adm") is not None else "—"), S["td_r"]),
                    Paragraph(str(dias), S["td_r"]),
                    Paragraph(fbrl(peso_fd.get(nq,0)*valor,0), S["td_r"]),
                ])
        if len(rows) > 1:
            story.append(_tabela(rows, prod_cols, zebra=True, font_size=7.0,
                                 header_font=5.8, lr_pad=3, tb_pad=4))
        story.append(Spacer(1, 4))

    # ── RENTABILIDADE ACUMULADA ───────────────────────────────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Desempenho", "Rentabilidade acumulada",
        "Evolução do retorno acumulado do portfólio frente ao CDI. "
        "Rentabilidade não é líquida de impostos.")
    def _cum(rets):
        out=[]; a=1.0
        for m in meses:
            a *= (1 + rets.get(m,0)); out.append(a-1)
        return out
    MESNOME = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
    labels = [f"{MESNOME[m[1]-1]}/{str(m[0])[2:]}" for m in meses]
    story.append(_img(chart_linha(meses, _cum(port_rets), _cum(cdi_rets), labels),
                      W/mm))
    story.append(Spacer(1, 10))
    # tabela portfolio/cdi/fundos (mês/ano/12m/período)
    def _lin(nome, rets, style_nome=None, bold=False):
        mm_ = rets.get(meses[-1], None) if rets else None
        return [Paragraph(nome, style_nome or (S["td_b"] if bold else S["td"])),
                Paragraph(fpct(mm_), S["td_r"]),
                Paragraph(fpct(_acum(rets, meses)), S["td_r"])]
    rrows = [[Paragraph("SÉRIE", S["th"]), Paragraph("MÊS", S["th"]),
              Paragraph("12 MESES", S["th"])]]
    chipP = f'<font color="{_hex(DEEP)}">■</font>'; chipC = f'<font color="{_hex(CYAN)}">■</font>'
    rrows.append([Paragraph(f"{chipP}  <b>Portfólio</b>", S["td_b"]),
                  Paragraph(fpct(port_rets.get(meses[-1])), S["td_r"]),
                  Paragraph(fpct(ret_total), S["td_r"])])
    rrows.append([Paragraph(f"{chipC}  CDI (benchmark)", S["td"]),
                  Paragraph(fpct(cdi_rets.get(meses[-1])), S["td_r"]),
                  Paragraph(fpct(cdi_total), S["td_r"])])
    story.append(_tabela(rrows, [W*0.6, W*0.2, W*0.2], zebra=False, font_size=8.6))

    # ── MÊS A MÊS (heatmap) ───────────────────────────────────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Desempenho mensal", "Rentabilidade mês a mês",
        "Retorno do portfólio e do CDI em cada mês e a aderência ao benchmark. "
        "Tons mais escuros = maior superação do CDI; vermelho = retorno negativo.")
    hm_hdr = [Paragraph("SÉRIE", S["th"])] + \
             [Paragraph(f"{MESNOME[m[1]-1].upper()}<br/>{str(m[0])[2:]}", S["th"]) for m in meses] + \
             [Paragraph("TOTAL", S["th"])]
    def _cell(v, pct=False):
        st_ = ParagraphStyle("c", parent=S["td"], alignment=TA_CENTER, fontSize=6.3)
        return Paragraph(fpct(v) if v is not None else "—", st_)
    row_cdi = [Paragraph("CDI", S["td_b"])] + [_cell(cdi_rets.get(m)) for m in meses] + [_cell(cdi_total)]
    row_prt = [Paragraph("Portfólio", S["td_b"])] + [_cell(port_rets.get(m)) for m in meses] + [_cell(ret_total)]
    # linha %CDI heat
    def _pcell(p, c):
        stc = ParagraphStyle("pc", parent=S["td"], alignment=TA_CENTER, fontSize=6.3,
                             textColor=INK, fontName=_ff(bold=True))
        if p is None or not c:
            return Paragraph("—", stc), WHITE
        ratio = p/c
        if ratio < 0:
            return Paragraph(f"{ratio*100:.0f}%", ParagraphStyle("n",parent=stc,textColor=HexColor("#9A4034"))), HexColor("#EBD0CD")
        t = min(ratio/2.6, 1.0)
        def mix(a,b): return int(a+(b-a)*t)
        c5=(179,204,216); c1=(0,42,58)
        bg = Color(mix(c5[0],c1[0])/255, mix(c5[1],c1[1])/255, mix(c5[2],c1[2])/255)
        fg = WHITE if t>0.5 else INK
        return Paragraph(f"{ratio*100:.0f}%", ParagraphStyle("p",parent=stc,textColor=fg)), bg
    pcells, pbgs = [], []
    for m in meses:
        cell, bg = _pcell(port_rets.get(m), cdi_rets.get(m)); pcells.append(cell); pbgs.append(bg)
    tot_cell, tot_bg = _pcell(ret_total, cdi_total)
    row_pct = [Paragraph("% do CDI", S["td_b"])] + pcells + [tot_cell]
    ncol = len(meses)+2
    hm_cw = [W*0.11] + [(W*0.89-W*0.09)/len(meses)]*len(meses) + [W*0.09]
    hm = Table([hm_hdr, row_cdi, row_prt, row_pct], colWidths=hm_cw)
    hm_ts = [("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
             ("ALIGN",(1,0),(-1,-1),"CENTER"),
             ("LINEBELOW",(0,0),(-1,0),1.2,INK),
             ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
             ("LEFTPADDING",(0,0),(-1,-1),1.5),("RIGHTPADDING",(0,0),(-1,-1),1.5),
             ("LINEBELOW",(0,1),(-1,1),0.6,LINE)]
    for j,bg in enumerate(pbgs, start=1):
        hm_ts.append(("BACKGROUND",(j,3),(j,3),bg))
    hm_ts.append(("BACKGROUND",(ncol-1,3),(ncol-1,3),tot_bg))
    hm.setStyle(TableStyle(hm_ts))
    story.append(hm); story.append(Spacer(1, 20))
    # cards consistência
    stats = Table([[
        [Paragraph("<b>Consistência</b>", S["sec_lbl"]),
         Paragraph(f"{m_pos} meses positivos e {m_neg} negativos. O portfólio superou "
                   f"o CDI em {acima} dos {len(meses)} meses. Melhor mês {fpct(maior)}; "
                   f"pior {fpct(menor)}.", S["body"])],
        [Paragraph("<b>Acima / abaixo do CDI</b>", S["sec_lbl"]),
         Paragraph(f"{acima} meses acima e {abaixo} abaixo do CDI. A aderência de "
                   f"12 meses foi de {fpct(pct_cdi,0) if pct_cdi else '—'} do CDI.", S["body"])],
    ]], colWidths=[W*0.5, W*0.5])
    stats.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("LINEABOVE",(0,0),(0,0),2,INK),
                               ("LINEABOVE",(1,0),(1,0),2,CYAN),
                               ("TOPPADDING",(0,0),(-1,-1),10),
                               ("LEFTPADDING",(1,0),(1,0),16)]))
    story.append(stats)

    # ── ATRIBUIÇÃO POR CLASSE (corrige o gráfico quebrado) ─────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Atribuição de performance", "Rentabilidade por classe",
        "Contribuição de cada classe para o retorno do período — retorno da classe "
        "× peso na carteira. A soma aproxima o retorno do portfólio.")
    contribs = []
    for cr in classes_ativas:
        # série mensal da classe (renormalizada dentro da classe), sobre a janela
        w_cls = peso_classe[cr]
        # pesos dos fundos da classe (fração do total)
        fundos_cls = [(f["nome_quantum"], aloc_fd.get(f["nome_quantum"],0)/100)
                      for sc in subclasses_da_classe(cr)
                      for f in fundos_por_classe(sc)
                      if aloc_fd.get(f["nome_quantum"],0) > 0]
        if not fundos_cls or w_cls <= 0:
            continue
        series = {nq: retornos_mensais_ativo(nq, fp) for nq,_ in fundos_cls}
        a = 1.0
        for m in meses:
            sw = sr = 0.0
            for nq, w in fundos_cls:
                r = series.get(nq, {}).get(m)
                if r is not None:
                    sw += w; sr += w*r
            if sw > 0:
                a *= (1 + sr/sw)   # retorno da classe no mês (renormalizado)
        ret_cls = a - 1
        contribs.append((cr, ret_cls * w_cls, _hex(COR_CLASSE.get(cr, TEAL))))
    contribs.sort(key=lambda x: -x[1])
    if contribs:
        story.append(_img(chart_barras(contribs), W/mm))
        soma = sum(c[1] for c in contribs)
        story.append(Spacer(1, 6))
        tot = Table([[Paragraph("ATRIBUIÇÃO TOTAL", ParagraphStyle("a",parent=S["th"],alignment=TA_RIGHT)),
                      Paragraph(f"+{soma*100:.2f} pp".replace(".",","),
                                ParagraphStyle("b",fontName=_ff(black=True),fontSize=16,
                                               textColor=INK,alignment=TA_RIGHT))]],
                    colWidths=[W*0.7, W*0.3])
        tot.setStyle(TableStyle([("LINEABOVE",(0,0),(-1,-1),1.2,INK),
                                 ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                 ("TOPPADDING",(0,0),(-1,-1),8)]))
        story.append(tot); story.append(Spacer(1, 16))
        lider = contribs[0]
        _pp_lider = f"+{lider[1]*100:.2f}".replace(".", ",")
        call2 = Table([[Paragraph(
            f"<b>Concentração do retorno.</b> A classe {lider[0]} responde por "
            f"{_pp_lider} pp — cerca de {lider[1]/soma*100:.0f}% de todo o "
            f"ganho do período. Boa parte do risco e do retorno vem dessa parcela.",
            S["body"])]], colWidths=[W])
        call2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),ZEBRA),
                                   ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),
                                   ("LEFTPADDING",(0,0),(-1,-1),16),("RIGHTPADDING",(0,0),(-1,-1),16)]))
        story.append(call2)

    # ── VOLATILIDADE ──────────────────────────────────────────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Risco", "Volatilidade por produto",
        f"Volatilidade anualizada de 12 meses por produto (portfólio: {fpct(vol_anual)}).")
    vols = []
    for cr in classes_ativas:
        for sc in subclasses_da_classe(cr):
            for f in fundos_por_classe(sc):
                nq = f["nome_quantum"]
                if aloc_fd.get(nq,0) > 0 and _f(nq,"vol_12m") is not None:
                    vols.append((nq.title(), _f(nq,"vol_12m"), _hex(COR_CLASSE.get(cr,TEAL))))
    vols.sort(key=lambda x: -x[1])
    if vols:
        story.append(_img(chart_barras_vol(vols), W/mm))

    # ── LIQUIDEZ ──────────────────────────────────────────────────────────────
    story.append(NextPageTemplate("content")); story.append(PageBreak())
    story += secao(S, "Liquidez", "Liquidez por prazo",
        "Perfil de liquidez da carteira pelo prazo estimado de disponibilização do resgate.")
    buckets = {"Até 30 dias": 0.0, "31 a 60 dias": 0.0, "Acima de 60 dias": 0.0,
               "A confirmar": 0.0}
    linhas_liq = {b: [] for b in buckets}
    for cr in classes_ativas:
        for sc in subclasses_da_classe(cr):
            for f in fundos_por_classe(sc):
                nq = f["nome_quantum"]; w = aloc_fd.get(nq,0)/100
                if w <= 0: continue
                d = f.get("dias_liq")
                if d is None: b = "A confirmar"
                elif d <= 30: b = "Até 30 dias"
                elif d <= 60: b = "31 a 60 dias"
                else: b = "Acima de 60 dias"
                buckets[b] += w
                linhas_liq[b].append((nq.title()[:46], w*valor,
                                      f.get("disponibilizacao") or (f"D+{d}" if d is not None else "a confirmar")))
    bucket_cor = {"Até 30 dias": DEEP, "31 a 60 dias": TEAL, "Acima de 60 dias": TEAL3,
                  "A confirmar": TEAL5}
    donut2 = [(b, w, _hex(bucket_cor[b])) for b, w in buckets.items() if w > 0]
    dimg2 = _img(chart_donut(donut2, ""), 52)
    leg2 = []
    for b, w in buckets.items():
        if w > 0:
            leg2.append([_chipbox(bucket_cor[b]), Paragraph(b, S["legend"]),
                         Paragraph(fpct(w), S["td_b"])])
    legt = Table(leg2, colWidths=[6*mm, 40*mm, 22*mm])
    legt.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-2),0.6,LINE),
                              ("ALIGN",(2,0),(2,-1),"RIGHT"),
                              ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                              ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story.append(Table([[dimg2, legt]], colWidths=[(PAGE_W-2*MARGIN)*0.42,(PAGE_W-2*MARGIN)*0.58],
                       style=[("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(0,0),"CENTER")]))

    # ── SOBRE / CONTATO (página escura) ───────────────────────────────────────
    story.append(NextPageTemplate("closing")); story.append(PageBreak())
    disc = ("Este material é um breve resumo de cunho meramente informativo, preparado e "
            "distribuído pela Mercury Wealth Management (“Mercury”), não configurando análise "
            "de valores mobiliários nem oferta ou recomendação de compra ou venda de qualquer "
            "produto. É ferramenta de simulação com uso de algoritmos, não configurando "
            "compromisso ou garantia. RENTABILIDADE PASSADA NÃO REPRESENTA GARANTIA DE "
            "RENTABILIDADE FUTURA. Fundos de investimento não contam com garantia do administrador, "
            "do gestor, de mecanismo de seguro ou do Fundo Garantidor de Crédito (FGC). A "
            "rentabilidade divulgada não é líquida de impostos. Há riscos inerentes aos mercados, "
            "podendo ocorrer perda total. Este material não deve ser reproduzido sem autorização "
            "da Mercury.")
    story.append(Spacer(1, 4))
    story.append(Paragraph("Sobre este material",
                 ParagraphStyle("sc", fontName=_ff(black=True), fontSize=22, textColor=WHITE)))
    story.append(Spacer(1, 12))
    story.append(Paragraph(disc, S["disc"]))
    story.append(Spacer(1, 26))
    contato = Table([[
        [Paragraph("FALE CONOSCO", ParagraphStyle("fc",fontName=_ff(bold=True),fontSize=7.5,
                    textColor=CYAN)),
         Paragraph("contato@mercurywm.com.br<br/>www.mercurywm.com.br",
                   ParagraphStyle("ct",fontName=_ff(),fontSize=10.5,textColor=WHITE,leading=17))],
        [Paragraph("ATENDIMENTO", ParagraphStyle("at",fontName=_ff(bold=True),fontSize=7.5,
                    textColor=CYAN)),
         Paragraph("Segunda a sexta, 9h às 18h<br/>(exceto feriados)",
                   ParagraphStyle("ct2",fontName=_ff(),fontSize=10.5,textColor=WHITE,leading=17))],
    ]], colWidths=[(PAGE_W-2*MARGIN)*0.5]*2)
    contato.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                 ("LINEABOVE",(0,0),(-1,0),1,HexColor("#1C4A5A")),
                                 ("TOPPADDING",(0,0),(-1,-1),16)]))
    story.append(contato)

    doc.build(story)
    return buf.getvalue()
