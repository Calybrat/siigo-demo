"""Retención, fuga y cohortes: por qué se van y cuáles se van a ir."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Retención, Fuga y Cohortes",
        "Cuántos se van, por qué, y quiénes están a punto de irse",
        "Ingresos"), unsafe_allow_html=True)

    meses = datos.meses()
    f1, _ = st.columns([2, 4])
    with f1:
        pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                key="ret_pais")

    ind = datos.indicadores_mes(pais_sel)
    nrr = datos.nrr_anual(pais_sel)
    grr = datos.grr_anual(pais_sel)
    churn_m = float(ind["churn_logo_pct"].tail(12).mean())
    churn_a = (1 - (1 - churn_m / 100) ** 12) * 100
    vida = 1 / (churn_m / 100)

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("NRR (12 meses)", pct(nrr), "Sano en pymes: ≥100%", nrr >= 100,
                      "🔁", "Valor de la base de hace un año, hoy."), unsafe_allow_html=True)
    k[1].markdown(kpi("GRR (12 meses)", pct(grr), "Sano en pymes: ≥80%", grr >= 80,
                      "🛡️", "Lo mismo, pero sin dejar que la expansión tape la fuga."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("Fuga de clientes", f"{churn_a:.1f}% al año",
                      f"{churn_m:.2f}% mensual promedio", churn_a < 20, "📉",
                      "Proporción de la base que cancela en doce meses."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Vida promedio", f"{vida:.0f} meses",
                      f"{vida/12:.1f} años de relación", vida > 40, "⏳",
                      "Cuánto dura un cliente antes de irse, al ritmo de fuga actual."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊  Motivos y planes", "🗓️  Cohortes",
                                "⚠️  Clientes en riesgo (Colombia)"])

    # ═══ Motivos de fuga ═════════════════════════════════════════════════════
    with tab1:
        mc = datos.motivos_churn()
        mc12 = mc[mc["mes"].isin(meses[-12:])]
        if pais_sel != "Todos":
            mc12 = mc12[mc12["pais"] == pais_sel]

        c1, c2 = st.columns([1.15, 1], gap="medium")
        with c1:
            g = (mc12.groupby("motivo")
                 .agg(clientes=("clientes", "sum"), mrr=("mrr_perdido_usd", "sum"))
                 .sort_values("mrr", ascending=True).reset_index())
            colores = [BAD if "soporte" in m or "competencia" in m else AZUL
                       for m in g["motivo"]]
            fig = go.Figure(go.Bar(
                y=g["motivo"], x=g["mrr"] * 12, orientation="h",
                marker_color=colores, text=[usd(v * 12) for v in g["mrr"]],
                textposition="auto", textfont=dict(size=10),
                customdata=g["clientes"],
                hovertemplate="<b>%{y}</b><br>ARR perdido %{x:$,.0f}<br>"
                              "%{customdata:,.0f} clientes<extra></extra>"))
            fig.update_xaxes(tickprefix="US$", tickformat=".2s")
            st.plotly_chart(light(fig, 380, "ARR perdido por motivo (12 meses)"),
                            use_container_width=True)
        with c2:
            evitable = mc12[mc12["motivo"].isin([
                "Mala experiencia de soporte", "Se fue a la competencia",
                "No logró implementar", "Funcionalidad faltante"])]
            no_evit = mc12[~mc12["motivo"].isin([
                "Mala experiencia de soporte", "Se fue a la competencia",
                "No logró implementar", "Funcionalidad faltante"])]
            fig = go.Figure(go.Pie(
                labels=["Se puede evitar desde adentro", "Fuera del control de Siigo"],
                values=[evitable["mrr_perdido_usd"].sum(), no_evit["mrr_perdido_usd"].sum()],
                hole=0.62, marker_colors=[NARANJA, "#C4D6E3"],
                texttemplate="%{percent:.0%}"))
            st.plotly_chart(light(fig, 380, "¿Cuánta fuga depende de una decisión interna?"),
                            use_container_width=True)

        pct_evit = (evitable["mrr_perdido_usd"].sum() /
                    mc12["mrr_perdido_usd"].sum() * 100)
        soporte = mc12[mc12["motivo"] == "Mala experiencia de soporte"]
        st.markdown(panel(
            "El dato incómodo",
            f"El <b>{pct_evit:.0f}%</b> del ARR que se pierde se va por razones que "
            f"dependen de Siigo: soporte, implementación, funcionalidad o competencia. "
            f"Solo el resto es porque el negocio del cliente cerró.<br><br>"
            f"Soporte solo explica <b>{usd(soporte['mrr_perdido_usd'].sum()*12)}</b> "
            f"de ARR perdido en doce meses, y sube justo en los meses de mayor carga "
            f"tributaria. No es un problema de producto: es un problema de capacidad "
            f"en marzo, abril, mayo, agosto y septiembre.",
            "⚠️", "alerta"), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("##### Fuga por plan")
        pl = (mc12.groupby("plan").agg(clientes=("clientes", "sum"),
                                       mrr=("mrr_perdido_usd", "sum")).reset_index())
        susc_ult = datos.suscripciones()
        susc_ult = susc_ult[susc_ult["mes"] == meses[-1]]
        if pais_sel != "Todos":
            susc_ult = susc_ult[susc_ult["pais"] == pais_sel]
        base = susc_ult.groupby("plan")["clientes"].sum()
        pl["base"] = pl["plan"].map(base)
        pl["churn_anual"] = pl["clientes"] / pl["base"] * 100
        pl = pl.sort_values("churn_anual", ascending=False)
        st.dataframe(pd.DataFrame({
            "Plan": pl["plan"],
            "Clientes activos": [f"{x:,.0f}" for x in pl["base"]],
            "Bajas 12 meses": [f"{x:,.0f}" for x in pl["clientes"]],
            "Fuga anual": [f"{x:.1f}%" for x in pl["churn_anual"]],
            "ARR perdido": [usd(x * 12) for x in pl["mrr"]],
        }), width="stretch", hide_index=True)

    # ═══ Cohortes ════════════════════════════════════════════════════════════
    with tab2:
        coh = datos.cohortes()
        if pais_sel != "Todos":
            coh = coh[coh["pais"] == pais_sel]
        g = (coh.groupby(["cohorte", "mes_vida"])
             .apply(lambda d: pd.Series({
                 "ret": (d["clientes_retenidos"].sum() /
                         d["clientes_inicial"].sum() * 100)}), include_groups=False)
             .reset_index())
        piv = g.pivot(index="cohorte", columns="mes_vida", values="ret")
        piv = piv.iloc[::-1]

        fig = go.Figure(go.Heatmap(
            z=piv.values, x=[f"M{c}" for c in piv.columns],
            y=[mes_es(m) for m in piv.index],
            colorscale=[[0, "#FBE3DE"], [0.5, AZUL_PALE], [1, AZUL]],
            zmin=40, zmax=100, colorbar=dict(ticksuffix="%", thickness=12),
            hovertemplate="Cohorte %{y}<br>Mes %{x}<br>Retención %{z:.1f}%<extra></extra>"))
        fig.update_layout(height=520, margin=dict(l=6, r=6, t=44, b=16),
                          paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Poppins, sans-serif", color=MUTED, size=11),
                          title=dict(text="Retención de clientes por cohorte de entrada",
                                     font=dict(size=14, color=TINTA), x=0))
        st.plotly_chart(fig, use_container_width=True)

        m1 = float(g[g["mes_vida"] == 1]["ret"].mean())
        m6 = float(g[g["mes_vida"] == 6]["ret"].mean())
        m12 = float(g[g["mes_vida"] == 12]["ret"].mean())
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            curva = g.groupby("mes_vida")["ret"].mean().reset_index()
            fig = go.Figure(go.Scatter(
                x=curva["mes_vida"], y=curva["ret"], mode="lines+markers",
                line=dict(color=AZUL, width=3), fill="tozeroy",
                fillcolor="rgba(0,157,255,.10)"))
            fig.update_xaxes(title="Meses desde el alta")
            fig.update_yaxes(ticksuffix="%", range=[40, 102])
            st.plotly_chart(light(fig, 320, "Curva de retención promedio"),
                            use_container_width=True)
        with c2:
            st.markdown(panel(
                "Dónde se rompe la relación",
                f"Al primer mes ya se ha ido el <b>{100-m1:.1f}%</b> de cada cohorte. "
                f"A los seis meses queda el <b>{m6:.0f}%</b> y al año el "
                f"<b>{m12:.0f}%</b>.<br><br>"
                f"La caída del primer mes es la más cara y la más recuperable: son "
                f"clientes que ya pagaron el CAC completo y nunca llegaron a emitir su "
                f"primera factura. Bajar esa caída un punto vale más que cualquier "
                f"campaña de adquisición, porque no cuesta CAC adicional.<br><br>"
                f"A partir del mes 12 la curva se aplana: quien sobrevive el primer año "
                f"se queda mucho tiempo.",
                "🔬"), unsafe_allow_html=True)

    # ═══ Clientes en riesgo ══════════════════════════════════════════════════
    with tab3:
        cli = datos.clientes()
        act = cli[cli["estado"] == "Activo"]
        riesgo = act[act["riesgo_fuga"]]

        k = st.columns(4, gap="small")
        k[0].markdown(kpi("Clientes en riesgo", f"{len(riesgo):,}",
                          f"{len(riesgo)/len(act)*100:.1f}% de la base activa",
                          False, "⚠️",
                          "Salud por debajo de 42 sobre 100."), unsafe_allow_html=True)
        k[1].markdown(kpi("ARR en riesgo", usd(riesgo["mrr_usd"].sum() * 12),
                          "Si no se hace nada", False, "💸",
                          "Ingreso anual expuesto en esos clientes."),
                      unsafe_allow_html=True)
        k[2].markdown(kpi("Sin entrar hace +30 días",
                          f"{(act['dias_sin_acceso'] > 30).sum():,}",
                          "La señal más temprana de fuga", False, "🚪",
                          "Quien deja de entrar deja de pagar tres meses después."),
                      unsafe_allow_html=True)
        k[3].markdown(kpi("Salud promedio", f"{act['salud'].mean():.0f}/100",
                          "Uso, módulos y antigüedad", act["salud"].mean() > 55, "❤️",
                          "Índice compuesto de qué tan enganchado está el cliente."),
                      unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            fig = go.Figure(go.Histogram(
                x=act["salud"], nbinsx=40, marker_color=AZUL_LT,
                marker_line=dict(width=0)))
            fig.add_vline(x=42, line_dash="dash", line_color=BAD,
                          annotation_text="umbral de riesgo", annotation_font_size=10)
            fig.update_xaxes(title="Índice de salud (0–100)")
            st.plotly_chart(light(fig, 320, "Distribución de la salud de los clientes"),
                            use_container_width=True)
        with c2:
            por_sector = (riesgo.groupby("sector")
                          .agg(n=("cliente_id", "count"), mrr=("mrr_usd", "sum"))
                          .sort_values("mrr", ascending=True).tail(9).reset_index())
            fig = go.Figure(go.Bar(
                y=por_sector["sector"], x=por_sector["mrr"] * 12, orientation="h",
                marker_color=NARANJA, customdata=por_sector["n"],
                hovertemplate="<b>%{y}</b><br>ARR en riesgo %{x:$,.0f}<br>"
                              "%{customdata:,.0f} clientes<extra></extra>"))
            fig.update_xaxes(tickprefix="US$", tickformat=".2s")
            st.plotly_chart(light(fig, 320, "ARR en riesgo por sector"),
                            use_container_width=True)

        st.markdown("##### Los 25 clientes de mayor ARR en riesgo")
        st.caption("Ordenados por lo que se pierde si se van. Es la lista de llamadas "
                   "de la semana para el equipo de retención.")
        top = riesgo.nlargest(25, "mrr_usd")[[
            "cliente_id", "plan", "sector", "ciudad", "antiguedad_meses",
            "mrr_usd", "salud", "dias_sin_acceso", "docs_mes"]].copy()
        st.dataframe(pd.DataFrame({
            "Cliente": top["cliente_id"], "Plan": top["plan"],
            "Sector": top["sector"], "Ciudad": top["ciudad"],
            "Antigüedad": [f"{x} meses" for x in top["antiguedad_meses"]],
            "ARR": [usd(x * 12) for x in top["mrr_usd"]],
            "Salud": top["salud"],
            "Sin entrar": [f"{x} días" for x in top["dias_sin_acceso"]],
            "Docs/mes": top["docs_mes"],
        }), width="stretch", hide_index=True)
