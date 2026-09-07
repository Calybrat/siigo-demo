"""
Paleta e identidad visual de Siigo.

Los colores no son una interpretación: salen de los archivos reales de la marca.
  · #009DFF  — único hex declarado en el CSS de siigo.com
  · #00A2FF / #00ABFF — píxeles dominantes del logo y del lockup con eslogan
  · #F28F17  — naranja del "+" en "+ que un software contable"

El logo que se usa en `assets/` es el SVG que sirve siigo.com
(`.../2025/10/Logo.svg`), en tres versiones de color generadas a partir de él.

La nube no es decoración: el isotipo de Siigo *es* una nube, y el producto se
llama Siigo Nube. Por eso el separador de cada módulo y el fondo del encabezado
la repiten en vez de usar una línea recta cualquiera.
"""
import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# ── Paleta de marca ──────────────────────────────────────────────────────────
AZUL        = "#009DFF"   # azul Siigo (CSS oficial del sitio)
AZUL_VIVO   = "#00A2FF"   # azul del logo
AZUL_DEEP   = "#0079C8"
AZUL_LT     = "#66C6FF"
AZUL_PALE   = "#CCEBFF"
AZUL_BG     = "#EDF7FF"
TINTA       = "#052E4A"   # azul noche: barra lateral y titulares
TINTA_SOFT  = "#0B4067"
NARANJA     = "#F28F17"   # acento del eslogan
NARANJA_LT  = "#FDEBD2"

# Roles de superficie (tema claro, como la marca)
BG      = "#F7FBFF"
SURF    = "#FFFFFF"
SURF2   = "#F1F8FE"
BORDER  = "#DCEAF5"
TEXT    = TINTA
MUTED   = "#6C8298"
DIM     = "#9FB4C6"

# Semánticos
GOOD  = "#12A575"
WARN  = "#E8A317"
BAD   = "#E0503F"
INFO  = "#5D6FE0"
GREEN, AMBER, RED, SKY = GOOD, WARN, BAD, AZUL
MORADO = "#7C5CE0"
TEAL   = "#12B5B0"

PALETTE = [AZUL, TINTA, NARANJA, TEAL, MORADO, AZUL_LT, GOOD, "#B0C4D4"]
PALETTE_PAIS = {"Colombia": AZUL, "México": TINTA, "Ecuador": NARANJA,
                "Perú": TEAL, "Uruguay": MORADO, "Chile": AZUL_LT}

_ASSETS = Path(__file__).parent.parent / "assets"
_DATA = Path(__file__).parent.parent / "data"

BANDERAS = {"Colombia": "bandera_co.png", "México": "bandera_mx.png",
            "Ecuador": "bandera_ec.png", "Perú": "bandera_pe.png",
            "Uruguay": "bandera_uy.png", "Chile": "bandera_cl.png"}


def leer_csv(nombre: str, **kw) -> pd.DataFrame:
    """Lee un archivo de data/, esté comprimido (.csv.gz) o no."""
    kw.setdefault("low_memory", False)
    for candidato in (_DATA / nombre, _DATA / f"{nombre}.gz"):
        if candidato.exists():
            return pd.read_csv(candidato, **kw)
    raise FileNotFoundError(f"No se encontró {nombre} en {_DATA}")


def asset_b64(nombre: str) -> str:
    """Devuelve un asset de marca como data URI listo para <img src=...>."""
    ruta = _ASSETS / nombre
    if not ruta.exists():
        return ""
    mime = "image/svg+xml" if ruta.suffix == ".svg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(ruta.read_bytes()).decode()}"


# ── Formato de cifras ────────────────────────────────────────────────────────
def usd(v, decimals=1) -> str:
    """Dólares: US$12,4M · US$856K. La moneda de reporte del grupo."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    s = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000_000:
        return f"{s}US${v/1_000_000_000:,.{decimals}f}B"
    if v >= 1_000_000:
        return f"{s}US${v/1_000_000:,.{decimals}f}M"
    if v >= 1_000:
        return f"{s}US${v/1_000:,.{decimals}f}K"
    return f"{s}US${v:,.0f}"


def cop(v, decimals=1) -> str:
    """Pesos colombianos: $1,2 B · $456 M · $12,3 K"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    s = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000_000_000:
        return f"{s}${v/1_000_000_000_000:,.{decimals}f} B"
    if v >= 1_000_000_000:
        return f"{s}${v/1_000_000_000:,.{decimals}f} MM"
    if v >= 1_000_000:
        return f"{s}${v/1_000_000:,.{decimals}f} M"
    if v >= 1_000:
        return f"{s}${v/1_000:,.0f} K"
    return f"{s}${v:,.0f}"


def num(v, decimals=0) -> str:
    try:
        return f"{float(v):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def miles(v) -> str:
    """Enteros grandes en forma corta: 1,2 M · 305 K · 8.420"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:,.2f} M"
    if abs(v) >= 100_000:
        return f"{v/1_000:,.0f} K"
    return f"{v:,.0f}"


def pct(v, decimals=1) -> str:
    try:
        return f"{float(v):.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def mes_es(m: str) -> str:
    """'2026-08' → 'ago 2026'"""
    n = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]
    try:
        a, b = m.split("-")
        return f"{n[int(b)-1]} {a}"
    except Exception:
        return m


# ── Plotly ───────────────────────────────────────────────────────────────────
def light(fig: go.Figure, height: int = 340, title: str = "") -> go.Figure:
    """Tema claro de Siigo para una figura de Plotly.

    La leyenda nunca va arriba: a esa altura pelea el mismo espacio que el
    título y lo termina tapando en cuanto hay más de dos series. Va debajo
    (barras y líneas) o a la derecha (donas), con margen reservado a propósito.
    """
    is_pie = any(getattr(tr, "type", None) == "pie" for tr in fig.data)
    n_cat = 0
    n_entries = 0
    for tr in fig.data:
        if getattr(tr, "type", None) == "pie":
            labels = tr.labels
            n_entries += len(labels) if labels is not None else 0
        elif getattr(tr, "name", None):
            n_entries += 1
    show_legend = is_pie or n_entries > 1

    if is_pie:
        legend = dict(orientation="v", x=1.02, y=0.5, xanchor="left",
                      yanchor="middle", font=dict(color=MUTED, size=11))
        margin = dict(l=6, r=140, t=44 if title else 16, b=16)
    else:
        # Cuánto espacio se comen las etiquetas del eje X. Con series de 24 meses
        # ("sep 2024") Plotly las rota 45°, y entonces ocupan alto, no ancho: si
        # no se reserva ese alto, la leyenda horizontal se les monta encima.
        etiquetas = []
        for tr in fig.data:
            xs = getattr(tr, "x", None)
            if xs is not None:
                etiquetas += [str(v) for v in xs if isinstance(v, str)]
        largo = max((len(e) for e in etiquetas), default=0)
        n_cat = len(set(etiquetas))
        alto_ticks = int(min(58, largo * 5.6)) if largo > 4 else 0

        if show_legend:
            rows = 1 if n_entries <= 4 else (2 if n_entries <= 8 else 3)
            base_b = 46 + 26 * rows + alto_ticks
            legend = dict(orientation="h",
                          y=-0.20 - 0.11 * (rows - 1) - alto_ticks / 420,
                          x=0.5, xanchor="center", yanchor="top",
                          font=dict(color=MUTED, size=11))
        else:
            base_b = 20 + alto_ticks
            legend = dict()
        margin = dict(l=6, r=30, t=44 if title else 16, b=base_b)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TINTA,
                                         family="Poppins, sans-serif"),
                   x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, -apple-system, system-ui, sans-serif",
                  color=MUTED, size=12),
        height=height, margin=margin, legend=legend, showlegend=show_legend,
        hovermode="x unified", colorway=PALETTE,
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER, tickfont=dict(color=MUTED))
    if not is_pie and n_cat > 14:
        # Con más de catorce categorías se muestran ~9 marcas: se lee mejor una
        # serie con menos etiquetas que una con todas amontonadas y rotadas.
        fig.update_xaxes(nticks=9)
    fig.update_yaxes(gridcolor="#E9F3FB", zeroline=False, tickfont=dict(color=MUTED))
    fig.update_traces(cliponaxis=False, selector=dict(type="bar"))
    return fig


dark = light  # alias retro-compatible


# ── Componentes de UI ────────────────────────────────────────────────────────
def kpi(label: str, value: str, delta: str = "", delta_good: bool = True,
        icon: str = "", ayuda: str = "") -> str:
    """Tarjeta de KPI. `ayuda` explica en una línea cómo leer el indicador."""
    color = GOOD if delta_good else BAD
    delta_html = (f'<p style="font-size:12px;font-weight:700;color:{color};'
                  f'margin:5px 0 0">{delta}</p>' if delta else "")
    icon_html = (f'<div style="font-size:19px;margin-bottom:6px;line-height:1">'
                 f'{icon}</div>' if icon else "")
    ayuda_html = (f'<p style="font-size:10.5px;color:{MUTED};margin:7px 0 0;'
                  f'line-height:1.4">{ayuda}</p>' if ayuda else "")
    return f"""
    <div style="background:{SURF};border:1px solid {BORDER};border-radius:14px;
      padding:15px 16px;height:100%;box-shadow:0 1px 3px rgba(5,46,74,.05)">
      {icon_html}
      <p style="font-size:10px;letter-spacing:.1em;text-transform:uppercase;
        color:{MUTED};margin:0;font-weight:700">{label}</p>
      <p style="font-size:24px;font-weight:800;color:{TINTA};margin:5px 0 0;
        letter-spacing:-.6px;line-height:1.15">{value}</p>
      {delta_html}{ayuda_html}
    </div>"""


def panel(titulo: str, cuerpo_html: str, icono: str = "", tono: str = "azul") -> str:
    """Panel de lectura del dato: qué dice y qué habría que decidir."""
    borde = {"azul": AZUL_PALE, "alerta": "#F6C8C0", "ok": "#B9E5D3",
             "naranja": "#F8DDB4"}.get(tono, AZUL_PALE)
    fondo = {"azul": AZUL_BG, "alerta": "#FDF1EF", "ok": "#EDF9F4",
             "naranja": "#FEF6EA"}.get(tono, AZUL_BG)
    return f"""
    <div style="background:{fondo};border:1px solid {borde};border-radius:14px;
      padding:16px 19px;margin:6px 0 2px">
      <p style="font-size:13px;font-weight:800;color:{TINTA};margin:0 0 8px">
        {icono} {titulo}</p>
      <div style="font-size:12.5px;color:#41627C;margin:0;line-height:1.72">
        {cuerpo_html}</div>
    </div>"""


def chip(texto: str, tono: str = "azul") -> str:
    c = {"azul": (AZUL_BG, AZUL_DEEP, AZUL_PALE),
         "ok": ("#EDF9F4", "#0B7C58", "#B9E5D3"),
         "alerta": ("#FDF1EF", "#B23A2C", "#F6C8C0"),
         "naranja": ("#FEF6EA", "#B26A0A", "#F8DDB4"),
         "neutro": (SURF2, MUTED, BORDER)}.get(tono, (AZUL_BG, AZUL_DEEP, AZUL_PALE))
    return (f'<span style="display:inline-block;background:{c[0]};color:{c[1]};'
            f'border:1px solid {c[2]};border-radius:999px;padding:3px 11px;'
            f'font-size:11px;font-weight:700;margin:2px 4px 2px 0">{texto}</span>')


def semaforo(valor: float, bueno: float, malo: float, invertido: bool = False) -> str:
    """Devuelve un color según el umbral. `invertido`: menos es mejor."""
    if invertido:
        return GOOD if valor <= bueno else (WARN if valor <= malo else BAD)
    return GOOD if valor >= bueno else (WARN if valor >= malo else BAD)


def estado_color(estado: str) -> str:
    m = {"Activo": GOOD, "En riesgo": WARN, "Cancelado": BAD, "Moroso": BAD,
         "Trial": INFO, "Nuevo": AZUL, "Reactivado": TEAL,
         "Aceptado": GOOD, "Rechazado": BAD, "Pendiente": WARN,
         "Resuelto": GOOD, "Abierto": WARN, "Escalado": BAD,
         "Migrado": GOOD, "En migración": WARN, "Sin iniciar": MUTED}
    return m.get(estado, MUTED)


# ── Nube de marca (isotipo simplificado, para separadores y fondos) ──────────
def nube_svg(color: str = AZUL, ancho: int = 26, opacidad: float = 1.0) -> str:
    return (f'<svg width="{ancho}" height="{int(ancho*0.62)}" viewBox="0 0 42 26" '
            f'fill="none" style="opacity:{opacidad};vertical-align:middle">'
            f'<path d="M33.2 25.5H9.6C4.3 25.5 0 21.3 0 16.1c0-4.8 3.6-8.8 8.4-9.4'
            f'C10.3 2.7 14.5 0 19.2 0c5.7 0 10.5 3.9 11.7 9.2 5.2.3 9.1 4.4 9.1 9.4'
            f'-.1 3.9-3 6.9-6.8 6.9z" fill="{color}"/></svg>')


CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap');
  html, body, [class*="css"] {{ font-family:'Poppins',-apple-system,system-ui,sans-serif; }}
  .stApp {{ background:{BG}; color:{TEXT}; }}

  section[data-testid="stSidebar"] {{
      background:linear-gradient(180deg,{TINTA} 0%,#03243A 100%); border-right:none; }}
  section[data-testid="stSidebar"] * {{ color:#D6E7F3; }}
  section[data-testid="stSidebar"] .stButton button {{
      background:rgba(255,255,255,.05); color:#D6E7F3 !important;
      border:1px solid rgba(0,157,255,.18); border-radius:11px;
      text-align:left; font-weight:600; font-size:12.5px; padding:7px 12px;
      transition:all .15s ease; }}
  section[data-testid="stSidebar"] .stButton button:hover {{
      background:{AZUL}2E; border-color:{AZUL}; color:#fff !important; }}

  .block-container {{ padding-top:1.5rem !important; max-width:1500px; }}
  h1,h2,h3,h4 {{ color:{TINTA} !important; font-family:'Poppins',sans-serif !important;
      font-weight:700 !important; letter-spacing:-.3px; }}
  div[data-testid="stMetricValue"] {{ color:{TINTA}; }}

  .stDataFrame {{ border-radius:12px; overflow:hidden; border:1px solid {BORDER}; }}
  thead tr th {{ background:{AZUL_BG} !important; color:{TINTA} !important;
      font-size:11px !important; text-transform:uppercase; letter-spacing:.05em;
      font-weight:700 !important; }}
  tbody tr:hover td {{ background:{SURF2} !important; }}

  div[data-baseweb="select"] > div {{ background:{SURF} !important;
      border-color:{BORDER} !important; border-radius:10px !important; }}
  div[data-baseweb="select"] span {{ color:{TINTA} !important; }}
  .stMultiSelect span[data-baseweb="tag"] {{ background:{AZUL} !important; color:#fff !important; }}
  .stMultiSelect span[data-baseweb="tag"] span {{ color:#fff !important;
      -webkit-text-fill-color:#fff !important; }}
  button[kind="primary"] {{ background:{AZUL} !important; border:none !important;
      border-radius:11px !important; font-weight:600 !important; }}

  .stTabs [data-baseweb="tab"] {{ background:{SURF2}; border-radius:11px 11px 0 0;
      font-weight:600; color:{MUTED}; font-size:13px; }}
  .stTabs [aria-selected="true"] {{ background:{SURF} !important; color:{TINTA} !important;
      border-bottom:2px solid {AZUL}; }}
  div[data-testid="stExpander"] {{ border:1px solid {BORDER} !important;
      background:{SURF} !important; border-radius:13px !important; }}
  div[data-testid="stExpander"] summary {{ font-weight:700; color:{TINTA} !important; }}
  label, .stSelectbox label, .stSlider label {{ color:{MUTED} !important;
      font-weight:600 !important; font-size:12px !important; }}
  hr {{ border-color:{BORDER}; }}
  .stProgress > div > div > div > div {{ background:{AZUL}; }}
</style>
"""

HEADER_CSS = f"""
<style>
  .sg-header {{ display:flex;align-items:center;gap:16px;padding:2px 0 }}
  .sg-logo {{ height:40px;width:auto }}
  .sg-title {{ font-size:22px;font-weight:800;color:{TINTA};letter-spacing:-.5px;line-height:1.15 }}
  .sg-sub {{ font-size:12.5px;color:{MUTED};margin-top:3px;font-weight:500 }}
  .sg-rule {{ height:3px;border-radius:99px;
      background:linear-gradient(90deg,{AZUL} 0%,{AZUL_LT} 42%,{NARANJA} 72%,transparent);
      margin:13px 0 20px }}
  .sg-eyebrow {{ font-size:10px;font-weight:800;letter-spacing:.16em;
      text-transform:uppercase;color:{AZUL};margin-bottom:2px }}
</style>
"""


def encabezado(titulo: str, subtitulo: str, eyebrow: str = "Panel de negocio") -> str:
    """Encabezado de módulo con el logo real de Siigo."""
    logo = asset_b64("logo_azul.svg")
    logo_html = (f'<img src="{logo}" class="sg-logo" alt="Siigo">' if logo
                 else f'<div class="sg-title">Siigo</div>')
    return f"""
    <div class="sg-header">
      {logo_html}
      <div style="border-left:2px solid {AZUL_PALE};padding-left:16px">
        <div class="sg-eyebrow">{eyebrow}</div>
        <div class="sg-title">{titulo}</div>
        <div class="sg-sub">{subtitulo}</div>
      </div>
      <div style="margin-left:auto;display:flex;gap:5px;align-items:center">
        {nube_svg(AZUL_PALE, 34)}{nube_svg(AZUL_LT, 24)}{nube_svg(AZUL, 16)}
      </div>
    </div><div class="sg-rule"></div>"""
