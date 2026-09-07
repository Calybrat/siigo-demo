"""
Carga de datos compartida.

Todos los módulos leen de aquí para que cada tabla se cargue UNA sola vez en
memoria: `st.cache_data` cachea por función, así que si cada módulo definiera su
propio loader se guardaría una copia por módulo.

Sobre los tipos: se hace downcast de las columnas numéricas, que es seguro. NO
se convierte el texto a `category`: al agrupar por columnas categóricas pandas
devuelve también las combinaciones que no existen, y eso metería filas en cero
en las gráficas (por ejemplo, Chile facturando US$0 en meses anteriores a su
apertura). Preferimos gastar algo más de memoria antes que mostrar un dato que
no ocurrió.

Aquí viven además los indicadores de SaaS que se usan en más de un módulo
(NRR, GRR, churn, LTV/CAC), para que todos los módulos den el mismo número.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

_DATA = Path(__file__).parent.parent / "data"

CORTE = pd.Timestamp("2026-08-31")
CORTE_TXT = "31 de agosto de 2026"
TRM = 4050.0


def _leer(nombre: str, **kw) -> pd.DataFrame:
    kw.setdefault("low_memory", False)
    for candidato in (_DATA / nombre, _DATA / f"{nombre}.gz"):
        if candidato.exists():
            return pd.read_csv(candidato, **kw)
    raise FileNotFoundError(f"No se encontró {nombre} en {_DATA}")


# ── Tablas ───────────────────────────────────────────────────────────────────
@st.cache_data
def paises() -> pd.DataFrame:
    return _leer("paises.csv")


@st.cache_data
def planes() -> pd.DataFrame:
    return _leer("planes.csv")


@st.cache_data(show_spinner="Cargando suscripciones…")
def suscripciones() -> pd.DataFrame:
    df = _leer("suscripciones_mensual.csv")
    df["clientes"] = pd.to_numeric(df["clientes"], downcast="integer")
    return df


@st.cache_data(show_spinner="Cargando el puente de ARR…")
def puente() -> pd.DataFrame:
    return _leer("arr_puente.csv")


@st.cache_data(show_spinner="Cargando clientes de Colombia…")
def clientes(con_fechas: bool = False) -> pd.DataFrame:
    df = _leer("clientes.csv")
    for c in ["usuarios", "antiguedad_meses", "mrr_cop", "docs_mes",
              "dias_sin_acceso", "salud", "nps", "contador_id"]:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    df["mrr_usd"] = pd.to_numeric(df["mrr_usd"], downcast="float")
    df["migrado_desde"] = df["migrado_desde"].fillna("")
    if con_fechas:
        df["fecha_alta"] = pd.to_datetime(df["fecha_alta"])
        df["fecha_baja"] = pd.to_datetime(df["fecha_baja"], errors="coerce")
    return df


@st.cache_data(show_spinner="Cargando el canal de contadores…")
def contadores() -> pd.DataFrame:
    return _leer("contadores.csv")


@st.cache_data
def cohortes() -> pd.DataFrame:
    return _leer("cohortes.csv")


@st.cache_data
def motivos_churn() -> pd.DataFrame:
    return _leer("motivos_churn.csv")


@st.cache_data
def embudo() -> pd.DataFrame:
    return _leer("embudo.csv")


@st.cache_data(show_spinner="Cargando documentos electrónicos…")
def documentos(con_fecha: bool = False) -> pd.DataFrame:
    df = _leer("documentos.csv")
    for c in ["emitidos", "aceptados", "rechazados", "latencia_p95_ms"]:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    if con_fecha:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


@st.cache_data
def rechazos() -> pd.DataFrame:
    return _leer("rechazos.csv")


@st.cache_data
def plataforma(con_fecha: bool = True) -> pd.DataFrame:
    df = _leer("plataforma.csv")
    if con_fecha:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


@st.cache_data
def incidentes() -> pd.DataFrame:
    return _leer("incidentes.csv")


@st.cache_data(show_spinner="Cargando tickets de soporte…")
def tickets() -> pd.DataFrame:
    df = _leer("tickets.csv")
    for c in ["primera_respuesta_min", "csat"]:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    df["resolucion_horas"] = pd.to_numeric(df["resolucion_horas"], downcast="float")
    return df


@st.cache_data
def nps() -> pd.DataFrame:
    return _leer("nps.csv")


@st.cache_data
def adopcion() -> pd.DataFrame:
    return _leer("adopcion.csv")


@st.cache_data(show_spinner="Cargando uso del producto…")
def uso() -> pd.DataFrame:
    df = _leer("uso_mensual.csv")
    for c in ["sesiones", "dias_activos", "docs_emitidos", "modulos_activos"]:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    return df


@st.cache_data
def finanzas() -> pd.DataFrame:
    return _leer("finanzas_mensual.csv")


@st.cache_data
def empleados() -> pd.DataFrame:
    return _leer("empleados.csv")


@st.cache_data
def migracion() -> pd.DataFrame:
    return _leer("migracion_aspel.csv")


@st.cache_data
def competencia() -> pd.DataFrame:
    return _leer("competencia.csv")


@st.cache_data
def meses() -> list:
    return sorted(suscripciones()["mes"].unique().tolist())


# ── Indicadores compartidos ──────────────────────────────────────────────────
# Todos los módulos calculan NRR, GRR y churn desde aquí para que ningún
# tablero contradiga a otro. Es el error más caro de un panel ejecutivo:
# dos pantallas que dan cifras distintas del mismo indicador.

@st.cache_data
def indicadores_mes(pais: str = "Todos") -> pd.DataFrame:
    """Serie mensual de los indicadores de SaaS, ya conciliados con el puente."""
    p = puente()
    if pais != "Todos":
        p = p[p["pais"] == pais]
    g = p.groupby("mes").agg(
        mrr_inicial=("mrr_inicial_usd", "sum"),
        nuevo=("nuevo_usd", "sum"),
        expansion=("expansion_usd", "sum"),
        reactivacion=("reactivacion_usd", "sum"),
        contraccion=("contraccion_usd", "sum"),
        churn=("churn_usd", "sum"),
        mrr_final=("mrr_final_usd", "sum"),
        clientes_inicial=("clientes_inicial", "sum"),
        clientes_nuevos=("clientes_nuevos", "sum"),
        clientes_baja=("clientes_baja", "sum"),
        clientes_final=("clientes_final", "sum"),
    ).reset_index()

    ini = g["mrr_inicial"].replace(0, np.nan)
    # NRR mira solo la base que ya existía: expansión y reactivación menos
    # contracción y fuga. El MRR nuevo NO entra: si entrara, cualquier empresa
    # que venda mucho parecería retener bien.
    g["nrr_pct"] = ((ini + g["expansion"] + g["reactivacion"]
                     + g["contraccion"] + g["churn"]) / ini * 100)
    g["grr_pct"] = ((ini + g["contraccion"] + g["churn"]) / ini * 100)
    g["churn_mrr_pct"] = (-g["churn"] / ini * 100)
    g["churn_logo_pct"] = (g["clientes_baja"] /
                           g["clientes_inicial"].replace(0, np.nan) * 100)
    g["arr_final"] = g["mrr_final"] * 12
    g["arpa"] = g["mrr_final"] / g["clientes_final"].replace(0, np.nan)
    return g


@st.cache_data
def nrr_anual(pais: str = "Todos") -> float:
    """NRR de los últimos 12 meses, encadenando los mensuales."""
    g = indicadores_mes(pais).tail(12)
    return float(np.prod(g["nrr_pct"] / 100) * 100)


@st.cache_data
def grr_anual(pais: str = "Todos") -> float:
    g = indicadores_mes(pais).tail(12)
    return float(np.prod(g["grr_pct"] / 100) * 100)


@st.cache_data
def unit_economics(pais: str = "Todos") -> dict:
    """CAC, LTV, meses de recuperación y relación LTV/CAC de los últimos 12 meses."""
    e = embudo()
    ms = meses()[-12:]
    e = e[e["mes"].isin(ms)]
    if pais != "Todos":
        e = e[e["pais"] == pais]
    pagados = e["pagados"].sum()
    inversion = e["inversion_usd"].sum()
    cac = inversion / pagados if pagados else 0

    ind = indicadores_mes(pais).tail(12)
    arpa = float(ind["arpa"].iloc[-1])
    churn_m = float(ind["churn_logo_pct"].mean()) / 100
    vida_meses = 1 / churn_m if churn_m else 0

    f = finanzas().tail(12)
    margen = float(f["margen_bruto_usd"].sum() / f["ingresos_usd"].sum())

    ltv = arpa * margen * vida_meses
    payback = cac / (arpa * margen) if arpa * margen else 0
    return {"cac": cac, "ltv": ltv, "arpa": arpa, "margen_bruto": margen,
            "vida_meses": vida_meses, "ltv_cac": ltv / cac if cac else 0,
            "payback_meses": payback, "clientes_nuevos": int(pagados),
            "inversion": inversion}


@st.cache_data
def regla_40() -> dict:
    """Crecimiento interanual + margen EBITDA. El indicador que mira el fondo."""
    f = finanzas()
    ing12 = float(f["ingresos_usd"].tail(12).sum())
    ing12_ant = float(f["ingresos_usd"].head(12).sum())
    crec = (ing12 / ing12_ant - 1) * 100
    ebitda_pct = float(f["ebitda_usd"].tail(12).sum()) / ing12 * 100
    return {"crecimiento": crec, "ebitda_pct": ebitda_pct,
            "regla40": crec + ebitda_pct, "ingresos_12m": ing12}
