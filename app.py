"""
app.py — Mercury Wealth Management · Gerador de Propostas v2
"""

import io, tempfile
from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Mercury — Propostas",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f8f8f6; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 900px; }
.step-bar { display:flex; gap:8px; margin-bottom:24px; }
.step { padding:5px 16px; border-radius:99px; font-size:12px; font-weight:500; }
.step-active  { background:#0a2744; color:#fff; }
.step-done    { background:#e8f5e9; color:#2e7d32; }
.step-pending { background:#f0f0ec; color:#aaa; }
.section-title { font-size:13px; font-weight:600; color:#0a2744;
                 margin:16px 0 6px; text-transform:uppercase; letter-spacing:.04em; }
.fund-header { display:flex; font-size:11px; color:#999; padding:4px 0;
               border-bottom:1px solid #eee; margin-bottom:2px; }
.class-card { background:#fff; border:1px solid #e5e5e0; border-radius:10px;
              padding:14px 16px; margin-bottom:12px; }
.class-name { font-size:13px; font-weight:600; color:#0a2744; margin-bottom:8px; }
.warn-box { background:#fff8e1; border:1px solid #ffe082; border-radius:8px;
            padding:10px 14px; font-size:12px; color:#795548; margin:6px 0; }
.ok-box   { background:#e8f5e9; border:1px solid #a5d6a7; border-radius:8px;
            padding:8px 14px; font-size:12px; color:#2e7d32; margin:6px 0; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
try:
    from mercury_data import calcular_metricas, ultima_data_atualizacao, cdi_acumulado
    from fundos_config_v2 import (FUNDOS, PERFIS_TATICA, PERFIS_METAS, PERFIS_BANDAS,
                                   fundos_por_macro, CLASSES_MACRO)
except ImportError as e:
    st.error(f"Dependência ausente: {e}")
    st.stop()

# ── Estado ────────────────────────────────────────────────────────────────────
for k, v in [("step", 1), ("quantum_file", None), ("metricas", None),
             ("aloc_classe", {}), ("aloc_fundo", {})]:
    if k not in st.session_state:
        st.session_state[k] = v

def fmt_pct(v):  return f"{v*100:.1f}%" if v is not None else "—"
def fmt_brl(v):
    if v is None: return "—"
    return "R$ {:,.0f}".format(v).replace(",","X").replace(".",",").replace("X",".")

BADGE = {"CDI":"#e8f5e9:#1b5e20",
         "Renda Fixa":"#e3f2fd:#1565c0",
         "Multimercados":"#ede7f6:#4527a0",
         "Ações":"#fce4ec:#880e4f"}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h2 style='margin:0 0 4px;color:#0a2744;font-size:22px;font-weight:600'>"
    "💎 Mercury · Gerador de Propostas</h2>", unsafe_allow_html=True)
st.divider()

passos = ["1 · Dados", "2 · Alocação", "3 · Gerar"]
html = '<div class="step-bar">'
for i, p in enumerate(passos, 1):
    cls = ("step-active" if i == st.session_state.step
           else "step-done" if i < st.session_state.step else "step-pending")
    html += f'<div class="step {cls}">{p}</div>'
st.markdown(html + "</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 1 — UPLOAD + DADOS DO CLIENTE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### Arquivo Quantum Axis")
        st.caption("Abra o Excel com QTLINK, aguarde atualizar e faça upload.")
        uploaded = st.file_uploader("quantum.xlsx", type=["xlsx"],
                                    label_visibility="collapsed")
        if uploaded:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(uploaded.read())
                fp = Path(tmp.name)
            try:
                met   = calcular_metricas(fp)
                dt    = ultima_data_atualizacao(fp)
                n_ok  = sum(1 for f in FUNDOS if f["nome_quantum"] in met
                            and met[f["nome_quantum"]].get("ret_12m") is not None)
                st.session_state.quantum_file = fp
                st.session_state.metricas     = met
                st.success(f"✓ {n_ok}/13 fundos · dados até {dt.strftime('%d/%m/%Y')}")
            except Exception as e:
                st.error(f"Erro: {e}")

        if st.session_state.metricas:
            st.markdown("**Rentabilidade 12m**")
            for f in FUNDOS:
                m   = st.session_state.metricas.get(f["nome_quantum"], {})
                r12 = m.get("ret_12m")
                pct = m.get("pct_cdi")
                bg, fg = BADGE.get(f["macro_classe"], "#eee:#333").split(":")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;'
                    f'padding:6px 0;border-bottom:1px solid #f5f5f5;font-size:13px">'
                    f'<span style="background:{bg};color:{fg};padding:2px 8px;'
                    f'border-radius:99px;font-size:10px;font-weight:600;flex-shrink:0">'
                    f'{f["macro_classe"]}</span>'
                    f'<span style="flex:1;color:#444">{f["nome_quantum"][:40]}</span>'
                    f'<span style="font-weight:600;color:#0a2744">{fmt_pct(r12)}</span>'
                    f'<span style="color:#aaa;font-size:11px;min-width:64px;text-align:right">'
                    f'{fmt_pct(pct)} CDI</span></div>',
                    unsafe_allow_html=True)

    with col2:
        st.markdown("#### Dados do cliente")
        nome_cliente = st.text_input("Nome do cliente")
        valor = st.number_input("Valor da proposta (R$)",
                                min_value=50_000, max_value=100_000_000,
                                value=500_000, step=50_000, format="%d")
        perfil = st.selectbox("Perfil de risco",
            ["Conservador", "Moderado", "Balanceado", "Crescimento", "Sofisticado"])

        tatica = PERFIS_TATICA[perfil]
        meta   = PERFIS_METAS[perfil]
        st.markdown("**Alocação tática sugerida**")
        cols4 = st.columns(4)
        for i, mc in enumerate(CLASSES_MACRO):
            with cols4[i]:
                st.metric(mc, fmt_pct(tatica[mc]), fmt_brl(tatica[mc]*valor))
        st.caption(f"Meta: {meta['retorno_pct_cdi']*100:.0f}% CDI · "
                   f"Vol: {meta['vol']*100:.1f}% a.a.")

        st.markdown("---")
        can_go = bool(nome_cliente) and st.session_state.quantum_file is not None
        if not can_go:
            st.caption("Preencha os dados e faça upload para continuar.")
        if st.button("Próximo →", disabled=not can_go, use_container_width=True):
            st.session_state.cliente_nome   = nome_cliente
            st.session_state.cliente_valor  = valor
            st.session_state.cliente_perfil = perfil
            # Inicializar alocação de classes com a tática
            st.session_state.aloc_classe = {mc: tatica[mc] for mc in CLASSES_MACRO}
            # Inicializar alocação de fundos: todos zerados (assessor preenche)
            st.session_state.aloc_fundo = {
                f["nome_quantum"]: 0.0 for f in FUNDOS
            }
            st.session_state.step = 2
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 2 — ALOCAÇÃO POR CLASSE E POR FUNDO
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    perfil  = st.session_state.cliente_perfil
    valor   = st.session_state.cliente_valor
    tatica  = PERFIS_TATICA[perfil]
    bandas  = PERFIS_BANDAS[perfil]
    metricas = st.session_state.metricas or {}

    st.markdown(f"#### Alocação — {st.session_state.cliente_nome} · {perfil}")

    # ── Seção A: alocação por macro-classe (sliders) ─────────────────────────
    st.markdown('<div class="section-title">1 · % por classe</div>',
                unsafe_allow_html=True)
    st.caption("Tática sugerida já preenchida. Ajuste se necessário.")

    aloc_classe = {}
    total_classe = 0.0

    col_sl, col_res = st.columns([3, 2], gap="large")
    with col_sl:
        for mc in CLASSES_MACRO:
            tac = tatica[mc] * 100
            mn, mx = bandas[mc]
            cur = st.session_state.aloc_classe.get(mc, tatica[mc]) * 100
            v = st.slider(f"{mc}", 0.0, 100.0, float(round(cur, 1)), 0.5,
                          format="%.1f%%",
                          help=f"Tática {tac:.0f}% · banda {mn*100:.0f}%–{mx*100:.0f}%")
            aloc_classe[mc] = v / 100
            total_classe   += v

    with col_res:
        st.markdown("**Resumo**")
        for mc in CLASSES_MACRO:
            v = aloc_classe.get(mc, 0)
            val_mc = v * valor
            bg, fg = BADGE.get(mc, "#eee:#333").split(":")
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f'padding:5px 0;font-size:13px">'
                f'<span style="background:{bg};color:{fg};padding:2px 8px;'
                f'border-radius:99px;font-size:10px;font-weight:600">{mc}</span>'
                f'<span style="font-weight:600;color:#0a2744">{v*100:.1f}%</span>'
                f'<span style="color:#888;font-size:12px">{fmt_brl(val_mc)}</span>'
                f'</div>', unsafe_allow_html=True)
        t = round(total_classe, 1)
        if abs(t - 100) < 0.1:
            st.markdown(f'<div class="ok-box">Total: {t:.1f}% ✓</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box">Total: {t:.1f}% — falta ajustar '
                        f'{abs(t-100):.1f}p.p.</div>', unsafe_allow_html=True)

        avisos = []
        for mc in CLASSES_MACRO:
            mn, mx = bandas[mc]
            v = aloc_classe[mc]
            if v < mn or v > mx:
                avisos.append(f"{mc} ({v*100:.0f}%) fora da banda "
                              f"{mn*100:.0f}%–{mx*100:.0f}%")
        if avisos:
            st.markdown('<div class="warn-box">⚠ Fora da banda:<br>' +
                        "<br>".join(avisos) + "</div>", unsafe_allow_html=True)

    # ── Seção B: mix de fundos por classe ────────────────────────────────────
    st.markdown('<div class="section-title">2 · Mix de fundos por classe</div>',
                unsafe_allow_html=True)
    st.caption("Defina o peso de cada fundo dentro da classe (deve somar 100%).")

    aloc_fundo = dict(st.session_state.aloc_fundo)
    erros_classe = []

    for mc in CLASSES_MACRO:
        fundos_mc = fundos_por_macro(mc)
        if not fundos_mc:
            continue

        pct_classe = aloc_classe.get(mc, 0)
        val_classe = pct_classe * valor
        bg, fg = BADGE.get(mc, "#eee:#333").split(":")

        st.markdown(
            f'<div class="class-card">'
            f'<div class="class-name">'
            f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:99px;font-size:11px;margin-right:8px">{mc}</span>'
            f'{pct_classe*100:.1f}% · {fmt_brl(val_classe)}</div>',
            unsafe_allow_html=True)

        # Cabeçalho
        st.markdown(
            '<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;'
            'font-size:11px;color:#aaa;padding:4px 0;border-bottom:1px solid #eee">'
            '<span>Fundo</span><span style="text-align:right">% na classe</span>'
            '<span style="text-align:right">Valor</span>'
            '<span style="text-align:right">12m</span>'
            '<span style="text-align:right">Vol</span></div>',
            unsafe_allow_html=True)

        total_mc = 0.0
        for f in fundos_mc:
            nq  = f["nome_quantum"]
            m   = metricas.get(nq, {})
            r12 = m.get("ret_12m")
            vol = m.get("vol_12m")
            cur_pct = aloc_fundo.get(nq, 0.0)

            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
            with c1:
                st.markdown(
                    f'<div style="font-size:12px;color:#333;padding:6px 0">'
                    f'{nq[:45]}</div>', unsafe_allow_html=True)
            with c2:
                novo_pct = st.number_input(
                    f"_{nq}_pct", min_value=0.0, max_value=100.0,
                    value=float(round(cur_pct, 1)), step=5.0, format="%.1f",
                    label_visibility="collapsed", key=f"pct_{nq}")
                aloc_fundo[nq] = novo_pct
                total_mc += novo_pct
            with c3:
                val_f = (novo_pct / 100) * val_classe if pct_classe > 0 else 0
                st.markdown(
                    f'<div style="font-size:12px;color:#555;padding:6px 0;text-align:right">'
                    f'{fmt_brl(val_f)}</div>', unsafe_allow_html=True)
            with c4:
                st.markdown(
                    f'<div style="font-size:12px;font-weight:600;color:#0a2744;'
                    f'padding:6px 0;text-align:right">{fmt_pct(r12)}</div>',
                    unsafe_allow_html=True)
            with c5:
                st.markdown(
                    f'<div style="font-size:12px;color:#888;padding:6px 0;text-align:right">'
                    f'{fmt_pct(vol)}</div>', unsafe_allow_html=True)

        t = round(total_mc, 1)
        if abs(t - 100) < 0.1:
            st.markdown(f'<div class="ok-box" style="margin-top:6px">Total: {t:.1f}% ✓</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box" style="margin-top:6px">'
                        f'Total: {t:.1f}% — falta {abs(t-100):.1f}p.p.</div>',
                        unsafe_allow_html=True)
            erros_classe.append(mc)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Navegação ─────────────────────────────────────────────────────────────
    st.markdown("---")
    cb, cf = st.columns([1, 3])
    with cb:
        if st.button("← Voltar"):
            st.session_state.aloc_classe = aloc_classe
            st.session_state.aloc_fundo  = aloc_fundo
            st.session_state.step = 1
            st.rerun()
    with cf:
        classe_ok = abs(round(total_classe, 1) - 100) < 0.1
        fundos_ok = len(erros_classe) == 0
        can_go = classe_ok and fundos_ok
        if not can_go:
            msgs = []
            if not classe_ok: msgs.append("classes não somam 100%")
            if erros_classe:  msgs.append(f"mix incompleto em: {', '.join(erros_classe)}")
            st.caption("⚠ " + " · ".join(msgs))
        if st.button("Gerar proposta →", disabled=not can_go,
                     use_container_width=True):
            st.session_state.aloc_classe = aloc_classe
            st.session_state.aloc_fundo  = aloc_fundo
            st.session_state.step = 3
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 3 — REVISÃO E DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    nome     = st.session_state.cliente_nome
    valor    = st.session_state.cliente_valor
    perfil   = st.session_state.cliente_perfil
    aloc_cl  = st.session_state.aloc_classe
    aloc_fd  = st.session_state.aloc_fundo
    metricas = st.session_state.metricas or {}

    st.markdown(f"#### Proposta — {nome}")

    # Cabeçalho
    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val in zip([c1,c2,c3,c4],
                              ["Cliente","Valor","Perfil","Data"],
                              [nome, fmt_brl(valor), perfil,
                               date.today().strftime("%d/%m/%Y")]):
        with col:
            st.metric(lbl, val)

    # Tabela completa
    st.markdown("**Composição detalhada**")
    import pandas as pd
    rows = []
    for mc in CLASSES_MACRO:
        pct_mc  = aloc_cl.get(mc, 0)
        val_mc  = pct_mc * valor
        fundos_mc = fundos_por_macro(mc)
        for f in fundos_mc:
            nq      = f["nome_quantum"]
            pct_fd  = aloc_fd.get(nq, 0) / 100   # % dentro da classe
            val_fd  = pct_fd * val_mc
            pct_tot = pct_fd * pct_mc              # % do total
            m       = metricas.get(nq, {})
            rows.append({
                "Classe":        mc,
                "Fundo":         nq[:55],
                "% Classe":      f"{aloc_fd.get(nq,0):.1f}%",
                "% Total":       f"{pct_tot*100:.1f}%",
                "Valor":         fmt_brl(val_fd),
                "Ret 12m":       fmt_pct(m.get("ret_12m")),
                "YTD":           fmt_pct(m.get("ytd")),
                "% CDI":         fmt_pct(m.get("pct_cdi")),
                "Vol":           fmt_pct(m.get("vol_12m")),
            })

    df = pd.DataFrame(rows)
    # Só mostrar linhas onde assessor alocou algo
    df_show = df[df["% Total"] != "0.0%"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # Downloads
    st.markdown("---")
    cp, cd, cn = st.columns([1, 1, 1])
    with cp:
        try:
            from gerar_ppt import gerar_ppt_proposta
            ppt = gerar_ppt_proposta(nome, valor, perfil, aloc_cl, aloc_fd, metricas)
            st.download_button("⬇ Baixar PPT", ppt,
                               f"Proposta_{nome.replace(' ','_')}.pptx",
                               "application/vnd.openxmlformats-officedocument"
                               ".presentationml.presentation",
                               use_container_width=True)
        except Exception as e:
            st.info(f"PPT em construção: {e}")
    with cd:
        try:
            from gerar_pdf import gerar_pdf_proposta
            pdf = gerar_pdf_proposta(nome, valor, perfil, aloc_cl, aloc_fd, metricas)
            st.download_button("⬇ Baixar PDF", pdf,
                               f"Proposta_{nome.replace(' ','_')}.pdf",
                               "application/pdf", use_container_width=True)
        except Exception as e:
            st.info(f"PDF em construção: {e}")
    with cn:
        if st.button("Nova proposta", use_container_width=True):
            for k in ["step","cliente_nome","cliente_valor","cliente_perfil",
                      "aloc_classe","aloc_fundo"]:
                st.session_state.pop(k, None)
            st.session_state.step = 1
            st.rerun()
