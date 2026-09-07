"""Planes, precios y módulos: dónde está el ingreso y dónde el upsell sin usar."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Planes, Precios y Módulos",
        "Siigo Nube, POS y complementos · precios de lista de Colombia 2026",
        "Ingresos"), unsafe_allow_html=True)

    meses = datos.meses()
    susc = datos.suscripciones()
    planes = datos.planes()
    cli = datos.clientes()
    act = cli[cli["estado"] == "Activo"]
    ult = susc[susc["mes"] == meses[-1]]

    total_arr = ult["mrr_usd"].sum() * 12
    nomina = act["nomina_electronica"].mean() * 100
    pay = act["siigo_pay"].mean() * 100
    pos = act["modulo_pos"].mean() * 100

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("ARR total", usd(total_arr),
                      f"{ult['clientes'].sum():,.0f} suscripciones", True, "🧩",
                      "Repartido entre siete planes en seis países."), unsafe_allow_html=True)
    k[1].markdown(kpi("Nómina Electrónica", pct(nomina),
                      "de la base la tiene contratada", nomina > 30, "👥",
                      "El complemento más vendido y el que más pega la relación."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("Siigo Pay", pct(pay), "de la base lo tiene activo",
                      pay > 20, "💳",
                      "Recaudo dentro del producto: monetiza sin subir el precio del plan."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Módulo POS", pct(pos), "de la base lo tiene", pos > 15, "🛒",
                      "Cajas y tiquetes para comercio y gastronomía."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["💰  Planes y precios", "🔓  Upsell sin usar",
                                "📈  Cómo se mueve la mezcla"])

    # ═══ Planes ══════════════════════════════════════════════════════════════
    with tab1:
        c1, c2 = st.columns([1.3, 1], gap="medium")
        with c1:
            g = ult.groupby("plan").agg(clientes=("clientes", "sum"),
                                        mrr=("mrr_usd", "sum")).reset_index()
            g["arr"] = g["mrr"] * 12
            g["arpa"] = g["mrr"] / g["clientes"]
            g = g.sort_values("arr")
            fig = go.Figure()
            fig.add_trace(go.Bar(y=g["plan"], x=g["arr"], orientation="h",
                                 marker_color=AZUL, name="ARR",
                                 text=[usd(v) for v in g["arr"]],
                                 textposition="auto", textfont=dict(size=10)))
            fig.update_xaxes(tickprefix="US$", tickformat=".2s")
            st.plotly_chart(light(fig, 360, "ARR por plan (grupo)"),
                            use_container_width=True)
        with c2:
            g2 = g.sort_values("clientes")
            fig = go.Figure(go.Bar(
                y=g2["plan"], x=g2["clientes"], orientation="h",
                marker_color=AZUL_LT, text=[miles(v) for v in g2["clientes"]],
                textposition="auto", textfont=dict(size=10)))
            st.plotly_chart(light(fig, 360, "Clientes por plan"),
                            use_container_width=True)

        st.markdown("##### Catálogo de Colombia · precios de lista 2026")
        pc = planes[planes["pais"] == "Colombia"].copy()
        base_co = ult[ult["pais"] == "Colombia"].groupby("plan").agg(
            clientes=("clientes", "sum"), mrr=("mrr_usd", "sum"))
        pc["clientes"] = pc["plan"].map(base_co["clientes"])
        pc["arpa_real"] = pc["plan"].map(base_co["mrr"] / base_co["clientes"])
        st.dataframe(pd.DataFrame({
            "Plan": pc["plan"], "Segmento": pc["segmento"],
            "Usuarios incluidos": pc["usuarios_incluidos"],
            "Precio de lista (COP/mes)": [
                f"${int(x):,}".replace(",", ".") if str(x).strip() not in ("", "nan")
                else "Gratis" for x in pc["precio_cop_mes"]],
            "Equivalente (USD/mes)": [f"US${x:,.2f}" for x in pc["precio_usd_mes"]],
            "Clientes en Colombia": [f"{x:,.0f}" for x in pc["clientes"]],
            "ARPA real (USD/mes)": [f"US${x:,.2f}" for x in pc["arpa_real"]],
            "Fuga de referencia": [f"{x:.2f}%/mes" for x in pc["churn_mensual_ref_pct"]],
        }), width="stretch", hide_index=True)

        st.markdown(panel(
            "Por qué el ARPA real no es el precio de lista",
            "El precio de lista es el punto de partida. El ARPA real de cada plan "
            "queda por encima cuando el cliente suma usuarios y complementos, y por "
            "debajo cuando entró con descuento de primer año o promoción de "
            "temporada.<br><br>"
            "<b>Siigo Contador</b> aparece con ARPA cero a propósito: es gratis. No es "
            "un plan que pierda plata, es el canal de distribución más grande de la "
            "compañía — de ahí salen los clientes que sí pagan.",
            "💡"), unsafe_allow_html=True)

    # ═══ Upsell ══════════════════════════════════════════════════════════════
    with tab2:
        sin_nomina = act[~act["nomina_electronica"]]
        sin_pay = act[~act["siigo_pay"]]
        # Solo se cuenta como oportunidad real quien tiene actividad suficiente
        cand_nomina = sin_nomina[(sin_nomina["docs_mes"] > 80) &
                                 (sin_nomina["salud"] > 55) &
                                 (sin_nomina["plan"] != "Siigo Contador")]
        cand_pay = sin_pay[(sin_pay["docs_mes"] > 120) & (sin_pay["salud"] > 50)]

        PRECIO_NOMINA_USD = 47_000 / datos.TRM
        PRECIO_PAY_USD = 38_000 / datos.TRM

        k = st.columns(3, gap="small")
        k[0].markdown(kpi(
            "Candidatos a Nómina", f"{len(cand_nomina):,}",
            f"{usd(len(cand_nomina)*PRECIO_NOMINA_USD*12)} de ARR potencial", True,
            "👥", "Clientes activos, con volumen y sanos, que aún no la tienen."),
            unsafe_allow_html=True)
        k[1].markdown(kpi(
            "Candidatos a Siigo Pay", f"{len(cand_pay):,}",
            f"{usd(len(cand_pay)*PRECIO_PAY_USD*12)} de ARR potencial", True, "💳",
            "Facturan lo suficiente como para que el recaudo les sirva."),
            unsafe_allow_html=True)
        k[2].markdown(kpi(
            "ARR de upsell identificado",
            usd(len(cand_nomina) * PRECIO_NOMINA_USD * 12 +
                len(cand_pay) * PRECIO_PAY_USD * 12),
            "Sin traer un solo cliente nuevo", True, "🔓",
            "Solo en la base de Colombia. Sin CAC de adquisición."),
            unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            g = (cand_nomina.groupby("plan").size()
                 .sort_values(ascending=True).reset_index(name="n"))
            fig = go.Figure(go.Bar(y=g["plan"], x=g["n"], orientation="h",
                                   marker_color=AZUL,
                                   text=[f"{v:,}" for v in g["n"]],
                                   textposition="auto", textfont=dict(size=10)))
            st.plotly_chart(light(fig, 320, "Candidatos a Nómina Electrónica, por plan"),
                            use_container_width=True)
        with c2:
            g = (cand_nomina.groupby("sector").size()
                 .sort_values(ascending=True).tail(9).reset_index(name="n"))
            fig = go.Figure(go.Bar(y=g["sector"], x=g["n"], orientation="h",
                                   marker_color=NARANJA,
                                   text=[f"{v:,}" for v in g["n"]],
                                   textposition="auto", textfont=dict(size=10)))
            st.plotly_chart(light(fig, 320, "Candidatos a Nómina, por sector"),
                            use_container_width=True)

        st.markdown(panel(
            "Este es el ARR más barato que existe",
            f"Traer un cliente nuevo cuesta <b>US${datos.unit_economics()['cac']:,.0f}</b>. "
            f"Venderle un módulo a alguien que ya está adentro, ya confía y ya emite "
            f"facturas cuesta una llamada.<br><br>"
            f"Los <b>{len(cand_nomina):,}</b> candidatos a Nómina no son la base "
            f"completa sin el módulo: son los que además están activos, tienen volumen "
            f"real de documentos y no están en riesgo de fuga. Es una lista sobre la que "
            f"se puede llamar mañana.",
            "🎯", "ok"), unsafe_allow_html=True)

        st.markdown("##### Los 20 candidatos de mayor potencial")
        top = cand_nomina.nlargest(20, "docs_mes")[[
            "cliente_id", "plan", "sector", "ciudad", "usuarios", "docs_mes",
            "salud", "mrr_usd"]]
        st.dataframe(pd.DataFrame({
            "Cliente": top["cliente_id"], "Plan": top["plan"],
            "Sector": top["sector"], "Ciudad": top["ciudad"],
            "Usuarios": top["usuarios"], "Docs/mes": [f"{x:,}" for x in top["docs_mes"]],
            "Salud": top["salud"],
            "ARR actual": [usd(x * 12) for x in top["mrr_usd"]],
            "ARR con Nómina": [usd((x + PRECIO_NOMINA_USD) * 12) for x in top["mrr_usd"]],
        }), width="stretch", hide_index=True)

    # ═══ Mezcla ══════════════════════════════════════════════════════════════
    with tab3:
        g = susc.groupby(["mes", "plan"])["mrr_usd"].sum().reset_index()
        tot = g.groupby("mes")["mrr_usd"].transform("sum")
        g["share"] = g["mrr_usd"] / tot * 100
        fig = go.Figure()
        for i, plan in enumerate(susc["plan"].unique()):
            sub = g[g["plan"] == plan]
            fig.add_trace(go.Scatter(
                x=[mes_es(m) for m in sub["mes"]], y=sub["share"], name=plan,
                mode="lines", stackgroup="one",
                line=dict(width=0.5, color=PALETTE[i % len(PALETTE)])))
        fig.update_yaxes(ticksuffix="%", range=[0, 100])
        st.plotly_chart(light(fig, 380, "Participación de cada plan en el MRR"),
                        use_container_width=True)

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            ar = susc.groupby("mes").apply(
                lambda d: d["mrr_usd"].sum() / d["clientes"].sum(),
                include_groups=False).reset_index(name="arpa")
            fig = go.Figure(go.Scatter(
                x=[mes_es(m) for m in ar["mes"]], y=ar["arpa"], mode="lines+markers",
                line=dict(color=AZUL, width=3), fill="tozeroy",
                fillcolor="rgba(0,157,255,.10)"))
            fig.update_yaxes(tickprefix="US$")
            st.plotly_chart(light(fig, 320, "ARPA del grupo (USD/mes)"),
                            use_container_width=True)
        with c2:
            arpa_ini = float(ar["arpa"].iloc[0])
            arpa_fin = float(ar["arpa"].iloc[-1])
            st.markdown(panel(
                "El ARPA sube, y no solo por el alza anual",
                f"El ingreso promedio por cliente pasó de <b>US${arpa_ini:.2f}</b> a "
                f"<b>US${arpa_fin:.2f}</b> en {len(meses)} meses: "
                f"<b>{(arpa_fin/arpa_ini-1)*100:.1f}%</b>.<br><br>"
                f"Una parte es el ajuste anual de precios de enero. El resto viene de "
                f"clientes que suman usuarios y contratan complementos. Esa segunda "
                f"parte es la que importa: es crecimiento que no depende de subir el "
                f"precio, y por eso no genera cancelaciones por precio.<br><br>"
                f"En los meses de enero se ve el salto del alza y, un mes después, "
                f"el repunte de cancelaciones por precio. Ese es el costo real "
                f"de cada punto de aumento.",
                "📈"), unsafe_allow_html=True)
