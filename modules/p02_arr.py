"""ARR y puente de ingresos: de dónde sale y por dónde se va cada dólar."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "ARR y Puente de Ingresos",
        "Qué entra, qué se expande y qué se pierde, mes a mes",
        "Ingresos"), unsafe_allow_html=True)

    p = datos.puente()
    susc = datos.suscripciones()
    meses = datos.meses()

    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                key="arr_pais")
    with f2:
        plan_sel = st.selectbox("Plan", ["Todos"] + sorted(p["plan"].unique()),
                                key="arr_plan")
    with f3:
        vent = st.selectbox("Ventana", ["Últimos 12 meses", "Últimos 6 meses",
                                        "Todo el histórico"], key="arr_vent")

    ms = {"Últimos 12 meses": meses[-12:], "Últimos 6 meses": meses[-6:],
          "Todo el histórico": meses[1:]}[vent]

    pf = p[p["mes"].isin(ms)]
    if pais_sel != "Todos":
        pf = pf[pf["pais"] == pais_sel]
    if plan_sel != "Todos":
        pf = pf[pf["plan"] == plan_sel]

    ini = pf[pf["mes"] == ms[0]]["mrr_inicial_usd"].sum()
    nuevo = pf["nuevo_usd"].sum()
    expan = pf["expansion_usd"].sum()
    react = pf["reactivacion_usd"].sum()
    contr = pf["contraccion_usd"].sum()      # ya viene negativo
    churn = pf["churn_usd"].sum()            # ya viene negativo
    fin_ = pf[pf["mes"] == ms[-1]]["mrr_final_usd"].sum()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    k = st.columns(4, gap="small")
    k[0].markdown(kpi("ARR de cierre", usd(fin_ * 12),
                      f"Partió en {usd(ini*12)}", fin_ > ini, "📈",
                      "MRR del último mes multiplicado por 12."), unsafe_allow_html=True)
    k[1].markdown(kpi("ARR nuevo", usd(nuevo * 12),
                      f"{nuevo/(nuevo+expan+react)*100:.0f}% de todo lo que entró",
                      True, "🌱", "Clientes que no existían antes de la ventana."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("ARR de expansión", usd((expan + react) * 12),
                      f"{(expan+react)/(nuevo+expan+react)*100:.0f}% de lo que entró",
                      True, "⬆️",
                      "Alza anual, más usuarios y más módulos en clientes que ya estaban."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("ARR perdido", usd(abs(churn + contr) * 12),
                      f"Fuga {usd(abs(churn)*12)} · bajas de plan {usd(abs(contr)*12)}",
                      False, "⬇️", "Cancelaciones más reducciones de plan o usuarios."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Puente en cascada ────────────────────────────────────────────────────
    etiquetas = [f"ARR inicial<br>{mes_es(ms[0])}", "Nuevo", "Expansión",
                 "Reactivación", "Contracción", "Fuga",
                 f"ARR final<br>{mes_es(ms[-1])}"]
    valores = [ini * 12, nuevo * 12, expan * 12, react * 12,
               contr * 12, churn * 12, fin_ * 12]
    medida = ["absolute", "relative", "relative", "relative",
              "relative", "relative", "total"]

    fig = go.Figure(go.Waterfall(
        orientation="v", measure=medida, x=etiquetas, y=valores,
        text=[usd(v) for v in valores], textposition="outside",
        textfont=dict(size=11, color=TINTA),
        connector=dict(line=dict(color=BORDER, width=1)),
        increasing=dict(marker=dict(color=AZUL)),
        decreasing=dict(marker=dict(color=BAD)),
        totals=dict(marker=dict(color=TINTA)),
    ))
    fig.update_yaxes(tickprefix="US$", tickformat=".2s")
    st.plotly_chart(light(fig, 400,
                          f"Puente de ARR · {vent.lower()} · "
                          f"{pais_sel if pais_sel != 'Todos' else 'grupo'}"),
                    use_container_width=True)

    neto = nuevo + expan + react + contr + churn
    st.markdown(panel(
        "Cómo se lee este puente",
        f"En {'los ' if vent.startswith('Últimos') else ''}{vent.lower()} entraron <b>{usd((nuevo+expan+react)*12)}</b> de ARR y se "
        f"perdieron <b>{usd(abs(churn+contr)*12)}</b>. El neto es "
        f"<b>{usd(neto*12)}</b>.<br><br>"
        f"Por cada dólar de ARR nuevo, se pierden "
        f"<b>{abs(churn+contr)/nuevo:.2f} dólares</b> de la base que ya existía. "
        f"Eso significa que de cada equipo comercial hay que descontar esa parte antes "
        f"de contar crecimiento: {'más de la mitad' if abs(churn+contr)/nuevo > 0.5 else 'una parte'} "
        f"del esfuerzo de ventas se va en reponer lo que se fue.",
        "🧭"), unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Movimiento mensual ───────────────────────────────────────────────────
    g = pf.groupby("mes").agg(
        nuevo=("nuevo_usd", "sum"), expansion=("expansion_usd", "sum"),
        reactivacion=("reactivacion_usd", "sum"),
        contraccion=("contraccion_usd", "sum"), churn=("churn_usd", "sum"),
        mrr=("mrr_final_usd", "sum")).reset_index()

    c1, c2 = st.columns([1.6, 1], gap="medium")
    with c1:
        fig = go.Figure()
        for col, nombre, color in [("nuevo", "Nuevo", AZUL),
                                   ("expansion", "Expansión", AZUL_LT),
                                   ("reactivacion", "Reactivación", TEAL),
                                   ("contraccion", "Contracción", NARANJA),
                                   ("churn", "Fuga", BAD)]:
            fig.add_trace(go.Bar(x=[mes_es(m) for m in g["mes"]], y=g[col] * 12,
                                 name=nombre, marker_color=color))
        fig.update_layout(barmode="relative")
        fig.update_yaxes(tickprefix="US$", tickformat=".2s")
        st.plotly_chart(light(fig, 350, "Movimiento de ARR cada mes"),
                        use_container_width=True)
    with c2:
        ult = susc[susc["mes"] == meses[-1]]
        if pais_sel != "Todos":
            ult = ult[ult["pais"] == pais_sel]
        por_plan = ult.groupby("plan").agg(
            clientes=("clientes", "sum"), mrr=("mrr_usd", "sum")).reset_index()
        por_plan["arr"] = por_plan["mrr"] * 12
        por_plan["arpa"] = por_plan["mrr"] / por_plan["clientes"]
        por_plan = por_plan.sort_values("arr", ascending=True)
        fig = go.Figure(go.Bar(
            y=por_plan["plan"], x=por_plan["arr"], orientation="h",
            marker_color=AZUL, text=[usd(v) for v in por_plan["arr"]],
            textposition="auto", textfont=dict(size=10),
            customdata=np.stack([por_plan["clientes"], por_plan["arpa"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>ARR %{x:$,.0f}<br>"
                          "%{customdata[0]:,.0f} clientes<br>"
                          "ARPA US$%{customdata[1]:.2f}<extra></extra>"))
        fig.update_xaxes(tickprefix="US$", tickformat=".2s")
        st.plotly_chart(light(fig, 350, "ARR por plan"), use_container_width=True)

    # ── Detalle por país ─────────────────────────────────────────────────────
    st.markdown("#### Aporte de cada país al crecimiento")
    det = []
    for pais in datos.paises()["pais"]:
        sp = p[(p["pais"] == pais) & (p["mes"].isin(ms))]
        if plan_sel != "Todos":
            sp = sp[sp["plan"] == plan_sel]
        if not len(sp):
            continue
        i0 = sp[sp["mes"] == ms[0]]["mrr_inicial_usd"].sum() * 12
        i1 = sp[sp["mes"] == ms[-1]]["mrr_final_usd"].sum() * 12
        det.append({
            "País": pais,
            "ARR inicial": usd(i0), "ARR final": usd(i1),
            "Crecimiento": f"{(i1/i0-1)*100:+.1f}%" if i0 else "—",
            "Nuevo": usd(sp["nuevo_usd"].sum() * 12),
            "Expansión": usd((sp["expansion_usd"].sum() + sp["reactivacion_usd"].sum()) * 12),
            "Perdido": usd(abs(sp["churn_usd"].sum() + sp["contraccion_usd"].sum()) * 12),
            "Aporte al crecimiento del grupo": i1 - i0,
        })
    d = pd.DataFrame(det)
    total_ap = d["Aporte al crecimiento del grupo"].sum()
    d["Aporte al crecimiento del grupo"] = [
        f"{x/total_ap*100:.0f}%" if total_ap else "—"
        for x in d["Aporte al crecimiento del grupo"]]
    st.dataframe(d, width="stretch", hide_index=True)

    st.caption("El puente cierra por construcción: ARR final = ARR inicial + nuevo + "
               "expansión + reactivación − contracción − fuga, en todos los meses, "
               "países y planes.")
