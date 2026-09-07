"""Migración Aspel → Siigo Nube: la adquisición más grande, convertida en operación."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Migración Aspel → Siigo Nube",
        "México · base de escritorio heredada de la adquisición de Aspel (2022)",
        "Canal y mercados"), unsafe_allow_html=True)

    m = datos.migracion()
    meses = datos.meses()
    ult = m.iloc[-1]
    ini = m.iloc[0]
    base = int(ult["base_desktop_inicial"])

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Avance de la migración", pct(ult["avance_pct"]),
                      f"{int(ult['migrados_acum']):,} de {base:,} licencias",
                      ult["avance_pct"] > 40, "📦",
                      "Cuentas de escritorio que ya operan en la nube."),
                  unsafe_allow_html=True)
    k[1].markdown(kpi("Pendientes", f"{int(ult['pendientes']):,}",
                      f"Al ritmo actual: {int(ult['pendientes']/max(ult['migrados_mes'],1))} meses",
                      False, "⏳",
                      "Licencias que siguen en escritorio."), unsafe_allow_html=True)
    k[2].markdown(kpi("Perdidos en el camino", f"{int(ult['perdidos_acum']):,}",
                      f"{ult['perdidos_acum']/base*100:.1f}% de la base original",
                      False, "💧",
                      "Se fueron en vez de migrar."), unsafe_allow_html=True)
    k[3].markdown(kpi("Salto de ARPA al migrar",
                      f"{ult['arpa_nube_usd']/ult['arpa_desktop_usd']:.1f}x",
                      f"US${ult['arpa_desktop_usd']:.2f} → US${ult['arpa_nube_usd']:.2f}",
                      True, "📈",
                      "Cuánto más paga la misma cuenta al pasar a la nube."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.55, 1], gap="medium")
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[mes_es(x) for x in m["mes"]], y=m["migrados_acum"], name="Migrados",
            mode="lines", stackgroup="uno", line=dict(width=0.5, color=AZUL),
            fillcolor="rgba(0,157,255,.75)"))
        fig.add_trace(go.Scatter(
            x=[mes_es(x) for x in m["mes"]], y=m["pendientes"], name="Pendientes",
            mode="lines", stackgroup="uno", line=dict(width=0.5, color=AZUL_PALE),
            fillcolor="rgba(204,235,255,.9)"))
        fig.add_trace(go.Scatter(
            x=[mes_es(x) for x in m["mes"]], y=m["perdidos_acum"], name="Perdidos",
            mode="lines", stackgroup="uno", line=dict(width=0.5, color=BAD),
            fillcolor="rgba(224,80,63,.65)"))
        fig.update_yaxes(tickformat=".2s")
        st.plotly_chart(light(fig, 380,
                              "Qué pasó con las 214.000 licencias heredadas"),
                        use_container_width=True)
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[mes_es(x) for x in m["mes"]], y=m["migrados_mes"],
                             name="Migrados en el mes", marker_color=AZUL))
        fig.add_trace(go.Bar(x=[mes_es(x) for x in m["mes"]], y=-m["perdidos_mes"],
                             name="Perdidos en el mes", marker_color=BAD))
        fig.update_layout(barmode="relative")
        st.plotly_chart(light(fig, 380, "Ritmo mensual"), use_container_width=True)

    # ── El costo de la lentitud ──────────────────────────────────────────────
    ritmo_actual = float(m["migrados_mes"].tail(3).mean())
    meses_restantes = ult["pendientes"] / max(ritmo_actual, 1)
    perdida_ritmo = float(m["perdidos_mes"].tail(3).mean())
    perdida_proyectada = perdida_ritmo * meses_restantes
    arr_perdido = perdida_proyectada * ult["arpa_nube_usd"] * 12
    arr_ganado = ult["pendientes"] * (ult["arpa_nube_usd"] - ult["arpa_desktop_usd"]) * 12

    l1, l2 = st.columns(2, gap="medium")
    with l1:
        st.markdown(panel(
            "Cada mes que tarda la migración tiene precio",
            f"Al ritmo de los últimos tres meses (<b>{ritmo_actual:,.0f}</b> cuentas "
            f"migradas al mes), terminar las <b>{int(ult['pendientes']):,}</b> "
            f"pendientes toma <b>{meses_restantes:.0f} meses</b> — hasta "
            f"{'2030' if meses_restantes > 40 else '2029'} aproximadamente.<br><br>"
            f"En ese tiempo, al ritmo de fuga actual, se pierden otras "
            f"<b>{perdida_proyectada:,.0f} cuentas</b>, que son "
            f"<b>{usd(arr_perdido)}</b> de ARR que ya no se va a capturar.<br><br>"
            f"Duplicar el ritmo de migración no solo adelanta ingreso: "
            f"<b>evita la mitad de esa pérdida</b>.",
            "⏱️", "alerta"), unsafe_allow_html=True)
    with l2:
        st.markdown(panel(
            "Y el premio del otro lado es grande",
            f"Una cuenta en escritorio paga <b>US${ult['arpa_desktop_usd']:.2f}</b> al "
            f"mes. La misma cuenta en Siigo Nube paga "
            f"<b>US${ult['arpa_nube_usd']:.2f}</b>: "
            f"<b>{ult['arpa_nube_usd']/ult['arpa_desktop_usd']:.1f} veces más</b>.<br><br>"
            f"Migrar las <b>{int(ult['pendientes']):,}</b> cuentas pendientes vale "
            f"<b>{usd(arr_ganado)}</b> de ARR incremental — sin adquirir un solo "
            f"cliente nuevo, sin CAC, sobre gente que ya paga.<br><br>"
            f"Es, por lejos, la bolsa de ARR más grande y más barata que tiene el "
            f"grupo identificada hoy.",
            "🎁", "ok"), unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    c3, c4 = st.columns([1, 1], gap="medium")
    with c3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[mes_es(x) for x in m["mes"]], y=m["csat_migracion"],
            mode="lines+markers", line=dict(color=NARANJA, width=3),
            fill="tozeroy", fillcolor="rgba(242,143,23,.10)"))
        fig.update_yaxes(range=[3, 5], title="CSAT del proceso (1–5)")
        st.plotly_chart(light(fig, 320,
                              "Satisfacción de quien acaba de migrar"),
                        use_container_width=True)
    with c4:
        # Escenarios de aceleración
        escenarios = []
        for mult, nombre in [(1.0, "Ritmo actual"), (1.5, "+50% de ritmo"),
                             (2.0, "Doble ritmo")]:
            r = ritmo_actual * mult
            meses_e = ult["pendientes"] / r
            perd = perdida_ritmo * meses_e
            escenarios.append({
                "esc": nombre, "meses": meses_e, "perdidas": perd,
                "arr": (ult["pendientes"] - perd) *
                       (ult["arpa_nube_usd"] - ult["arpa_desktop_usd"]) * 12})
        ee = pd.DataFrame(escenarios)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ee["esc"], y=ee["arr"], marker_color=[DIM, AZUL_LT, AZUL],
                             text=[usd(v) for v in ee["arr"]], textposition="outside",
                             textfont=dict(size=11),
                             customdata=np.stack([ee["meses"], ee["perdidas"]], axis=-1),
                             hovertemplate="<b>%{x}</b><br>ARR capturado %{y:$,.0f}<br>"
                                           "Termina en %{customdata[0]:.0f} meses<br>"
                                           "Cuentas perdidas: %{customdata[1]:,.0f}"
                                           "<extra></extra>"))
        fig.update_yaxes(tickprefix="US$", tickformat=".2s")
        st.plotly_chart(light(fig, 320,
                              "ARR que se captura según el ritmo de migración"),
                        use_container_width=True)

    st.markdown("##### Detalle mes a mes")
    st.dataframe(pd.DataFrame({
        "Mes": [mes_es(x) for x in m["mes"]],
        "Migrados": [f"{int(x):,}" for x in m["migrados_mes"]],
        "Perdidos": [f"{int(x):,}" for x in m["perdidos_mes"]],
        "Migrados acumulados": [f"{int(x):,}" for x in m["migrados_acum"]],
        "Pendientes": [f"{int(x):,}" for x in m["pendientes"]],
        "Avance": [f"{x:.1f}%" for x in m["avance_pct"]],
        "ARPA escritorio": [f"US${x:.2f}" for x in m["arpa_desktop_usd"]],
        "ARPA nube": [f"US${x:.2f}" for x in m["arpa_nube_usd"]],
        "CSAT migración": [f"{x:.2f}" for x in m["csat_migracion"]],
    }).iloc[::-1], width="stretch", hide_index=True)

    st.caption("Aspel se integró al Grupo Siigo en febrero de 2022. Era el estándar "
               "histórico de software administrativo para MiPymes en México, con más "
               "de un millón de empresas atendidas en 40 años. El tamaño de la base "
               "de escritorio pendiente y el ritmo de migración de este panel son "
               "supuestos del modelo del demo.")
