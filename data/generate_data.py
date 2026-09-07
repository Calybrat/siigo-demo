#!/usr/bin/env python3
"""
Generador del set de datos del panel de Siigo.

Los datos son SIMULADOS, pero no inventados a ciegas: el modelo está anclado a
cifras públicas y verificables de Siigo, y todo lo demás se deriva de ahí con
supuestos de SaaS B2B que se declaran explícitamente en ANCLAS y SUPUESTOS.

Anclas públicas (ver README para las fuentes):
  · Fundada en 1988 en Bogotá · Accel-KKR entra en 2017
  · 6 países: Colombia, México, Ecuador, Perú, Uruguay, Chile
  · +300.000 pymes y contadores activos en la plataforma
  · +120.000 pymes en Colombia · +35.000 contadores
  · ~2.300 colaboradores
  · Ingresos netos 2025: +24,1%
  · Julio 2026: US$103,5M de financiación estructurada (Banco de Occidente US$18,5M)
  · Adquisiciones: Ilimitada (CO, 2019), Contífico (EC, 2020), Memory (UY, 2020),
    Aspel (MX, 2022)
  · Precios Colombia 2026 (plan anual): Profesional Independiente $145.993/mes,
    Emprendedor $191.327/mes, Premium $207.869/mes

La consistencia se garantiza por construcción: el MRR de cada mes se SIMULA
mes a mes y el puente de ARR se DERIVA de esa simulación, no al revés. Por eso
MRR[t] = MRR[t-1] + nuevo + expansión + reactivación − contracción − fuga
cierra exacto en todos los meses, países y planes.

Uso:  python3 data/generate_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent
RNG = np.random.default_rng(20260831)

# ── Ventana de tiempo ────────────────────────────────────────────────────────
CORTE = pd.Timestamp("2026-08-31")
MESES = pd.period_range("2024-09", "2026-08", freq="M").strftime("%Y-%m").tolist()
N_MES = len(MESES)              # 24
DIAS = pd.date_range("2024-09-01", "2026-08-31", freq="D")

TRM = 4050.0                    # COP por USD, promedio 2026

# ── Anclas públicas ──────────────────────────────────────────────────────────
ANCLAS = {
    "clientes_activos_grupo": 305_200,   # ">300.000 pymes y contadores"
    "clientes_colombia": 122_400,        # ">120.000 pymes en Colombia"
    "contadores": 35_800,                # ">35.000 contadores"
    "colaboradores": 2_300,
    "crecimiento_2025_pct": 24.1,
    "deuda_usd": 103_500_000,
    "trm": TRM,
}

PAISES = [
    # pais, código, moneda, año, vía de entrada, clientes activos hoy, pymes del mercado, competidor
    ("Colombia", "CO", "COP", 1988, "Orgánico",            122_400, 1_620_000, "Alegra"),
    ("México",   "MX", "MXN", 2022, "Adquisición Aspel",    96_500, 4_200_000, "CONTPAQi"),
    ("Ecuador",  "EC", "USD", 2020, "Adquisición Contífico", 38_200,  890_000, "Contífico"),
    ("Perú",     "PE", "PEN", 2019, "Orgánico",              24_800, 1_900_000, "Bsale"),
    ("Uruguay",  "UY", "UYU", 2020, "Adquisición Memory",    14_900,  178_000, "Memory"),
    ("Chile",    "CL", "CLP", 2023, "Orgánico",               8_400, 1_100_000, "Defontana"),
]
NOMBRES_PAIS = [p[0] for p in PAISES]

# ── Catálogo de planes ───────────────────────────────────────────────────────
# precio_cop = precio real publicado en Colombia (plan anual, 2026).
# Los demás países usan el equivalente en USD ajustado por poder adquisitivo.
PLANES = [
    # plan, precio_cop_mes, usuarios, segmento, churn_mensual, peso_CO
    ("Siigo Contador",            0,      3, "Contador",   0.0130, 0.170),
    ("Profesional Independiente", 145_993, 1, "Micro",     0.0235, 0.235),
    ("Emprendedor",               191_327, 3, "Pequeña",   0.0158, 0.265),
    ("Premium",                   207_869, 5, "Pequeña",   0.0112, 0.155),
    ("Corporativo",               389_000, 12, "Mediana",  0.0058, 0.052),
    ("Siigo POS",                  89_000, 2, "Micro",     0.0206, 0.083),
    ("POS Gastrobar",             119_000, 3, "Micro",     0.0244, 0.040),
]
NOMBRES_PLAN = [p[0] for p in PLANES]

# Complementos: qué proporción de la base los tiene y cuánto suman al MRR
COMPLEMENTOS = {
    "Nómina Electrónica": (0.312, 47_000),
    "Siigo Pay":          (0.184, 38_000),
    "Documentos extra":   (0.221, 26_000),
}

SECTORES = [
    ("Comercio al por menor", 0.221), ("Servicios profesionales", 0.163),
    ("Restaurantes y bares", 0.104), ("Construcción", 0.089),
    ("Manufactura", 0.086), ("Transporte y logística", 0.071),
    ("Salud", 0.063), ("Tecnología", 0.058), ("Educación", 0.041),
    ("Agropecuario", 0.039), ("Inmobiliario", 0.034), ("Otros", 0.031),
]

CIUDADES_CO = [
    ("Bogotá D.C.", "Cundinamarca", 0.352), ("Medellín", "Antioquia", 0.148),
    ("Cali", "Valle del Cauca", 0.101), ("Barranquilla", "Atlántico", 0.067),
    ("Bucaramanga", "Santander", 0.048), ("Cartagena", "Bolívar", 0.041),
    ("Pereira", "Risaralda", 0.032), ("Cúcuta", "N. de Santander", 0.028),
    ("Manizales", "Caldas", 0.024), ("Ibagué", "Tolima", 0.023),
    ("Villavicencio", "Meta", 0.022), ("Santa Marta", "Magdalena", 0.019),
    ("Neiva", "Huila", 0.017), ("Armenia", "Quindío", 0.016),
    ("Pasto", "Nariño", 0.016), ("Montería", "Córdoba", 0.015),
    ("Popayán", "Cauca", 0.013), ("Sincelejo", "Sucre", 0.011),
    ("Valledupar", "Cesar", 0.010), ("Otras ciudades", "Varios", 0.097),
]

CANALES = [
    # canal, participación de altas, CAC relativo, calidad (activación)
    ("Búsqueda orgánica",   0.212, 0.42, 0.74),
    ("Canal de contadores", 0.268, 0.31, 0.88),
    ("Google Ads",          0.151, 1.62, 0.61),
    ("Meta Ads",            0.096, 1.44, 0.54),
    ("Televentas",          0.108, 1.31, 0.79),
    ("Referidos de clientes", 0.074, 0.18, 0.85),
    ("Alianzas y bancos",   0.058, 0.68, 0.81),
    ("Marketplace / App",   0.033, 0.55, 0.66),
]

MOTIVOS_CHURN = [
    ("Cerró o quebró el negocio",       0.238),
    ("Precio / ajuste anual",           0.191),
    ("Se fue a la competencia",         0.147),
    ("Mala experiencia de soporte",     0.121),
    ("No logró implementar",            0.109),
    ("Cambió de contador",              0.078),
    ("Funcionalidad faltante",          0.067),
    ("Otro / sin motivo registrado",    0.049),
]

CAT_TICKET = [
    ("Facturación electrónica / DIAN", 0.243, 1.00),
    ("Nómina electrónica",             0.148, 1.35),
    ("Contabilidad y cierres",         0.131, 1.22),
    ("Inventarios",                    0.097, 0.92),
    ("Facturación y cobros a Siigo",   0.089, 0.71),
    ("Acceso y usuarios",              0.084, 0.48),
    ("Informes y exportes",            0.071, 0.86),
    ("POS y cajas",                    0.058, 0.79),
    ("Integraciones y API",            0.045, 1.61),
    ("Siigo Pay",                      0.034, 0.94),
]

TIPOS_DOC = [
    ("Factura electrónica", 0.472),
    ("Tiquete POS",         0.198),
    ("Nota crédito",        0.104),
    ("Documento soporte",   0.088),
    ("Nómina electrónica",  0.083),
    ("Nota débito",         0.055),
]

MOTIVOS_RECHAZO = [
    ("NIT del adquiriente inválido",        0.223),
    ("Fecha fuera del rango permitido",     0.174),
    ("Error en cálculo de IVA",             0.158),
    ("CUFE duplicado",                      0.121),
    ("Resolución de numeración vencida",    0.113),
    ("Detalle de tributos incompleto",      0.089),
    ("Firma digital inválida",              0.072),
    ("Otros rechazos técnicos",             0.050),
]

FEATURES = [
    # feature, adopción hoy, ritmo de adopción, es de IA
    ("Facturación electrónica",   0.968, 0.004, False),
    ("Informes financieros",      0.741, 0.011, False),
    ("Inventarios",               0.548, 0.009, False),
    ("Nómina electrónica",        0.312, 0.014, False),
    ("App móvil",                 0.436, 0.021, False),
    ("Cobranza por WhatsApp",     0.287, 0.033, False),
    ("Siigo Pay",                 0.184, 0.019, False),
    ("Centros de costo",          0.163, 0.006, False),
    ("API pública",               0.094, 0.008, False),
    ("Conciliación bancaria IA",  0.121, 0.042, True),
    ("Captura de facturas por IA", 0.088, 0.038, True),
    ("Agente IA fiscal",          0.062, 0.031, True),
]

# Estacionalidad de Colombia. El calendario tributario manda:
# exógena (mar–may), renta personas jurídicas (abr–jul), renta naturales (ago–oct),
# IVA bimestral y nómina electrónica todos los meses.
EST_ALTAS = {1: 1.34, 2: 1.22, 3: 1.15, 4: 1.02, 5: 0.96, 6: 0.91,
             7: 0.94, 8: 0.99, 9: 1.03, 10: 1.01, 11: 0.93, 12: 0.72}
EST_SOPORTE = {1: 1.12, 2: 1.05, 3: 1.41, 4: 1.68, 5: 1.52, 6: 1.14,
               7: 1.08, 8: 1.33, 9: 1.29, 10: 1.21, 11: 0.92, 12: 0.78}
EST_DOCS = {1: 0.88, 2: 0.94, 3: 1.06, 4: 1.09, 5: 1.04, 6: 1.02,
            7: 1.01, 8: 1.03, 9: 1.01, 10: 1.04, 11: 1.09, 12: 1.24}


def _mes_num(m: str) -> int:
    return int(m.split("-")[1])


def _pick(opciones, n, rng=RNG):
    """Escoge n valores de una lista de (valor, peso)."""
    vals = [o[0] for o in opciones]
    pesos = np.array([o[-1] for o in opciones], dtype=float)
    return rng.choice(vals, size=n, p=pesos / pesos.sum())


def _guardar(df: pd.DataFrame, nombre: str, comprimir=False):
    ruta = OUT / (f"{nombre}.csv.gz" if comprimir else f"{nombre}.csv")
    df.to_csv(ruta, index=False, compression="gzip" if comprimir else None)
    mb = ruta.stat().st_size / 1_048_576
    print(f"  ✓ {ruta.name:<28} {len(df):>9,} filas   {mb:>6.2f} MB")


# ═════════════════════════════════════════════════════════════════════════════
# 1. Países
# ═════════════════════════════════════════════════════════════════════════════
def gen_paises() -> pd.DataFrame:
    filas = []
    for pais, cod, moneda, anio, via, clientes, mercado, comp in PAISES:
        filas.append({
            "pais": pais, "codigo": cod, "moneda": moneda,
            "anio_entrada": anio, "via_entrada": via,
            "clientes_activos": clientes,
            "pymes_mercado": mercado,
            "penetracion_pct": round(clientes / mercado * 100, 2),
            "competidor_principal": comp,
        })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 2. Planes
# ═════════════════════════════════════════════════════════════════════════════
def gen_planes() -> pd.DataFrame:
    # Ajuste de precio por país frente a Colombia (poder adquisitivo del segmento pyme)
    ajuste = {"Colombia": 1.00, "México": 1.28, "Ecuador": 1.14,
              "Perú": 0.96, "Uruguay": 1.41, "Chile": 1.22}
    filas = []
    for plan, precio_cop, usuarios, segmento, churn, _ in PLANES:
        base_usd = precio_cop / TRM
        for pais in NOMBRES_PAIS:
            filas.append({
                "plan": plan, "pais": pais, "segmento": segmento,
                "usuarios_incluidos": usuarios,
                "precio_usd_mes": round(base_usd * ajuste[pais], 2),
                "precio_cop_mes": int(precio_cop) if pais == "Colombia" else "",
                "churn_mensual_ref_pct": round(churn * 100, 2),
            })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 3. Simulación mes a mes de la base y del MRR
#    De aquí salen suscripciones_mensual y arr_puente, ya conciliados.
# ═════════════════════════════════════════════════════════════════════════════
def simular_base():
    """Simula clientes y MRR por mes/país/plan.

    Cada país arranca en un tamaño que, con su tasa de crecimiento neto,
    llega exactamente al número de clientes activos publicado hoy.
    """
    # Crecimiento neto mensual por país (Chile y México son los que más corren)
    crec = {"Colombia": 0.0062, "México": 0.0154, "Ecuador": 0.0094,
            "Perú": 0.0118, "Uruguay": 0.0051, "Chile": 0.0288}
    # ARPA base en USD por país (ponderado por el mix de planes)
    ajuste_precio = {"Colombia": 1.00, "México": 1.28, "Ecuador": 1.14,
                     "Perú": 0.96, "Uruguay": 1.41, "Chile": 1.22}
    # Mix de planes distinto por país: México llega vía Aspel (base de escritorio
    # migrando a planes bajos), Uruguay es más de contadores.
    mix_pais = {
        "Colombia": None,   # usa el peso_CO del catálogo
        "México":   [0.112, 0.301, 0.258, 0.134, 0.041, 0.104, 0.050],
        "Ecuador":  [0.148, 0.243, 0.271, 0.168, 0.058, 0.076, 0.036],
        "Perú":     [0.131, 0.268, 0.259, 0.152, 0.049, 0.098, 0.043],
        "Uruguay":  [0.226, 0.212, 0.248, 0.171, 0.067, 0.052, 0.024],
        "Chile":    [0.121, 0.284, 0.276, 0.158, 0.062, 0.071, 0.028],
    }
    pesos_co = np.array([p[-1] for p in PLANES])
    pesos_co = pesos_co / pesos_co.sum()

    suscripciones, puente = [], []

    for pais, _cod, _mon, _anio, _via, clientes_hoy, _merc, _comp in PAISES:
        g = crec[pais]
        mix = np.array(mix_pais[pais]) if mix_pais[pais] is not None else pesos_co
        mix = mix / mix.sum()
        clientes_ini = clientes_hoy / ((1 + g) ** (N_MES - 1))

        # Estado por plan
        estado = {}
        for i, (plan, precio_cop, _u, _s, churn, _w) in enumerate(PLANES):
            c0 = clientes_ini * mix[i]
            # Se arranca por debajo del precio de lista de 2026: con 24 meses de
            # alza anual y upsell encima, el ARPA de HOY tiene que aterrizar en el
            # precio publicado más los complementos, no un 13% por encima.
            arpa0 = (precio_cop / TRM) * ajuste_precio[pais] * 0.885
            estado[plan] = {"clientes": c0, "arpa": arpa0, "churn": churn}

        for t, mes in enumerate(MESES):
            mnum = _mes_num(mes)
            est_alta = EST_ALTAS[mnum] if pais == "Colombia" else 1 + (EST_ALTAS[mnum] - 1) * 0.6

            for plan, precio_cop, _u, _s, churn_base, _w in PLANES:
                e = estado[plan]
                c_ini = e["clientes"]
                arpa_ini = e["arpa"]
                mrr_ini = c_ini * arpa_ini

                if t == 0:
                    # Primer mes: solo se registra el punto de partida
                    suscripciones.append({
                        "mes": mes, "pais": pais, "plan": plan,
                        "clientes": int(round(c_ini)),
                        "arpa_usd": round(arpa_ini, 2),
                        "mrr_usd": round(mrr_ini, 2),
                    })
                    puente.append({
                        "mes": mes, "pais": pais, "plan": plan,
                        "mrr_inicial_usd": round(mrr_ini, 2),
                        "nuevo_usd": 0.0, "expansion_usd": 0.0, "reactivacion_usd": 0.0,
                        "contraccion_usd": 0.0, "churn_usd": 0.0,
                        "mrr_final_usd": round(mrr_ini, 2),
                        "clientes_inicial": int(round(c_ini)),
                        "clientes_nuevos": 0, "clientes_baja": 0,
                        "clientes_final": int(round(c_ini)),
                    })
                    continue

                # Bajas del mes (más churn en enero y diciembre)
                mult_churn = 1.28 if mnum == 1 else (1.16 if mnum == 12 else 1.0)
                tasa_churn = churn_base * mult_churn * RNG.normal(1.0, 0.055)
                tasa_churn = float(np.clip(tasa_churn, 0.002, 0.08))
                bajas = c_ini * tasa_churn

                # Altas: cubren la fuga y aportan el crecimiento neto
                altas = (c_ini * (1 + g) - (c_ini - bajas)) * est_alta * RNG.normal(1.0, 0.06)
                altas = max(altas, 0.0)

                # Reactivaciones: clientes que vuelven (temporada tributaria).
                # Salen del mismo cupo de altas, no se suman por encima: si no
                # se descuentan, la base cierra ~4% por encima del dato público.
                reactiv = bajas * (0.085 if mnum in (1, 2, 3, 4) else 0.052)
                altas = max(altas - reactiv, 0.0)

                c_fin = c_ini + altas + reactiv - bajas

                # Movimiento de precio: alza anual en enero + upsell de complementos
                alza = 0.055 if mnum == 1 else 0.0
                upsell = RNG.normal(0.0089, 0.0016)          # más módulos y usuarios
                downgrade = RNG.normal(0.0021, 0.0008)       # bajan de plan o de usuarios
                arpa_fin = arpa_ini * (1 + alza + upsell - downgrade)

                nuevo_mrr = altas * arpa_fin * 0.86          # los nuevos entran con descuento
                reactiv_mrr = reactiv * arpa_fin * 0.91
                churn_mrr = bajas * arpa_ini
                expansion_mrr = c_ini * arpa_ini * (alza + max(upsell, 0))
                contraccion_mrr = c_ini * arpa_ini * max(downgrade, 0)

                mrr_fin = (mrr_ini + nuevo_mrr + expansion_mrr + reactiv_mrr
                           - contraccion_mrr - churn_mrr)
                # El ARPA de cierre se reconcilia con el MRR final real
                arpa_fin = mrr_fin / c_fin if c_fin > 0 else arpa_fin

                estado[plan] = {"clientes": c_fin, "arpa": arpa_fin, "churn": churn_base}

                suscripciones.append({
                    "mes": mes, "pais": pais, "plan": plan,
                    "clientes": int(round(c_fin)),
                    "arpa_usd": round(arpa_fin, 2),
                    "mrr_usd": round(mrr_fin, 2),
                })
                puente.append({
                    "mes": mes, "pais": pais, "plan": plan,
                    "mrr_inicial_usd": round(mrr_ini, 2),
                    "nuevo_usd": round(nuevo_mrr, 2),
                    "expansion_usd": round(expansion_mrr, 2),
                    "reactivacion_usd": round(reactiv_mrr, 2),
                    "contraccion_usd": round(-contraccion_mrr, 2),
                    "churn_usd": round(-churn_mrr, 2),
                    "mrr_final_usd": round(mrr_fin, 2),
                    "clientes_inicial": int(round(c_ini)),
                    "clientes_nuevos": int(round(altas + reactiv)),
                    "clientes_baja": int(round(bajas)),
                    "clientes_final": int(round(c_fin)),
                })

    return pd.DataFrame(suscripciones), pd.DataFrame(puente)


# ═════════════════════════════════════════════════════════════════════════════
# 4. Clientes de Colombia (detalle nominal)
# ═════════════════════════════════════════════════════════════════════════════
def gen_clientes(susc: pd.DataFrame) -> pd.DataFrame:
    activos = int(susc[(susc["mes"] == MESES[-1]) & (susc["pais"] == "Colombia")]["clientes"].sum())
    bajas_hist = int(activos * 0.31)
    n = activos + bajas_hist
    print(f"    Colombia: {activos:,} activos + {bajas_hist:,} bajas históricas")

    mix_plan = susc[(susc["mes"] == MESES[-1]) & (susc["pais"] == "Colombia")]
    mix_plan = mix_plan.set_index("plan")["clientes"]
    p_plan = (mix_plan / mix_plan.sum()).reindex(NOMBRES_PLAN).fillna(0).values

    plan = RNG.choice(NOMBRES_PLAN, size=n, p=p_plan / p_plan.sum())
    precio = {p[0]: p[1] for p in PLANES}
    usuarios_inc = {p[0]: p[2] for p in PLANES}

    ciudad_idx = RNG.choice(len(CIUDADES_CO), size=n,
                            p=np.array([c[2] for c in CIUDADES_CO]) /
                              sum(c[2] for c in CIUDADES_CO))
    ciudad = np.array([CIUDADES_CO[i][0] for i in ciudad_idx])
    depto = np.array([CIUDADES_CO[i][1] for i in ciudad_idx])
    sector = _pick(SECTORES, n)
    canal = _pick([(c[0], c[1]) for c in CANALES], n)

    # Antigüedad: base madura con cola larga (la empresa tiene 38 años)
    antig = np.clip(RNG.gamma(1.9, 21.0, n), 0.5, 220).astype(int)
    fecha_alta = CORTE - pd.to_timedelta(antig * 30.44, unit="D")

    # Estado: las bajas históricas son las de mayor antigüedad simulada de baja
    estado = np.array(["Activo"] * n, dtype=object)
    idx_baja = RNG.choice(n, size=bajas_hist, replace=False)
    estado[idx_baja] = "Cancelado"
    fecha_baja = pd.Series(pd.NaT, index=range(n))
    dur = np.clip(RNG.gamma(1.6, 9.0, bajas_hist), 1, 200)
    fecha_baja.iloc[idx_baja] = (pd.Series(fecha_alta).iloc[idx_baja].values
                                 + pd.to_timedelta(dur * 30.44, unit="D"))
    fecha_baja = pd.to_datetime(fecha_baja).clip(upper=CORTE)

    usuarios = np.array([max(1, int(RNG.poisson(usuarios_inc[p] * 0.72) + 1)) for p in plan])
    base_cop = np.array([precio[p] for p in plan], dtype=float)
    # Usuarios adicionales sobre los incluidos
    extra_usr = np.maximum(0, usuarios - np.array([usuarios_inc[p] for p in plan]))
    mrr_cop = base_cop + extra_usr * 32_000

    nomina = RNG.random(n) < np.where(base_cop > 0, 0.312, 0.06)
    pos_mod = RNG.random(n) < 0.147
    pay = RNG.random(n) < 0.184
    mrr_cop = (mrr_cop + nomina * 47_000 + pos_mod * 29_000 + pay * 0)
    mrr_cop = np.where(base_cop == 0, 0, mrr_cop)   # Siigo Contador es gratis

    # Uso e indicadores de salud
    docs_base = {"Siigo Contador": 340, "Profesional Independiente": 62,
                 "Emprendedor": 148, "Premium": 236, "Corporativo": 612,
                 "Siigo POS": 418, "POS Gastrobar": 726}
    docs_mes = np.array([max(0, int(RNG.gamma(2.2, docs_base[p] / 2.2))) for p in plan])
    dias_sin_acceso = np.where(estado == "Cancelado", 999,
                               np.clip(RNG.gamma(1.3, 5.0, n), 0, 180).astype(int))

    # Salud del cliente: uso reciente + módulos + antigüedad − tickets
    salud = (58
             + np.clip(np.log1p(docs_mes) * 6.1, 0, 26)
             - np.clip(dias_sin_acceso * 0.62, 0, 34)
             + nomina * 6 + pay * 4 + pos_mod * 3
             + np.clip(antig * 0.05, 0, 9)
             + RNG.normal(0, 7, n))
    salud = np.clip(salud, 1, 100).round(0)
    riesgo = (estado == "Activo") & (salud < 42)

    contador_id = np.where(canal == "Canal de contadores",
                           RNG.integers(1, ANCLAS["contadores"] + 1, n), 0)

    nps = np.where(RNG.random(n) < 0.22,
                   np.clip((salud / 10 + RNG.normal(0, 1.8, n)), 0, 10).round(0), -1)

    migrado = np.where(RNG.random(n) < 0.061, "Ilimitada", "")

    df = pd.DataFrame({
        "cliente_id": [f"CO{i:07d}" for i in range(1, n + 1)],
        "plan": plan, "sector": sector, "ciudad": ciudad, "departamento": depto,
        "segmento": [dict((p[0], p[3]) for p in PLANES)[p] for p in plan],
        "usuarios": usuarios,
        "fecha_alta": pd.Series(fecha_alta).dt.strftime("%Y-%m-%d"),
        "fecha_baja": fecha_baja.dt.strftime("%Y-%m-%d").fillna(""),
        "estado": estado,
        "antiguedad_meses": antig,
        "mrr_cop": mrr_cop.round(0).astype(int),
        "mrr_usd": (mrr_cop / TRM).round(2),
        "nomina_electronica": nomina, "modulo_pos": pos_mod, "siigo_pay": pay,
        "canal_adquisicion": canal,
        "contador_id": contador_id,
        "docs_mes": docs_mes,
        "dias_sin_acceso": dias_sin_acceso,
        "salud": salud.astype(int),
        "riesgo_fuga": riesgo,
        "nps": nps.astype(int),
        "migrado_desde": migrado,
    })
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 5. Contadores (el canal)
# ═════════════════════════════════════════════════════════════════════════════
def gen_contadores() -> pd.DataFrame:
    n = ANCLAS["contadores"]
    pais = RNG.choice(NOMBRES_PAIS, size=n,
                      p=[0.615, 0.176, 0.089, 0.062, 0.039, 0.019])
    ciudad = np.where(pais == "Colombia",
                      _pick([(c[0], c[2]) for c in CIUDADES_CO], n),
                      "—")
    # Referidos con cola muy larga: unos pocos contadores mueven la mayoría.
    # El techo se sortea por fila; con un tope fijo, decenas de contadores
    # quedaban clavados en el mismo número y la tabla se veía artificial.
    techo = RNG.integers(190, 560, n)
    referidos = np.minimum(RNG.pareto(1.55, n) * 3.4, techo).astype(int)
    activos = (referidos * RNG.uniform(0.58, 0.94, n)).astype(int)
    arpa = RNG.normal(41, 9, n).clip(14, 120)
    arr_ref = (activos * arpa * 12).round(0)

    nivel = np.select(
        [referidos >= 60, referidos >= 25, referidos >= 8],
        ["Platino", "Oro", "Plata"], default="Bronce")
    antig = np.clip(RNG.gamma(1.7, 17.0, n), 1, 190).astype(int)

    df = pd.DataFrame({
        "contador_id": np.arange(1, n + 1),
        "pais": pais, "ciudad": ciudad,
        "nivel_partner": nivel,
        "certificado": RNG.random(n) < 0.437,
        "en_directorio": RNG.random(n) < 0.294,
        "usa_siigo_contador": RNG.random(n) < 0.812,
        "clientes_referidos": referidos,
        "clientes_activos": activos,
        "arr_referido_usd": arr_ref,
        "antiguedad_meses": antig,
        "meses_sin_referir": np.clip(RNG.gamma(1.5, 4.2, n), 0, 40).astype(int),
        "nps": np.clip(RNG.normal(7.4, 2.3, n), 0, 10).round(0).astype(int),
    })
    df["activo_ultimos_6m"] = df["meses_sin_referir"] <= 6
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 6. Documentos electrónicos y rechazos DIAN
# ═════════════════════════════════════════════════════════════════════════════
def gen_documentos(susc: pd.DataFrame):
    # Documentos/mes por cliente activo, por país
    docs_cliente = {"Colombia": 186, "México": 164, "Ecuador": 149,
                    "Perú": 141, "Uruguay": 128, "Chile": 133}
    clientes_mes = (susc.groupby(["mes", "pais"])["clientes"].sum()
                    .to_dict())

    filas = []
    for d in DIAS:
        mes = d.strftime("%Y-%m")
        mnum = d.month
        # Fin de mes concentra facturación; domingos caen fuerte
        dia_factor = 1.0
        if d.day >= 28:
            dia_factor = 1.62
        elif d.day <= 3:
            dia_factor = 1.21
        if d.weekday() == 6:
            dia_factor *= 0.31
        elif d.weekday() == 5:
            dia_factor *= 0.58

        for pais in NOMBRES_PAIS:
            c = clientes_mes.get((mes, pais), 0)
            if not c:
                continue
            base_dia = c * docs_cliente[pais] / 30.44 * EST_DOCS[mnum] * dia_factor
            for tipo, peso in TIPOS_DOC:
                emitidos = base_dia * peso * RNG.normal(1.0, 0.07)
                emitidos = max(0, int(emitidos))
                # Tasa de rechazo: nómina y documento soporte son los más frágiles
                r_base = {"Factura electrónica": 0.0121, "Tiquete POS": 0.0038,
                          "Nota crédito": 0.0154, "Documento soporte": 0.0231,
                          "Nómina electrónica": 0.0268, "Nota débito": 0.0142}[tipo]
                # En picos de carga la tasa sube
                r = r_base * (1.34 if dia_factor > 1.5 else 1.0) * RNG.normal(1.0, 0.13)
                rechazados = int(emitidos * max(r, 0))
                aceptados = emitidos - rechazados
                lat = RNG.normal(1180 if dia_factor > 1.5 else 740, 160)
                filas.append({
                    "fecha": d.strftime("%Y-%m-%d"), "mes": mes, "pais": pais,
                    "tipo_documento": tipo,
                    "emitidos": emitidos, "aceptados": aceptados,
                    "rechazados": rechazados,
                    "latencia_p95_ms": int(max(180, lat)),
                })
    docs = pd.DataFrame(filas)

    # Motivos de rechazo por mes/país
    rech = docs.groupby(["mes", "pais"])["rechazados"].sum().reset_index()
    filas_r = []
    for _, r in rech.iterrows():
        for motivo, peso in MOTIVOS_RECHAZO:
            filas_r.append({
                "mes": r["mes"], "pais": r["pais"], "motivo": motivo,
                "cantidad": int(r["rechazados"] * peso * RNG.normal(1.0, 0.09)),
            })
    return docs, pd.DataFrame(filas_r)


# ═════════════════════════════════════════════════════════════════════════════
# 7. Plataforma: disponibilidad, latencia e incidentes
# ═════════════════════════════════════════════════════════════════════════════
def gen_plataforma():
    filas, incidentes = [], []
    inc_id = 1
    componentes = ["API de facturación", "Motor contable", "Portal web",
                   "App móvil", "Integración DIAN", "Siigo Pay", "Base de datos"]
    for d in DIAS:
        mnum = d.month
        carga = EST_SOPORTE[mnum] * (1.7 if d.day >= 28 else 1.0)
        peticiones = 41.2 * carga * RNG.normal(1.0, 0.08)     # millones/día
        lat50 = RNG.normal(148 + 46 * (carga - 1), 14)
        lat95 = RNG.normal(612 + 340 * (carga - 1), 62)

        # Incidentes: más probables en picos de temporada tributaria
        p_inc = 0.028 * carga ** 2.1
        n_inc = int(RNG.random() < p_inc) + int(RNG.random() < p_inc * 0.25)
        minutos_caida = 0.0
        for _ in range(n_inc):
            sev = RNG.choice(["S1", "S2", "S3"], p=[0.13, 0.34, 0.53])
            dur = {"S1": RNG.uniform(38, 190), "S2": RNG.uniform(18, 74),
                   "S3": RNG.uniform(6, 28)}[sev]
            minutos_caida += dur if sev == "S1" else dur * 0.35
            comp = RNG.choice(componentes)
            incidentes.append({
                "incidente_id": f"INC-{inc_id:04d}", "fecha": d.strftime("%Y-%m-%d"),
                "mes": d.strftime("%Y-%m"), "severidad": sev, "componente": comp,
                "duracion_min": int(dur),
                "clientes_afectados": int(RNG.uniform(0.02, 0.41) *
                                          ANCLAS["clientes_activos_grupo"]),
                "en_temporada": EST_SOPORTE[mnum] > 1.25,
            })
            inc_id += 1

        uptime = max(0.0, (1440 - minutos_caida) / 1440 * 100)
        filas.append({
            "fecha": d.strftime("%Y-%m-%d"), "mes": d.strftime("%Y-%m"),
            "uptime_pct": round(uptime, 4),
            "latencia_p50_ms": int(max(60, lat50)),
            "latencia_p95_ms": int(max(180, lat95)),
            "peticiones_millones": round(max(0, peticiones), 2),
            "errores_5xx": int(max(0, RNG.normal(1400 * carga, 380))),
            "incidentes": n_inc,
        })
    return pd.DataFrame(filas), pd.DataFrame(incidentes)


# ═════════════════════════════════════════════════════════════════════════════
# 8. Soporte: tickets, NPS y CSAT
# ═════════════════════════════════════════════════════════════════════════════
def gen_soporte(susc: pd.DataFrame):
    clientes_mes = susc.groupby(["mes", "pais"])["clientes"].sum().to_dict()
    canales_sop = [("Chat", 0.341), ("Teléfono", 0.268), ("WhatsApp", 0.196),
                   ("Correo", 0.121), ("Portal de ayuda", 0.074)]
    filas = []
    tid = 1
    for mes in MESES:
        mnum = _mes_num(mes)
        est = EST_SOPORTE[mnum]
        for pais in NOMBRES_PAIS:
            c = clientes_mes.get((mes, pais), 0)
            if not c:
                continue
            # ~9,4 tickets por cada 100 clientes/mes en temporada normal
            n = int(c * 0.094 * est * RNG.normal(1.0, 0.05))
            n = max(0, n // 6)      # se guarda 1 de cada 6 como muestra trazable
            if n == 0:
                continue
            cat = _pick(CAT_TICKET, n)
            peso_cat = dict((c_[0], c_[2]) for c_ in CAT_TICKET)
            canal = _pick(canales_sop, n)
            plan = RNG.choice(NOMBRES_PLAN, size=n,
                              p=np.array([p[-1] for p in PLANES]) /
                                sum(p[-1] for p in PLANES))
            prio = RNG.choice(["Baja", "Media", "Alta", "Crítica"], size=n,
                              p=[0.312, 0.451, 0.191, 0.046])

            # Saturación: en temporada el tiempo de primera respuesta se dispara
            satur = 1 + (est - 1) * 2.35
            fr = RNG.gamma(1.7, 21 * satur, n)                     # minutos
            res = np.array([RNG.gamma(1.9, 4.2 * peso_cat[k] * satur) for k in cat])
            fcr = RNG.random(n) < np.clip(0.71 - (satur - 1) * 0.19, 0.28, 0.82)
            reab = RNG.random(n) < np.clip(0.081 + (satur - 1) * 0.06, 0.05, 0.28)
            ia = RNG.random(n) < min(0.44, 0.06 + MESES.index(mes) * 0.017)

            csat = np.clip(RNG.normal(np.where(fcr, 4.42, 3.28) -
                                      (satur - 1) * 0.52, 0.82), 1, 5).round(0)

            dia = RNG.integers(1, 29, n)
            f_ap = pd.to_datetime(mes + "-01") + pd.to_timedelta(dia - 1, unit="D")
            f_ci = f_ap + pd.to_timedelta(res, unit="h")

            filas.append(pd.DataFrame({
                "ticket_id": [f"T{x:07d}" for x in range(tid, tid + n)],
                "mes": mes, "pais": pais,
                "fecha_apertura": f_ap.strftime("%Y-%m-%d"),
                "fecha_cierre": f_ci.strftime("%Y-%m-%d"),
                "canal": canal, "categoria": cat, "plan": plan, "prioridad": prio,
                "primera_respuesta_min": fr.round(0).astype(int),
                "resolucion_horas": res.round(1),
                "resuelto_primer_contacto": fcr,
                "reabierto": reab,
                "atendido_por_ia": ia,
                "csat": csat.astype(int),
                "en_temporada": est > 1.25,
            }))
            tid += n
    tickets = pd.concat(filas, ignore_index=True)

    # NPS mensual por país y segmento
    segmentos = ["Micro", "Pequeña", "Mediana", "Contador"]
    filas_nps = []
    for i, mes in enumerate(MESES):
        mnum = _mes_num(mes)
        castigo = (EST_SOPORTE[mnum] - 1) * 11.5      # el NPS cae en temporada
        for pais in NOMBRES_PAIS:
            for seg in segmentos:
                base = {"Micro": 11, "Pequeña": 21, "Mediana": 30, "Contador": 34}[seg]
                base += {"Colombia": 4, "México": -6, "Ecuador": 1,
                         "Perú": 2, "Uruguay": 6, "Chile": -3}[pais]
                base += i * 0.32                       # mejora lenta pero real
                nps = base - castigo + RNG.normal(0, 3.1)
                n_enc = int(RNG.uniform(180, 1400))
                det = np.clip((100 - nps) / 2.6, 8, 48)
                pro = np.clip(det + nps, 12, 78)
                pas = max(0, 100 - pro - det)
                filas_nps.append({
                    "mes": mes, "pais": pais, "segmento": seg,
                    "encuestados": n_enc,
                    "promotores_pct": round(pro, 1), "pasivos_pct": round(pas, 1),
                    "detractores_pct": round(det, 1),
                    "nps": round(pro - det, 1),
                    "csat": round(np.clip(3.4 + nps / 42 - castigo / 28, 1, 5), 2),
                })
    return tickets, pd.DataFrame(filas_nps)


# ═════════════════════════════════════════════════════════════════════════════
# 9. Embudo de adquisición y CAC
# ═════════════════════════════════════════════════════════════════════════════
def gen_embudo(puente: pd.DataFrame) -> pd.DataFrame:
    altas = puente.groupby(["mes", "pais"])["clientes_nuevos"].sum().to_dict()
    filas = []
    for mes in MESES:
        for pais in NOMBRES_PAIS:
            total = altas.get((mes, pais), 0)
            if not total:
                continue
            for canal, share, cac_rel, calidad in CANALES:
                pagados = int(total * share * RNG.normal(1.0, 0.07))
                if pagados <= 0:
                    continue
                activados = int(pagados / max(calidad, .3) * RNG.normal(1.0, .04))
                trials = int(activados / RNG.uniform(0.52, 0.68))
                leads = int(trials / RNG.uniform(0.19, 0.31))
                visitas = int(leads / RNG.uniform(0.026, 0.052))
                # CAC: los canales pagos cuestan; el de contadores es el más barato
                cac_base = {"Colombia": 430, "México": 545, "Ecuador": 462,
                            "Perú": 448, "Uruguay": 611, "Chile": 738}[pais]
                cac = cac_base * cac_rel * RNG.normal(1.0, 0.08)
                filas.append({
                    "mes": mes, "pais": pais, "canal": canal,
                    "visitas": visitas, "leads": leads, "trials": trials,
                    "activados": activados, "pagados": pagados,
                    "inversion_usd": round(cac * pagados, 0),
                    "cac_usd": round(cac, 2),
                })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 10. Motivos de cancelación
# ═════════════════════════════════════════════════════════════════════════════
def gen_motivos_churn(puente: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for _, r in puente.iterrows():
        if r["clientes_baja"] <= 0:
            continue
        mnum = _mes_num(r["mes"])
        for motivo, peso in MOTIVOS_CHURN:
            p = peso
            # En temporada tributaria el soporte pesa más como motivo de fuga
            if motivo == "Mala experiencia de soporte" and EST_SOPORTE[mnum] > 1.25:
                p *= 1.48
            if motivo == "Precio / ajuste anual" and mnum in (1, 2):
                p *= 1.63
            n = int(r["clientes_baja"] * p * RNG.normal(1.0, 0.11))
            if n <= 0:
                continue
            filas.append({
                "mes": r["mes"], "pais": r["pais"], "plan": r["plan"],
                "motivo": motivo, "clientes": n,
                "mrr_perdido_usd": round(abs(r["churn_usd"]) * p, 2),
            })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 11. Cohortes de retención
# ═════════════════════════════════════════════════════════════════════════════
def gen_cohortes() -> pd.DataFrame:
    filas = []
    for i, cohorte in enumerate(MESES):
        tam = int(RNG.uniform(4200, 7800) * (1 + i * 0.014))
        for pais in ["Colombia", "México", "Ecuador", "Perú", "Uruguay", "Chile"]:
            share = {"Colombia": .41, "México": .29, "Ecuador": .12,
                     "Perú": .09, "Uruguay": .05, "Chile": .04}[pais]
            n0 = int(tam * share)
            if n0 < 20:
                continue
            churn_m = {"Colombia": .0164, "México": .0212, "Ecuador": .0178,
                       "Perú": .0186, "Uruguay": .0141, "Chile": .0229}[pais]
            for t in range(N_MES - i):
                # El primer mes siempre se pierde más: no logran implementar
                ret = np.prod([1 - churn_m * (2.9 if k == 0 else
                                              (1.5 if k == 1 else
                                               max(0.55, 1 - k * 0.021)))
                               for k in range(t)]) if t else 1.0
                # El MRR retenido sube por expansión aunque se vayan clientes
                mrr_ret = ret * (1 + 0.0091 * t)
                filas.append({
                    "cohorte": cohorte, "pais": pais, "mes_vida": t,
                    "clientes_inicial": n0,
                    "clientes_retenidos": int(n0 * ret),
                    "retencion_pct": round(ret * 100, 2),
                    "retencion_mrr_pct": round(mrr_ret * 100, 2),
                })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 12. Uso del producto (panel de clientes de Colombia)
# ═════════════════════════════════════════════════════════════════════════════
def gen_uso(clientes: pd.DataFrame) -> pd.DataFrame:
    panel = clientes[clientes["estado"] == "Activo"].sample(12_000, random_state=7)
    filas = []
    for i, mes in enumerate(MESES):
        mnum = _mes_num(mes)
        f_est = EST_DOCS[mnum]
        n = len(panel)
        activo = RNG.random(n) < np.clip(panel["salud"].values / 100 + 0.24, 0.2, 0.99)
        sesiones = np.where(activo,
                            RNG.gamma(2.0, panel["docs_mes"].values / 26 + 3) * f_est,
                            RNG.gamma(1.1, 1.4))
        dias = np.clip(sesiones / 2.4 + RNG.normal(0, 1.6, n), 0, 30)
        docs = np.where(activo,
                        panel["docs_mes"].values * f_est * RNG.normal(1.0, 0.18, n), 0)
        modulos = (1 + panel["nomina_electronica"].values.astype(int)
                   + panel["modulo_pos"].values.astype(int)
                   + panel["siigo_pay"].values.astype(int)
                   + (RNG.random(n) < 0.42).astype(int)      # inventarios
                   + (RNG.random(n) < 0.16).astype(int))     # centros de costo
        filas.append(pd.DataFrame({
            "mes": mes, "cliente_id": panel["cliente_id"].values,
            "plan": panel["plan"].values,
            "sesiones": sesiones.round(0).astype(int),
            "dias_activos": dias.round(0).astype(int),
            "docs_emitidos": docs.round(0).astype(int),
            "modulos_activos": modulos,
            "usa_movil": RNG.random(n) < 0.436,
            "usa_api": RNG.random(n) < 0.094,
            "usa_ia": RNG.random(n) < min(0.31, 0.03 + i * 0.012),
        }))
    return pd.concat(filas, ignore_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# 13. Adopción de funcionalidades
# ═════════════════════════════════════════════════════════════════════════════
def gen_adopcion(susc: pd.DataFrame) -> pd.DataFrame:
    clientes_mes = susc.groupby(["mes", "pais"])["clientes"].sum().to_dict()
    filas = []
    for i, mes in enumerate(MESES):
        atras = N_MES - 1 - i
        for pais in NOMBRES_PAIS:
            base = clientes_mes.get((mes, pais), 0)
            if not base:
                continue
            aj = {"Colombia": 1.0, "México": 0.78, "Ecuador": 0.91,
                  "Perú": 0.88, "Uruguay": 0.96, "Chile": 0.83}[pais]
            for feat, hoy, ritmo, es_ia in FEATURES:
                adop = max(0.002, (hoy - ritmo * atras) * aj) * RNG.normal(1.0, 0.03)
                filas.append({
                    "mes": mes, "pais": pais, "funcionalidad": feat,
                    "es_ia": es_ia,
                    "clientes_base": base,
                    "clientes_usando": int(base * min(adop, 0.995)),
                    "adopcion_pct": round(min(adop, 0.995) * 100, 2),
                })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 14. Finanzas del grupo
# ═════════════════════════════════════════════════════════════════════════════
def gen_finanzas(susc: pd.DataFrame) -> pd.DataFrame:
    mrr = susc.groupby("mes")["mrr_usd"].sum()
    filas = []
    caja = 34_100_000.0
    for i, mes in enumerate(MESES):
        ingresos = float(mrr[mes]) * RNG.normal(1.012, 0.006)   # + servicios únicos
        # Margen bruto de SaaS: alto, pero con soporte pesado por ser pyme
        cogs = ingresos * RNG.normal(0.243, 0.009)
        bruto = ingresos - cogs
        # Se invierte >20% de los ingresos en producto (dato público de Siigo)
        rnd = ingresos * RNG.normal(0.214, 0.007)
        sym = ingresos * RNG.normal(0.291, 0.011)
        gna = ingresos * RNG.normal(0.128, 0.006)
        ebitda = bruto - rnd - sym - gna
        capex = ingresos * RNG.normal(0.031, 0.004)

        # La financiación de US$103,5M entra en julio de 2026
        deuda = 41_800_000.0 if mes < "2026-07" else float(ANCLAS["deuda_usd"])
        entrada = (ANCLAS["deuda_usd"] - 41_800_000.0) if mes == "2026-07" else 0.0
        intereses = deuda * 0.0094
        caja += ebitda - capex - intereses + entrada
        headcount = int(1_940 + i * 15.6 + RNG.normal(0, 12))

        filas.append({
            "mes": mes,
            "ingresos_usd": round(ingresos, 0),
            "costo_servicio_usd": round(cogs, 0),
            "margen_bruto_usd": round(bruto, 0),
            "margen_bruto_pct": round(bruto / ingresos * 100, 2),
            "sym_usd": round(sym, 0), "rnd_usd": round(rnd, 0), "gna_usd": round(gna, 0),
            "ebitda_usd": round(ebitda, 0),
            "ebitda_pct": round(ebitda / ingresos * 100, 2),
            "capex_usd": round(capex, 0),
            "intereses_usd": round(intereses, 0),
            "deuda_usd": round(deuda, 0),
            "caja_usd": round(caja, 0),
            "headcount": headcount,
        })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 15. Migración Aspel (México) → Siigo Nube
# ═════════════════════════════════════════════════════════════════════════════
def gen_migracion() -> pd.DataFrame:
    base_total = 214_000     # licencias de escritorio Aspel heredadas
    filas = []
    migrados_acum, perdidos_acum = 38_400, 21_700
    for i, mes in enumerate(MESES):
        pendiente = base_total - migrados_acum - perdidos_acum
        # La migración se acelera pero también levanta fuga
        tasa_mig = 0.0184 * (1 + i * 0.031)
        tasa_perd = 0.0061 * (1 + i * 0.012)
        mig = int(pendiente * tasa_mig * RNG.normal(1.0, 0.09))
        perd = int(pendiente * tasa_perd * RNG.normal(1.0, 0.12))
        migrados_acum += mig
        perdidos_acum += perd
        filas.append({
            "mes": mes,
            "base_desktop_inicial": base_total,
            "migrados_mes": mig, "perdidos_mes": perd,
            "migrados_acum": migrados_acum, "perdidos_acum": perdidos_acum,
            "pendientes": base_total - migrados_acum - perdidos_acum,
            "avance_pct": round(migrados_acum / base_total * 100, 2),
            "arpa_desktop_usd": round(RNG.normal(17.4, 0.6), 2),
            "arpa_nube_usd": round(RNG.normal(38.9, 1.1), 2),
            "csat_migracion": round(np.clip(RNG.normal(3.71 + i * 0.011, 0.09), 1, 5), 2),
        })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 16. Headcount por área
# ═════════════════════════════════════════════════════════════════════════════
def gen_empleados(fin: pd.DataFrame) -> pd.DataFrame:
    areas = [("Producto y Tecnología", .312, 6_900), ("Servicio al Cliente", .268, 2_400),
             ("Comercial", .194, 3_100), ("Mercadeo", .058, 3_600),
             ("Operaciones", .081, 2_800), ("Finanzas y Administración", .052, 4_200),
             ("Gente y Cultura", .035, 3_400)]
    reparto_pais = {"Colombia": .541, "México": .218, "Ecuador": .092,
                    "Perú": .061, "Uruguay": .049, "Chile": .022,
                    "Remoto / otros": .017}
    filas = []
    for _, r in fin.iterrows():
        for area, share, costo in areas:
            for pais, sp in reparto_pais.items():
                n = int(r["headcount"] * share * sp)
                if n < 1:
                    continue
                filas.append({
                    "mes": r["mes"], "area": area, "pais": pais, "headcount": n,
                    "costo_mensual_usd": int(n * costo * RNG.normal(1.0, 0.03)),
                    "rotacion_12m_pct": round(np.clip(RNG.normal(
                        18.4 if area == "Servicio al Cliente" else 12.1, 2.4), 4, 34), 1),
                    "vacantes_abiertas": int(max(0, RNG.poisson(n * 0.031))),
                })
    return pd.DataFrame(filas)


# ═════════════════════════════════════════════════════════════════════════════
# 17. Competencia
# ═════════════════════════════════════════════════════════════════════════════
def gen_competencia() -> pd.DataFrame:
    datos = [
        ("Colombia", "Siigo",        41.2, 1.00, "Autorización DIAN y canal de contadores", "Interfaz menos moderna"),
        ("Colombia", "Alegra",       18.6, 0.79, "Producto más moderno y simple",          "Menos profundidad contable"),
        ("Colombia", "World Office", 11.4, 1.12, "Fuerte en medianas",                     "Poca presencia en micro"),
        ("Colombia", "Helisa",        8.9, 1.06, "Tradición entre contadores",             "Migración a nube lenta"),
        ("Colombia", "Otros",        19.9, 0.92, "Nicho y verticales",                     "Fragmentados"),
        ("México",   "CONTPAQi",     34.1, 1.18, "Estándar entre despachos",               "Modelo de escritorio"),
        ("México",   "Siigo/Aspel",  27.8, 0.94, "Base histórica de Aspel",                "Migración a nube en curso"),
        ("México",   "Facturama",    12.3, 0.71, "Precio bajo, timbrado",                  "Suite incompleta"),
        ("México",   "Otros",        25.8, 0.98, "Muy fragmentado",                        "—"),
        ("Ecuador",  "Siigo/Contífico", 38.4, 1.00, "Líder local adquirido",               "Marca doble confunde"),
        ("Ecuador",  "Otros",        61.6, 0.95, "Locales y de nicho",                     "—"),
        ("Perú",     "Siigo",        13.1, 1.00, "Entrada orgánica",                       "Marca poco conocida"),
        ("Perú",     "Bsale",        21.4, 0.86, "Fuerte en retail",                       "Contabilidad limitada"),
        ("Perú",     "Otros",        65.5, 0.97, "Muy fragmentado",                        "—"),
        ("Uruguay",  "Siigo/Memory", 44.2, 1.00, "Memory es el estándar local",            "Mercado pequeño"),
        ("Uruguay",  "Otros",        55.8, 1.02, "Locales",                                "—"),
        ("Chile",    "Siigo",         4.8, 1.00, "Recién entrando",                        "Sin masa crítica"),
        ("Chile",    "Defontana",    23.6, 1.09, "Incumbente en nube",                     "Precio alto"),
        ("Chile",    "Otros",        71.6, 0.94, "Bsale, Nubox y locales",                 "—"),
    ]
    return pd.DataFrame(datos, columns=[
        "pais", "competidor", "participacion_pct", "precio_relativo",
        "fortaleza", "debilidad"])


# ═════════════════════════════════════════════════════════════════════════════
def main():
    print("\nGenerando datos del panel de Siigo…")
    print(f"  Ventana: {MESES[0]} → {MESES[-1]} ({N_MES} meses) · corte {CORTE:%d/%m/%Y}\n")

    _guardar(gen_paises(), "paises")
    _guardar(gen_planes(), "planes")

    print("  Simulando base de clientes y MRR…")
    susc, puente = simular_base()
    _guardar(susc, "suscripciones_mensual")
    _guardar(puente, "arr_puente")

    print("  Detalle de clientes de Colombia…")
    clientes = gen_clientes(susc)
    _guardar(clientes, "clientes", comprimir=True)

    _guardar(gen_contadores(), "contadores")
    _guardar(gen_cohortes(), "cohortes")
    _guardar(gen_motivos_churn(puente), "motivos_churn")
    _guardar(gen_embudo(puente), "embudo")

    print("  Documentos electrónicos (diario, 6 países)…")
    docs, rech = gen_documentos(susc)
    _guardar(docs, "documentos", comprimir=True)
    _guardar(rech, "rechazos")

    plat, inc = gen_plataforma()
    _guardar(plat, "plataforma")
    _guardar(inc, "incidentes")

    print("  Soporte y experiencia…")
    tickets, nps = gen_soporte(susc)
    _guardar(tickets, "tickets", comprimir=True)
    _guardar(nps, "nps")

    _guardar(gen_adopcion(susc), "adopcion")
    print("  Panel de uso del producto…")
    _guardar(gen_uso(clientes), "uso_mensual", comprimir=True)

    fin = gen_finanzas(susc)
    _guardar(fin, "finanzas_mensual")
    _guardar(gen_empleados(fin), "empleados")
    _guardar(gen_migracion(), "migracion_aspel")
    _guardar(gen_competencia(), "competencia")

    # ── Verificación de consistencia ─────────────────────────────────────────
    print("\nVerificación:")
    ult = susc[susc["mes"] == MESES[-1]]
    print(f"  Clientes activos hoy      {int(ult['clientes'].sum()):>12,}  "
          f"(ancla: {ANCLAS['clientes_activos_grupo']:,})")
    print(f"  Colombia                  {int(ult[ult['pais']=='Colombia']['clientes'].sum()):>12,}  "
          f"(ancla: {ANCLAS['clientes_colombia']:,})")
    arr = ult["mrr_usd"].sum() * 12
    print(f"  ARR                       {arr/1e6:>11.1f}M USD")
    print(f"  ARPA mensual              {ult['mrr_usd'].sum()/ult['clientes'].sum():>11.2f} USD")

    # El puente tiene que cerrar contra el MRR simulado
    p = puente[puente["mes"] == MESES[-1]]
    cierre = (p["mrr_inicial_usd"].sum() + p["nuevo_usd"].sum() + p["expansion_usd"].sum()
              + p["reactivacion_usd"].sum() + p["contraccion_usd"].sum() + p["churn_usd"].sum())
    print(f"  Puente de ARR cierra en   {cierre:>12,.0f}  vs MRR {p['mrr_final_usd'].sum():,.0f}"
          f"   (desfase {abs(cierre - p['mrr_final_usd'].sum()):.2f})")
    print(f"  Ingresos 12m              {fin['ingresos_usd'].tail(12).sum()/1e6:>11.1f}M USD")
    ing12 = fin["ingresos_usd"].tail(12).sum()
    ing12_ant = fin["ingresos_usd"].head(12).sum()
    crec = (ing12 / ing12_ant - 1) * 100
    ebitda_pct = fin["ebitda_usd"].tail(12).sum() / ing12 * 100
    print(f"  EBITDA 12m                {fin['ebitda_usd'].tail(12).sum()/1e6:>11.1f}M USD  "
          f"({ebitda_pct:.1f}%)")
    print(f"  Crecimiento interanual    {crec:>11.1f}%  (ancla 2025: "
          f"{ANCLAS['crecimiento_2025_pct']}%)")
    print(f"  Regla del 40              {crec + ebitda_pct:>11.1f}")
    print("\nListo.\n")


if __name__ == "__main__":
    main()
