"""Plataforma: disponibilidad, latencia e incidentes, contra el calendario tributario."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Plataforma y Confiabilidad",
        "Disponibilidad, tiempos de respuesta e incidentes · 6 países sobre la misma nube",
        "Producto y operación"), unsafe_allow_html=True)

    plat = datos.plataforma()
    inc = datos.incidentes()
    meses = datos.meses()

    vent = st.selectbox("Ventana", ["Últimos 90 días", "Últimos 12 meses",
                                    "Todo el histórico"], key="plat_vent")
    dias = {"Últimos 90 días": 90, "Últimos 12 meses": 365,
            "Todo el histórico": len(plat)}[vent]
    p = plat.tail(dias)
    inc_v = inc[inc["fecha"] >= p["fecha"].min().strftime("%Y-%m-%d")]

    uptime = float(p["uptime_pct"].mean())
    minutos_caidos = (100 - uptime) / 100 * 24 * 60 * len(p)
    s1 = int((inc_v["severidad"] == "S1").sum())

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Disponibilidad", f"{uptime:.3f}%",
                      f"Compromiso habitual del sector: 99,9%", uptime >= 99.9, "🟢",
                      "Porcentaje del tiempo con el servicio arriba."),
                  unsafe_allow_html=True)
    k[1].markdown(kpi("Tiempo fuera de servicio", f"{minutos_caidos:,.0f} min",
                      f"En {len(p)} días", minutos_caidos < len(p) * 1.44, "⏱️",
                      "Minutos acumulados de indisponibilidad en la ventana."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("Latencia p95", f"{p['latencia_p95_ms'].mean():,.0f} ms",
                      f"Mediana p50: {p['latencia_p50_ms'].mean():,.0f} ms",
                      p["latencia_p95_ms"].mean() < 900, "⚡",
                      "El 5% de peticiones más lentas."), unsafe_allow_html=True)
    k[3].markdown(kpi("Incidentes graves (S1)", f"{s1}",
                      f"{len(inc_v)} incidentes en total", s1 <= 2, "🚨",
                      "Caídas con impacto amplio en clientes."), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.6, 1], gap="medium")
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=p["fecha"], y=p["uptime_pct"], mode="lines", name="Disponibilidad",
            line=dict(color=AZUL, width=1.6)))
        fig.add_hline(y=99.9, line_dash="dash", line_color=NARANJA,
                      annotation_text="99,9%", annotation_font_size=10)
        fig.update_yaxes(ticksuffix="%", range=[max(97, p["uptime_pct"].min() - 0.4), 100.05])
        st.plotly_chart(light(fig, 340, "Disponibilidad diaria"),
                        use_container_width=True)
    with c2:
        sev = inc_v.groupby("severidad").agg(
            n=("incidente_id", "count"), dur=("duracion_min", "sum")).reset_index()
        fig = go.Figure(go.Bar(
            x=sev["severidad"], y=sev["n"],
            marker_color=[BAD, WARN, AZUL_LT][:len(sev)],
            text=[f"{v}" for v in sev["n"]], textposition="outside",
            textfont=dict(size=12), customdata=sev["dur"],
            hovertemplate="<b>%{x}</b><br>%{y} incidentes<br>"
                          "%{customdata:,.0f} min acumulados<extra></extra>"))
        st.plotly_chart(light(fig, 340, "Incidentes por severidad"),
                        use_container_width=True)

    c3, c4 = st.columns([1, 1], gap="medium")
    with c3:
        pm = plat.groupby("mes").agg(
            lat=("latencia_p95_ms", "mean"), peticiones=("peticiones_millones", "sum"),
            uptime=("uptime_pct", "mean")).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[mes_es(m) for m in pm["mes"]], y=pm["peticiones"],
                             name="Peticiones (millones)", marker_color=AZUL_PALE))
        fig.add_trace(go.Scatter(x=[mes_es(m) for m in pm["mes"]], y=pm["lat"],
                                 name="Latencia p95 (ms)", yaxis="y2",
                                 mode="lines+markers",
                                 line=dict(color=BAD, width=2.5)))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                      ticksuffix=" ms", tickfont=dict(color=BAD)))
        st.plotly_chart(light(fig, 340, "Carga y latencia mes a mes"),
                        use_container_width=True)
    with c4:
        comp = (inc.groupby("componente")
                .agg(n=("incidente_id", "count"), dur=("duracion_min", "sum"))
                .sort_values("dur", ascending=True).reset_index())
        fig = go.Figure(go.Bar(
            y=comp["componente"], x=comp["dur"], orientation="h",
            marker_color=NARANJA, text=[f"{v:,.0f} min" for v in comp["dur"]],
            textposition="auto", textfont=dict(size=10), customdata=comp["n"],
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} minutos<br>"
                          "%{customdata} incidentes<extra></extra>"))
        st.plotly_chart(light(fig, 340,
                              "Minutos de incidente acumulados por componente"),
                        use_container_width=True)

    # ── La correlación que importa ───────────────────────────────────────────
    en_temp = inc[inc["en_temporada"]]
    fuera = inc[~inc["en_temporada"]]
    meses_temp = len([m for m in meses if int(m.split("-")[1]) in (3, 4, 5, 8, 9, 10)])
    meses_fuera = len(meses) - meses_temp

    l1, l2 = st.columns(2, gap="medium")
    with l1:
        st.markdown(panel(
            "Los incidentes no son aleatorios: siguen el calendario de la DIAN",
            f"En los meses de mayor carga tributaria (marzo a mayo, agosto a octubre) "
            f"ocurren <b>{len(en_temp)/max(meses_temp,1):.1f} incidentes por mes</b>. "
            f"En el resto del año, <b>{len(fuera)/max(meses_fuera,1):.1f}</b>.<br><br>"
            f"Es {len(en_temp)/max(meses_temp,1)/max(len(fuera)/max(meses_fuera,1),.01):.1f} "
            f"veces más. Y no es mala suerte: es que el sistema se dimensiona para un "
            f"promedio y la carga real no es promedio.<br><br>"
            f"El impacto se acumula: <b>{en_temp['clientes_afectados'].sum():,.0f}</b> "
            f"clientes-incidente en temporada contra "
            f"<b>{fuera['clientes_afectados'].sum():,.0f}</b> fuera de ella.",
            "📉", "alerta"), unsafe_allow_html=True)
    with l2:
        picos = plat.nsmallest(6, "uptime_pct")[["fecha", "uptime_pct",
                                                 "latencia_p95_ms", "incidentes"]]
        st.markdown("##### Los seis peores días")
        st.dataframe(pd.DataFrame({
            "Fecha": picos["fecha"].dt.strftime("%d/%m/%Y"),
            "Disponibilidad": [f"{x:.3f}%" for x in picos["uptime_pct"]],
            "Fuera de servicio": [f"{(100-x)/100*1440:,.0f} min"
                                  for x in picos["uptime_pct"]],
            "Latencia p95": [f"{x:,.0f} ms" for x in picos["latencia_p95_ms"]],
            "Incidentes": picos["incidentes"],
        }), width="stretch", hide_index=True)

    st.markdown("##### Incidentes registrados en la ventana")
    tabla = inc_v.sort_values("fecha", ascending=False).head(30)
    st.dataframe(pd.DataFrame({
        "Incidente": tabla["incidente_id"],
        "Fecha": tabla["fecha"],
        "Severidad": tabla["severidad"],
        "Componente": tabla["componente"],
        "Duración": [f"{x} min" for x in tabla["duracion_min"]],
        "Clientes afectados": [f"{x:,}" for x in tabla["clientes_afectados"]],
        "En temporada tributaria": ["Sí" if x else "No" for x in tabla["en_temporada"]],
    }), width="stretch", hide_index=True)

    st.caption("S1: caída con impacto amplio. S2: degradación seria. "
               "S3: falla acotada a un componente o a un grupo de clientes.")
