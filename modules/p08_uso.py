"""Uso del producto: quién entra, qué usa y quién se está apagando."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Uso del Producto y Adopción",
        "Panel de 12.000 clientes de Colombia · adopción de módulos en los 6 países",
        "Producto y operación"), unsafe_allow_html=True)

    uso = datos.uso()
    ad = datos.adopcion()
    meses = datos.meses()
    ult = meses[-1]

    u = uso[uso["mes"] == ult]
    u_ant = uso[uso["mes"] == meses[-13]]
    activos = u[u["dias_activos"] >= 1]
    engaged = u[u["dias_activos"] >= 10]

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Clientes que entraron este mes",
                      pct(len(activos) / len(u) * 100),
                      f"{len(activos):,} de {len(u):,} del panel",
                      len(activos) / len(u) > 0.75, "🚪",
                      "Abrieron el producto al menos un día."), unsafe_allow_html=True)
    k[1].markdown(kpi("Uso frecuente", pct(len(engaged) / len(u) * 100),
                      "10 o más días en el mes",
                      len(engaged) / len(u) > 0.4, "🔥",
                      "El grupo que de verdad tiene el negocio dentro de Siigo."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("Módulos activos por cliente",
                      f"{u['modulos_activos'].mean():.2f}",
                      f"Hace un año: {u_ant['modulos_activos'].mean():.2f}",
                      u["modulos_activos"].mean() > u_ant["modulos_activos"].mean(),
                      "🧩", "Cuantos más módulos, más difícil es irse."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Usan alguna función de IA",
                      pct(u["usa_ia"].mean() * 100),
                      f"Hace un año: {u_ant['usa_ia'].mean()*100:.1f}%",
                      u["usa_ia"].mean() > u_ant["usa_ia"].mean(), "🤖",
                      "Conciliación bancaria, captura de facturas o agente fiscal."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📦  Adopción de módulos", "🔗  Uso y permanencia",
                                "🤖  Funciones de IA"])

    # ═══ Adopción ════════════════════════════════════════════════════════════
    with tab1:
        f1, _ = st.columns([2, 4])
        with f1:
            pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                    key="uso_pais")
        af = ad[ad["mes"] == ult]
        if pais_sel != "Todos":
            af = af[af["pais"] == pais_sel]
        g = (af.groupby(["funcionalidad", "es_ia"])
             .apply(lambda d: pd.Series({
                 "adop": d["clientes_usando"].sum() / d["clientes_base"].sum() * 100,
                 "n": d["clientes_usando"].sum()}), include_groups=False)
             .reset_index().sort_values("adop"))

        c1, c2 = st.columns([1.35, 1], gap="medium")
        with c1:
            fig = go.Figure(go.Bar(
                y=g["funcionalidad"], x=g["adop"], orientation="h",
                marker_color=[MORADO if ia else AZUL for ia in g["es_ia"]],
                text=[f"{v:.0f}%" for v in g["adop"]], textposition="auto",
                textfont=dict(size=10), customdata=g["n"],
                hovertemplate="<b>%{y}</b><br>Adopción %{x:.1f}%<br>"
                              "%{customdata:,.0f} clientes<extra></extra>"))
            fig.update_xaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 420,
                                  "Adopción por funcionalidad · morado = IA"),
                            use_container_width=True)
        with c2:
            ev = ad.groupby(["mes", "funcionalidad"]).apply(
                lambda d: d["clientes_usando"].sum() / d["clientes_base"].sum() * 100,
                include_groups=False).reset_index(name="adop")
            destacar = ["Nómina electrónica", "Siigo Pay", "Cobranza por WhatsApp",
                        "App móvil", "Conciliación bancaria IA"]
            fig = go.Figure()
            for i, f in enumerate(destacar):
                sub = ev[ev["funcionalidad"] == f]
                fig.add_trace(go.Scatter(
                    x=[mes_es(m) for m in sub["mes"]], y=sub["adop"], name=f,
                    mode="lines", line=dict(width=2.5,
                                            color=PALETTE[i % len(PALETTE)])))
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 420, "Cómo se mueve la adopción"),
                            use_container_width=True)

        nom = float(g[g["funcionalidad"] == "Nómina electrónica"]["adop"].iloc[0])
        fe = float(g[g["funcionalidad"] == "Facturación electrónica"]["adop"].iloc[0])
        st.markdown(panel(
            "Casi todos facturan; muy pocos hacen todo lo demás",
            f"La <b>facturación electrónica</b> la usa el <b>{fe:.0f}%</b>: es la razón "
            f"por la que la mayoría compró Siigo, y es obligatoria ante la DIAN.<br><br>"
            f"<b>Nómina electrónica</b> está en <b>{nom:.0f}%</b>. Eso significa que "
            f"dos de cada tres clientes liquidan su nómina en otra parte — en Excel, "
            f"en otro software, o se la hace el contador aparte. Cada uno de esos es "
            f"una relación que se puede profundizar sin CAC.<br><br>"
            f"El patrón general es claro: <b>Siigo entra por la obligación tributaria "
            f"y se queda ahí.</b> El resto del producto está subutilizado, y ese es "
            f"justo el territorio donde la relación se vuelve difícil de romper.",
            "📦"), unsafe_allow_html=True)

    # ═══ Uso y permanencia ═══════════════════════════════════════════════════
    with tab2:
        cli = datos.clientes()
        act = cli[cli["estado"] == "Activo"]
        bins = [0, 1, 2, 3, 4, 7]
        etiquetas = ["1 módulo", "2", "3", "4", "5 o más"]
        act = act.copy()
        act["n_mod"] = (1 + act["nomina_electronica"].astype(int)
                        + act["modulo_pos"].astype(int)
                        + act["siigo_pay"].astype(int))
        g = act.groupby("n_mod").agg(
            n=("cliente_id", "count"), salud=("salud", "mean"),
            riesgo=("riesgo_fuga", "mean"), mrr=("mrr_usd", "mean")).reset_index()

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=g["n_mod"].astype(str), y=g["riesgo"] * 100,
                                 marker_color=[BAD if v > 0.2 else
                                               (WARN if v > 0.12 else GOOD)
                                               for v in g["riesgo"]],
                                 text=[f"{v*100:.1f}%" for v in g["riesgo"]],
                                 textposition="outside", textfont=dict(size=11)))
            fig.update_xaxes(title="Módulos contratados")
            fig.update_yaxes(title="Clientes en riesgo de fuga", ticksuffix="%")
            st.plotly_chart(light(fig, 340, "Más módulos, menos riesgo de fuga"),
                            use_container_width=True)
        with c2:
            u2 = u.copy()
            u2["rango"] = pd.cut(u2["dias_activos"], [-1, 0, 3, 9, 19, 31],
                                 labels=["0 días", "1–3", "4–9", "10–19", "20+"])
            gg = u2.groupby("rango", observed=True).agg(
                n=("cliente_id", "count"),
                docs=("docs_emitidos", "mean")).reset_index()
            fig = go.Figure(go.Bar(
                x=gg["rango"].astype(str), y=gg["n"],
                marker_color=[BAD, WARN, AZUL_LT, AZUL, TINTA],
                text=[f"{v:,}" for v in gg["n"]], textposition="outside",
                textfont=dict(size=10)))
            fig.update_xaxes(title="Días que entró al producto en el mes")
            st.plotly_chart(light(fig, 340, "Intensidad de uso del panel"),
                            use_container_width=True)

        r1 = float(g[g["n_mod"] == 1]["riesgo"].iloc[0]) * 100
        r4 = float(g[g["n_mod"] == g["n_mod"].max()]["riesgo"].iloc[0]) * 100
        cero = int((u["dias_activos"] == 0).sum())
        st.markdown(panel(
            "El uso predice la cancelación mejor que cualquier encuesta",
            f"Un cliente con <b>un solo módulo</b> tiene <b>{r1:.1f}%</b> de "
            f"probabilidad de estar en riesgo. Con <b>cuatro</b>, baja a "
            f"<b>{r4:.1f}%</b>. No es casualidad: cada módulo adicional mete más "
            f"del negocio del cliente adentro de Siigo, y sacarlo cuesta más.<br><br>"
            f"Este mes <b>{cero:,} clientes del panel</b> "
            f"({cero/len(u)*100:.1f}%) no abrieron el producto ni un día. Están "
            f"pagando y no lo usan. Ese grupo es el que cancela en el próximo "
            f"ciclo de renovación, y hoy nadie los está llamando porque siguen "
            f"apareciendo como clientes al día.",
            "🔗", "alerta"), unsafe_allow_html=True)

        st.markdown("##### Comportamiento por número de módulos")
        st.dataframe(pd.DataFrame({
            "Módulos": g["n_mod"],
            "Clientes": [f"{x:,}" for x in g["n"]],
            "Salud promedio": [f"{x:.0f}/100" for x in g["salud"]],
            "En riesgo de fuga": [f"{x*100:.1f}%" for x in g["riesgo"]],
            "ARPA": [f"US${x:.2f}" for x in g["mrr"]],
            "ARR del grupo": [usd(n * m * 12) for n, m in zip(g["n"], g["mrr"])],
        }), width="stretch", hide_index=True)

    # ═══ IA ══════════════════════════════════════════════════════════════════
    with tab3:
        ia = ad[ad["es_ia"]]
        ev = ia.groupby(["mes", "funcionalidad"]).apply(
            lambda d: d["clientes_usando"].sum() / d["clientes_base"].sum() * 100,
            include_groups=False).reset_index(name="adop")

        c1, c2 = st.columns([1.4, 1], gap="medium")
        with c1:
            fig = go.Figure()
            for i, f in enumerate(ia["funcionalidad"].unique()):
                sub = ev[ev["funcionalidad"] == f]
                fig.add_trace(go.Scatter(
                    x=[mes_es(m) for m in sub["mes"]], y=sub["adop"], name=f,
                    mode="lines+markers",
                    line=dict(width=2.8, color=[MORADO, AZUL, TEAL][i % 3])))
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 360, "Adopción de las funciones de IA"),
                            use_container_width=True)
        with c2:
            ia_ult = ia[ia["mes"] == ult].groupby("pais").apply(
                lambda d: d["clientes_usando"].sum() / d["clientes_base"].sum() * 100,
                include_groups=False).sort_values().reset_index(name="adop")
            fig = go.Figure(go.Bar(
                y=ia_ult["pais"], x=ia_ult["adop"], orientation="h",
                marker_color=[PALETTE_PAIS.get(x, AZUL) for x in ia_ult["pais"]],
                text=[f"{v:.1f}%" for v in ia_ult["adop"]], textposition="auto",
                textfont=dict(size=10)))
            fig.update_xaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 360, "Adopción de IA por país"),
                            use_container_width=True)

        con_ia = u[u["usa_ia"]]
        sin_ia = u[~u["usa_ia"]]
        st.markdown(panel(
            "La IA todavía es de una minoría, y esa minoría se comporta distinto",
            f"Quien usa alguna función de IA entra <b>{con_ia['dias_activos'].mean():.1f} "
            f"días</b> al mes; quien no la usa, "
            f"<b>{sin_ia['dias_activos'].mean():.1f}</b>. Emite "
            f"<b>{con_ia['docs_emitidos'].mean()/max(sin_ia['docs_emitidos'].mean(),1):.1f} "
            f"veces</b> más documentos.<br><br>"
            f"No prueba que la IA cause el uso — es igual de posible que los clientes "
            f"más intensos sean los que se animan a probarla. Pero sí dice dónde "
            f"buscar los siguientes: los clientes de alto volumen que <b>todavía no</b> "
            f"la han activado son el público obvio para el próximo lanzamiento, y hoy "
            f"son <b>{len(sin_ia[sin_ia['docs_emitidos'] > sin_ia['docs_emitidos'].median()*2]):,}</b> "
            f"solo dentro de este panel de 12.000.",
            "🤖", "ok"), unsafe_allow_html=True)

    st.caption("El panel de uso sigue a 12.000 clientes activos de Colombia mes a mes. "
               "La adopción de módulos sí cubre la base completa de los seis países.")
