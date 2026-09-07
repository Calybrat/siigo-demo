"""Soporte y experiencia: el punto que los usuarios señalan y lo que cuesta."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Soporte y Experiencia",
        "Tickets, tiempos, NPS y CSAT · el indicador que más pesa en la fuga evitable",
        "Producto y operación"), unsafe_allow_html=True)

    tk = datos.tickets()
    n = datos.nps()
    meses = datos.meses()
    ult = meses[-1]

    f1, f2 = st.columns([2, 2])
    with f1:
        pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                key="sop_pais")
    with f2:
        vent = st.selectbox("Ventana", ["Últimos 12 meses", "Último mes",
                                        "Todo el histórico"], key="sop_vent")
    ms = {"Últimos 12 meses": meses[-12:], "Último mes": [ult],
          "Todo el histórico": meses}[vent]

    t = tk[tk["mes"].isin(ms)]
    nn = n[n["mes"].isin(ms)]
    if pais_sel != "Todos":
        t = t[t["pais"] == pais_sel]
        nn = nn[nn["pais"] == pais_sel]

    # El set guarda 1 de cada 6 tickets como muestra trazable
    FACTOR = 6
    fcr = t["resuelto_primer_contacto"].mean() * 100
    csat = t["csat"].mean()
    fr_med = t["primera_respuesta_min"].median()
    nps_val = float((nn["nps"] * nn["encuestados"]).sum() /
                    max(nn["encuestados"].sum(), 1))

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Tickets del período", miles(len(t) * FACTOR),
                      f"{len(t)*FACTOR/max(len(ms),1):,.0f} al mes en promedio",
                      True, "🎫",
                      "Contactos de clientes que pidieron ayuda."), unsafe_allow_html=True)
    k[1].markdown(kpi("Primera respuesta", f"{fr_med:,.0f} min",
                      f"Percentil 90: {t['primera_respuesta_min'].quantile(.9):,.0f} min",
                      fr_med < 45, "⏱️",
                      "Mediana de lo que tarda alguien en contestar."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("Resuelto al primer contacto", pct(fcr),
                      "Referencia del sector: 70%", fcr >= 70, "✅",
                      "Casos cerrados sin que el cliente tenga que volver."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("NPS", f"{nps_val:.0f}",
                      f"CSAT de los tickets: {csat:.2f}/5", nps_val >= 30, "💬",
                      "Los usuarios califican el soporte por debajo del producto."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🌡️  La temporada tributaria", "📊  Qué preguntan",
                                "💬  NPS y satisfacción"])

    # ═══ Temporada ═══════════════════════════════════════════════════════════
    with tab1:
        tt = tk if pais_sel == "Todos" else tk[tk["pais"] == pais_sel]
        g = tt.groupby("mes").agg(
            n=("ticket_id", "count"),
            fr=("primera_respuesta_min", "median"),
            fcr=("resuelto_primer_contacto", "mean"),
            csat=("csat", "mean")).reset_index()
        g["n"] = g["n"] * FACTOR

        fig = go.Figure()
        fig.add_trace(go.Bar(x=[mes_es(m) for m in g["mes"]], y=g["n"],
                             name="Tickets", marker_color=AZUL_PALE))
        fig.add_trace(go.Scatter(x=[mes_es(m) for m in g["mes"]], y=g["fr"],
                                 name="Primera respuesta (min)", yaxis="y2",
                                 mode="lines+markers",
                                 line=dict(color=BAD, width=3)))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                      ticksuffix=" min", tickfont=dict(color=BAD)))
        fig.update_yaxes(tickformat=".2s")
        st.plotly_chart(light(fig, 380,
                              "Volumen de tickets y tiempo de primera respuesta"),
                        use_container_width=True)

        en_t = t[t["en_temporada"]]
        fuera = t[~t["en_temporada"]]
        c1, c2, c3 = st.columns(3, gap="medium")
        for col, titulo, a, b, suf, mejor_bajo in [
            (c1, "Primera respuesta", en_t["primera_respuesta_min"].median(),
             fuera["primera_respuesta_min"].median(), " min", True),
            (c2, "Resuelto al primer contacto", en_t["resuelto_primer_contacto"].mean() * 100,
             fuera["resuelto_primer_contacto"].mean() * 100, "%", False),
            (c3, "CSAT", en_t["csat"].mean(), fuera["csat"].mean(), " / 5", False),
        ]:
            peor = (a > b) if mejor_bajo else (a < b)
            with col:
                fig = go.Figure(go.Bar(
                    x=["En temporada", "Fuera de temporada"], y=[a, b],
                    marker_color=[BAD if peor else GOOD, AZUL_LT],
                    text=[f"{a:,.1f}{suf}", f"{b:,.1f}{suf}"],
                    textposition="outside", textfont=dict(size=12)))
                st.plotly_chart(light(fig, 280, titulo), use_container_width=True)

        deterioro = (en_t["primera_respuesta_min"].median() /
                     max(fuera["primera_respuesta_min"].median(), 1))
        mc = datos.motivos_churn()
        mc12 = mc[mc["mes"].isin(meses[-12:])]
        if pais_sel != "Todos":
            mc12 = mc12[mc12["pais"] == pais_sel]
        churn_sop = mc12[mc12["motivo"] == "Mala experiencia de soporte"]

        st.markdown(panel(
            "El soporte no es malo todo el año: se rompe cinco meses",
            f"Fuera de temporada, la primera respuesta llega en "
            f"<b>{fuera['primera_respuesta_min'].median():,.0f} minutos</b> y el "
            f"<b>{fuera['resuelto_primer_contacto'].mean()*100:.0f}%</b> de los casos "
            f"se cierra de una. En marzo, abril, mayo, agosto y septiembre eso pasa a "
            f"<b>{en_t['primera_respuesta_min'].median():,.0f} minutos</b> "
            f"({deterioro:.1f} veces más) y "
            f"<b>{en_t['resuelto_primer_contacto'].mean()*100:.0f}%</b>.<br><br>"
            f"Esos cinco meses explican "
            f"<b>{usd(churn_sop['mrr_perdido_usd'].sum()*12)}</b> de ARR perdido por "
            f"mala experiencia de soporte en el año.<br><br>"
            f"<b>La conclusión operativa:</b> no es un problema de calidad del equipo, "
            f"es de capacidad en fechas conocidas con doce meses de anticipación. "
            f"El calendario de la DIAN se publica; la contratación temporal se "
            f"puede planear contra él.",
            "🌡️", "alerta"), unsafe_allow_html=True)

    # ═══ Qué preguntan ═══════════════════════════════════════════════════════
    with tab2:
        c1, c2 = st.columns([1.3, 1], gap="medium")
        with c1:
            g = (t.groupby("categoria")
                 .agg(n=("ticket_id", "count"),
                      res=("resolucion_horas", "mean"),
                      fcr=("resuelto_primer_contacto", "mean"))
                 .sort_values("n", ascending=True).reset_index())
            g["n"] = g["n"] * FACTOR
            fig = go.Figure(go.Bar(
                y=g["categoria"], x=g["n"], orientation="h", marker_color=AZUL,
                text=[miles(v) for v in g["n"]], textposition="auto",
                textfont=dict(size=10),
                customdata=np.stack([g["res"], g["fcr"] * 100], axis=-1),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} tickets<br>"
                              "Resolución %{customdata[0]:.1f} h<br>"
                              "Primer contacto %{customdata[1]:.0f}%<extra></extra>"))
            fig.update_xaxes(tickformat=".2s")
            st.plotly_chart(light(fig, 400, "Tickets por categoría"),
                            use_container_width=True)
        with c2:
            gc = t.groupby("canal").size().sort_values().reset_index(name="n")
            gc["n"] = gc["n"] * FACTOR
            fig = go.Figure(go.Pie(labels=gc["canal"], values=gc["n"], hole=0.6,
                                   marker_colors=PALETTE,
                                   texttemplate="%{percent:.0%}"))
            st.plotly_chart(light(fig, 400, "Por dónde llegan"),
                            use_container_width=True)

        # Coste por categoría: volumen × tiempo de resolución
        g["costo_horas"] = g["n"] * g["res"]
        peor = g.nlargest(1, "costo_horas").iloc[0]
        ia_pct = t["atendido_por_ia"].mean() * 100
        ia_ev = tk.groupby("mes")["atendido_por_ia"].mean().reset_index()

        c3, c4 = st.columns([1, 1], gap="medium")
        with c3:
            fig = go.Figure(go.Scatter(
                x=[mes_es(m) for m in ia_ev["mes"]],
                y=ia_ev["atendido_por_ia"] * 100, mode="lines+markers",
                line=dict(color=MORADO, width=3), fill="tozeroy",
                fillcolor="rgba(124,92,224,.10)"))
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 320,
                                  "Tickets atendidos con asistencia de IA"),
                            use_container_width=True)
        with c4:
            st.markdown(panel(
                "Dónde está el costo real del soporte",
                f"La categoría más cara no es la más frecuente. "
                f"<b>{peor['categoria']}</b> consume "
                f"<b>{peor['costo_horas']:,.0f} horas</b> de equipo al año: "
                f"{miles(peor['n'])} tickets por {peor['res']:.1f} horas de "
                f"resolución promedio.<br><br>"
                f"Hoy la IA atiende el <b>{ia_pct:.0f}%</b> de los tickets y la curva "
                f"sube todos los meses. Pero conviene dirigirla: automatizar la "
                f"categoría de mayor volumen alivia el conteo; automatizar la de "
                f"mayor <b>costo en horas</b> libera gente para los casos que "
                f"realmente necesitan una persona.",
                "🧮"), unsafe_allow_html=True)

        st.markdown("##### Detalle por categoría")
        gd = g.sort_values("costo_horas", ascending=False)
        st.dataframe(pd.DataFrame({
            "Categoría": gd["categoria"],
            "Tickets": [f"{x:,.0f}" for x in gd["n"]],
            "Mezcla": [f"{x/gd['n'].sum()*100:.1f}%" for x in gd["n"]],
            "Resolución promedio": [f"{x:.1f} h" for x in gd["res"]],
            "Resuelto al primer contacto": [f"{x*100:.0f}%" for x in gd["fcr"]],
            "Horas de equipo al año": [f"{x:,.0f}" for x in gd["costo_horas"]],
        }), width="stretch", hide_index=True)

    # ═══ NPS ═════════════════════════════════════════════════════════════════
    with tab3:
        c1, c2 = st.columns([1.5, 1], gap="medium")
        with c1:
            nt = n if pais_sel == "Todos" else n[n["pais"] == pais_sel]
            g = nt.groupby("mes").apply(
                lambda d: pd.Series({
                    "nps": (d["nps"] * d["encuestados"]).sum() / d["encuestados"].sum(),
                    "csat": (d["csat"] * d["encuestados"]).sum() / d["encuestados"].sum()}),
                include_groups=False).reset_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[mes_es(m) for m in g["mes"]], y=g["nps"],
                                     name="NPS", mode="lines+markers",
                                     line=dict(color=AZUL, width=3)))
            fig.add_hline(y=30, line_dash="dot", line_color=MUTED,
                          annotation_text="referencia B2B: 30",
                          annotation_font_size=10)
            st.plotly_chart(light(fig, 340, "NPS mes a mes"),
                            use_container_width=True)
        with c2:
            seg = nt[nt["mes"] == ult].groupby("segmento").apply(
                lambda d: (d["nps"] * d["encuestados"]).sum() / d["encuestados"].sum(),
                include_groups=False).sort_values().reset_index(name="nps")
            fig = go.Figure(go.Bar(
                y=seg["segmento"], x=seg["nps"], orientation="h",
                marker_color=[GOOD if v >= 30 else (WARN if v >= 15 else BAD)
                              for v in seg["nps"]],
                text=[f"{v:.0f}" for v in seg["nps"]], textposition="auto",
                textfont=dict(size=11)))
            st.plotly_chart(light(fig, 340, "NPS por segmento"),
                            use_container_width=True)

        ult_n = nt[nt["mes"] == ult]
        pro = float((ult_n["promotores_pct"] * ult_n["encuestados"]).sum() /
                    ult_n["encuestados"].sum())
        det = float((ult_n["detractores_pct"] * ult_n["encuestados"]).sum() /
                    ult_n["encuestados"].sum())
        micro = float(seg[seg["segmento"] == "Micro"]["nps"].iloc[0])
        cont = float(seg[seg["segmento"] == "Contador"]["nps"].iloc[0])

        c3, c4 = st.columns([1, 1], gap="medium")
        with c3:
            fig = go.Figure(go.Bar(
                x=[pro, 100 - pro - det, det], y=["", "", ""], orientation="h",
                marker_color=[GOOD, "#D9E4EC", BAD],
                text=[f"Promotores {pro:.0f}%", f"Pasivos {100-pro-det:.0f}%",
                      f"Detractores {det:.0f}%"],
                textposition="inside", textfont=dict(size=11, color="white")))
            fig.update_layout(barmode="stack", showlegend=False)
            fig.update_xaxes(ticksuffix="%", range=[0, 100])
            st.plotly_chart(light(fig, 200, "Composición del NPS del último mes"),
                            use_container_width=True)
        with c4:
            st.markdown(panel(
                "El contador califica mejor que la pyme",
                f"Los contadores dan <b>{cont:.0f}</b> de NPS; los micronegocios, "
                f"<b>{micro:.0f}</b>. La diferencia es de "
                f"<b>{cont-micro:.0f} puntos</b>.<br><br>"
                f"Tiene sentido: el contador usa Siigo todos los días, conoce los "
                f"atajos y sabe a quién llamar. El dueño de un micronegocio entra "
                f"cuatro veces al mes, se topa con un rechazo de la DIAN y no tiene "
                f"contexto para resolverlo solo.<br><br>"
                f"Es el mismo producto con dos experiencias distintas — y el segmento "
                f"que peor califica es justo el más numeroso y el que más se va.",
                "💬"), unsafe_allow_html=True)

        st.markdown("##### NPS por país y segmento · último mes")
        piv = n[n["mes"] == ult].pivot_table(index="pais", columns="segmento",
                                             values="nps", aggfunc="mean")
        st.dataframe(piv.round(0).astype(int), width="stretch")

    st.caption("El set guarda uno de cada seis tickets como muestra trazable; los "
               "totales del panel ya vienen reexpresados al volumen completo. "
               "El NPS y el CSAT de relación salen de la encuesta mensual, "
               "no de los tickets.")
