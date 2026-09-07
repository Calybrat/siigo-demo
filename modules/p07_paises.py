"""Expansión regional: seis países, cuatro adquisiciones y una tesis por mercado."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Expansión Regional",
        "Colombia, México, Ecuador, Perú, Uruguay y Chile · orgánico y por adquisición",
        "Canal y mercados"), unsafe_allow_html=True)

    p = datos.paises()
    susc = datos.suscripciones()
    meses = datos.meses()
    comp = datos.competencia()
    ult = susc[susc["mes"] == meses[-1]]
    ant = susc[susc["mes"] == meses[-13]]

    arr_pais = ult.groupby("pais")["mrr_usd"].sum() * 12
    arr_pais_ant = ant.groupby("pais")["mrr_usd"].sum() * 12
    cli_pais = ult.groupby("pais")["clientes"].sum()
    crecs = ((arr_pais / arr_pais_ant - 1) * 100).sort_values()

    # ── Tarjetas por país ────────────────────────────────────────────────────
    st.markdown("##### Los seis mercados de un vistazo")
    cols = st.columns(6, gap="small")
    for i, row in p.iterrows():
        pais = row["pais"]
        arr = float(arr_pais.get(pais, 0))
        crec = (arr / arr_pais_ant.get(pais, 1) - 1) * 100
        bandera = asset_b64(BANDERAS.get(pais, ""))
        img = (f'<img src="{bandera}" style="width:26px;height:26px;border-radius:50%;'
               f'object-fit:cover">' if bandera else "🌎")
        color = PALETTE_PAIS.get(pais, AZUL)
        cols[i].markdown(f"""
        <div style="background:{SURF};border:1px solid {BORDER};border-top:3px solid {color};
          border-radius:14px;padding:14px 13px;height:100%;
          box-shadow:0 1px 3px rgba(5,46,74,.05)">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:9px">
            {img}
            <div style="font-size:13px;font-weight:800;color:{TINTA}">{pais}</div>
          </div>
          <div style="font-size:19px;font-weight:800;color:{TINTA};letter-spacing:-.5px">
            {usd(arr)}</div>
          <div style="font-size:11px;font-weight:700;color:{GOOD if crec>0 else BAD};
            margin-top:3px">▲ {crec:.1f}% año</div>
          <div style="font-size:10.5px;color:{MUTED};margin-top:8px;line-height:1.6">
            {miles(cli_pais.get(pais,0))} clientes<br>
            {row['penetracion_pct']:.2f}% del mercado<br>
            <span style="color:{AZUL}">{row['via_entrada']}</span><br>
            desde {int(row['anio_entrada'])}
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊  Tamaño y crecimiento", "🎯  Penetración y techo",
                                "⚔️  Competencia por mercado"])

    # ═══ Tamaño ══════════════════════════════════════════════════════════════
    with tab1:
        c1, c2 = st.columns([1.5, 1], gap="medium")
        with c1:
            g = susc.groupby(["mes", "pais"])["mrr_usd"].sum().reset_index()
            fig = go.Figure()
            for pais in p["pais"]:
                sub = g[g["pais"] == pais]
                fig.add_trace(go.Scatter(
                    x=[mes_es(m) for m in sub["mes"]], y=sub["mrr_usd"] * 12,
                    name=pais, mode="lines",
                    line=dict(color=PALETTE_PAIS.get(pais, AZUL), width=2.5)))
            fig.update_yaxes(tickprefix="US$", tickformat=".2s", type="log")
            st.plotly_chart(light(fig, 380, "ARR por país · escala logarítmica"),
                            use_container_width=True)
            st.caption("Escala logarítmica a propósito: en escala lineal Colombia y "
                       "México aplastan a los cuatro mercados pequeños y no se ve "
                       "cuál está creciendo más rápido.")
        with c2:
            fig = go.Figure(go.Bar(
                y=crecs.index, x=crecs.values, orientation="h",
                marker_color=[PALETTE_PAIS.get(x, AZUL) for x in crecs.index],
                text=[f"{v:+.1f}%" for v in crecs.values], textposition="auto",
                textfont=dict(size=10)))
            fig.update_xaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 380, "Crecimiento del ARR en 12 meses"),
                            use_container_width=True)

        chile_crec = float(crecs.get("Chile", 0))
        col_arr = float(arr_pais["Colombia"])
        st.markdown(panel(
            "Dos negocios distintos dentro de la misma empresa",
            f"<b>Colombia</b> aporta <b>{usd(col_arr)}</b>, el "
            f"<b>{col_arr/arr_pais.sum()*100:.0f}%</b> del ARR del grupo, y crece "
            f"<b>{float(crecs['Colombia']):.1f}%</b>. Es un mercado maduro donde Siigo "
            f"ya es líder: el crecimiento viene de ARPA, no de logos nuevos.<br><br>"
            f"<b>Chile</b> crece <b>{chile_crec:.1f}%</b> pero sobre una base de "
            f"{usd(float(arr_pais['Chile']))}. Es un mercado donde todavía no hay masa "
            f"crítica y cada punto de crecimiento cuesta el CAC más alto de los seis.<br><br>"
            f"Mezclar los dos en un solo número de crecimiento del grupo esconde la "
            f"decisión real: <b>cuánto capital de los US$103,5M va a defender Colombia "
            f"y cuánto a abrir Chile.</b>",
            "🗺️"), unsafe_allow_html=True)

    # ═══ Penetración ═════════════════════════════════════════════════════════
    with tab2:
        pp = p.copy()
        pp["arr"] = pp["pais"].map(arr_pais)
        pp["arpa"] = pp["arr"] / 12 / pp["pais"].map(cli_pais)
        pp["crec"] = pp["pais"].map(crecs)

        fig = go.Figure()
        for _, r in pp.iterrows():
            fig.add_trace(go.Scatter(
                x=[r["penetracion_pct"]], y=[r["crec"]], mode="markers+text",
                marker=dict(size=np.sqrt(r["arr"]) / 90 + 16,
                            color=PALETTE_PAIS.get(r["pais"], AZUL),
                            line=dict(color="white", width=2)),
                text=[r["pais"]], textposition="top center",
                textfont=dict(size=11, color=TINTA), name=r["pais"],
                hovertemplate=(f"<b>{r['pais']}</b><br>"
                               f"Penetración {r['penetracion_pct']:.2f}%<br>"
                               f"Crecimiento {r['crec']:.1f}%<br>"
                               f"ARR {usd(r['arr'])}<br>"
                               f"{r['clientes_activos']:,} de {r['pymes_mercado']:,} pymes"
                               "<extra></extra>")))
        fig.update_xaxes(title="Penetración del mercado de pymes", ticksuffix="%")
        fig.update_yaxes(title="Crecimiento del ARR (12 meses)", ticksuffix="%")
        fig.update_layout(showlegend=False)
        st.plotly_chart(light(fig, 420,
                              "Dónde hay techo · el tamaño de la burbuja es el ARR"),
                        use_container_width=True)

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            pp2 = pp.sort_values("penetracion_pct")
            fig = go.Figure()
            fig.add_trace(go.Bar(y=pp2["pais"], x=pp2["clientes_activos"],
                                 orientation="h", name="Clientes de Siigo",
                                 marker_color=AZUL))
            fig.add_trace(go.Bar(y=pp2["pais"],
                                 x=pp2["pymes_mercado"] - pp2["clientes_activos"],
                                 orientation="h", name="Pymes sin Siigo",
                                 marker_color=AZUL_PALE))
            fig.update_layout(barmode="stack")
            fig.update_xaxes(type="log")
            st.plotly_chart(light(fig, 330, "Mercado direccionable por país"),
                            use_container_width=True)
        with c2:
            st.markdown(panel(
                "El techo no está donde parece",
                f"<b>Uruguay</b> tiene la penetración más alta "
                f"({float(pp[pp['pais']=='Uruguay']['penetracion_pct'].iloc[0]):.2f}%) "
                f"pero el mercado más pequeño: "
                f"{int(pp[pp['pais']=='Uruguay']['pymes_mercado'].iloc[0]):,} pymes en "
                f"total. Ahí el crecimiento solo puede venir de ARPA.<br><br>"
                f"<b>México</b> tiene {int(pp[pp['pais']=='México']['pymes_mercado'].iloc[0]):,} "
                f"pymes y una penetración de "
                f"{float(pp[pp['pais']=='México']['penetracion_pct'].iloc[0]):.2f}%. "
                f"Es el mercado con más espacio en términos absolutos, y ya hay una "
                f"base heredada de Aspel para trabajarlo.<br><br>"
                f"<b>Perú</b> es el caso incómodo: mercado grande, penetración "
                f"{float(pp[pp['pais']=='Perú']['penetracion_pct'].iloc[0]):.2f}% y "
                f"entrada orgánica desde 2019. Siete años y todavía sin masa crítica.",
                "📐"), unsafe_allow_html=True)

        st.dataframe(pd.DataFrame({
            "País": pp["pais"],
            "Entrada": [f"{int(a)} · {v}" for a, v in
                        zip(pp["anio_entrada"], pp["via_entrada"])],
            "Clientes": [f"{x:,}" for x in pp["clientes_activos"]],
            "Pymes en el mercado": [f"{x:,}" for x in pp["pymes_mercado"]],
            "Penetración": [f"{x:.2f}%" for x in pp["penetracion_pct"]],
            "ARR": [usd(x) for x in pp["arr"]],
            "ARPA": [f"US${x:.2f}" for x in pp["arpa"]],
            "Crecimiento": [f"{x:+.1f}%" for x in pp["crec"]],
            "Competidor principal": pp["competidor_principal"],
        }), width="stretch", hide_index=True)

    # ═══ Competencia ═════════════════════════════════════════════════════════
    with tab3:
        pais_c = st.selectbox("Mercado", comp["pais"].unique().tolist(), key="comp_pais")
        cc = comp[comp["pais"] == pais_c].sort_values("participacion_pct",
                                                      ascending=False)
        c1, c2 = st.columns([1, 1.2], gap="medium")
        with c1:
            colores = [AZUL if "Siigo" in x else
                       ("#C4D6E3" if x == "Otros" else NARANJA)
                       for x in cc["competidor"]]
            fig = go.Figure(go.Pie(
                labels=cc["competidor"], values=cc["participacion_pct"], hole=0.58,
                marker_colors=colores, texttemplate="%{percent:.0%}",
                sort=False))
            st.plotly_chart(light(fig, 340, f"Participación estimada · {pais_c}"),
                            use_container_width=True)
        with c2:
            fig = go.Figure(go.Bar(
                x=cc["competidor"], y=cc["precio_relativo"],
                marker_color=colores,
                text=[f"{v:.2f}x" for v in cc["precio_relativo"]],
                textposition="outside", textfont=dict(size=10)))
            fig.add_hline(y=1.0, line_dash="dot", line_color=MUTED,
                          annotation_text="precio de Siigo", annotation_font_size=10)
            fig.update_yaxes(title="Precio relativo a Siigo")
            st.plotly_chart(light(fig, 340, "Cómo se posiciona el precio"),
                            use_container_width=True)

        st.markdown("##### Fortalezas y debilidades declaradas")
        st.dataframe(pd.DataFrame({
            "Competidor": cc["competidor"],
            "Participación": [f"{x:.1f}%" for x in cc["participacion_pct"]],
            "Precio vs Siigo": [f"{x:.2f}x" for x in cc["precio_relativo"]],
            "Fortaleza": cc["fortaleza"],
            "Debilidad": cc["debilidad"],
        }), width="stretch", hide_index=True)

        st.markdown(panel(
            "El problema de marca que dejan las adquisiciones",
            "En Ecuador el producto sigue siendo <b>Contífico</b>, en Uruguay "
            "<b>Memory</b> y en México <b>Aspel</b>. Cada marca local mantiene el "
            "reconocimiento que ya tenía, pero el grupo pierde la posibilidad de "
            "contar una sola historia regional al cliente y al canal.<br><br>"
            "Es una decisión de negocio, no un descuido: unificar demasiado rápido "
            "cuesta clientes que compraron la marca local. Pero mientras dure, hay "
            "que medirlo — un contador que atiende clientes en tres países hoy "
            "aprende tres productos que por dentro son el mismo.",
            "🏷️", "naranja"), unsafe_allow_html=True)

    st.caption("Las participaciones de mercado son estimaciones del modelo del demo, "
               "no cifras auditadas. Los años de entrada y las adquisiciones "
               "(Ilimitada 2019, Contífico 2020, Memory 2020, Aspel 2022) sí son "
               "información pública.")
