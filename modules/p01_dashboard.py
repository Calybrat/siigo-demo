"""Tablero ejecutivo: las ocho cifras con las que se abre un comité."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Tablero Ejecutivo",
        "Colombia · México · Ecuador · Perú · Uruguay · Chile — "
        f"corte al {datos.CORTE_TXT}"), unsafe_allow_html=True)

    susc = datos.suscripciones()
    fin = datos.finanzas()
    meses = datos.meses()
    ult, ant = meses[-1], meses[-13]

    c1, c2 = st.columns([2, 4])
    with c1:
        pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                key="db_pais")

    s = susc if pais_sel == "Todos" else susc[susc["pais"] == pais_sel]
    ind = datos.indicadores_mes(pais_sel)
    r40 = datos.regla_40()
    ue = datos.unit_economics(pais_sel)

    s_ult = s[s["mes"] == ult]
    s_ant = s[s["mes"] == ant]
    arr = s_ult["mrr_usd"].sum() * 12
    arr_ant = s_ant["mrr_usd"].sum() * 12
    crec_arr = (arr / arr_ant - 1) * 100 if arr_ant else 0
    clientes = int(s_ult["clientes"].sum())
    clientes_ant = int(s_ant["clientes"].sum())
    nrr = datos.nrr_anual(pais_sel)
    grr = datos.grr_anual(pais_sel)
    churn_mes = float(ind["churn_logo_pct"].tail(12).mean())
    arpa = float(ind["arpa"].iloc[-1])

    # ── Fila 1: la salud del ingreso ─────────────────────────────────────────
    k = st.columns(4, gap="small")
    k[0].markdown(kpi(
        "ARR", usd(arr), f"▲ {crec_arr:.1f}% en 12 meses", crec_arr > 0, "📈",
        "Ingreso recurrente anualizado: el MRR de cierre × 12."), unsafe_allow_html=True)
    k[1].markdown(kpi(
        "Clientes activos", miles(clientes),
        f"▲ {(clientes/clientes_ant-1)*100:.1f}% en 12 meses", clientes > clientes_ant,
        "🏢", "Pymes y contadores con suscripción viva."), unsafe_allow_html=True)
    k[2].markdown(kpi(
        "NRR (12 meses)", pct(nrr), "Referencia sana en pymes: 100%", nrr >= 100, "🔁",
        "Cuánto vale hoy la base de hace un año, sin contar clientes nuevos."),
        unsafe_allow_html=True)
    k[3].markdown(kpi(
        "ARPA mensual", f"US${arpa:,.2f}", f"Fuga de clientes: {churn_mes:.2f}%/mes",
        churn_mes < 1.8, "🧾", "Ingreso promedio por cliente al mes."),
        unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Fila 2: lo que mira el fondo y lo que duele en la operación ──────────
    docs = datos.documentos()
    docs_ult = docs[docs["mes"] == ult]
    if pais_sel != "Todos":
        docs_ult = docs_ult[docs_ult["pais"] == pais_sel]
    emitidos = int(docs_ult["emitidos"].sum())
    rechazo = docs_ult["rechazados"].sum() / max(emitidos, 1) * 100

    n = datos.nps()
    n_ult = n[n["mes"] == ult]
    if pais_sel != "Todos":
        n_ult = n_ult[n_ult["pais"] == pais_sel]
    nps_val = float((n_ult["nps"] * n_ult["encuestados"]).sum() /
                    max(n_ult["encuestados"].sum(), 1))

    plat = datos.plataforma()
    uptime = float(plat.tail(90)["uptime_pct"].mean())

    k2 = st.columns(4, gap="small")
    k2[0].markdown(kpi(
        "Regla del 40", f"{r40['regla40']:.1f}",
        f"{r40['crecimiento']:.1f}% crecimiento + {r40['ebitda_pct']:.1f}% EBITDA",
        r40["regla40"] >= 40, "⚖️",
        "Crecimiento + margen. Es el número con el que un fondo juzga a un SaaS."),
        unsafe_allow_html=True)
    k2[1].markdown(kpi(
        "LTV / CAC", f"{ue['ltv_cac']:.1f}x",
        f"Se recupera en {ue['payback_meses']:.0f} meses", ue["ltv_cac"] >= 3, "🎯",
        "Cuánto deja un cliente frente a lo que costó traerlo."), unsafe_allow_html=True)
    k2[2].markdown(kpi(
        "Documentos del mes", miles(emitidos), f"Rechazo DIAN: {rechazo:.2f}%",
        rechazo < 1.5, "🧾",
        "Facturas, nóminas y tiquetes emitidos por los clientes."), unsafe_allow_html=True)
    k2[3].markdown(kpi(
        "NPS", f"{nps_val:.0f}", f"Disponibilidad 90 días: {uptime:.3f}%",
        nps_val >= 30, "💬",
        "Promotores menos detractores. La referencia en software B2B es 30."),
        unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Gráficos ─────────────────────────────────────────────────────────────
    g1, g2 = st.columns([1.7, 1], gap="medium")
    with g1:
        piv = s.groupby(["mes", "pais"])["mrr_usd"].sum().reset_index()
        piv["arr"] = piv["mrr_usd"] * 12
        fig = go.Figure()
        for p in datos.paises()["pais"]:
            sub = piv[piv["pais"] == p]
            if len(sub):
                fig.add_trace(go.Bar(x=[mes_es(m) for m in sub["mes"]], y=sub["arr"],
                                     name=p, marker_color=PALETTE_PAIS.get(p, AZUL)))
        fig.update_layout(barmode="stack")
        fig.update_yaxes(tickprefix="US$", tickformat=".2s")
        st.plotly_chart(light(fig, 340, "ARR por país (USD)"), use_container_width=True)
    with g2:
        mix = s_ult.groupby("plan")["mrr_usd"].sum().sort_values(ascending=False)
        mix = mix[mix > 0]
        fig = go.Figure(go.Pie(labels=mix.index, values=mix.values, hole=0.6,
                               marker_colors=PALETTE, texttemplate="%{percent:.0%}",
                               customdata=[usd(x * 12) for x in mix.values],
                               hovertemplate="<b>%{label}</b><br>ARR %{customdata}<extra></extra>"))
        st.plotly_chart(light(fig, 340, "De dónde viene el ARR, por plan"),
                        use_container_width=True)

    g3, g4 = st.columns([1, 1], gap="medium")
    with g3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[mes_es(m) for m in ind["mes"]], y=ind["nrr_pct"],
                                 name="NRR", mode="lines+markers",
                                 line=dict(color=AZUL, width=2.5)))
        fig.add_trace(go.Scatter(x=[mes_es(m) for m in ind["mes"]], y=ind["grr_pct"],
                                 name="GRR", mode="lines+markers",
                                 line=dict(color=NARANJA, width=2.5)))
        fig.add_hline(y=100, line_dash="dot", line_color=MUTED,
                      annotation_text="100%", annotation_font_size=10)
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(light(fig, 320, "Retención mensual del ingreso"),
                        use_container_width=True)
    with g4:
        f = fin.copy()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[mes_es(m) for m in f["mes"]], y=f["ingresos_usd"],
                             name="Ingresos", marker_color=AZUL_PALE))
        fig.add_trace(go.Scatter(x=[mes_es(m) for m in f["mes"]], y=f["ebitda_usd"],
                                 name="EBITDA", mode="lines+markers", yaxis="y",
                                 line=dict(color=NARANJA, width=2.5)))
        fig.update_yaxes(tickprefix="US$", tickformat=".2s")
        st.plotly_chart(light(fig, 320, "Ingresos y EBITDA del grupo (USD)"),
                        use_container_width=True)

    # ── Lectura del tablero ──────────────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    l1, l2 = st.columns(2, gap="medium")

    with l1:
        falta = 40 - r40["regla40"]
        st.markdown(panel(
            "Lo que dice el tablero",
            f"El grupo cierra en <b>{usd(arr)}</b> de ARR creciendo "
            f"<b>{r40['crecimiento']:.1f}%</b>, con <b>{r40['ebitda_pct']:.1f}%</b> de "
            f"margen EBITDA. La Regla del 40 queda en <b>{r40['regla40']:.1f}</b>, "
            f"{'a ' + f'{falta:.1f}' + ' puntos del umbral' if falta > 0 else 'por encima del umbral'} "
            f"que suele exigir un fondo de crecimiento.<br><br>"
            f"El NRR está en <b>{nrr:.1f}%</b>: la base de hace un año vale hoy "
            f"{'menos' if nrr < 100 else 'más'} que entonces. La expansión "
            f"(alza anual, más usuarios, más módulos) "
            f"{'no alcanza a' if nrr < 100 else 'alcanza a'} compensar la fuga de "
            f"<b>{churn_mes:.2f}% mensual</b>, que anualizada es "
            f"<b>{(1-(1-churn_mes/100)**12)*100:.0f}%</b> de los clientes.",
            "📌"), unsafe_allow_html=True)

    with l2:
        emb = datos.embudo()
        emb12 = emb[emb["mes"].isin(meses[-12:])]
        if pais_sel != "Todos":
            emb12 = emb12[emb12["pais"] == pais_sel]
        por_canal = emb12.groupby("canal").agg(
            pagados=("pagados", "sum"), inv=("inversion_usd", "sum"))
        por_canal["cac"] = por_canal["inv"] / por_canal["pagados"]
        barato = por_canal.sort_values("cac").index[0]
        cac_barato = por_canal.loc[barato, "cac"]
        caro = por_canal.sort_values("cac").index[-1]
        cac_caro = por_canal.loc[caro, "cac"]

        st.markdown(panel(
            "Las dos palancas más cortas",
            f"<b>1. Mover altas hacia el canal más barato.</b> Traer un cliente por "
            f"<b>{caro}</b> cuesta <b>US${cac_caro:,.0f}</b>; por <b>{barato}</b> cuesta "
            f"<b>US${cac_barato:,.0f}</b>, {cac_caro/cac_barato:.1f} veces menos. "
            f"Cada punto de mezcla que se mueva baja el CAC promedio de "
            f"US${ue['cac']:,.0f} y acorta el retorno de {ue['payback_meses']:.0f} meses.<br><br>"
            f"<b>2. Cerrar la fuga por soporte.</b> Es el motivo de cancelación que más "
            f"sube en temporada tributaria, y es el único de la lista que depende "
            f"enteramente de una decisión interna.",
            "🎯", "naranja"), unsafe_allow_html=True)

    st.caption(
        "Datos simulados con fines de demostración, anclados a cifras públicas de Siigo "
        "(6 países, +300.000 pymes y contadores, +35.000 contadores, ~2.300 colaboradores, "
        "+24,1% de ingresos en 2025, US$103,5M de financiación en julio de 2026). "
        "Moneda de reporte: dólares.")
