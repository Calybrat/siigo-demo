"""Facturación electrónica: el volumen que Siigo mueve y lo que la DIAN rechaza."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.formatters import *
from utils import datos


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Facturación Electrónica y DIAN",
        "Proveedor tecnológico autorizado · facturas, nómina, documento soporte y POS",
        "Producto y operación"), unsafe_allow_html=True)

    docs = datos.documentos()
    rech = datos.rechazos()
    meses = datos.meses()
    ult, ant = meses[-1], meses[-13]

    f1, f2 = st.columns([2, 2])
    with f1:
        pais_sel = st.selectbox("País", ["Todos"] + datos.paises()["pais"].tolist(),
                                key="dian_pais")
    with f2:
        tipo_sel = st.selectbox("Tipo de documento",
                                ["Todos"] + sorted(docs["tipo_documento"].unique()),
                                key="dian_tipo")

    d = docs.copy()
    if pais_sel != "Todos":
        d = d[d["pais"] == pais_sel]
    if tipo_sel != "Todos":
        d = d[d["tipo_documento"] == tipo_sel]

    d_ult = d[d["mes"] == ult]
    d_ant = d[d["mes"] == ant]
    emitidos = int(d_ult["emitidos"].sum())
    emitidos_ant = int(d_ant["emitidos"].sum())
    rechazados = int(d_ult["rechazados"].sum())
    tasa = rechazados / max(emitidos, 1) * 100
    tasa_ant = d_ant["rechazados"].sum() / max(emitidos_ant, 1) * 100
    lat = float(d_ult["latencia_p95_ms"].mean())

    k = st.columns(4, gap="small")
    k[0].markdown(kpi("Documentos del mes", miles(emitidos),
                      f"▲ {(emitidos/max(emitidos_ant,1)-1)*100:.1f}% vs hace un año",
                      emitidos > emitidos_ant, "🧾",
                      "Todo lo que los clientes emitieron a través de Siigo."),
                  unsafe_allow_html=True)
    k[1].markdown(kpi("Tasa de rechazo", pct(tasa, 2),
                      f"Hace un año: {tasa_ant:.2f}%", tasa <= tasa_ant, "❌",
                      "Documentos que la autoridad tributaria devolvió."),
                  unsafe_allow_html=True)
    k[2].markdown(kpi("Documentos rechazados", miles(rechazados),
                      "Cada uno es una llamada al soporte", False, "📞",
                      "El rechazo no es solo un dato técnico: genera un ticket."),
                  unsafe_allow_html=True)
    k[3].markdown(kpi("Latencia en el percentil 95", f"{lat:,.0f} ms",
                      "Meta interna: menos de 1.000 ms", lat < 1000, "⚡",
                      "Lo que tarda el 5% más lento de las emisiones."),
                  unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈  Volumen y estacionalidad", "❌  Por qué rechazan",
                                "📅  El pico de fin de mes"])

    # ═══ Volumen ═════════════════════════════════════════════════════════════
    with tab1:
        c1, c2 = st.columns([1.5, 1], gap="medium")
        with c1:
            g = (docs if pais_sel == "Todos" else docs[docs["pais"] == pais_sel])
            g = g.groupby(["mes", "tipo_documento"])["emitidos"].sum().reset_index()
            fig = go.Figure()
            for i, t in enumerate(g["tipo_documento"].unique()):
                sub = g[g["tipo_documento"] == t]
                fig.add_trace(go.Bar(x=[mes_es(m) for m in sub["mes"]],
                                     y=sub["emitidos"], name=t,
                                     marker_color=PALETTE[i % len(PALETTE)]))
            fig.update_layout(barmode="stack")
            fig.update_yaxes(tickformat=".2s")
            st.plotly_chart(light(fig, 380, "Documentos emitidos por mes y tipo"),
                            use_container_width=True)
        with c2:
            mix = d_ult.groupby("tipo_documento")["emitidos"].sum().sort_values(
                ascending=False)
            fig = go.Figure(go.Pie(labels=mix.index, values=mix.values, hole=0.6,
                                   marker_colors=PALETTE,
                                   texttemplate="%{percent:.0%}"))
            st.plotly_chart(light(fig, 380, "Mezcla del último mes"),
                            use_container_width=True)

        c3, c4 = st.columns([1, 1], gap="medium")
        with c3:
            por_tipo = d.groupby("tipo_documento").apply(
                lambda x: x["rechazados"].sum() / x["emitidos"].sum() * 100,
                include_groups=False).sort_values().reset_index(name="tasa")
            fig = go.Figure(go.Bar(
                y=por_tipo["tipo_documento"], x=por_tipo["tasa"], orientation="h",
                marker_color=[BAD if v > 2 else (WARN if v > 1.2 else GOOD)
                              for v in por_tipo["tasa"]],
                text=[f"{v:.2f}%" for v in por_tipo["tasa"]], textposition="auto",
                textfont=dict(size=10)))
            fig.update_xaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 330, "Tasa de rechazo por tipo de documento"),
                            use_container_width=True)
        with c4:
            ev = d.groupby("mes").apply(
                lambda x: x["rechazados"].sum() / x["emitidos"].sum() * 100,
                include_groups=False).reset_index(name="tasa")
            fig = go.Figure(go.Scatter(
                x=[mes_es(m) for m in ev["mes"]], y=ev["tasa"], mode="lines+markers",
                line=dict(color=BAD, width=2.8), fill="tozeroy",
                fillcolor="rgba(224,80,63,.09)"))
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(light(fig, 330, "Tasa de rechazo mes a mes"),
                            use_container_width=True)

        peor = por_tipo.iloc[-1]
        st.markdown(panel(
            "Nómina y documento soporte son los que más se caen",
            f"<b>{peor['tipo_documento']}</b> se rechaza en el "
            f"<b>{peor['tasa']:.2f}%</b> de los casos, frente al "
            f"<b>{por_tipo.iloc[0]['tasa']:.2f}%</b> de "
            f"{por_tipo.iloc[0]['tipo_documento']}. La diferencia no es aleatoria: "
            f"son los documentos con más campos obligatorios y más reglas de "
            f"validación.<br><br>"
            f"El costo no está en el rechazo mismo — está en que cada rechazo produce "
            f"un cliente confundido llamando al soporte, justo en los meses donde el "
            f"soporte ya está saturado. Bajar la tasa de rechazo <b>es</b> una "
            f"iniciativa de soporte, aunque la ejecute el equipo de producto.",
            "🔍", "naranja"), unsafe_allow_html=True)

    # ═══ Motivos ═════════════════════════════════════════════════════════════
    with tab2:
        r = rech[rech["mes"].isin(meses[-12:])]
        if pais_sel != "Todos":
            r = r[r["pais"] == pais_sel]
        g = r.groupby("motivo")["cantidad"].sum().sort_values().reset_index()
        total_r = g["cantidad"].sum()

        c1, c2 = st.columns([1.35, 1], gap="medium")
        with c1:
            # Los tres primeros motivos son de datos del cliente, no del sistema
            evitables = ["NIT del adquiriente inválido", "Fecha fuera del rango permitido",
                         "Error en cálculo de IVA", "Resolución de numeración vencida",
                         "Detalle de tributos incompleto"]
            fig = go.Figure(go.Bar(
                y=g["motivo"], x=g["cantidad"], orientation="h",
                marker_color=[NARANJA if m in evitables else AZUL for m in g["motivo"]],
                text=[f"{v/total_r*100:.0f}%" for v in g["cantidad"]],
                textposition="auto", textfont=dict(size=10),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} rechazos<extra></extra>"))
            fig.update_xaxes(tickformat=".2s")
            st.plotly_chart(light(fig, 400,
                                  "Motivos de rechazo · naranja = se puede prevenir "
                                  "validando antes de enviar"),
                            use_container_width=True)
        with c2:
            prev = g[g["motivo"].isin(evitables)]["cantidad"].sum()
            fig = go.Figure(go.Pie(
                labels=["Se puede validar antes de enviar", "Requiere corrección técnica"],
                values=[prev, total_r - prev], hole=0.62,
                marker_colors=[NARANJA, "#C4D6E3"], texttemplate="%{percent:.0%}"))
            st.plotly_chart(light(fig, 400, "¿Cuánto rechazo es prevenible?"),
                            use_container_width=True)

        # Impacto en soporte
        tk = datos.tickets()
        tk_dian = tk[tk["categoria"] == "Facturación electrónica / DIAN"]
        st.markdown(panel(
            "El caso de negocio de una validación previa",
            f"El <b>{prev/total_r*100:.0f}%</b> de los rechazos "
            f"({prev:,.0f} en doce meses) son errores en los datos que el cliente "
            f"escribió: un NIT mal digitado, una fecha fuera de rango, un IVA mal "
            f"calculado. Todos <b>detectables antes</b> de enviar el documento.<br><br>"
            f"En el mismo período, <b>{len(tk_dian)*6:,.0f} tickets</b> "
            f"(el {len(tk_dian)/len(tk)*100:.0f}% de todo el soporte) fueron de "
            f"facturación electrónica. Si una validación previa evitara la mitad de "
            f"los rechazos prevenibles, el equipo de soporte recibiría miles de "
            f"tickets menos <b>en los meses donde más saturado está</b>.<br><br>"
            f"Es la clase de decisión que se toma una vez en producto y se cobra "
            f"todos los meses en operación.",
            "💡", "ok"), unsafe_allow_html=True)

        st.markdown("##### Rechazos por país y motivo (12 meses)")
        piv = r.pivot_table(index="motivo", columns="pais", values="cantidad",
                            aggfunc="sum", fill_value=0)
        piv["Total"] = piv.sum(axis=1)
        piv = piv.sort_values("Total", ascending=False)
        st.dataframe(piv.apply(lambda c: c.map(lambda v: f"{v:,.0f}")),
                     width="stretch")

    # ═══ Pico de fin de mes ══════════════════════════════════════════════════
    with tab3:
        dd = datos.documentos(con_fecha=True)
        if pais_sel != "Todos":
            dd = dd[dd["pais"] == pais_sel]
        dd = dd.copy()
        dd["dia"] = dd["fecha"].dt.day
        por_dia = dd.groupby("dia").agg(
            emitidos=("emitidos", "sum"), rechazados=("rechazados", "sum"),
            lat=("latencia_p95_ms", "mean")).reset_index()
        por_dia["emitidos"] = por_dia["emitidos"] / 24     # promedio por mes
        por_dia["tasa"] = por_dia["rechazados"] / (por_dia["emitidos"] * 24) * 100

        fig = go.Figure()
        fig.add_trace(go.Bar(x=por_dia["dia"], y=por_dia["emitidos"],
                             name="Documentos (promedio del día)",
                             marker_color=AZUL_PALE))
        fig.add_trace(go.Scatter(x=por_dia["dia"], y=por_dia["lat"],
                                 name="Latencia p95 (ms)", yaxis="y2",
                                 mode="lines+markers",
                                 line=dict(color=BAD, width=2.8)))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                      ticksuffix=" ms", tickfont=dict(color=BAD)))
        fig.update_xaxes(title="Día del mes", dtick=2)
        fig.update_yaxes(tickformat=".2s")
        st.plotly_chart(light(fig, 380,
                              "El sistema no tiene carga pareja: se concentra al cierre"),
                        use_container_width=True)

        pico = por_dia[por_dia["dia"] >= 28]["emitidos"].mean()
        valle = por_dia[(por_dia["dia"] >= 10) & (por_dia["dia"] <= 20)]["emitidos"].mean()
        lat_pico = por_dia[por_dia["dia"] >= 28]["lat"].mean()
        lat_valle = por_dia[(por_dia["dia"] >= 10) &
                            (por_dia["dia"] <= 20)]["lat"].mean()

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            st.markdown(panel(
                "Se paga infraestructura para cuatro días al mes",
                f"Del día 28 en adelante se emiten <b>{pico/valle:.1f} veces</b> más "
                f"documentos que a mitad de mes ({miles(pico)} contra {miles(valle)} "
                f"al día). La latencia sube de <b>{lat_valle:,.0f} ms</b> a "
                f"<b>{lat_pico:,.0f} ms</b>, y la tasa de rechazo sube con ella.<br><br>"
                f"La capacidad se dimensiona para el pico, así que durante veinticinco "
                f"días del mes buena parte de esa infraestructura está ociosa. Ese es "
                f"el costo de servicio que se ve en el margen bruto.",
                "📅"), unsafe_allow_html=True)
        with c2:
            st.markdown(panel(
                "Y encima está la estacionalidad tributaria",
                "Al pico de fin de mes se le suman los meses de mayor carga: "
                "<b>marzo a mayo</b> por la información exógena y la renta de "
                "personas jurídicas, y <b>agosto a octubre</b> por la renta de "
                "personas naturales.<br><br>"
                "El resultado es que el peor día del año — un 30 de abril — junta las "
                "dos cosas. Ahí es donde se caen las cosas, donde el soporte colapsa "
                "y donde se generan las cancelaciones que se ven tres meses después.",
                "⚠️", "alerta"), unsafe_allow_html=True)

    st.caption("Siigo es proveedor tecnológico autorizado por la DIAN en Colombia. "
               "Los volúmenes y tasas de este panel son simulados a partir de la base "
               "de clientes del modelo.")
