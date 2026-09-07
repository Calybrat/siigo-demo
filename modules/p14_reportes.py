"""Reportes automáticos: el informe que hoy alguien arma a mano cada mes."""
import datetime
import io

import numpy as np
import pandas as pd
import streamlit as st

from utils.formatters import *
from utils import datos


REPORTES = {
    "Comité directivo (mensual)":
        "Las cifras del mes con la lectura de qué cambió y qué hay que decidir. "
        "Para el comité de dirección.",
    "Reporte al accionista (trimestral)":
        "ARR, NRR, Regla del 40, unit economics y avance de la migración. "
        "El paquete que espera un fondo de crecimiento.",
    "Operación de servicio al cliente (semanal)":
        "Volumen, tiempos, categorías y saturación de temporada. "
        "Para el equipo que responde los tickets.",
    "Canal de contadores (mensual)":
        "Quién refiere, quién se apagó y qué contadores llamar esta semana.",
    "Salud de la base (semanal)":
        "Clientes en riesgo, ARR expuesto y la lista priorizada de retención.",
}


def _kpis():
    """Todos los números del reporte salen de una sola función, para que ningún
    reporte contradiga al panel ni a otro reporte."""
    f = datos.finanzas()
    susc = datos.suscripciones()
    meses = datos.meses()
    ult, ant = meses[-1], meses[-13]
    s_ult = susc[susc["mes"] == ult]
    s_ant = susc[susc["mes"] == ant]
    r40 = datos.regla_40()
    ue = datos.unit_economics()
    ind = datos.indicadores_mes()
    doce = f.tail(12)

    tk = datos.tickets()
    t12 = tk[tk["mes"].isin(meses[-12:])]
    n = datos.nps()
    n_ult = n[n["mes"] == ult]
    docs = datos.documentos()
    d_ult = docs[docs["mes"] == ult]
    cli = datos.clientes()
    act = cli[cli["estado"] == "Activo"]
    mig = datos.migracion().iloc[-1]
    cont = datos.contadores()
    plat = datos.plataforma()

    return {
        "mes": ult, "mes_txt": mes_es(ult),
        "arr": s_ult["mrr_usd"].sum() * 12,
        "arr_ant": s_ant["mrr_usd"].sum() * 12,
        "clientes": int(s_ult["clientes"].sum()),
        "clientes_ant": int(s_ant["clientes"].sum()),
        "arpa": float(ind["arpa"].iloc[-1]),
        "nrr": datos.nrr_anual(), "grr": datos.grr_anual(),
        "churn_mes": float(ind["churn_logo_pct"].tail(12).mean()),
        "ingresos12": doce["ingresos_usd"].sum(),
        "ebitda12": doce["ebitda_usd"].sum(),
        "margen_bruto": doce["margen_bruto_usd"].sum() / doce["ingresos_usd"].sum() * 100,
        "r40": r40, "ue": ue,
        "caja": float(f.iloc[-1]["caja_usd"]), "deuda": float(f.iloc[-1]["deuda_usd"]),
        "headcount": int(f.iloc[-1]["headcount"]),
        "tickets12": len(t12) * 6,
        "fr_temp": float(t12[t12["en_temporada"]]["primera_respuesta_min"].median()),
        "fr_fuera": float(t12[~t12["en_temporada"]]["primera_respuesta_min"].median()),
        "fcr": float(t12["resuelto_primer_contacto"].mean() * 100),
        "csat": float(t12["csat"].mean()),
        "nps": float((n_ult["nps"] * n_ult["encuestados"]).sum() /
                     n_ult["encuestados"].sum()),
        "docs": int(d_ult["emitidos"].sum()),
        "rechazo": float(d_ult["rechazados"].sum() / d_ult["emitidos"].sum() * 100),
        "uptime": float(plat.tail(90)["uptime_pct"].mean()),
        "riesgo_n": int(act["riesgo_fuga"].sum()),
        "riesgo_arr": float(act[act["riesgo_fuga"]]["mrr_usd"].sum() * 12),
        "mig": mig,
        "cont_total": len(cont), "cont_activos": int(cont["activo_ultimos_6m"].sum()),
        "cont_arr": float(cont["arr_referido_usd"].sum()),
        "susc": susc, "meses": meses, "cli": cli, "cont": cont, "t12": t12,
    }


def _comite(k) -> str:
    crec_arr = (k["arr"] / k["arr_ant"] - 1) * 100
    falta = 40 - k["r40"]["regla40"]
    return f"""# Comité directivo · {k['mes_txt']}

**Grupo Siigo · Colombia, México, Ecuador, Perú, Uruguay y Chile**
Corte al {datos.CORTE_TXT}. Moneda de reporte: dólares.

---

## 1. Dónde estamos

| Indicador | Valor | Comentario |
|---|---|---|
| ARR | {usd(k['arr'])} | {crec_arr:+.1f}% en doce meses |
| Clientes activos | {k['clientes']:,} | {(k['clientes']/k['clientes_ant']-1)*100:+.1f}% en doce meses |
| ARPA mensual | US${k['arpa']:.2f} | |
| NRR (12 meses) | {k['nrr']:.1f}% | Referencia sana en pymes: 100% |
| GRR (12 meses) | {k['grr']:.1f}% | Referencia sana en pymes: 80% |
| Fuga de clientes | {k['churn_mes']:.2f}%/mes | {(1-(1-k['churn_mes']/100)**12)*100:.1f}% anualizada |
| Ingresos 12 meses | {usd(k['ingresos12'])} | |
| EBITDA 12 meses | {usd(k['ebitda12'])} | {k['r40']['ebitda_pct']:.1f}% de los ingresos |
| Regla del 40 | **{k['r40']['regla40']:.1f}** | {k['r40']['crecimiento']:.1f}% crecimiento + {k['r40']['ebitda_pct']:.1f}% margen |
| LTV / CAC | {k['ue']['ltv_cac']:.1f}x | CAC US${k['ue']['cac']:,.0f}, se recupera en {k['ue']['payback_meses']:.0f} meses |
| NPS | {k['nps']:.0f} | Referencia B2B: 30 |

## 2. Las tres cosas que hay que decidir

**1 · La Regla del 40 está en {k['r40']['regla40']:.1f}.**
{'Faltan ' + f"{falta:.1f}" + ' puntos para el umbral que exige un fondo de crecimiento. Un punto de crecimiento y un punto de margen valen lo mismo para el indicador: ' + usd(falta/100*k['ingresos12']) + ' de ingreso adicional, o el mismo monto de gasto menos.' if falta > 0 else 'Está por encima del umbral. La pregunta ya no es cómo llegar, sino cómo sostenerlo mientras se abre Chile.'}

**2 · El NRR está en {k['nrr']:.1f}%.**
La base de hace un año vale hoy {'menos' if k['nrr'] < 100 else 'más'} que entonces. La expansión —alza anual, más usuarios, más módulos— {'no alcanza a compensar' if k['nrr'] < 100 else 'compensa'} la fuga. Mientras eso no cambie, cada dólar de ARR nuevo que trae el equipo comercial repone en lugar de sumar.

**3 · La migración de Aspel avanza al {k['mig']['avance_pct']:.1f}%.**
Quedan {int(k['mig']['pendientes']):,} licencias de escritorio. Cada una vale {k['mig']['arpa_nube_usd']/k['mig']['arpa_desktop_usd']:.1f} veces más en la nube. Es la bolsa de ARR más grande y más barata identificada, y el ritmo actual la termina en {int(k['mig']['pendientes']/max(k['mig']['migrados_mes'],1))} meses.

## 3. Operación

- **Documentos electrónicos del mes:** {miles(k['docs'])}, con {k['rechazo']:.2f}% de rechazo.
- **Disponibilidad (90 días):** {k['uptime']:.3f}%.
- **Soporte:** {miles(k['tickets12'])} tickets en doce meses. Primera respuesta de {k['fr_fuera']:.0f} minutos fuera de temporada y {k['fr_temp']:.0f} en marzo–mayo y agosto–octubre. Resuelto al primer contacto: {k['fcr']:.0f}%.
- **Base en riesgo:** {k['riesgo_n']:,} clientes de Colombia con {usd(k['riesgo_arr'])} de ARR expuesto.
- **Canal de contadores:** {k['cont_total']:,} registrados, {k['cont_activos']:,} activos en los últimos seis meses, {usd(k['cont_arr'])} de ARR referido.

## 4. Lo que se propone

1. **Planear la capacidad de soporte contra el calendario de la DIAN.** Las fechas se conocen con un año de anticipación y el deterioro es de {k['fr_temp']/k['fr_fuera']:.1f} veces. Es el motivo de fuga evitable más grande.
2. **Mover mezcla de canales pagos al canal de contadores.** Baja el CAC sin bajar altas.
3. **Acelerar la migración de Aspel.** Cada mes de demora tiene un costo cuantificado en cuentas perdidas.

---
*Generado automáticamente desde el panel. Datos simulados para demostración.*
"""


def _accionista(k) -> str:
    return f"""# Reporte al accionista · corte {k['mes_txt']}

**Grupo Siigo** · Software contable y administrativo para pymes y contadores
Colombia · México · Ecuador · Perú · Uruguay · Chile

---

## Resumen

| | |
|---|---|
| ARR | **{usd(k['arr'])}** |
| Crecimiento del ARR (12 m) | {(k['arr']/k['arr_ant']-1)*100:+.1f}% |
| Ingresos (12 m) | {usd(k['ingresos12'])} |
| Crecimiento de ingresos | {k['r40']['crecimiento']:+.1f}% |
| Margen bruto | {k['margen_bruto']:.1f}% |
| EBITDA (12 m) | {usd(k['ebitda12'])} ({k['r40']['ebitda_pct']:.1f}%) |
| **Regla del 40** | **{k['r40']['regla40']:.1f}** |
| Clientes activos | {k['clientes']:,} |
| ARPA | US${k['arpa']:.2f}/mes |
| NRR / GRR | {k['nrr']:.1f}% / {k['grr']:.1f}% |
| CAC | US${k['ue']['cac']:,.0f} |
| LTV / CAC | {k['ue']['ltv_cac']:.1f}x |
| Recuperación del CAC | {k['ue']['payback_meses']:.0f} meses |
| Caja | {usd(k['caja'])} |
| Deuda | {usd(k['deuda'])} ({k['deuda']/k['ebitda12']:.1f}x EBITDA) |
| Equipo | {k['headcount']:,} personas |

## ARR por país

{_tabla_paises(k)}

## Lectura

El crecimiento de {k['r40']['crecimiento']:.1f}% se sostiene sobre dos motores distintos.
Colombia, mercado maduro donde Siigo ya es líder, crece principalmente por ARPA: alza
anual de precios y adopción de módulos. México, Ecuador y Chile crecen por base de
clientes, con CAC más alto y NRR más bajo.

El NRR consolidado de {k['nrr']:.1f}% es el indicador a vigilar. En un negocio de
micronegocios la fuga estructural es alta —la primera causa de cancelación es que el
cliente cerró el negocio— y por eso la expansión tiene que hacer más trabajo. Las
palancas identificadas y cuantificadas son tres: migración de la base de Aspel,
adopción de Nómina Electrónica y Siigo Pay sobre la base existente, y reactivación
del canal de contadores dormido.

La operación de financiación de julio de 2026 (US$103,5M, con Banco de Occidente
aportando US$18,5M) deja la deuda en {k['deuda']/k['ebitda12']:.1f} veces EBITDA.

---
*Datos simulados para demostración, anclados a información pública de Siigo.*
"""


def _tabla_paises(k) -> str:
    s = k["susc"]
    ult, ant = k["meses"][-1], k["meses"][-13]
    a = s[s["mes"] == ult].groupby("pais")["mrr_usd"].sum() * 12
    b = s[s["mes"] == ant].groupby("pais")["mrr_usd"].sum() * 12
    c = s[s["mes"] == ult].groupby("pais")["clientes"].sum()
    filas = ["| País | ARR | Crecimiento 12 m | Clientes | ARPA |",
             "|---|---|---|---|---|"]
    for pais in datos.paises()["pais"]:
        filas.append(f"| {pais} | {usd(a[pais])} | {(a[pais]/b[pais]-1)*100:+.1f}% | "
                     f"{c[pais]:,} | US${a[pais]/12/c[pais]:.2f} |")
    filas.append(f"| **Grupo** | **{usd(a.sum())}** | "
                 f"**{(a.sum()/b.sum()-1)*100:+.1f}%** | **{c.sum():,}** | "
                 f"**US${a.sum()/12/c.sum():.2f}** |")
    return "\n".join(filas)


def _soporte(k) -> str:
    t = k["t12"]
    cat = (t.groupby("categoria")
           .agg(n=("ticket_id", "count"), res=("resolucion_horas", "mean"),
                fcr=("resuelto_primer_contacto", "mean"))
           .sort_values("n", ascending=False))
    filas = ["| Categoría | Tickets (12 m) | Resolución | Primer contacto |",
             "|---|---|---|---|"]
    for c, r in cat.iterrows():
        filas.append(f"| {c} | {r['n']*6:,.0f} | {r['res']:.1f} h | {r['fcr']*100:.0f}% |")

    return f"""# Operación de servicio al cliente · semana del {datetime.date.today():%d/%m/%Y}

## Los números

- **Tickets en 12 meses:** {miles(k['tickets12'])}
- **Primera respuesta:** {k['fr_fuera']:.0f} min fuera de temporada · **{k['fr_temp']:.0f} min en temporada**
- **Resuelto al primer contacto:** {k['fcr']:.0f}% (referencia del sector: 70%)
- **CSAT de tickets:** {k['csat']:.2f} / 5
- **NPS:** {k['nps']:.0f}

## Por categoría

{chr(10).join(filas)}

## El problema de fondo

El soporte no está mal todo el año: se rompe cinco meses. En marzo, abril y mayo
(información exógena y renta de personas jurídicas) y en agosto y septiembre (renta
de personas naturales), la primera respuesta pasa de {k['fr_fuera']:.0f} a
{k['fr_temp']:.0f} minutos — **{k['fr_temp']/k['fr_fuera']:.1f} veces más**.

Esos cinco meses son la principal causa de la fuga que sí depende de una decisión
interna. Y son fechas conocidas con doce meses de anticipación: el calendario
tributario se publica.

## Lo que se propone

1. **Contratación temporal planeada contra el calendario de la DIAN**, no reactiva.
2. **Validación previa de documentos electrónicos.** La mayoría de los rechazos son
   errores de datos del cliente detectables antes de enviar. Cada rechazo evitado es
   un ticket que no entra, justo en los meses de saturación.
3. **Dirigir la automatización con IA a la categoría de mayor costo en horas**, no a
   la de mayor volumen.

---
*Generado automáticamente desde el panel. Datos simulados para demostración.*
"""


def _canal(k) -> str:
    c = k["cont"]
    dormidos = c[(~c["activo_ultimos_6m"]) & (c["clientes_referidos"] >= 8)]
    orden = c.sort_values("arr_referido_usd", ascending=False).reset_index(drop=True)
    top20 = orden.head(int(len(orden) * 0.2))["arr_referido_usd"].sum() / c["arr_referido_usd"].sum() * 100
    arpa_ref = c["arr_referido_usd"].sum() / max(c["clientes_activos"].sum(), 1)

    filas = ["| Contador | País | Nivel | Referidos | Activos | ARR aportado |",
             "|---|---|---|---|---|---|"]
    for _, r in orden.head(15).iterrows():
        filas.append(f"| C-{int(r['contador_id']):05d} | {r['pais']} | "
                     f"{r['nivel_partner']} | {r['clientes_referidos']:,} | "
                     f"{r['clientes_activos']:,} | {usd(r['arr_referido_usd'])} |")

    return f"""# Canal de contadores · {k['mes_txt']}

## Estado de la red

- **Contadores registrados:** {len(c):,}
- **Activos (refirieron en 6 meses):** {int(c['activo_ultimos_6m'].sum()):,} ({c['activo_ultimos_6m'].mean()*100:.0f}%)
- **ARR que trae el canal:** {usd(c['arr_referido_usd'].sum())}
- **Clientes activos referidos:** {int(c['clientes_activos'].sum()):,}
- **Certificados:** {c['certificado'].mean()*100:.0f}% · **En el directorio:** {c['en_directorio'].mean()*100:.0f}%

## Concentración

El 20% de los contadores trae el **{top20:.0f}%** del ARR del canal. Los
{len(c[c['nivel_partner']=='Platino']):,} contadores Platino aportan
{usd(c[c['nivel_partner']=='Platino']['arr_referido_usd'].sum())}.

Es riesgo y oportunidad: perder cien contadores Platino duele más que perder mil
pymes, pero el resto de la red está subutilizada.

## La lista de esta semana

**{len(dormidos):,} contadores** ya refirieron ocho o más clientes y llevan más de
seis meses sin referir a nadie. El {dormidos['certificado'].mean()*100:.0f}% está
certificado. No hay que reclutarlos: hay que llamarlos.

Si cada uno vuelve a referir **un solo cliente**, son
**{usd(len(dormidos)*arpa_ref)}** de ARR, con el CAC de una llamada.

## Los 15 que más aportan

{chr(10).join(filas)}

---
*Generado automáticamente desde el panel. Datos simulados para demostración.*
"""


def _salud(k) -> str:
    cli = k["cli"]
    act = cli[cli["estado"] == "Activo"]
    riesgo = act[act["riesgo_fuga"]]
    top = riesgo.nlargest(20, "mrr_usd")
    filas = ["| Cliente | Plan | Sector | Ciudad | ARR | Salud | Sin entrar |",
             "|---|---|---|---|---|---|---|"]
    for _, r in top.iterrows():
        filas.append(f"| {r['cliente_id']} | {r['plan']} | {r['sector']} | "
                     f"{r['ciudad']} | {usd(r['mrr_usd']*12)} | {r['salud']}/100 | "
                     f"{r['dias_sin_acceso']} días |")

    sin_uso = int((act["dias_sin_acceso"] > 30).sum())
    return f"""# Salud de la base · Colombia · semana del {datetime.date.today():%d/%m/%Y}

## Estado

- **Clientes activos:** {len(act):,}
- **En riesgo de fuga:** {len(riesgo):,} ({len(riesgo)/len(act)*100:.1f}%)
- **ARR expuesto:** {usd(riesgo['mrr_usd'].sum()*12)}
- **Sin entrar hace más de 30 días:** {sin_uso:,}
- **Salud promedio de la base:** {act['salud'].mean():.0f}/100

## La señal más temprana

{sin_uso:,} clientes llevan más de un mes sin abrir el producto. Siguen pagando y
siguen apareciendo al día en el sistema de facturación, así que nadie los está
llamando. Ese grupo es el que cancela en el próximo ciclo de renovación.

Un cliente con **un solo módulo** contratado tiene mucho más riesgo que uno con
cuatro. Cada módulo adicional mete más del negocio del cliente adentro de Siigo.

## Los 20 clientes de mayor ARR en riesgo

{chr(10).join(filas)}

---
*Generado automáticamente desde el panel. Datos simulados para demostración.*
"""


GENERADORES = {
    "Comité directivo (mensual)": _comite,
    "Reporte al accionista (trimestral)": _accionista,
    "Operación de servicio al cliente (semanal)": _soporte,
    "Canal de contadores (mensual)": _canal,
    "Salud de la base (semanal)": _salud,
}


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Reportes Automáticos",
        "El informe que hoy alguien arma a mano cada mes, generado desde los mismos datos",
        "Dirección"), unsafe_allow_html=True)

    st.markdown(panel(
        "Por qué esto importa más de lo que parece",
        "En la mayoría de las empresas el informe mensual lo arma una persona "
        "exportando de varios sistemas a Excel. Toma días, llega tarde y cada versión "
        "sale distinta porque cada quien calcula el churn a su manera.<br><br>"
        "Estos reportes salen de las <b>mismas funciones</b> que alimentan el panel. "
        "Si el tablero dice que el NRR es 95%, el reporte al accionista dice 95%. "
        "No pueden contradecirse porque no hay dos cálculos.<br><br>"
        "Y en producción, esto no se abre: <b>llega solo</b> al correo, el lunes a "
        "las 7 de la mañana.",
        "📄"), unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2.2, 1])
    with c1:
        tipo = st.selectbox("Reporte", list(REPORTES.keys()), key="rep_tipo")
    with c2:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        st.caption(REPORTES[tipo])

    with st.spinner("Generando el reporte…"):
        k = _kpis()
        texto = GENERADORES[tipo](k)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    d1, d2, _ = st.columns([1, 1, 3])
    nombre = tipo.split(" (")[0].lower().replace(" ", "_")
    with d1:
        st.download_button("⬇️  Descargar (Markdown)", texto,
                           file_name=f"siigo_{nombre}_{k['mes']}.md",
                           mime="text/markdown", use_container_width=True)
    with d2:
        # El resumen de indicadores también se entrega como tabla
        resumen = pd.DataFrame({
            "Indicador": ["ARR", "Clientes activos", "ARPA mensual (USD)",
                          "NRR 12m (%)", "GRR 12m (%)", "Fuga mensual (%)",
                          "Ingresos 12m (USD)", "EBITDA 12m (USD)",
                          "Margen bruto (%)", "Regla del 40",
                          "CAC (USD)", "LTV/CAC", "Payback (meses)",
                          "NPS", "CSAT tickets", "Disponibilidad 90d (%)",
                          "Caja (USD)", "Deuda (USD)", "Equipo"],
            "Valor": [k["arr"], k["clientes"], round(k["arpa"], 2),
                      round(k["nrr"], 1), round(k["grr"], 1), round(k["churn_mes"], 2),
                      k["ingresos12"], k["ebitda12"], round(k["margen_bruto"], 1),
                      round(k["r40"]["regla40"], 1), round(k["ue"]["cac"]),
                      round(k["ue"]["ltv_cac"], 1), round(k["ue"]["payback_meses"], 1),
                      round(k["nps"]), round(k["csat"], 2), round(k["uptime"], 3),
                      k["caja"], k["deuda"], k["headcount"]],
        })
        buf = io.StringIO()
        resumen.to_csv(buf, index=False)
        st.download_button("⬇️  Indicadores (CSV)", buf.getvalue(),
                           file_name=f"siigo_indicadores_{k['mes']}.csv",
                           mime="text/csv", use_container_width=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{SURF};border:1px solid {BORDER};border-radius:14px;'
        f'padding:26px 32px;box-shadow:0 1px 3px rgba(5,46,74,.05)">',
        unsafe_allow_html=True)
    st.markdown(texto)
    st.markdown("</div>", unsafe_allow_html=True)
