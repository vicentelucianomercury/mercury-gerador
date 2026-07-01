"""
app.py — Mercury Wealth Management · Gerador de Propostas v2
"""
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Mercury — Propostas", page_icon="💎",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#f8f8f6; }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:2rem; max-width:940px; }
.step-bar{display:flex;gap:8px;margin-bottom:24px}
.step{padding:5px 16px;border-radius:99px;font-size:12px;font-weight:500}
.step-active{background:#0a2744;color:#fff}
.step-done{background:#e8f5e9;color:#2e7d32}
.step-pending{background:#f0f0ec;color:#aaa}
.group-header{font-size:11px;font-weight:600;color:#fff;background:#0a2744;
  padding:4px 10px;border-radius:4px;margin:12px 0 4px;display:inline-block}
.class-card{background:#fff;border:1px solid #e5e5e0;border-radius:10px;
  padding:12px 14px;margin-bottom:8px}
.ok-box{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;
  padding:7px 12px;font-size:12px;color:#2e7d32;margin:6px 0}
.warn-box{background:#fff8e1;border:1px solid #ffe082;border-radius:6px;
  padding:7px 12px;font-size:12px;color:#795548;margin:6px 0}
</style>
""", unsafe_allow_html=True)

try:
    from mercury_data import calcular_metricas, ultima_data_atualizacao, cdi_acumulado
    from fundos_config_v2 import (FUNDOS, CLASSES, CLASSES_RF, PERFIS_TATICA,
                                   PERFIS_BANDAS, PERFIS_METAS, fundos_por_classe)
except ImportError as e:
    st.error(f"Dependência ausente: {e}")
    st.stop()

# ── Estado ────────────────────────────────────────────────────────────────────
for k, v in [("step",1),("quantum_file",None),("metricas",None),
             ("aloc_classe",{}),("aloc_fundo",{})]:
    if k not in st.session_state: st.session_state[k] = v

def fmt_pct(v): return f"{v*100:.1f}%" if v is not None else "—"
def fmt_brl(v):
    if v is None: return "—"
    return "R$ {:,.0f}".format(v).replace(",","X").replace(".",",").replace("X",".")

# Cores por classe
CORES = {
    "Caixa":                  "#e8f5e9:#1b5e20",
    "Crédito Corporativo":    "#e3f2fd:#1565c0",
    "Crédito Estruturado":    "#bbdefb:#0d47a1",
    "Renda Fixa Inflação/Pré":"#e8eaf6:#283593",
    "Multimercado":           "#ede7f6:#4527a0",
    "Offshore USD":           "#fff9c4:#f57f17",
    "Offshore BRL":           "#fff3e0:#e65100",
    "Renda Variável":         "#fce4ec:#880e4f",
    "Imobiliários":           "#f3e5f5:#6a1b9a",
    "Private Equity/VC":      "#efebe9:#3e2723",
}

def badge(classe):
    bg, fg = CORES.get(classe, "#eee:#333").split(":")
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:99px;font-size:10px;font-weight:600">{classe}</span>')

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h2 style='margin:0 0 4px;color:#0a2744;font-size:22px;font-weight:600'>"
            "💎 Mercury · Gerador de Propostas</h2>", unsafe_allow_html=True)
st.divider()

passos = ["1 · Dados","2 · Alocação","3 · Gerar"]
html = '<div class="step-bar">'
for i, p in enumerate(passos,1):
    cls = ("step-active" if i==st.session_state.step
           else "step-done" if i<st.session_state.step else "step-pending")
    html += f'<div class="step {cls}">{p}</div>'
st.markdown(html+"</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 1
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    col1, col2 = st.columns([1,1], gap="large")

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
                met = calcular_metricas(fp)
                dt  = ultima_data_atualizacao(fp)
                n   = sum(1 for f in FUNDOS
                          if met.get(f["nome_quantum"],{}).get("ret_12m") is not None)
                st.session_state.quantum_file = fp
                st.session_state.metricas     = met
                st.success(f"✓ {n}/13 fundos · dados até {dt.strftime('%d/%m/%Y')}")
            except Exception as e:
                st.error(f"Erro: {e}")

        if st.session_state.metricas:
            st.markdown("**Rentabilidade 12m**")
            for f in FUNDOS:
                m   = st.session_state.metricas.get(f["nome_quantum"],{})
                r12 = m.get("ret_12m")
                pct = m.get("pct_cdi")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'padding:5px 0;border-bottom:1px solid #f5f5f5;font-size:12px">'
                    f'{badge(f["classe"])}'
                    f'<span style="flex:1;color:#444">{f["nome_quantum"][:42]}</span>'
                    f'<span style="font-weight:600;color:#0a2744">{fmt_pct(r12)}</span>'
                    f'<span style="color:#aaa;font-size:11px;min-width:60px;'
                    f'text-align:right">{fmt_pct(pct)} CDI</span></div>',
                    unsafe_allow_html=True)

    with col2:
        st.markdown("#### Dados do cliente")
        nome_cliente = st.text_input("Nome do cliente")
        valor = st.number_input("Valor da proposta (R$)", min_value=50_000,
                                max_value=100_000_000, value=500_000,
                                step=50_000, format="%d")
        perfil = st.selectbox("Perfil de risco",
            ["Conservador","Moderado","Balanceado","Crescimento","Sofisticado"])

        tatica = PERFIS_TATICA[perfil]
        meta   = PERFIS_METAS[perfil]
        st.markdown("**Alocação tática sugerida**")

        # Mostrar RF agrupado + outras classes
        rf_total = sum(tatica[c] for c in CLASSES_RF)
        outros = {c: tatica[c] for c in CLASSES if c not in CLASSES_RF and tatica[c]>0}
        c1,c2 = st.columns(2)
        with c1:
            st.metric("Renda Fixa (grupo)", fmt_pct(rf_total), fmt_brl(rf_total*valor))
            for c in CLASSES_RF:
                if tatica[c] > 0:
                    st.caption(f"  · {c}: {tatica[c]*100:.1f}%")
        with c2:
            for c, v in outros.items():
                st.metric(c, fmt_pct(v), fmt_brl(v*valor))

        st.caption(f"Objetivo: {meta['objetivo']} · Vol: {meta['vol']*100:.0f}%")
        st.markdown("---")
        can_go = bool(nome_cliente) and st.session_state.quantum_file is not None
        if not can_go:
            st.caption("Preencha os dados e faça upload para continuar.")
        if st.button("Próximo →", disabled=not can_go, use_container_width=True):
            st.session_state.cliente_nome   = nome_cliente
            st.session_state.cliente_valor  = valor
            st.session_state.cliente_perfil = perfil
            st.session_state.aloc_classe = {c: tatica[c] for c in CLASSES}
            st.session_state.aloc_fundo  = {f["nome_quantum"]:0.0 for f in FUNDOS}
            st.session_state.step = 2
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 2
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    perfil   = st.session_state.cliente_perfil
    valor    = st.session_state.cliente_valor
    tatica   = PERFIS_TATICA[perfil]
    bandas   = PERFIS_BANDAS[perfil]
    metricas = st.session_state.metricas or {}

    st.markdown(f"#### Alocação — {st.session_state.cliente_nome} · {perfil}")

    # ── Seção A: % por classe ─────────────────────────────────────────────────
    st.markdown("##### 1 · % por classe de ativo")
    st.caption("Tática sugerida já preenchida. Ajuste se necessário.")

    aloc_classe = {}
    col_sl, col_sum = st.columns([3,2], gap="large")

    with col_sl:
        # Grupo Renda Fixa
        st.markdown('<div class="group-header">Renda Fixa</div>',
                    unsafe_allow_html=True)
        for c in CLASSES_RF:
            mn, mx = bandas[c]
            cur = st.session_state.aloc_classe.get(c, tatica[c]) * 100
            v = st.slider(c, 0.0, 100.0, float(round(cur,1)), 0.5,
                          format="%.1f%%",
                          help=f"Tática {tatica[c]*100:.1f}% · banda {mn*100:.0f}%–{mx*100:.0f}%",
                          key=f"sl_{c}")
            aloc_classe[c] = v/100

        # Outras classes
        st.markdown('<div class="group-header">Outras classes</div>',
                    unsafe_allow_html=True)
        outras_classes = [c for c in CLASSES if c not in CLASSES_RF]
        for c in outras_classes:
            mn, mx = bandas[c]
            cur = st.session_state.aloc_classe.get(c, tatica[c]) * 100
            v = st.slider(c, 0.0, 100.0, float(round(cur,1)), 0.5,
                          format="%.1f%%",
                          help=f"Tática {tatica[c]*100:.1f}% · banda {mn*100:.0f}%–{mx*100:.0f}%",
                          key=f"sl_{c}")
            aloc_classe[c] = v/100

    total_cl = round(sum(aloc_classe.values())*100, 1)

    with col_sum:
        st.markdown("**Resumo**")
        rf_t = sum(aloc_classe[c] for c in CLASSES_RF)
        st.markdown(
            f'<div style="font-size:12px;font-weight:600;color:#0a2744;padding:4px 0">'
            f'Renda Fixa (grupo): {rf_t*100:.1f}% · {fmt_brl(rf_t*valor)}</div>',
            unsafe_allow_html=True)
        for c in CLASSES_RF:
            v = aloc_classe[c]
            if v > 0:
                bg, fg = CORES.get(c,"#eee:#333").split(":")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:6px;'
                    f'padding:3px 0 3px 12px;font-size:12px">'
                    f'<span style="background:{bg};color:{fg};padding:1px 6px;'
                    f'border-radius:99px;font-size:10px">{c}</span>'
                    f'<span>{v*100:.1f}%</span>'
                    f'<span style="color:#999">{fmt_brl(v*valor)}</span></div>',
                    unsafe_allow_html=True)

        st.markdown('<div style="margin:8px 0 4px;font-size:12px;font-weight:600;'
                    'color:#0a2744">Outras classes</div>', unsafe_allow_html=True)
        for c in outras_classes:
            v = aloc_classe[c]
            if v > 0:
                bg, fg = CORES.get(c,"#eee:#333").split(":")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:6px;'
                    f'padding:3px 0;font-size:12px">'
                    f'<span style="background:{bg};color:{fg};padding:1px 6px;'
                    f'border-radius:99px;font-size:10px">{c}</span>'
                    f'<span>{v*100:.1f}%</span>'
                    f'<span style="color:#999">{fmt_brl(v*valor)}</span></div>',
                    unsafe_allow_html=True)

        if abs(total_cl-100)<0.1:
            st.markdown(f'<div class="ok-box">Total: {total_cl:.1f}% ✓</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box">Total: {total_cl:.1f}% '
                        f'(falta {abs(total_cl-100):.1f}p.p.)</div>',
                        unsafe_allow_html=True)

        avisos = [f"{c}: {aloc_classe[c]*100:.0f}% fora da banda "
                  f"{bandas[c][0]*100:.0f}%–{bandas[c][1]*100:.0f}%"
                  for c in CLASSES
                  if aloc_classe[c]<bandas[c][0] or aloc_classe[c]>bandas[c][1]]
        if avisos:
            st.markdown('<div class="warn-box">⚠ Fora da banda:<br>'
                        + "<br>".join(avisos)+"</div>", unsafe_allow_html=True)

    # ── Seção B: mix por fundo ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 2 · Mix de fundos por classe")
    st.caption("Defina o peso de cada fundo dentro da classe (deve somar 100%). "
               "Classes sem fundo aprovado ficam em aberto.")

    aloc_fundo  = dict(st.session_state.aloc_fundo)
    erros_classe = []

    for c in CLASSES:
        fundos_c = fundos_por_classe(c)
        pct_c    = aloc_classe.get(c, 0)
        val_c    = pct_c * valor
        if pct_c == 0:
            continue  # não exibir classes zeradas

        bg, fg = CORES.get(c,"#eee:#333").split(":")

        st.markdown(
            f'<div class="class-card">'
            f'<div style="font-size:13px;font-weight:600;color:#0a2744;margin-bottom:8px">'
            f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:99px;font-size:11px;margin-right:8px">{c}</span>'
            f'{pct_c*100:.1f}% · {fmt_brl(val_c)}</div>',
            unsafe_allow_html=True)

        if not fundos_c:
            st.caption("Sem fundo aprovado nessa classe por enquanto.")
            st.markdown("</div>", unsafe_allow_html=True)
            continue

        # Cabeçalho da tabela
        hc1,hc2,hc3,hc4,hc5 = st.columns([3,1,1,1,1])
        with hc1: st.caption("Fundo")
        with hc2: st.caption("% na classe")
        with hc3: st.caption("Valor")
        with hc4: st.caption("Ret 12m")
        with hc5: st.caption("Vol")

        total_mc = 0.0
        for f in fundos_c:
            nq  = f["nome_quantum"]
            m   = metricas.get(nq,{})
            r12 = m.get("ret_12m")
            vol = m.get("vol_12m")
            cur = aloc_fundo.get(nq,0.0)
            fc1,fc2,fc3,fc4,fc5 = st.columns([3,1,1,1,1])
            with fc1:
                st.markdown(f'<div style="font-size:12px;color:#333;padding:5px 0">'
                            f'{nq[:50]}</div>', unsafe_allow_html=True)
            with fc2:
                novo = st.number_input("", min_value=0.0, max_value=100.0,
                                       value=float(round(cur,1)), step=5.0,
                                       format="%.1f", label_visibility="collapsed",
                                       key=f"pct_{nq}")
                aloc_fundo[nq] = novo
                total_mc += novo
            with fc3:
                vf = (novo/100)*val_c
                st.markdown(f'<div style="font-size:11px;color:#555;padding:5px 0;'
                            f'text-align:right">{fmt_brl(vf)}</div>',
                            unsafe_allow_html=True)
            with fc4:
                st.markdown(f'<div style="font-size:12px;font-weight:600;'
                            f'color:#0a2744;padding:5px 0;text-align:right">'
                            f'{fmt_pct(r12)}</div>', unsafe_allow_html=True)
            with fc5:
                st.markdown(f'<div style="font-size:11px;color:#888;padding:5px 0;'
                            f'text-align:right">{fmt_pct(vol)}</div>',
                            unsafe_allow_html=True)

        t = round(total_mc,1)
        if abs(t-100)<0.1:
            st.markdown(f'<div class="ok-box" style="margin-top:6px">'
                        f'Total: {t:.1f}% ✓</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box" style="margin-top:6px">'
                        f'Total: {t:.1f}% — falta {abs(t-100):.1f}p.p.</div>',
                        unsafe_allow_html=True)
            erros_classe.append(c)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Navegação ─────────────────────────────────────────────────────────────
    st.markdown("---")
    cb, cf = st.columns([1,3])
    with cb:
        if st.button("← Voltar"):
            st.session_state.aloc_classe = aloc_classe
            st.session_state.aloc_fundo  = aloc_fundo
            st.session_state.step = 1
            st.rerun()
    with cf:
        classe_ok = abs(total_cl-100)<0.1
        fundos_ok = len(erros_classe)==0
        if not (classe_ok and fundos_ok):
            msgs = []
            if not classe_ok: msgs.append("classes não somam 100%")
            if erros_classe:  msgs.append(f"mix incompleto: {', '.join(erros_classe)}")
            st.caption("⚠ " + " · ".join(msgs))
        if st.button("Gerar proposta →", disabled=not(classe_ok and fundos_ok),
                     use_container_width=True):
            st.session_state.aloc_classe = aloc_classe
            st.session_state.aloc_fundo  = aloc_fundo
            st.session_state.step = 3
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 3
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    nome     = st.session_state.cliente_nome
    valor    = st.session_state.cliente_valor
    perfil   = st.session_state.cliente_perfil
    aloc_cl  = st.session_state.aloc_classe
    aloc_fd  = st.session_state.aloc_fundo
    metricas = st.session_state.metricas or {}

    st.markdown(f"#### Proposta — {nome}")
    c1,c2,c3,c4 = st.columns(4)
    for col,lbl,val in zip([c1,c2,c3,c4],
                            ["Cliente","Valor","Perfil","Data"],
                            [nome,fmt_brl(valor),perfil,
                             date.today().strftime("%d/%m/%Y")]):
        with col: st.metric(lbl,val)

    st.markdown("**Composição detalhada**")
    import pandas as pd
    rows = []
    for c in CLASSES:
        pct_c = aloc_cl.get(c,0)
        if pct_c == 0: continue
        val_c = pct_c*valor
        fundos_c = fundos_por_classe(c)
        if fundos_c:
            for f in fundos_c:
                nq    = f["nome_quantum"]
                p_fd  = aloc_fd.get(nq,0)/100
                val_f = p_fd*val_c
                p_tot = p_fd*pct_c
                m     = metricas.get(nq,{})
                if val_f == 0: continue
                rows.append({"Classe":c,"Fundo":nq[:55],
                             "% Total":f"{p_tot*100:.1f}%",
                             "Valor":fmt_brl(val_f),
                             "Ret 12m":fmt_pct(m.get("ret_12m")),
                             "YTD":fmt_pct(m.get("ytd")),
                             "% CDI":fmt_pct(m.get("pct_cdi")),
                             "Vol":fmt_pct(m.get("vol_12m"))})
        else:
            rows.append({"Classe":c,"Fundo":"(sem fundo aprovado)",
                        "% Total":f"{pct_c*100:.1f}%",
                        "Valor":fmt_brl(val_c),
                        "Ret 12m":"—","YTD":"—","% CDI":"—","Vol":"—"})

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    cp,cd,cn = st.columns([1,1,1])
    with cp:
        try:
            from gerar_ppt import gerar_ppt_proposta
            ppt = gerar_ppt_proposta(nome,valor,perfil,aloc_cl,aloc_fd,metricas)
            st.download_button("⬇ Baixar PPT", ppt,
                               f"Proposta_{nome.replace(' ','_')}.pptx",
                               "application/vnd.openxmlformats-officedocument"
                               ".presentationml.presentation",
                               use_container_width=True)
        except Exception as e:
            st.info(f"PPT em construção")
    with cd:
        try:
            from gerar_pdf import gerar_pdf_proposta
            pdf = gerar_pdf_proposta(nome,valor,perfil,aloc_cl,aloc_fd,metricas)
            st.download_button("⬇ Baixar PDF", pdf,
                               f"Proposta_{nome.replace(' ','_')}.pdf",
                               "application/pdf", use_container_width=True)
        except Exception as e:
            st.info(f"PDF em construção")
    with cn:
        if st.button("Nova proposta", use_container_width=True):
            for k in ["step","cliente_nome","cliente_valor","cliente_perfil",
                      "aloc_classe","aloc_fundo"]:
                st.session_state.pop(k,None)
            st.session_state.step = 1
            st.rerun()
