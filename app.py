import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from utils.formatters import (CSS, HEADER_CSS, asset_b64, nube_svg,
                              AZUL, AZUL_LT, AZUL_PALE, NARANJA, TINTA)
from utils.visitas import registrar_visita, panel_solicitado, render_panel_visitas

st.set_page_config(
    page_title="Siigo · Panel de Negocio | Calybrat",
    page_icon="☁️",
    layout="wide",
)

# El demo es de acceso libre: solo se deja constancia de la visita.
registrar_visita()

st.markdown(CSS + HEADER_CSS, unsafe_allow_html=True)

# Agrupado por la pregunta que responde, no por el área que lo produce.
GRUPOS = [
    ("Vista general", [
        ("🏠  Tablero Ejecutivo",          "p01_dashboard"),
    ]),
    ("Ingresos", [
        ("📈  ARR y Puente de Ingresos",   "p02_arr"),
        ("🔁  Retención, Fuga y Cohortes", "p03_retencion"),
        ("🎯  Adquisición y Unit Economics", "p04_adquisicion"),
        ("🧩  Planes, Precios y Módulos",  "p05_planes"),
    ]),
    ("Canal y mercados", [
        ("🧮  Canal de Contadores",        "p06_contadores"),
        ("🌎  Expansión Regional",         "p07_paises"),
        ("🇲🇽  Migración Aspel → Nube",     "p12_aspel"),
    ]),
    ("Producto y operación", [
        ("💡  Uso del Producto y Adopción", "p08_uso"),
        ("🧾  Facturación Electrónica y DIAN", "p09_dian"),
        ("⚙️  Plataforma y Confiabilidad", "p10_plataforma"),
        ("🎧  Soporte y Experiencia",      "p11_soporte"),
    ]),
    ("Dirección", [
        ("💰  Finanzas y Regla del 40",    "p13_finanzas"),
        ("📄  Reportes Automáticos",       "p14_reportes"),
        ("🤖  Agente IA Siigo",            "p15_agente"),
    ]),
]
PAGES = {label: mod for _, items in GRUPOS for label, mod in items}

with st.sidebar:
    logo = asset_b64("logo_blanco.svg")
    logo_html = (f'<img src="{logo}" style="height:46px;width:auto" alt="Siigo">'
                 if logo else
                 '<div style="font-size:24px;font-weight:900;color:#fff">Siigo</div>')
    st.markdown(f"""
    <div style="padding:14px 4px 4px">
      {logo_html}
      <div style="font-size:9.5px;color:{AZUL_LT};margin-top:10px;font-weight:800;
        letter-spacing:.16em;text-transform:uppercase">Panel de negocio</div>
      <div style="font-size:10.5px;color:#7EA0B8;margin-top:3px">
        6 países · corte 31 ago 2026</div>
      <div style="height:3px;border-radius:99px;margin:13px 0 2px;
        background:linear-gradient(90deg,{AZUL} 0%,{AZUL} 48%,{AZUL_LT} 48%,
        {AZUL_LT} 74%,{NARANJA} 74%,{NARANJA} 88%,transparent)"></div>
    </div>
    """, unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = list(PAGES.keys())[0]

    for grupo, items in GRUPOS:
        st.markdown(
            f'<div style="font-size:9px;font-weight:800;letter-spacing:.17em;'
            f'text-transform:uppercase;color:#5F8AA8;margin:15px 0 5px 4px">{grupo}</div>',
            unsafe_allow_html=True)
        for label, _mod in items:
            if st.button(label, key=f"nav_{label}", width="stretch"):
                st.session_state.page = label

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:16px 16px 10px;text-align:center;
      border-top:1px solid rgba(255,255,255,.10)">
      <div style="margin-bottom:9px;opacity:.85">
        {nube_svg(AZUL_LT, 30)}{nube_svg(AZUL, 20)}
      </div>
      <div style="font-size:10.5px;color:#5F8AA8;margin-bottom:2px">Construido por</div>
      <div style="font-size:15px;font-weight:900;color:#fff;letter-spacing:.4px">Calybrat</div>
      <div style="font-size:9.5px;color:#4E7590;margin-top:5px;line-height:1.55">
        © 2026 · Demo con datos simulados<br>anclados a cifras públicas de Siigo
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Panel interno de accesos (solo con ?accesos=… en la URL) ──────────────────
if panel_solicitado():
    render_panel_visitas()
    st.stop()

# ── Módulo activo ─────────────────────────────────────────────────────────────
module_name = PAGES[st.session_state.page]
try:
    mod = __import__(f"modules.{module_name}", fromlist=[module_name])
    mod.render()
except Exception as e:
    st.error(f"Error cargando módulo: {e}")
    import traceback
    st.code(traceback.format_exc())
