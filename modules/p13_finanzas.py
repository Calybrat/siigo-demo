"""Finanzas del grupo: P&L de SaaS, Regla del 40 y la deuda de julio de 2026."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Finanzas y Regla del 40",
        "Estado de resultados del grupo · caja, deuda y estructura de costos",
        "Dirección"), unsafe_allow_html=True)

    f = datos.finanzas()
    emp = datos.empleados()
    r40 = datos.regla_40()
    meses = datos.meses()

    ult = f.iloc[-1]
    doce = f.tail(12)
    doce_ant = f.head(12)
    ing12 = doce["ingresos_usd"].sum()

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Ingresos (12 meses)", usd(ing12),
                      f"▲ {r40['crecimiento']:.1f}% vs los 12 anteriores", True, "💵",
                      "Suscripciones más servicios, en dólares."), unsafe_allow_html=True)
    k[1].markdown(kpi("Margen bruto", pct(doce["margen_bruto_usd"].sum() / ing12 * 100),
                      "Referencia en SaaS: 75–80%",
                      doce["margen_bruto_usd"].sum() / ing12 > 0.72, "📊",
                      "Después del costo de servir: nube, soporte e infraestructura."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("EBITDA (12 meses)", usd(doce["ebitda_usd"].sum()),
                      f"{r40['ebitda_pct']:.1f}% de los ingresos",
                      r40["ebitda_pct"] > 10, "🏦",
                      "Lo que deja la operación antes de intereses e impuestos."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Regla del 40", f"{r40['regla40']:.1f}",
                      "Umbral que exige un fondo de crecimiento: 40",
                      r40["regla40"] >= 40, "⚖️",
                      "Crecimiento más margen. Un punto de cada uno vale lo mismo."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["⚖️  La Regla del 40", "📊  Estructura de costos",
                                "🏦  Caja, deuda y equipo"])

    # ═══ Regla del 40 ════════════════════════════════════════════════════════
    with tab1:
        # Serie móvil: crecimiento y margen mes a mes con ventana de 12
        serie = []
        for i in range(12, len(f)):
            v12 = f.iloc[i - 11:i + 1]
            prev = f.iloc[max(0, i - 23):i - 11]
            if len(prev) < 6:
                continue
            crec = (v12["ingresos_usd"].sum() /
                    prev["ingresos_usd"].sum() * (len(prev) / 12) - 1) * 100
            eb = v12["ebitda_usd"].sum() / v12["ingresos_usd"].sum() * 100
            serie.append({"mes": f.iloc[i]["mes"], "crec": crec, "ebitda": eb,
                          "r40": crec + eb})
        s = pd.DataFrame(serie)

        c1, c2 = st.columns([1.4, 1], gap="medium")
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=[mes_es(m) for m in s["mes"]], y=s["crec"],
                                 name="Crecimiento", marker_color=AZUL))
            fig.add_trace(go.Bar(x=[mes_es(m) for m in s["mes"]], y=s["ebitda"],
                                 name="Margen EBITDA", marker_color=NARANJA))
            fig.add_trace(go.Scatter(x=[mes_es(m) for m in s["mes"]], y=s["r40"],
                                     name="Suma", mode="lines+markers",
                                     line=dict(color=TINTA, width=3)))
            fig.add_hline(y=40, line_dash="dash", line_color=BAD,
                          annotation_text="umbral 40", annotation_font_size=10)
            fig.update_layout(barmode="stack")
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 380, "Regla del 40, mes a mes"),
                            use_container_width=True)
        with c2:
            falta = 40 - r40["regla40"]
            ing_extra = falta / 100 * ing12
            st.markdown(panel(
                "Faltan puntos, y hay dos formas de conseguirlos",
                f"Hoy la suma da <b>{r40['regla40']:.1f}</b>: "
                f"{r40['crecimiento']:.1f} de crecimiento más "
                f"{r40['ebitda_pct']:.1f} de margen. "
                f"{'Faltan <b>' + f'{falta:.1f}' + ' puntos</b>' if falta > 0 else 'Está por encima del umbral'}.<br><br>"
                f"<b>Por crecimiento:</b> {falta:.1f} puntos más son "
                f"<b>{usd(ing_extra)}</b> de ingreso adicional al año.<br><br>"
                f"<b>Por margen:</b> los mismos {falta:.1f} puntos son "
                f"<b>{usd(ing_extra)}</b> de gasto menos — con el mismo ingreso.<br><br>"
                f"Valen exactamente lo mismo para el indicador. La diferencia es que "
                f"recortar gasto es inmediato y crecer toma trimestres.",
                "⚖️", "naranja" if falta > 0 else "ok"), unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        # Dónde salen esos puntos
        ue = datos.unit_economics()
        emb = datos.embudo()
        emb12 = emb[emb["mes"].isin(meses[-12:])]
        inv_pagada = emb12[emb12["canal"].isin(["Google Ads", "Meta Ads"])]["inversion_usd"].sum()
        st.markdown(panel(
            "De dónde saldrían esos puntos, en concreto",
            f"<b>1 · Mezcla de canales.</b> Google Ads y Meta Ads consumieron "
            f"<b>{usd(inv_pagada)}</b> en doce meses con el CAC más alto de todos. "
            f"Mover una parte al canal de contadores baja gasto de mercadeo sin "
            f"bajar altas: sube el margen sin tocar el crecimiento.<br><br>"
            f"<b>2 · Migración de Aspel.</b> Convertir la base de escritorio pendiente "
            f"a Siigo Nube es ARR incremental sin CAC: sube el crecimiento sin tocar "
            f"el margen.<br><br>"
            f"<b>3 · Upsell de módulos.</b> Nómina y Siigo Pay sobre clientes que ya "
            f"están adentro suben ARPA con costo marginal casi nulo: suben los dos "
            f"lados a la vez.<br><br>"
            f"Las tres están cuantificadas en los módulos de este mismo panel. "
            f"Ninguna requiere capital nuevo.",
            "🎯", "ok"), unsafe_allow_html=True)

    # ═══ Costos ══════════════════════════════════════════════════════════════
    with tab2:
        c1, c2 = st.columns([1.5, 1], gap="medium")
        with c1:
            fig = go.Figure()
            for col, nombre, color in [
                ("costo_servicio_usd", "Costo de servicio", "#9FB4C6"),
                ("rnd_usd", "Producto y tecnología", AZUL),
                ("sym_usd", "Comercial y mercadeo", NARANJA),
                ("gna_usd", "Administración", AZUL_PALE),
                ("ebitda_usd", "EBITDA", GOOD),
            ]:
                fig.add_trace(go.Bar(x=[mes_es(m) for m in f["mes"]],
                                     y=f[col] / f["ingresos_usd"] * 100,
                                     name=nombre, marker_color=color))
            fig.update_layout(barmode="stack")
            fig.update_yaxes(ticksuffix="%", range=[0, 100])
            st.plotly_chart(light(fig, 380,
                                  "Cada 100 dólares de ingreso, en qué se van"),
                            use_container_width=True)
        with c2:
            vals = [doce["costo_servicio_usd"].sum(), doce["rnd_usd"].sum(),
                    doce["sym_usd"].sum(), doce["gna_usd"].sum(),
                    doce["ebitda_usd"].sum()]
            fig = go.Figure(go.Pie(
                labels=["Costo de servicio", "Producto y tecnología",
                        "Comercial y mercadeo", "Administración", "EBITDA"],
                values=vals, hole=0.6,
                marker_colors=["#9FB4C6", AZUL, NARANJA, AZUL_PALE, GOOD],
                texttemplate="%{percent:.0%}", sort=False))
            st.plotly_chart(light(fig, 380, "Últimos 12 meses"),
                            use_container_width=True)

        rnd_pct = doce["rnd_usd"].sum() / ing12 * 100
        sym_pct = doce["sym_usd"].sum() / ing12 * 100
        st.markdown(panel(
            "Una estructura de costos de empresa que invierte en producto",
            f"<b>{rnd_pct:.1f}%</b> de los ingresos va a producto y tecnología. "
            f"Siigo declara públicamente que invierte más del 20% de sus ingresos en "
            f"innovación, y el modelo lo refleja.<br><br>"
            f"<b>{sym_pct:.1f}%</b> va a comercial y mercadeo. Es el rubro más grande "
            f"después del costo de servicio, y el que tiene la palanca más rápida: "
            f"cada punto de CAC que baja la mezcla de canales baja este número "
            f"directamente.<br><br>"
            f"El <b>costo de servicio</b> "
            f"({doce['costo_servicio_usd'].sum()/ing12*100:.1f}%) es alto para un "
            f"SaaS puro, y hay una razón estructural: atender micronegocios exige "
            f"soporte humano, y la infraestructura se dimensiona para los picos de "
            f"cierre de mes y de temporada tributaria.",
            "🧮"), unsafe_allow_html=True)

        st.markdown("##### Estado de resultados · últimos 12 meses")
        pl = pd.DataFrame({
            "Concepto": ["Ingresos", "Costo de servicio", "Margen bruto",
                         "Producto y tecnología", "Comercial y mercadeo",
                         "Administración", "EBITDA", "Intereses", "Inversión (capex)"],
            "USD": [ing12, -doce["costo_servicio_usd"].sum(),
                    doce["margen_bruto_usd"].sum(), -doce["rnd_usd"].sum(),
                    -doce["sym_usd"].sum(), -doce["gna_usd"].sum(),
                    doce["ebitda_usd"].sum(), -doce["intereses_usd"].sum(),
                    -doce["capex_usd"].sum()],
        })
        pl["% de ingresos"] = [f"{v/ing12*100:.1f}%" for v in pl["USD"]]
        pl["USD"] = [usd(v) for v in pl["USD"]]
        st.dataframe(pl, width="stretch", hide_index=True)

    # ═══ Caja y deuda ════════════════════════════════════════════════════════
    with tab3:
        c1, c2 = st.columns([1.5, 1], gap="medium")
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[mes_es(m) for m in f["mes"]], y=f["caja_usd"],
                                     name="Caja", mode="lines",
                                     line=dict(color=GOOD, width=3),
                                     fill="tozeroy", fillcolor="rgba(18,165,117,.09)"))
            fig.add_trace(go.Scatter(x=[mes_es(m) for m in f["mes"]], y=f["deuda_usd"],
                                     name="Deuda", mode="lines",
                                     line=dict(color=BAD, width=3, dash="dash")))
            fig.add_annotation(x=mes_es("2026-07"), y=float(ult["deuda_usd"]),
                               text="US$103,5M · julio 2026", showarrow=True,
                               arrowhead=2, arrowcolor=MUTED, ax=-70, ay=-40,
                               font=dict(size=10, color=TINTA))
            fig.update_yaxes(tickprefix="US$", tickformat=".2s")
            st.plotly_chart(light(fig, 360, "Caja y deuda del grupo"),
                            use_container_width=True)
        with c2:
            st.markdown(panel(
                "La financiación de julio cambia la conversación",
                f"En julio de 2026 el grupo cerró una operación estructurada de "
                f"<b>US$103,5 millones</b>, con Banco de Occidente aportando "
                f"US$18,5 millones. La deuda pasó de "
                f"<b>{usd(float(f[f['mes']=='2026-06']['deuda_usd'].iloc[0]))}</b> a "
                f"<b>{usd(float(ult['deuda_usd']))}</b>.<br><br>"
                f"Con <b>{usd(float(ult['caja_usd']))}</b> en caja y un EBITDA de "
                f"<b>{usd(doce['ebitda_usd'].sum())}</b> al año, la relación deuda "
                f"sobre EBITDA queda en "
                f"<b>{float(ult['deuda_usd'])/doce['ebitda_usd'].sum():.1f}x</b>.<br><br>"
                f"Eso deja margen, pero también obligación: la deuda hay que servirla "
                f"con caja operativa, y eso pone piso al EBITDA que se puede sacrificar "
                f"para crecer.",
                "🏦"), unsafe_allow_html=True)

        c3, c4 = st.columns([1.3, 1], gap="medium")
        with c3:
            e_ult = emp[emp["mes"] == meses[-1]]
            g = e_ult.groupby("area").agg(
                n=("headcount", "sum"), costo=("costo_mensual_usd", "sum"),
                rot=("rotacion_12m_pct", "mean")).sort_values("n").reset_index()
            fig = go.Figure(go.Bar(
                y=g["area"], x=g["n"], orientation="h", marker_color=AZUL,
                text=[f"{v:,}" for v in g["n"]], textposition="auto",
                textfont=dict(size=10),
                customdata=np.stack([g["costo"], g["rot"]], axis=-1),
                hovertemplate="<b>%{y}</b><br>%{x:,} personas<br>"
                              "Costo mensual %{customdata[0]:$,.0f}<br>"
                              "Rotación %{customdata[1]:.1f}%<extra></extra>"))
            st.plotly_chart(light(fig, 340, "Equipo por área"),
                            use_container_width=True)
        with c4:
            gp = e_ult.groupby("pais")["headcount"].sum().sort_values(ascending=False)
            fig = go.Figure(go.Pie(labels=gp.index, values=gp.values, hole=0.6,
                                   marker_colors=PALETTE,
                                   texttemplate="%{percent:.0%}"))
            st.plotly_chart(light(fig, 340, "Equipo por país"),
                            use_container_width=True)

        total_hc = int(e_ult["headcount"].sum())
        rot_sop = float(e_ult[e_ult["area"] == "Servicio al Cliente"]["rotacion_12m_pct"].mean())
        rot_otros = float(e_ult[e_ult["area"] != "Servicio al Cliente"]["rotacion_12m_pct"].mean())
        st.markdown(panel(
            "Ingreso por persona, y el área que más gente pierde",
            f"Con <b>{total_hc:,} personas</b> y <b>{usd(ing12)}</b> de ingreso, "
            f"cada colaborador genera <b>{usd(ing12/total_hc, 0)}</b> al año. Es una "
            f"cifra baja frente a un SaaS de mercado desarrollado, y tiene una "
            f"explicación directa: el modelo de Siigo incluye soporte humano intensivo "
            f"para un cliente que no es contador de profesión.<br><br>"
            f"<b>Servicio al Cliente</b> rota al <b>{rot_sop:.1f}%</b> anual, frente al "
            f"<b>{rot_otros:.1f}%</b> del resto de la compañía. Cada salida se lleva "
            f"contexto acumulado sobre el producto y la norma tributaria, y el "
            f"reemplazo tarda meses en llegar al mismo nivel. Es una de las causas "
            f"de que el tiempo de respuesta se dispare justo cuando más se necesita.",
            "👥", "alerta"), unsafe_allow_html=True)

    st.caption("Moneda de reporte: dólares, como corresponde a un grupo con operación "
               "en seis monedas y un accionista internacional (Accel-KKR, desde 2017). "
               "La financiación de US$103,5M de julio de 2026 es información pública; "
               "el resto del estado de resultados es simulado.")
