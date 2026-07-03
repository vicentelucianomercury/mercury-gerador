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
[data-testid="stAppViewContainer"]{background:#f5f5f2}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:2rem;max-width:980px}
.step-bar{display:flex;gap:8px;margin-bottom:24px}
.step{padding:6px 18px;border-radius:99px;font-size:12px;font-weight:500}
.step-active{background:#1d7490;color:#fff}
.step-done{background:#e8f5e9;color:#2e7d32}
.step-pending{background:#ebebeb;color:#aaa}
.group-lbl{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:#fff;background:#1d7490;padding:3px 10px;border-radius:4px;
  display:inline-block;margin:16px 0 6px}
.class-card{background:#fff;border:1px solid #e0e0dc;border-radius:12px;
  padding:16px 20px;margin-bottom:10px}
.class-title{font-size:13px;font-weight:600;color:#231f20;
  display:flex;align-items:center;gap:8px;margin-bottom:12px}
.ok-box{background:#f0faf2;border:1px solid #b2dfdb;border-radius:6px;
  padding:7px 14px;font-size:12px;color:#1b5e20;margin-top:8px;text-align:center}
.warn-box{background:#fffde7;border:1px solid #fff176;border-radius:6px;
  padding:7px 14px;font-size:12px;color:#795548;margin-top:8px;text-align:center}
</style>
""", unsafe_allow_html=True)

try:
    from mercury_data import calcular_metricas, ultima_data_atualizacao, cdi_acumulado
    import fundos_config_v2 as fcfg
    from fundos_config_v2 import (FUNDOS, CLASSES, CLASSES_RF, PERFIS_TATICA,
                                   PERFIS_BANDAS, PERFIS_METAS, fundos_por_classe)
    from matriz_loader import carregar_matriz
except ImportError as e:
    st.error(f"Dependência ausente: {e}"); st.stop()

for k,v in [("step",1),("quantum_file",None),("metricas",None),
            ("aloc_classe",{}),("aloc_fundo",{}),
            # Matriz vinda do Excel (persistida na sessão — subir 1x serve
            # p/ várias propostas; só pede de novo se a página recarregar)
            ("matriz_bytes",None),("matriz_nome",""),("matriz_cfg",None),
            ("matriz_hash",None),("matriz_confirmada",False)]:
    if k not in st.session_state: st.session_state[k] = v

# A cada rerun, sincroniza o módulo de config com a matriz da SESSÃO.
# (Mutação de módulo é estado de processo; isto garante que cada execução
#  reflita a matriz desta sessão — e que os geradores de PDF/PPT, que
#  importam de fundos_config_v2 em tempo de chamada, vejam a mesma matriz.)
if st.session_state.matriz_cfg is not None and st.session_state.matriz_confirmada:
    fcfg.aplicar_matriz(st.session_state.matriz_cfg)
else:
    fcfg.restaurar_padrao()

def fmt_pct(v): return f"{v*100:.1f}%" if v is not None else "—"
def fmt_brl(v):
    if v is None: return "—"
    return "R$ {:,.0f}".format(v).replace(",","X").replace(".",",").replace("X",".")

CORES = {
    "Caixa":                  ("#e8f5e9","#1b5e20"),
    "Crédito Corporativo":    ("#e3f2fd","#1565c0"),
    "Crédito Estruturado":    ("#dce8fb","#0d47a1"),
    "Renda Fixa Inflação/Pré":("#e8eaf6","#283593"),
    "Multimercado":           ("#ede7f6","#4527a0"),
    "Offshore USD":           ("#fff9c4","#f57f17"),
    "Offshore BRL":           ("#fff3e0","#e65100"),
    "Renda Variável":         ("#fce4ec","#880e4f"),
    "Imobiliários":           ("#f3e5f5","#6a1b9a"),
    "Private Equity/VC":      ("#efebe9","#3e2723"),
}

def badge_html(c):
    bg,fg = CORES.get(c,("#eee","#333"))
    return (f'<span style="background:{bg};color:{fg};padding:3px 10px;'
            f'border-radius:99px;font-size:11px;font-weight:600">{c}</span>')

# Header
from pathlib import Path as _P
_logo = _P(__file__).parent / "assets" / "logo.png"
_c1, _c2 = st.columns([1, 6])
with _c1:
    if _logo.exists():
        st.image(str(_logo), width=90)
with _c2:
    st.markdown("<h2 style='margin:14px 0 0;color:#231f20;font-size:22px;"
                "font-weight:700;letter-spacing:.02em'>Gerador de Propostas</h2>"
                "<div style='color:#1d7490;font-size:11px;font-weight:600;"
                "letter-spacing:.14em'>MERCURY WEALTH MANAGEMENT</div>",
                unsafe_allow_html=True)
st.divider()

passos = ["1 · Dados","2 · Alocação","3 · Gerar"]
html = '<div class="step-bar">'
for i,p in enumerate(passos,1):
    cls = ("step-active" if i==st.session_state.step
           else "step-done" if i<st.session_state.step else "step-pending")
    html += f'<div class="step {cls}">{p}</div>'
st.markdown(html+"</div>", unsafe_allow_html=True)

# ── Qual matriz está em uso (sempre visível — o usuário nunca deve gerar
#    proposta sem saber se usou a planilha nova ou o padrão do sistema)
if st.session_state.matriz_confirmada and st.session_state.matriz_cfg:
    st.markdown(
        f'<div class="ok-box" style="text-align:left;margin:-8px 0 16px">'
        f'Matriz em uso: <b>planilha enviada</b> '
        f'({st.session_state.matriz_nome}) ✓</div>',
        unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="warn-box" style="text-align:left;margin:-8px 0 16px">'
        'Matriz em uso: <b>padrão do sistema</b> (nenhuma planilha da matriz '
        'enviada/confirmada — os valores são os fixos do código).</div>',
        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 1
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    col1,col2 = st.columns([1,1], gap="large")
    with col1:
        st.markdown("#### Arquivo Quantum Axis")
        st.caption("Abra o Excel com QTLINK, aguarde atualizar e faça upload.")
        uploaded = st.file_uploader("quantum.xlsx", type=["xlsx"],
                                    label_visibility="collapsed")
        if uploaded:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(uploaded.read()); fp = Path(tmp.name)
            try:
                met = calcular_metricas(fp)
                dt  = ultima_data_atualizacao(fp)
                n   = sum(1 for f in FUNDOS
                          if met.get(f["nome_quantum"],{}).get("ret_12m") is not None)
                st.session_state.quantum_file = fp
                st.session_state.metricas     = met
                # Se a matriz veio antes das cotas, refaz o cruzamento
                # fundo↔série com as séries recém-carregadas
                if st.session_state.matriz_bytes is not None:
                    confirmada = st.session_state.matriz_confirmada
                    st.session_state.matriz_cfg = carregar_matriz(
                        st.session_state.matriz_bytes,
                        st.session_state.matriz_nome,
                        nomes_series=set(met.keys()))
                    st.session_state.matriz_confirmada = (
                        confirmada and st.session_state.matriz_cfg.valida)
                st.success(f"✓ {n}/{len(FUNDOS)} fundos · dados até {dt.strftime('%d/%m/%Y')}")
                faltando = [f["nome_quantum"] for f in FUNDOS
                            if f["nome_quantum"] not in met]
                if faltando:
                    st.warning("⚠ Fundos aprovados NÃO encontrados no arquivo "
                               "(verifique se o nome mudou na Quantum): "
                               + "; ".join(x[:40] for x in faltando))
            except Exception as e:
                st.error(f"Erro: {e}")

        # ── Planilha da Matriz (fundos + táticas + bandas) — opcional ────────
        st.markdown("#### Planilha da Matriz")
        st.caption("Excel com as abas “Matriz Editavel” e “Lista de Fundos "
                   "Aprovados”. Sem ela, o app usa a matriz padrão do sistema.")
        up_mx = st.file_uploader("matriz.xlsx", type=["xlsx"],
                                 label_visibility="collapsed", key="up_matriz")
        if up_mx is not None:
            raw = up_mx.getvalue()
            h = hash(raw)
            if h != st.session_state.matriz_hash:
                # arquivo novo (ou corrigido): reprocessa e exige nova confirmação
                series = (set(st.session_state.metricas.keys())
                          if st.session_state.metricas else None)
                st.session_state.matriz_cfg = carregar_matriz(
                    raw, up_mx.name, nomes_series=series)
                st.session_state.matriz_bytes = raw
                st.session_state.matriz_nome  = up_mx.name
                st.session_state.matriz_hash  = h
                st.session_state.matriz_confirmada = False

        cfg_mx = st.session_state.matriz_cfg
        if cfg_mx is not None:
            if not cfg_mx.valida:
                st.error("A planilha da matriz tem problemas e **não será "
                         "usada** até serem corrigidos:")
                for e in cfg_mx.erros:
                    st.markdown(f"- ✗ {e}")
                st.caption("Corrija a planilha e envie novamente. Enquanto "
                           "isso, não é possível avançar.")
            else:
                for a in cfg_mx.avisos:
                    st.warning(a)
                n_perfis = len(cfg_mx.tatica)
                n_fundos = len(cfg_mx.fundos)
                st.markdown(f"**Li da planilha:** {n_perfis} perfis · "
                            f"{n_fundos} fundos. Confira as táticas:")
                # prévia: classes × perfis (só linhas com alguma alocação)
                perfis_l = list(cfg_mx.tatica.keys())
                linhas = []
                for c in CLASSES:
                    vals = [cfg_mx.tatica[p].get(c, 0.0) for p in perfis_l]
                    if any(v > 0 for v in vals):
                        linhas.append([c] + [f"{v*100:.1f}%".replace(".", ",")
                                             for v in vals])
                import pandas as _pd
                st.dataframe(
                    _pd.DataFrame(linhas, columns=["Classe"] + perfis_l),
                    hide_index=True, use_container_width=True)
                if st.session_state.matriz_confirmada:
                    st.success("Matriz confirmada — em uso nesta sessão.")
                else:
                    st.info("Revise acima. A matriz só substitui o padrão "
                            "depois que você confirmar.")
                    if st.button("✓ Confirmar e usar esta matriz",
                                 use_container_width=True):
                        st.session_state.matriz_confirmada = True
                        st.rerun()

        if st.session_state.metricas:
            st.markdown("**Rentabilidade 12m**")
            for f in FUNDOS:
                m = st.session_state.metricas.get(f["nome_quantum"],{})
                r12 = m.get("ret_12m"); pct = m.get("pct_cdi")
                bg,fg = CORES.get(f["classe"],("#eee","#333"))
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'padding:6px 0;border-bottom:1px solid #f0f0ec;font-size:12px">'
                    f'<span style="background:{bg};color:{fg};padding:2px 8px;'
                    f'border-radius:99px;font-size:10px;font-weight:600;'
                    f'white-space:nowrap">{f["classe"]}</span>'
                    f'<span style="flex:1;color:#444">{f["nome_quantum"][:42]}</span>'
                    f'<span style="font-weight:600;color:#231f20;min-width:40px;'
                    f'text-align:right">{fmt_pct(r12)}</span>'
                    f'<span style="color:#bbb;font-size:11px;min-width:58px;'
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
        tatica = PERFIS_TATICA[perfil]; meta = PERFIS_METAS[perfil]
        st.markdown("**Alocação tática sugerida**")
        rf_total = sum(tatica[c] for c in CLASSES_RF)
        c1,c2 = st.columns(2)
        with c1:
            st.metric("Renda Fixa (grupo)", fmt_pct(rf_total), fmt_brl(rf_total*valor))
            for c in CLASSES_RF:
                if tatica[c]>0: st.caption(f"  · {c}: {tatica[c]*100:.1f}%")
        with c2:
            for c in CLASSES:
                if c not in CLASSES_RF and tatica[c]>0:
                    st.metric(c, fmt_pct(tatica[c]), fmt_brl(tatica[c]*valor))
        st.caption(f"Objetivo: {meta['objetivo']} · Vol: {meta['vol']*100:.0f}%")
        st.markdown("---")
        # Estado da matriz: "padrao" (sem planilha) e "confirmada" liberam;
        # "invalida" e "pendente de confirmação" travam.
        mx = st.session_state.matriz_cfg
        matriz_ok = (mx is None) or (mx.valida and st.session_state.matriz_confirmada)
        can_go = bool(nome_cliente) and st.session_state.quantum_file is not None \
                 and matriz_ok
        if not can_go:
            if mx is not None and not mx.valida:
                st.caption("Corrija a planilha da matriz (erros ao lado) para continuar.")
            elif mx is not None and not st.session_state.matriz_confirmada:
                st.caption("Confirme a matriz enviada (ou remova o arquivo) para continuar.")
            else:
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

    # ── Sliders por classe ────────────────────────────────────────────────────
    st.markdown("##### 1 · % por classe de ativo")
    st.caption("Tática sugerida já preenchida. Ajuste se necessário.")
    aloc_classe = {}
    col_sl,col_sum = st.columns([3,2], gap="large")
    with col_sl:
        st.markdown('<div class="group-lbl">Renda Fixa</div>', unsafe_allow_html=True)
        for c in CLASSES_RF:
            mn,mx = bandas[c]
            cur = st.session_state.aloc_classe.get(c, tatica[c])*100
            v = st.slider(c, 0.0, 100.0, float(round(cur,1)), 0.5,
                          format="%.1f%%",
                          help=f"Tática {tatica[c]*100:.1f}% · banda {mn*100:.0f}%–{mx*100:.0f}%",
                          key=f"sl_{c}")
            aloc_classe[c] = v/100
        st.markdown('<div class="group-lbl">Outras classes</div>', unsafe_allow_html=True)
        for c in [x for x in CLASSES if x not in CLASSES_RF]:
            mn,mx = bandas[c]
            cur = st.session_state.aloc_classe.get(c, tatica[c])*100
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
            f'<div style="font-size:13px;font-weight:600;color:#231f20;'
            f'padding:6px 0;border-bottom:1px solid #eee;margin-bottom:4px">'
            f'Renda Fixa (grupo) — {rf_t*100:.1f}%</div>', unsafe_allow_html=True)
        for c in CLASSES_RF:
            v = aloc_classe[c]
            if v>0:
                bg,fg = CORES.get(c,("#eee","#333"))
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;padding:4px 0 4px 10px;font-size:12px">'
                    f'<span style="background:{bg};color:{fg};padding:1px 8px;'
                    f'border-radius:99px;font-size:10px">{c}</span>'
                    f'<span style="font-weight:600">{v*100:.1f}%</span>'
                    f'<span style="color:#999">{fmt_brl(v*valor)}</span></div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;font-weight:600;color:#231f20;'
                    'padding:8px 0 4px">Outras</div>', unsafe_allow_html=True)
        for c in [x for x in CLASSES if x not in CLASSES_RF]:
            v = aloc_classe[c]
            if v>0:
                bg,fg = CORES.get(c,("#eee","#333"))
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;padding:4px 0;font-size:12px">'
                    f'<span style="background:{bg};color:{fg};padding:1px 8px;'
                    f'border-radius:99px;font-size:10px">{c}</span>'
                    f'<span style="font-weight:600">{v*100:.1f}%</span>'
                    f'<span style="color:#999">{fmt_brl(v*valor)}</span></div>',
                    unsafe_allow_html=True)
        st.markdown("---")
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
        for av in avisos:
            st.markdown(f'<div class="warn-box">⚠ {av}</div>', unsafe_allow_html=True)

    # ── Mix por fundo (%  do TOTAL da carteira) ───────────────────────────────
    st.markdown("---")
    st.markdown("##### 2 · Mix de fundos")
    st.caption("Informe o % de cada fundo em relação ao **total da carteira**. "
               "A soma dentro de cada classe deve igualar o % da classe.")

    aloc_fundo   = dict(st.session_state.aloc_fundo)
    erros_classe = []

    for c in CLASSES:
        pct_c = aloc_classe.get(c,0)
        val_c = pct_c * valor
        if pct_c == 0: continue
        fundos_c = fundos_por_classe(c)
        bg,fg = CORES.get(c,("#eee","#333"))

        st.markdown(
            f'<div class="class-card">'
            f'<div class="class-title">'
            f'<span style="background:{bg};color:{fg};padding:3px 12px;'
            f'border-radius:99px;font-size:11px;font-weight:600">{c}</span>'
            f'<span style="color:#555">{pct_c*100:.1f}% da carteira</span>'
            f'<span style="color:#aaa;font-size:12px">·</span>'
            f'<span style="color:#231f20;font-weight:600">{fmt_brl(val_c)}</span>'
            f'</div>', unsafe_allow_html=True)

        if not fundos_c:
            st.caption("Sem fundo aprovado nessa classe.")
            st.markdown("</div>", unsafe_allow_html=True)
            continue

        # Cabeçalho
        h0,h1,h2,h3,h4,h5,h6,h7 = st.columns([3.2,1,1.2,0.9,0.9,0.9,0.9,0.9])
        for col,lbl in zip([h0,h1,h2,h3,h4,h5,h6,h7],
                           ["Fundo","% total","Valor","Ret 6m","Ret 12m","Ret 24m","YTD","Vol 12m"]):
            with col:
                st.markdown(f'<div style="font-size:10px;color:#aaa;font-weight:500;'
                            f'text-transform:uppercase;letter-spacing:.04em;'
                            f'padding-bottom:4px;border-bottom:1px solid #eee">'
                            f'{lbl}</div>', unsafe_allow_html=True)

        total_mc = 0.0
        for f in fundos_c:
            nq  = f["nome_quantum"]
            m   = metricas.get(nq,{})
            cur = aloc_fundo.get(nq,0.0)
            cf,cp,cv,cr6,cr12,cr24,cytd,cvol = st.columns([3.2,1,1.2,0.9,0.9,0.9,0.9,0.9])
            with cf:
                st.markdown(f'<div style="font-size:12px;color:#333;padding:7px 0 3px">'
                            f'{nq[:50]}</div>', unsafe_allow_html=True)
            with cp:
                # Input como % do TOTAL (máx = % da classe)
                novo = st.number_input(
                    "", min_value=0.0, max_value=float(round(pct_c*100,1)),
                    value=(float(round(cur,1)) if cur > 0 else None),
                    step=0.5, format="%.1f", placeholder="—",
                    label_visibility="collapsed", key=f"pct_{nq}")
                novo = novo if novo is not None else 0.0
                aloc_fundo[nq] = novo
                total_mc += novo
            with cv:
                vf = (novo/100)*valor
                st.markdown(f'<div style="font-size:11px;color:#666;'
                            f'padding:7px 0 3px;text-align:right">'
                            f'{fmt_brl(vf)}</div>', unsafe_allow_html=True)
            for col_r,key in [(cr6,"ret_6m"),(cr12,"ret_12m"),(cr24,"ret_24m"),
                              (cytd,"ytd"),(cvol,"vol_12m")]:
                with col_r:
                    val_m = m.get(key)
                    cor = "#231f20" if key!="vol_12m" else "#666"
                    st.markdown(
                        f'<div style="font-size:12px;font-weight:{"600" if key!="vol_12m" else "400"};'
                        f'color:{cor};padding:7px 0 3px;text-align:center">'
                        f'{fmt_pct(val_m)}</div>', unsafe_allow_html=True)

        t = round(total_mc,1)
        target = round(pct_c*100,1)
        if abs(t-target)<0.1:
            st.markdown(f'<div class="ok-box">Total: {t:.1f}% = {target:.1f}% da classe ✓</div>',
                        unsafe_allow_html=True)
        else:
            diff = target - t
            st.markdown(f'<div class="warn-box">Total: {t:.1f}% — '
                        f'{"falta" if diff>0 else "excede em"} {abs(diff):.1f}p.p. '
                        f'(classe = {target:.1f}%)</div>', unsafe_allow_html=True)
            erros_classe.append(c)

        st.markdown("</div>", unsafe_allow_html=True)

    # Navegação
    st.markdown("---")
    cb,cf = st.columns([1,3])
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
        if pct_c==0: continue
        for f in fundos_por_classe(c):
            nq   = f["nome_quantum"]
            p_tot = aloc_fd.get(nq,0)/100
            val_f = p_tot*valor
            if val_f==0: continue
            m = metricas.get(nq,{})
            rows.append({"Classe":c,"Fundo":nq[:55],
                         "% Total":fmt_pct(p_tot),
                         "Valor":fmt_brl(val_f),
                         "Ret 6m":fmt_pct(m.get("ret_6m")),
                         "Ret 12m":fmt_pct(m.get("ret_12m")),
                         "Ret 24m":fmt_pct(m.get("ret_24m")),
                         "YTD":fmt_pct(m.get("ytd")),
                         "Vol 12m":fmt_pct(m.get("vol_12m"))})

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Downloads + navegação
    st.markdown("---")
    cb,cp,cd,cn = st.columns([1,1,1,1])

    with cb:
        if st.button("← Voltar e editar", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

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
            st.error(f"Erro PPT: {e}")

    with cd:
        try:
            from gerar_pdf import gerar_pdf_proposta
            pdf = gerar_pdf_proposta(nome,valor,perfil,aloc_cl,aloc_fd,metricas,
                                     quantum_file=st.session_state.quantum_file)
            st.download_button("⬇ Baixar PDF", pdf,
                               f"Proposta_{nome.replace(' ','_')}.pdf",
                               "application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"Erro PDF: {e}")

    with cn:
        if st.button("Nova proposta", use_container_width=True):
            for k in ["step","cliente_nome","cliente_valor","cliente_perfil",
                      "aloc_classe","aloc_fundo"]:
                st.session_state.pop(k,None)
            st.session_state.step = 1
            st.rerun()
