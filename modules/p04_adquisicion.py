"""Adquisición y unit economics: qué cuesta traer un cliente y cuándo se paga."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Adquisición y Unit Economics",
        "Del visitante al cliente que paga, y cuánto cuesta cada paso",
        "Ingresos"), unsafe_allow_html=True)

    meses = datos.meses()
    f1, f2 = st.columns([2, 2])
    with f1:
        pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                key="adq_pais")
    with f2:
        vent = st.selectbox("Ventana", ["Últimos 12 meses", "Últimos 3 meses",
                                        "Todo el histórico"], key="adq_vent")
    ms = {"Últimos 12 meses": meses[-12:], "Últimos 3 meses": meses[-3:],
          "Todo el histórico": meses}[vent]

    e = datos.embudo()
    e = e[e["mes"].isin(ms)]
    if pais_sel != "Todos":
        e = e[e["pais"] == pais_sel]

    ue = datos.unit_economics(pais_sel)
    cac = e["inversion_usd"].sum() / max(e["pagados"].sum(), 1)

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("CAC", f"US${cac:,.0f}",
                      f"{e['pagados'].sum():,.0f} clientes nuevos", cac < 450, "🎯",
                      "Inversión comercial y de mercadeo dividida entre los clientes que entraron."),
                  unsafe_allow_html=True)
    k[1].markdown(kpi("LTV", usd(ue["ltv"], 0),
                      f"ARPA US${ue['arpa']:.2f} × margen {ue['margen_bruto']*100:.0f}% "
                      f"× {ue['vida_meses']:.0f} meses", True, "💎",
                      "Lo que deja un cliente en toda su vida, después del costo de servirlo."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("LTV / CAC", f"{ue['ltv_cac']:.1f}x", "Umbral sano: 3x",
                      ue["ltv_cac"] >= 3, "⚖️",
                      "Cuántas veces recupera Siigo lo que invirtió en traer al cliente."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Recuperación del CAC", f"{ue['payback_meses']:.0f} meses",
                      "Umbral sano en pymes: menos de 12",
                      ue["payback_meses"] <= 12, "⏱️",
                      "Cuánto tarda un cliente en devolver lo que costó."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Embudo ───────────────────────────────────────────────────────────────
    c1, c2 = st.columns([1, 1.25], gap="medium")
    with c1:
        etapas = [("Visitas al sitio", e["visitas"].sum()),
                  ("Leads", e["leads"].sum()),
                  ("Pruebas iniciadas", e["trials"].sum()),
                  ("Cuentas activadas", e["activados"].sum()),
                  ("Clientes que pagan", e["pagados"].sum())]
        fig = go.Figure(go.Funnel(
            y=[x[0] for x in etapas], x=[x[1] for x in etapas],
            marker=dict(color=[AZUL_PALE, AZUL_LT, AZUL, AZUL_DEEP, TINTA]),
            textinfo="value+percent initial",
            textfont=dict(size=11, color=TINTA)))
        fig.update_layout(height=380, margin=dict(l=6, r=6, t=44, b=16),
                          paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Poppins, sans-serif", color=MUTED),
                          title=dict(text="Embudo de adquisición", x=0,
                                     font=dict(size=14, color=TINTA)))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        can = e.groupby("canal").agg(
            pagados=("pagados", "sum"), inv=("inversion_usd", "sum"),
            trials=("trials", "sum"), activados=("activados", "sum")).reset_index()
        can["cac"] = can["inv"] / can["pagados"]
        can["conv"] = can["pagados"] / can["trials"] * 100
        can = can.sort_values("cac")
        colores = [GOOD if x < cac * 0.8 else (BAD if x > cac * 1.3 else AZUL)
                   for x in can["cac"]]
        fig = go.Figure(go.Bar(
            x=can["canal"], y=can["cac"], marker_color=colores,
            text=[f"US${v:,.0f}" for v in can["cac"]], textposition="outside",
            textfont=dict(size=10),
            customdata=np.stack([can["pagados"], can["conv"]], axis=-1),
            hovertemplate="<b>%{x}</b><br>CAC US$%{y:,.0f}<br>"
                          "%{customdata[0]:,.0f} clientes<br>"
                          "Conversión prueba→pago %{customdata[1]:.0f}%<extra></extra>"))
        fig.add_hline(y=cac, line_dash="dot", line_color=MUTED,
                      annotation_text=f"promedio US${cac:,.0f}",
                      annotation_font_size=10)
        fig.update_yaxes(tickprefix="US$")
        fig.update_xaxes(tickangle=-32)
        st.plotly_chart(light(fig, 380, "Costo de adquisición por canal"),
                        use_container_width=True)

    # ── La palanca de mezcla ─────────────────────────────────────────────────
    can2 = can.set_index("canal")
    barato = can2["cac"].idxmin()
    caro = can2["cac"].idxmax()
    share_barato = can2.loc[barato, "pagados"] / can2["pagados"].sum() * 100
    share_caro = can2.loc[caro, "pagados"] / can2["pagados"].sum() * 100
    # Simulación: mover 10 puntos de mezcla del canal caro al barato
    nuevo_cac = ((can2["inv"].sum()
                  - can2.loc[caro, "cac"] * can2["pagados"].sum() * 0.10
                  + can2.loc[barato, "cac"] * can2["pagados"].sum() * 0.10)
                 / can2["pagados"].sum())

    st.markdown(panel(
        "La mezcla de canales es la palanca, no el presupuesto",
        f"<b>{barato}</b> trae clientes a <b>US${can2.loc[barato,'cac']:,.0f}</b> y hoy "
        f"aporta el <b>{share_barato:.0f}%</b> de las altas. "
        f"<b>{caro}</b> cuesta <b>US${can2.loc[caro,'cac']:,.0f}</b> "
        f"({can2.loc[caro,'cac']/can2.loc[barato,'cac']:.1f} veces más) y aporta el "
        f"<b>{share_caro:.0f}%</b>.<br><br>"
        f"Mover <b>10 puntos</b> de la mezcla de uno al otro, sin gastar un dólar más, "
        f"lleva el CAC de <b>US${cac:,.0f}</b> a <b>US${nuevo_cac:,.0f}</b> y la "
        f"recuperación de {ue['payback_meses']:.0f} a "
        f"<b>{nuevo_cac/(ue['arpa']*ue['margen_bruto']):.0f} meses</b>. "
        f"En un año eso libera <b>{usd((cac-nuevo_cac)*e['pagados'].sum())}</b> de caja.",
        "🎚️", "ok"), unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Evolución y calidad ──────────────────────────────────────────────────
    c3, c4 = st.columns([1.4, 1], gap="medium")
    with c3:
        ev = datos.embudo()
        if pais_sel != "Todos":
            ev = ev[ev["pais"] == pais_sel]
        ev = ev.groupby("mes").agg(pagados=("pagados", "sum"),
                                   inv=("inversion_usd", "sum")).reset_index()
        ev["cac"] = ev["inv"] / ev["pagados"]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[mes_es(m) for m in ev["mes"]], y=ev["pagados"],
                             name="Clientes nuevos", marker_color=AZUL_PALE))
        fig.add_trace(go.Scatter(x=[mes_es(m) for m in ev["mes"]], y=ev["cac"],
                                 name="CAC (US$)", mode="lines+markers", yaxis="y2",
                                 line=dict(color=NARANJA, width=2.5)))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                      tickprefix="US$", tickfont=dict(color=NARANJA)))
        st.plotly_chart(light(fig, 340, "Altas y CAC mes a mes"),
                        use_container_width=True)
    with c4:
        can["act_pct"] = can["activados"] / can["trials"] * 100
        can3 = can.sort_values("act_pct", ascending=True)
        fig = go.Figure(go.Bar(
            y=can3["canal"], x=can3["act_pct"], orientation="h",
            marker_color=[GOOD if v > 75 else (WARN if v > 60 else BAD)
                          for v in can3["act_pct"]],
            text=[f"{v:.0f}%" for v in can3["act_pct"]], textposition="auto",
            textfont=dict(size=10)))
        fig.update_xaxes(ticksuffix="%")
        st.plotly_chart(light(fig, 340, "Calidad del canal: cuántos llegan a activarse"),
                        use_container_width=True)

    st.markdown("##### Rendimiento por canal")
    tabla = can.sort_values("cac").copy()
    st.dataframe(pd.DataFrame({
        "Canal": tabla["canal"],
        "Clientes nuevos": [f"{x:,.0f}" for x in tabla["pagados"]],
        "Mezcla": [f"{x/tabla['pagados'].sum()*100:.1f}%" for x in tabla["pagados"]],
        "Inversión": [usd(x) for x in tabla["inv"]],
        "CAC": [f"US${x:,.0f}" for x in tabla["cac"]],
        "Prueba → pago": [f"{x:.0f}%" for x in tabla["conv"]],
        "Activación": [f"{x:.0f}%" for x in tabla["act_pct"]],
        "LTV / CAC": [f"{ue['ltv']/x:.1f}x" for x in tabla["cac"]],
    }), width="stretch", hide_index=True)

    st.caption("El LTV usa el margen bruto real del grupo y la vida derivada de la fuga "
               "observada, no una vida supuesta. Es el cálculo conservador.")
