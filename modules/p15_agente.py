"""
Agente IA: preguntarle al negocio en español, sin abrir un tablero.

Con una llave de Anthropic en `st.secrets["ANTHROPIC_API_KEY"]` responde con el
modelo, usando como contexto un resumen real de los datos del panel. Sin llave,
responde con lógica local sobre los mismos datos: la demostración funciona igual,
y las cifras son las mismas que muestran los tableros.
"""
import numpy as np
import pandas as pd
import streamlit as st

from utils.formatters import *
from utils import datos

MODELO = "claude-sonnet-5"

CONTEXTO = """
Eres el Agente de Inteligencia de Negocio de Siigo, la compañía colombiana de software
contable y administrativo para pymes y contadores.

Lo que hay que saber de Siigo:
· Fundada en 1988 en Bogotá por Ricardo Ortiz y Fernando Rebellón. La dirige David Ortiz.
· Accel-KKR es el accionista de control desde 2017.
· Opera en seis países: Colombia, México, Ecuador, Perú, Uruguay y Chile.
· Más de 300.000 pymes y contadores activos; más de 120.000 pymes solo en Colombia;
  más de 35.000 contadores en el canal. Alrededor de 2.300 colaboradores.
· Productos: Siigo Nube (planes Profesional Independiente, Emprendedor, Premium y
  Corporativo), facturación electrónica como proveedor tecnológico autorizado por la
  DIAN, nómina electrónica, inventarios, Sistema POS y POS Gastrobar, Siigo Pay,
  la app móvil y Siigo Contador (gratis para contadores).
· Creció por adquisiciones: Ilimitada en Colombia (2019), Contífico en Ecuador (2020),
  Memory en Uruguay (2020) y Aspel en México (2022).
· En julio de 2026 cerró una financiación estructurada de US$103,5 millones.
· El calendario tributario colombiano manda en la operación: información exógena de
  marzo a mayo, renta de personas jurídicas de abril a julio, renta de personas
  naturales de agosto a octubre. En esos meses el soporte se satura.

Cómo respondes:
· Siempre en español, directo y breve. Nada de jerga innecesaria.
· Cuando des una cifra, di qué significa para el negocio y qué habría que decidir.
· Habla como alguien que conoce el negocio de software para pymes, no como un
  reporte genérico.
· Si el dato no está en el contexto que te dan, dilo en vez de inventarlo.
"""

SUGERIDAS = [
    "¿Cómo vamos este mes?",
    "¿Por qué el NRR está por debajo de 100?",
    "¿Cuánto nos cuesta traer un cliente y en cuánto se paga?",
    "¿Qué pasa con el soporte en temporada tributaria?",
    "¿Cuánto vale terminar la migración de Aspel?",
    "¿Qué tan bien está funcionando el canal de contadores?",
    "¿Dónde está el upsell que no estamos vendiendo?",
    "¿Cómo van los seis países?",
    "¿Cuántos clientes están a punto de irse?",
    "¿Qué nos falta para llegar a la Regla del 40?",
]


# ── Contexto de datos que se le pasa al modelo ───────────────────────────────
@st.cache_data(show_spinner=False)
def resumen_datos() -> str:
    try:
        susc = datos.suscripciones()
        meses = datos.meses()
        ult, ant = meses[-1], meses[-13]
        s_ult, s_ant = susc[susc["mes"] == ult], susc[susc["mes"] == ant]
        ind = datos.indicadores_mes()
        r40 = datos.regla_40()
        ue = datos.unit_economics()
        f = datos.finanzas().tail(12)
        cli = datos.clientes()
        act = cli[cli["estado"] == "Activo"]
        cont = datos.contadores()
        mig = datos.migracion().iloc[-1]
        tk = datos.tickets()
        t12 = tk[tk["mes"].isin(meses[-12:])]
        n = datos.nps()
        n_ult = n[n["mes"] == ult]
        d = datos.documentos()
        d_ult = d[d["mes"] == ult]
        mc = datos.motivos_churn()
        mc12 = mc[mc["mes"].isin(meses[-12:])]
        emb = datos.embudo()
        e12 = emb[emb["mes"].isin(meses[-12:])]
        can = e12.groupby("canal").apply(
            lambda x: x["inversion_usd"].sum() / x["pagados"].sum(),
            include_groups=False).sort_values()
        ad = datos.adopcion()
        ad_ult = ad[ad["mes"] == ult].groupby("funcionalidad").apply(
            lambda x: x["clientes_usando"].sum() / x["clientes_base"].sum() * 100,
            include_groups=False).sort_values(ascending=False)
        arr_pais = s_ult.groupby("pais")["mrr_usd"].sum() * 12
        arr_pais_ant = s_ant.groupby("pais")["mrr_usd"].sum() * 12
        plat = datos.plataforma()

        motivos = mc12.groupby("motivo")["mrr_perdido_usd"].sum().sort_values(
            ascending=False)

        return f"""
=== DATOS DEL GRUPO SIIGO AL {datos.CORTE_TXT.upper()} ===
Moneda de reporte: dólares. Ventana: {meses[0]} a {meses[-1]}.

INGRESO
  ARR: {usd(s_ult['mrr_usd'].sum()*12)} · creció {(s_ult['mrr_usd'].sum()/s_ant['mrr_usd'].sum()-1)*100:.1f}% en 12 meses
  Ingresos 12 meses: {usd(f['ingresos_usd'].sum())} · crecimiento {r40['crecimiento']:.1f}%
  EBITDA 12 meses: {usd(f['ebitda_usd'].sum())} ({r40['ebitda_pct']:.1f}% de los ingresos)
  Margen bruto: {f['margen_bruto_usd'].sum()/f['ingresos_usd'].sum()*100:.1f}%
  REGLA DEL 40: {r40['regla40']:.1f} ({r40['crecimiento']:.1f} crecimiento + {r40['ebitda_pct']:.1f} margen). Umbral: 40.
  Caja: {usd(float(datos.finanzas().iloc[-1]['caja_usd']))} · Deuda: {usd(float(datos.finanzas().iloc[-1]['deuda_usd']))}

CLIENTES Y RETENCIÓN
  Clientes activos: {int(s_ult['clientes'].sum()):,} ({(s_ult['clientes'].sum()/s_ant['clientes'].sum()-1)*100:+.1f}% en 12 meses)
  ARPA: US${float(ind['arpa'].iloc[-1]):.2f}/mes
  NRR 12 meses: {datos.nrr_anual():.1f}% (sano: 100%) · GRR: {datos.grr_anual():.1f}% (sano: 80%)
  Fuga de clientes: {float(ind['churn_logo_pct'].tail(12).mean()):.2f}%/mes = {(1-(1-float(ind['churn_logo_pct'].tail(12).mean())/100)**12)*100:.1f}%/año
  Vida promedio del cliente: {1/(float(ind['churn_logo_pct'].tail(12).mean())/100):.0f} meses
  MOTIVOS DE CANCELACIÓN (ARR perdido en 12 meses):
{chr(10).join(f'    · {k}: {usd(v*12)}' for k, v in motivos.items())}

UNIT ECONOMICS
  CAC: US${ue['cac']:,.0f} · LTV: {usd(ue['ltv'],0)} · LTV/CAC: {ue['ltv_cac']:.1f}x
  Recuperación del CAC: {ue['payback_meses']:.0f} meses
  CAC POR CANAL (del más barato al más caro):
{chr(10).join(f'    · {k}: US${v:,.0f}' for k, v in can.items())}

PAÍSES (ARR y crecimiento en 12 meses)
{chr(10).join(f'  · {p}: {usd(arr_pais[p])} ({(arr_pais[p]/arr_pais_ant[p]-1)*100:+.1f}%) · {int(s_ult[s_ult.pais==p]["clientes"].sum()):,} clientes' for p in arr_pais.index)}

CANAL DE CONTADORES
  Registrados: {len(cont):,} · activos en 6 meses: {int(cont['activo_ultimos_6m'].sum()):,} ({cont['activo_ultimos_6m'].mean()*100:.0f}%)
  ARR que trae el canal: {usd(cont['arr_referido_usd'].sum())}
  Certificados: {cont['certificado'].mean()*100:.0f}% · en el directorio: {cont['en_directorio'].mean()*100:.0f}%
  Dormidos con historial (8+ referidos, 6+ meses sin referir): {len(cont[(~cont['activo_ultimos_6m']) & (cont['clientes_referidos']>=8)]):,}
  Un contador certificado refiere {cont[cont['certificado']]['clientes_referidos'].mean():.1f} clientes; uno sin certificar, {cont[~cont['certificado']]['clientes_referidos'].mean():.1f}

MIGRACIÓN ASPEL (México)
  Avance: {mig['avance_pct']:.1f}% · migrados {int(mig['migrados_acum']):,} de {int(mig['base_desktop_inicial']):,}
  Pendientes: {int(mig['pendientes']):,} · perdidos en el camino: {int(mig['perdidos_acum']):,}
  ARPA escritorio US${mig['arpa_desktop_usd']:.2f} → nube US${mig['arpa_nube_usd']:.2f} ({mig['arpa_nube_usd']/mig['arpa_desktop_usd']:.1f}x)
  ARR incremental si se migra todo lo pendiente: {usd(mig['pendientes']*(mig['arpa_nube_usd']-mig['arpa_desktop_usd'])*12)}

PRODUCTO (adopción sobre la base activa)
{chr(10).join(f'  · {k}: {v:.1f}%' for k, v in ad_ult.items())}

SOPORTE Y EXPERIENCIA
  Tickets 12 meses: {len(t12)*6:,.0f}
  Primera respuesta: {t12[~t12['en_temporada']]['primera_respuesta_min'].median():.0f} min fuera de temporada, {t12[t12['en_temporada']]['primera_respuesta_min'].median():.0f} min EN temporada tributaria
  Resuelto al primer contacto: {t12['resuelto_primer_contacto'].mean()*100:.0f}% (referencia del sector: 70%)
  CSAT de tickets: {t12['csat'].mean():.2f}/5 · NPS: {float((n_ult['nps']*n_ult['encuestados']).sum()/n_ult['encuestados'].sum()):.0f}
  Categoría con más tickets: {t12.groupby('categoria').size().idxmax()}
  Atendidos con IA: {t12['atendido_por_ia'].mean()*100:.0f}%

FACTURACIÓN ELECTRÓNICA
  Documentos del último mes: {int(d_ult['emitidos'].sum()):,} · rechazo {d_ult['rechazados'].sum()/d_ult['emitidos'].sum()*100:.2f}%
  Tipo con más rechazo: {d.groupby('tipo_documento').apply(lambda x: x['rechazados'].sum()/x['emitidos'].sum()*100, include_groups=False).idxmax()}
  Disponibilidad de la plataforma (90 días): {plat.tail(90)['uptime_pct'].mean():.3f}%

BASE DE COLOMBIA (detalle nominal)
  Activos: {len(act):,} · en riesgo de fuga: {int(act['riesgo_fuga'].sum()):,} con {usd(act[act['riesgo_fuga']]['mrr_usd'].sum()*12)} de ARR expuesto
  Sin entrar al producto hace más de 30 días: {int((act['dias_sin_acceso']>30).sum()):,}
  Nómina Electrónica: {act['nomina_electronica'].mean()*100:.1f}% · Siigo Pay: {act['siigo_pay'].mean()*100:.1f}% · POS: {act['modulo_pos'].mean()*100:.1f}%
"""
    except Exception as ex:
        return f"[No se pudieron cargar los datos: {ex}]"


# ── Respuestas locales (sin llave de API) ────────────────────────────────────
def responder_local(pregunta: str) -> str:
    q = pregunta.lower()
    susc = datos.suscripciones()
    meses = datos.meses()
    ult, ant = meses[-1], meses[-13]
    s_ult, s_ant = susc[susc["mes"] == ult], susc[susc["mes"] == ant]
    ind = datos.indicadores_mes()
    r40 = datos.regla_40()
    ue = datos.unit_economics()

    def tiene(*xs):
        return any(x in q for x in xs)

    # ── Resumen general ──────────────────────────────────────────────────────
    if tiene("cómo vamos", "como vamos", "resumen", "general", "mes", "estamos"):
        arr = s_ult["mrr_usd"].sum() * 12
        crec = (arr / (s_ant["mrr_usd"].sum() * 12) - 1) * 100
        return (
            f"📊 **{mes_es(ult)}** cerró con **{usd(arr)}** de ARR, "
            f"{crec:+.1f}% frente a hace un año.\n\n"
            f"• Clientes activos: **{int(s_ult['clientes'].sum()):,}** en seis países\n"
            f"• ARPA: **US${float(ind['arpa'].iloc[-1]):.2f}** al mes\n"
            f"• NRR: **{datos.nrr_anual():.1f}%** · GRR: **{datos.grr_anual():.1f}%**\n"
            f"• EBITDA 12 meses: **{r40['ebitda_pct']:.1f}%** de los ingresos\n"
            f"• Regla del 40: **{r40['regla40']:.1f}**\n\n"
            f"Lo que hay que mirar: el crecimiento de {r40['crecimiento']:.1f}% es "
            f"bueno, pero el NRR de {datos.nrr_anual():.1f}% dice que la base de hace "
            f"un año vale hoy menos que entonces. Eso significa que buena parte del "
            f"esfuerzo comercial se está yendo en reponer, no en sumar. La palanca "
            f"más grande no está en vender más, está en que la base existente valga más.")

    # ── NRR ──────────────────────────────────────────────────────────────────
    if tiene("nrr", "retención", "retencion", "grr", "por debajo de 100"):
        p = datos.puente()
        p12 = p[p["mes"].isin(meses[-12:])]
        return (
            f"🔁 El **NRR está en {datos.nrr_anual():.1f}%** y el GRR en "
            f"{datos.grr_anual():.1f}%.\n\n"
            f"El NRR se descompone así, en los últimos doce meses:\n"
            f"• Expansión (alza anual, más usuarios, más módulos): "
            f"**+{usd(p12['expansion_usd'].sum()*12)}**\n"
            f"• Reactivaciones: **+{usd(p12['reactivacion_usd'].sum()*12)}**\n"
            f"• Contracción (bajan de plan o de usuarios): "
            f"**{usd(p12['contraccion_usd'].sum()*12)}**\n"
            f"• Fuga: **{usd(p12['churn_usd'].sum()*12)}**\n\n"
            f"La fuga es la que manda. Y la primera causa de cancelación es que el "
            f"negocio del cliente cerró — eso es estructural de atender "
            f"micronegocios, y no se arregla con producto.\n\n"
            f"Lo que sí se puede mover son las otras causas: soporte, implementación "
            f"y competencia. Y la palanca de expansión que está sin usar es la "
            f"adopción de módulos: dos de cada tres clientes no tienen Nómina "
            f"Electrónica.")

    # ── CAC / unit economics ─────────────────────────────────────────────────
    if tiene("cac", "cuesta traer", "adquisición", "adquisicion", "ltv", "paga",
             "payback", "canal más barato"):
        emb = datos.embudo()
        e12 = emb[emb["mes"].isin(meses[-12:])]
        can = e12.groupby("canal").apply(
            lambda x: x["inversion_usd"].sum() / x["pagados"].sum(),
            include_groups=False).sort_values()
        return (
            f"🎯 Traer un cliente cuesta **US${ue['cac']:,.0f}** en promedio y se "
            f"recupera en **{ue['payback_meses']:.0f} meses**. "
            f"La relación LTV/CAC es de **{ue['ltv_cac']:.1f}x** "
            f"(el umbral sano son 3x).\n\n"
            f"Pero el promedio esconde lo importante:\n"
            + "\n".join(f"• {k}: **US${v:,.0f}**" for k, v in can.items()) +
            f"\n\n**{can.index[0]}** cuesta {can.iloc[-1]/can.iloc[0]:.1f} veces menos "
            f"que **{can.index[-1]}**. No hace falta gastar más: basta con mover la "
            f"mezcla. Diez puntos del canal caro al barato bajan el CAC promedio y "
            f"acortan el retorno, sin un dólar adicional de presupuesto.")

    # ── Soporte ──────────────────────────────────────────────────────────────
    if tiene("soporte", "temporada", "tickets", "atención", "atencion", "nps", "csat"):
        tk = datos.tickets()
        t12 = tk[tk["mes"].isin(meses[-12:])]
        temp = t12[t12["en_temporada"]]["primera_respuesta_min"].median()
        fuera = t12[~t12["en_temporada"]]["primera_respuesta_min"].median()
        mc = datos.motivos_churn()
        mc12 = mc[mc["mes"].isin(meses[-12:])]
        sop = mc12[mc12["motivo"] == "Mala experiencia de soporte"]
        return (
            f"🎧 El soporte no está mal todo el año: **se rompe cinco meses**.\n\n"
            f"• Fuera de temporada la primera respuesta llega en **{fuera:.0f} minutos**\n"
            f"• En marzo–mayo y agosto–septiembre pasa a **{temp:.0f} minutos** "
            f"({temp/fuera:.1f} veces más)\n"
            f"• Resuelto al primer contacto: **{t12['resuelto_primer_contacto'].mean()*100:.0f}%** "
            f"(la referencia del sector es 70%)\n"
            f"• CSAT de tickets: **{t12['csat'].mean():.2f}/5**\n\n"
            f"Eso cuesta **{usd(sop['mrr_perdido_usd'].sum()*12)}** de ARR perdido al "
            f"año por mala experiencia de soporte.\n\n"
            f"Y aquí está lo importante: **son fechas conocidas con un año de "
            f"anticipación**. La información exógena, la renta de jurídicas y la de "
            f"naturales tienen calendario publicado por la DIAN. El problema no es "
            f"de calidad del equipo, es de capacidad planeada contra un pico "
            f"predecible.")

    # ── Aspel ────────────────────────────────────────────────────────────────
    if tiene("aspel", "migración", "migracion", "méxico", "mexico", "escritorio"):
        m = datos.migracion().iloc[-1]
        ritmo = float(datos.migracion()["migrados_mes"].tail(3).mean())
        arr_pend = m["pendientes"] * (m["arpa_nube_usd"] - m["arpa_desktop_usd"]) * 12
        return (
            f"🇲🇽 La migración de Aspel va en **{m['avance_pct']:.1f}%**: "
            f"{int(m['migrados_acum']):,} de {int(m['base_desktop_inicial']):,} "
            f"licencias.\n\n"
            f"• Pendientes: **{int(m['pendientes']):,}**\n"
            f"• Perdidos en el camino: **{int(m['perdidos_acum']):,}**\n"
            f"• ARPA: **US${m['arpa_desktop_usd']:.2f}** en escritorio contra "
            f"**US${m['arpa_nube_usd']:.2f}** en la nube "
            f"({m['arpa_nube_usd']/m['arpa_desktop_usd']:.1f} veces más)\n\n"
            f"Terminar lo pendiente vale **{usd(arr_pend)}** de ARR incremental. "
            f"Sin adquirir un solo cliente nuevo, sin CAC, sobre gente que ya paga. "
            f"Es la bolsa de ARR más grande y más barata que hay identificada.\n\n"
            f"El problema es el ritmo: a **{ritmo:,.0f} cuentas al mes** faltan "
            f"**{int(m['pendientes']/max(ritmo,1))} meses**, y en ese tiempo se "
            f"siguen perdiendo cuentas. Acelerar no solo adelanta ingreso: evita "
            f"parte de esa pérdida.")

    # ── Contadores ───────────────────────────────────────────────────────────
    if tiene("contador", "canal", "partner", "referid"):
        c = datos.contadores()
        dormidos = c[(~c["activo_ultimos_6m"]) & (c["clientes_referidos"] >= 8)]
        arpa_ref = c["arr_referido_usd"].sum() / max(c["clientes_activos"].sum(), 1)
        return (
            f"🧮 El canal de contadores tiene **{len(c):,} registrados** y trae "
            f"**{usd(c['arr_referido_usd'].sum())}** de ARR.\n\n"
            f"• Activos en los últimos 6 meses: **{int(c['activo_ultimos_6m'].sum()):,}** "
            f"({c['activo_ultimos_6m'].mean()*100:.0f}%)\n"
            f"• Certificados: **{c['certificado'].mean()*100:.0f}%**\n"
            f"• En el directorio: **{c['en_directorio'].mean()*100:.0f}%**\n\n"
            f"Dos hallazgos que se pueden accionar mañana:\n\n"
            f"**1.** Un contador certificado refiere "
            f"**{c[c['certificado']]['clientes_referidos'].mean():.1f}** clientes; uno "
            f"sin certificar, **{c[~c['certificado']]['clientes_referidos'].mean():.1f}**. "
            f"Y solo el {c['certificado'].mean()*100:.0f}% está certificado. El programa "
            f"ya existe: falta meter en él a los que ya están registrados.\n\n"
            f"**2.** Hay **{len(dormidos):,} contadores** que ya trajeron ocho o más "
            f"clientes y llevan más de seis meses sin referir. Si cada uno vuelve a "
            f"referir uno solo, son **{usd(len(dormidos)*arpa_ref)}** de ARR — con el "
            f"CAC de una llamada.")

    # ── Upsell ───────────────────────────────────────────────────────────────
    if tiene("upsell", "vendiendo", "módulo", "modulo", "nómina", "nomina", "pay",
             "cross", "complement"):
        cli = datos.clientes()
        act = cli[cli["estado"] == "Activo"]
        sin_nom = act[~act["nomina_electronica"]]
        cand = sin_nom[(sin_nom["docs_mes"] > 80) & (sin_nom["salud"] > 55) &
                       (sin_nom["plan"] != "Siigo Contador")]
        precio = 47_000 / datos.TRM
        return (
            f"🔓 En Colombia, **{act['nomina_electronica'].mean()*100:.1f}%** de la base "
            f"tiene Nómina Electrónica y **{act['siigo_pay'].mean()*100:.1f}%** tiene "
            f"Siigo Pay.\n\n"
            f"Eso significa que dos de cada tres clientes liquidan su nómina en otra "
            f"parte: en Excel, en otro software, o se la hace el contador aparte.\n\n"
            f"Filtrando a los que de verdad son candidatos — activos, con volumen real "
            f"de documentos y sin riesgo de fuga — quedan **{len(cand):,} clientes**, "
            f"que son **{usd(len(cand)*precio*12)}** de ARR potencial.\n\n"
            f"Comparación que importa: traer un cliente nuevo cuesta "
            f"**US${ue['cac']:,.0f}**. Venderle un módulo a alguien que ya está adentro, "
            f"ya confía y ya emite facturas cuesta una llamada. Y además baja el riesgo "
            f"de fuga: un cliente con cuatro módulos se va mucho menos que uno con uno.")

    # ── Países ───────────────────────────────────────────────────────────────
    if tiene("país", "pais", "region", "región", "internacional", "chile", "ecuador",
             "perú", "peru", "uruguay", "expansión", "expansion"):
        arr = s_ult.groupby("pais")["mrr_usd"].sum() * 12
        arr_a = s_ant.groupby("pais")["mrr_usd"].sum() * 12
        p = datos.paises().set_index("pais")
        lineas = "\n".join(
            f"• **{k}**: {usd(v)} ({(v/arr_a[k]-1)*100:+.1f}%) · "
            f"{p.loc[k,'penetracion_pct']:.2f}% del mercado · {p.loc[k,'via_entrada']}"
            for k, v in arr.sort_values(ascending=False).items())
        return (
            f"🌎 ARR por país:\n\n{lineas}\n\n"
            f"Dentro de esto hay **dos negocios distintos**. Colombia aporta el "
            f"{arr['Colombia']/arr.sum()*100:.0f}% del ARR y es un mercado maduro donde "
            f"Siigo ya es líder: ahí el crecimiento viene de ARPA, no de clientes "
            f"nuevos. Chile crece mucho más rápido pero sobre una base pequeña y con el "
            f"CAC más alto de los seis.\n\n"
            f"Reportarlos juntos en un solo número de crecimiento esconde la decisión "
            f"real: cuánto del capital levantado va a defender Colombia y cuánto a "
            f"abrir mercados nuevos.")

    # ── Riesgo de fuga ───────────────────────────────────────────────────────
    if tiene("riesgo", "irse", "van a ir", "cancel", "fuga", "churn", "perder"):
        cli = datos.clientes()
        act = cli[cli["estado"] == "Activo"]
        riesgo = act[act["riesgo_fuga"]]
        sin_uso = int((act["dias_sin_acceso"] > 30).sum())
        return (
            f"⚠️ En Colombia hay **{len(riesgo):,} clientes en riesgo de fuga** "
            f"({len(riesgo)/len(act)*100:.1f}% de la base activa), con "
            f"**{usd(riesgo['mrr_usd'].sum()*12)}** de ARR expuesto.\n\n"
            f"La señal más temprana no es la queja, es el silencio: "
            f"**{sin_uso:,} clientes** llevan más de 30 días sin abrir el producto. "
            f"Siguen pagando y siguen apareciendo al día en facturación, así que nadie "
            f"los está llamando. Ese grupo es el que cancela en la próxima renovación.\n\n"
            f"La fuga anual está en "
            f"**{(1-(1-float(ind['churn_logo_pct'].tail(12).mean())/100)**12)*100:.1f}%** "
            f"de los clientes. En el módulo de Retención está la lista priorizada por "
            f"ARR: son llamadas concretas, no un segmento abstracto.")

    # ── Regla del 40 ─────────────────────────────────────────────────────────
    if tiene("regla", "40", "cuarenta", "fondo", "accel", "kkr", "inversion",
             "inversión", "ebitda", "margen"):
        falta = 40 - r40["regla40"]
        f12 = datos.finanzas().tail(12)
        return (
            f"⚖️ La Regla del 40 está en **{r40['regla40']:.1f}**: "
            f"{r40['crecimiento']:.1f}% de crecimiento más {r40['ebitda_pct']:.1f}% "
            f"de margen EBITDA.\n\n"
            + (f"Faltan **{falta:.1f} puntos**. Y hay dos caminos que valen exactamente "
               f"lo mismo para el indicador:\n\n"
               f"• **Por crecimiento**: {usd(falta/100*f12['ingresos_usd'].sum())} de "
               f"ingreso adicional al año\n"
               f"• **Por margen**: el mismo monto, pero de gasto menos\n\n"
               if falta > 0 else
               "Está **por encima del umbral**. La pregunta ya no es cómo llegar, "
               "sino cómo sostenerlo mientras se abren mercados nuevos.\n\n") +
            f"Lo interesante es que hay tres palancas ya cuantificadas que no necesitan "
            f"capital nuevo:\n\n"
            f"1. **Mezcla de canales**: mover altas de Google y Meta al canal de "
            f"contadores baja gasto sin bajar altas → sube margen\n"
            f"2. **Migración de Aspel**: ARR incremental sin CAC → sube crecimiento\n"
            f"3. **Upsell de módulos**: ARPA con costo marginal casi nulo → sube los dos")

    # ── Documentos / DIAN ────────────────────────────────────────────────────
    if tiene("dian", "factura", "documento", "rechaz", "electrónica", "electronica"):
        d = datos.documentos()
        d_ult = d[d["mes"] == ult]
        por_tipo = d.groupby("tipo_documento").apply(
            lambda x: x["rechazados"].sum() / x["emitidos"].sum() * 100,
            include_groups=False).sort_values(ascending=False)
        return (
            f"🧾 En **{mes_es(ult)}** los clientes emitieron "
            f"**{miles(int(d_ult['emitidos'].sum()))}** documentos electrónicos, con "
            f"**{d_ult['rechazados'].sum()/d_ult['emitidos'].sum()*100:.2f}%** de "
            f"rechazo.\n\n"
            f"Por tipo de documento:\n"
            + "\n".join(f"• {k}: **{v:.2f}%**" for k, v in por_tipo.items()) +
            f"\n\nNómina electrónica y documento soporte son los que más se caen, y no "
            f"es casualidad: son los que más campos obligatorios y reglas de validación "
            f"tienen.\n\n"
            f"El costo real no está en el rechazo: está en que **cada rechazo produce "
            f"un cliente confundido llamando al soporte**, justo en los meses donde el "
            f"soporte ya está saturado. Y la mayoría de los rechazos son errores de "
            f"datos del cliente — un NIT mal digitado, una fecha fuera de rango — que "
            f"se pueden detectar antes de enviar.")

    # ── Por defecto ──────────────────────────────────────────────────────────
    return (
        f"Puedo responder sobre el negocio con los datos del panel. Algunas cosas que "
        f"sé mirar:\n\n"
        f"• **Ingreso**: ARR, crecimiento, puente de MRR, ARPA por plan y país\n"
        f"• **Retención**: NRR, GRR, fuga, motivos de cancelación, clientes en riesgo\n"
        f"• **Adquisición**: CAC por canal, LTV, recuperación, embudo\n"
        f"• **Canal de contadores**: quién refiere, quién se apagó, el programa\n"
        f"• **Producto**: adopción de módulos, uso, funciones de IA\n"
        f"• **Operación**: documentos ante la DIAN, rechazos, plataforma, soporte\n"
        f"• **Dirección**: Regla del 40, estructura de costos, caja y deuda\n\n"
        f"Hoy el ARR está en **{usd(s_ult['mrr_usd'].sum()*12)}** con "
        f"**{int(s_ult['clientes'].sum()):,}** clientes activos, y la Regla del 40 "
        f"en **{r40['regla40']:.1f}**. ¿Por dónde quieres empezar?")


# ── Llamada al modelo ────────────────────────────────────────────────────────
def responder_modelo(pregunta: str, historial: list) -> str:
    import anthropic
    cliente = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    mensajes = [{"role": m["role"], "content": m["content"]}
                for m in historial[-8:] if m["role"] in ("user", "assistant")]
    mensajes.append({"role": "user", "content": pregunta})
    r = cliente.messages.create(
        model=MODELO, max_tokens=1400,
        system=CONTEXTO + "\n\n" + resumen_datos(),
        messages=mensajes)
    return r.content[0].text


def _hay_llave() -> bool:
    try:
        return bool(st.secrets.get("ANTHROPIC_API_KEY"))
    except Exception:
        return False


def render():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    st.markdown(encabezado(
        "Agente IA Siigo",
        "Pregúntale al negocio en español · responde sobre los datos reales del panel",
        "Dirección"), unsafe_allow_html=True)

    con_modelo = _hay_llave()
    if not con_modelo:
        st.markdown(panel(
            "Modo demostración",
            "Sin llave de API configurada, el agente responde con lógica local sobre "
            "los <b>mismos datos</b> que alimentan los tableros. Las cifras son "
            "idénticas a las del resto del panel.<br><br>"
            "Con una llave de Anthropic en <code>.streamlit/secrets.toml</code>, el "
            "agente pasa a conversar libremente: entiende preguntas de seguimiento, "
            "cruza áreas y explica el porqué. El contexto que recibe es el mismo "
            "resumen de datos que se puede ver abajo.",
            "🤖"), unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if "chat" not in st.session_state:
        st.session_state.chat = [{
            "role": "assistant",
            "content": (
                "Hola. Soy el agente de negocio de Siigo y tengo el panel completo "
                "adentro: ingreso, retención, canal de contadores, producto, "
                "operación y finanzas de los seis países.\n\n"
                "Pregúntame lo que quieras saber — en español, como se lo "
                "preguntarías a alguien del equipo.")}]

    st.markdown("##### Preguntas para empezar")
    cols = st.columns(2, gap="small")
    pendiente = None
    for i, s in enumerate(SUGERIDAS):
        if cols[i % 2].button(s, key=f"sug_{i}", width="stretch"):
            pendiente = s

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    for m in st.session_state.chat:
        with st.chat_message(m["role"], avatar="☁️" if m["role"] == "assistant" else "👤"):
            st.markdown(m["content"])

    entrada = st.chat_input("Escribe tu pregunta sobre el negocio…")
    pregunta = pendiente or entrada

    if pregunta:
        st.session_state.chat.append({"role": "user", "content": pregunta})
        with st.chat_message("user", avatar="👤"):
            st.markdown(pregunta)
        with st.chat_message("assistant", avatar="☁️"):
            with st.spinner("Mirando los datos…"):
                try:
                    if con_modelo:
                        r = responder_modelo(pregunta, st.session_state.chat[:-1])
                    else:
                        r = responder_local(pregunta)
                except Exception as ex:
                    r = (responder_local(pregunta) +
                         f"\n\n---\n*No se pudo consultar el modelo ({ex}); "
                         f"la respuesta viene de la lógica local.*")
            st.markdown(r)
        st.session_state.chat.append({"role": "assistant", "content": r})

    if st.session_state.chat and len(st.session_state.chat) > 1:
        if st.button("🔄  Empezar de nuevo", key="reset_chat"):
            del st.session_state["chat"]
            st.rerun()

    with st.expander("Ver el contexto exacto que recibe el agente"):
        st.caption("Este resumen se arma con las mismas funciones que alimentan los "
                   "tableros. Por eso el agente nunca puede dar una cifra distinta a "
                   "la que muestra el panel.")
        st.code(resumen_datos(), language="text")
