"""El canal de contadores: la red que distribuye Siigo sin costo de adquisición."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Canal de Contadores",
        "+35.000 contadores · Siigo Contador gratis · directorio y programa de partners",
        "Canal y mercados"), unsafe_allow_html=True)

    c = datos.contadores()
    cli = datos.clientes()
    emb = datos.embudo()
    meses = datos.meses()

    f1, _ = st.columns([2, 4])
    with f1:
        pais_sel = st.selectbox("País", ["Todos"] + sorted(c["pais"].unique()),
                                key="cont_pais")
    cf = c if pais_sel == "Todos" else c[c["pais"] == pais_sel]

    activos = cf[cf["activo_ultimos_6m"]]
    arr_canal = cf["arr_referido_usd"].sum()
    emb12 = emb[emb["mes"].isin(meses[-12:])]
    if pais_sel != "Todos":
        emb12 = emb12[emb12["pais"] == pais_sel]
    canal12 = emb12[emb12["canal"] == "Canal de contadores"]
    cac_canal = canal12["inversion_usd"].sum() / max(canal12["pagados"].sum(), 1)
    cac_total = emb12["inversion_usd"].sum() / max(emb12["pagados"].sum(), 1)

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Contadores registrados", f"{len(cf):,}",
                      f"{len(activos):,} refirieron en los últimos 6 meses",
                      len(activos) / len(cf) > 0.5, "🧮",
                      "La red de distribución más grande de la compañía."),
                  unsafe_allow_html=True)
    k[1].markdown(kpi("ARR que trae el canal", usd(arr_canal),
                      f"{cf['clientes_activos'].sum():,.0f} clientes activos referidos",
                      True, "💰",
                      "Ingreso anual de las pymes que llegaron por un contador."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("CAC del canal", f"US${cac_canal:,.0f}",
                      f"{cac_total/cac_canal:.1f}x más barato que el promedio",
                      True, "🎯",
                      "Lo que cuesta traer un cliente por recomendación de su contador."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Contadores dormidos",
                      f"{(~cf['activo_ultimos_6m']).sum():,}",
                      f"{(~cf['activo_ultimos_6m']).mean()*100:.0f}% de la red",
                      False, "😴",
                      "Registrados, pero sin referir a nadie en medio año."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏆  Quién mueve el canal", "😴  La red dormida",
                                "🎁  Programa de partners"])

    # ═══ Concentración ═══════════════════════════════════════════════════════
    with tab1:
        orden = cf.sort_values("arr_referido_usd", ascending=False).reset_index(drop=True)
        orden["acum"] = orden["arr_referido_usd"].cumsum() / arr_canal * 100
        orden["pct_contadores"] = (orden.index + 1) / len(orden) * 100

        c1, c2 = st.columns([1.3, 1], gap="medium")
        with c1:
            paso = max(1, len(orden) // 400)
            sub = orden.iloc[::paso]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sub["pct_contadores"], y=sub["acum"], mode="lines",
                line=dict(color=AZUL, width=3), fill="tozeroy",
                fillcolor="rgba(0,157,255,.10)", name="ARR acumulado"))
            fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines",
                                     line=dict(color=DIM, dash="dot", width=1.5),
                                     name="Si todos aportaran igual"))
            top20 = float(orden[orden["pct_contadores"] <= 20]["acum"].max())
            fig.add_vline(x=20, line_dash="dash", line_color=NARANJA,
                          annotation_text=f"20% de la red → {top20:.0f}% del ARR",
                          annotation_font_size=10)
            fig.update_xaxes(title="% de contadores, del que más aporta al que menos",
                             ticksuffix="%")
            fig.update_yaxes(title="% del ARR del canal", ticksuffix="%")
            st.plotly_chart(light(fig, 380, "Concentración del canal"),
                            use_container_width=True)
        with c2:
            niv = (cf.groupby("nivel_partner")
                   .agg(n=("contador_id", "count"), arr=("arr_referido_usd", "sum"),
                        ref=("clientes_activos", "sum")).reset_index())
            orden_niv = ["Platino", "Oro", "Plata", "Bronce"]
            niv["o"] = niv["nivel_partner"].map({n: i for i, n in enumerate(orden_niv)})
            niv = niv.sort_values("o")
            fig = go.Figure(go.Bar(
                x=niv["nivel_partner"], y=niv["arr"],
                marker_color=[NARANJA, "#E8B33C", "#9AAEBD", "#C08A5E"],
                text=[usd(v) for v in niv["arr"]], textposition="outside",
                textfont=dict(size=10), customdata=niv["n"],
                hovertemplate="<b>%{x}</b><br>ARR %{y:$,.0f}<br>"
                              "%{customdata:,.0f} contadores<extra></extra>"))
            fig.update_yaxes(tickprefix="US$", tickformat=".2s")
            st.plotly_chart(light(fig, 380, "ARR por nivel del programa"),
                            use_container_width=True)

        st.markdown(panel(
            "La red está muy concentrada, y eso es riesgo y oportunidad a la vez",
            f"El <b>20% de los contadores</b> trae el <b>{top20:.0f}%</b> del ARR del "
            f"canal. Los <b>{len(cf[cf['nivel_partner']=='Platino']):,}</b> contadores "
            f"Platino solos aportan "
            f"<b>{usd(cf[cf['nivel_partner']=='Platino']['arr_referido_usd'].sum())}</b>.<br><br>"
            f"<b>El riesgo:</b> perder cien contadores Platino duele más que perder mil "
            f"pymes. Son relaciones personales, no contratos.<br><br>"
            f"<b>La oportunidad:</b> el resto de la red está subutilizada. No hace falta "
            f"reclutar contadores nuevos, hace falta activar los que ya se registraron.",
            "🏆"), unsafe_allow_html=True)

        st.markdown("##### Los 20 contadores que más aportan")
        top = orden.head(20)
        st.dataframe(pd.DataFrame({
            "Contador": [f"C-{int(x):05d}" for x in top["contador_id"]],
            "País": top["pais"], "Ciudad": top["ciudad"],
            "Nivel": top["nivel_partner"],
            "Certificado": ["Sí" if x else "No" for x in top["certificado"]],
            "Clientes referidos": [f"{x:,}" for x in top["clientes_referidos"]],
            "Activos hoy": [f"{x:,}" for x in top["clientes_activos"]],
            "ARR que aporta": [usd(x) for x in top["arr_referido_usd"]],
            "NPS": top["nps"],
        }), width="stretch", hide_index=True)

    # ═══ Red dormida ═════════════════════════════════════════════════════════
    with tab2:
        dormidos = cf[~cf["activo_ultimos_6m"]]
        # Los que ya demostraron que saben referir, pero se apagaron
        valiosos = dormidos[dormidos["clientes_referidos"] >= 8]
        arpa_ref = arr_canal / max(cf["clientes_activos"].sum(), 1)

        k = st.columns(3, gap="small")
        k[0].markdown(kpi("Dormidos con historial", f"{len(valiosos):,}",
                          "Ya refirieron 8 o más clientes antes", False, "😴",
                          "Saben usar el producto y saben venderlo. Se apagaron."),
                      unsafe_allow_html=True)
        k[1].markdown(kpi("Clientes que trajeron en su momento",
                          f"{valiosos['clientes_referidos'].sum():,}",
                          f"Hoy activos: {valiosos['clientes_activos'].sum():,}",
                          True, "📦", "Prueba de que el canal funciona con ellos."),
                      unsafe_allow_html=True)
        k[2].markdown(kpi("ARR si vuelven a referir 1 cliente",
                          usd(len(valiosos) * arpa_ref),
                          "Un solo cliente por contador reactivado", True, "🔔",
                          "El escenario más conservador posible."), unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            g = (cf.groupby(pd.cut(cf["meses_sin_referir"],
                                   [-1, 3, 6, 12, 18, 24, 100],
                                   labels=["0–3", "4–6", "7–12", "13–18",
                                           "19–24", "+24"]), observed=True)
                 .size().reset_index(name="n"))
            g.columns = ["rango", "n"]
            fig = go.Figure(go.Bar(
                x=g["rango"].astype(str), y=g["n"],
                marker_color=[GOOD, GOOD, WARN, WARN, BAD, BAD],
                text=[f"{v:,}" for v in g["n"]], textposition="outside",
                textfont=dict(size=10)))
            fig.update_xaxes(title="Meses sin referir a nadie")
            st.plotly_chart(light(fig, 330, "Cuánto lleva apagado cada contador"),
                            use_container_width=True)
        with c2:
            g2 = (valiosos.groupby("nivel_partner").size()
                  .reset_index(name="n"))
            fig = go.Figure(go.Pie(
                labels=g2["nivel_partner"], values=g2["n"], hole=0.6,
                marker_colors=[NARANJA, "#E8B33C", "#C08A5E", "#9AAEBD"],
                texttemplate="%{percent:.0%}"))
            st.plotly_chart(light(fig, 330,
                                  "Nivel de los contadores dormidos con historial"),
                            use_container_width=True)

        st.markdown(panel(
            "Una lista de llamadas, no una campaña de marca",
            f"Hay <b>{len(valiosos):,} contadores</b> que ya trajeron ocho o más "
            f"clientes a Siigo y llevan más de seis meses sin referir a nadie. "
            f"No son desconocidos: están registrados, muchos usan Siigo Contador "
            f"gratis todos los días y el "
            f"<b>{valiosos['certificado'].mean()*100:.0f}%</b> está certificado.<br><br>"
            f"Reactivar esta lista no requiere presupuesto de medios. Requiere que "
            f"alguien los llame. Si cada uno vuelve a referir <b>un solo cliente</b>, "
            f"son <b>{usd(len(valiosos)*arpa_ref)}</b> de ARR — y el CAC de ese ARR es "
            f"el costo de la llamada.",
            "📞", "naranja"), unsafe_allow_html=True)

    # ═══ Programa ════════════════════════════════════════════════════════════
    with tab3:
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            cert = cf.groupby("certificado").agg(
                n=("contador_id", "count"),
                ref=("clientes_referidos", "mean"),
                arr=("arr_referido_usd", "mean")).reset_index()
            cert["etiqueta"] = ["Sin certificar", "Certificado"]
            fig = go.Figure(go.Bar(
                x=cert["etiqueta"], y=cert["ref"],
                marker_color=[DIM, AZUL],
                text=[f"{v:.1f}" for v in cert["ref"]], textposition="outside",
                textfont=dict(size=11)))
            fig.update_yaxes(title="Clientes referidos en promedio")
            st.plotly_chart(light(fig, 320, "Certificarse cambia el comportamiento"),
                            use_container_width=True)
        with c2:
            dire = cf.groupby("en_directorio").agg(
                ref=("clientes_referidos", "mean")).reset_index()
            dire["etiqueta"] = ["Fuera del directorio", "En el directorio"]
            fig = go.Figure(go.Bar(
                x=dire["etiqueta"], y=dire["ref"],
                marker_color=[DIM, NARANJA],
                text=[f"{v:.1f}" for v in dire["ref"]], textposition="outside",
                textfont=dict(size=11)))
            fig.update_yaxes(title="Clientes referidos en promedio")
            st.plotly_chart(light(fig, 320, "Estar en el directorio también"),
                            use_container_width=True)

        certif = cf[cf["certificado"]]
        no_certif = cf[~cf["certificado"]]
        st.markdown(panel(
            "Los dos programas que ya existen no están aprovechados",
            f"Un contador <b>certificado</b> refiere en promedio "
            f"<b>{certif['clientes_referidos'].mean():.1f}</b> clientes; uno sin "
            f"certificar, <b>{no_certif['clientes_referidos'].mean():.1f}</b>. "
            f"Y hoy solo el <b>{cf['certificado'].mean()*100:.0f}%</b> de la red está "
            f"certificado.<br><br>"
            f"Con el <b>directorio de contadores</b> pasa igual: quien aparece en él "
            f"refiere más, y solo está el <b>{cf['en_directorio'].mean()*100:.0f}%</b>.<br><br>"
            f"No hace falta inventar un programa nuevo. Hace falta meter en los dos "
            f"programas existentes a los contadores que ya están registrados. "
            f"Llevar la certificación del {cf['certificado'].mean()*100:.0f}% al 60% son "
            f"<b>{int(len(cf)*(0.60-cf['certificado'].mean())):,} contadores</b> "
            f"que empiezan a comportarse como los que más refieren.",
            "🎁", "ok"), unsafe_allow_html=True)

        st.markdown("##### Cómo se reparte la red por país")
        g = cf.groupby("pais").agg(
            contadores=("contador_id", "count"),
            activos=("activo_ultimos_6m", "sum"),
            certificados=("certificado", "sum"),
            referidos=("clientes_activos", "sum"),
            arr=("arr_referido_usd", "sum")).reset_index()
        g = g.sort_values("arr", ascending=False)
        st.dataframe(pd.DataFrame({
            "País": g["pais"],
            "Contadores": [f"{x:,}" for x in g["contadores"]],
            "Activos (6 meses)": [f"{x:,}" for x in g["activos"]],
            "% activos": [f"{a/t*100:.0f}%" for a, t in zip(g["activos"], g["contadores"])],
            "% certificados": [f"{a/t*100:.0f}%" for a, t in zip(g["certificados"], g["contadores"])],
            "Clientes referidos activos": [f"{x:,}" for x in g["referidos"]],
            "ARR del canal": [usd(x) for x in g["arr"]],
        }), width="stretch", hide_index=True)
