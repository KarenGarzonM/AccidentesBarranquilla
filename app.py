"""
app.py

Entry point de la aplicación Streamlit.
Solo orquesta: configura la página, conecta los módulos
y delega el renderizado a ui/.

La navegación multipágina la maneja Streamlit automáticamente
detectando la carpeta pages/.
"""

import streamlit as st

from config.settings import settings
from data.mongo_client import get_collection
from data.repositories.accidentes_repo import resumen_coleccion
from ui.styles import apply_global_styles
from ui.components.metrics import (
    render_kpis_principales,
    render_sin_datos,
    render_estado_conexion,
)

# ── Configuración de página ────────────────────────────────────────────────

st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()

# ── Conexión a MongoDB ─────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _get_col():
    return get_collection()


try:
    col      = _get_col()
    resumen  = resumen_coleccion(col)
    mongo_ok = True
except Exception:
    mongo_ok = False
    resumen  = {}

render_estado_conexion(mongo_ok, resumen.get("total_documentos", 0))

# ── Hero ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <h1>Accidentalidad en Barranquilla</h1>
  <p>
    Este dashboard interactivo presenta un análisis exploratorio de los accidentes de tránsito en la ciudad de Barranquilla, 
    construido a partir de datos oficiales obtenidos desde la API de Datos Abiertos Colombia. 
    La información es procesada y almacenada en MongoDB Atlas, y posteriormente visualizada mediante herramientas como Streamlit y Plotly.
    <br><br>
    Cada punto representado en el mapa corresponde a un evento real, lo que permite dimensionar la magnitud del fenómeno 
    y comprender su distribución espacial y temporal. A través de esta herramienta, es posible identificar patrones de accidentalidad 
    según variables como la hora, la ubicación y el año, aportando una perspectiva analítica sobre la dinámica del tránsito en la ciudad.
  </p>
  <br>
  <span class="badge">📡 API REST</span>
  <span class="badge">🍃 MongoDB Atlas</span>
  <span class="badge">📊 Plotly</span>
  <span class="badge">🐍 Python</span>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────────

if mongo_ok and resumen.get("total_documentos", 0) > 0:
    render_kpis_principales(resumen)
else:
    render_sin_datos()

st.markdown("<br>", unsafe_allow_html=True)

# ── Tarjetas de navegación ─────────────────────────────────────────────────

st.markdown("### 🗺️ Navegación de la aplicación")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">📡</div>
      <h3>API</h3>
      <p>Accede a los datos abiertos de datos.gov.co mediante una API REST.
        En esta sección se realiza la extracción y carga inicial de la información hacia la base de datos.
      </p>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">🍃</div>
      <h3>MongoDB</h3>
      <p>Explora los documentos almacenados en MongoDB Atlas,
        comprendiendo la estructura y organización de los datos recolectados.
      </p>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">📊</div>
      <h3>Gráficos</h3>
      <p>Analiza los datos mediante gráficos interactivos,
        aplicando filtros por año, nivel de gravedad y tipo de accidente
        para identificar patrones relevantes
      </p>
    </div>""", unsafe_allow_html=True)

# ── Flujo de datos ─────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### ⚙️ Flujo de datos")
st.markdown("""
<div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:1.5rem 2rem;">
  <p style="color:#8b949e;margin:0;font-size:0.95rem;text-align:center;">
    <span style="color:#f0883e;font-weight:600;">datos.gov.co API REST</span>
    &nbsp;→&nbsp;<span style="color:#e6edf3;">api_extractor.py</span>
    &nbsp;→&nbsp;<span style="color:#3fb950;font-weight:600;">MongoDB Atlas</span>
    &nbsp;→&nbsp;<span style="color:#e6edf3;">transformers.py</span>
    &nbsp;→&nbsp;<span style="color:#79c0ff;font-weight:600;">Gráficos Plotly</span>
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<small style='color:#8b949e'>"
    "<br>"
    "Este flujo representa el ciclo completo de los datos: desde su extracción en fuentes oficiales, "
    "pasando por procesos de almacenamiento y transformación, hasta su posterior análisis visual. "
    "<br>"
    "La información es actualizada automáticamente cada 24 horas, garantizando una visión consistente y reciente del fenómeno.<br>"
    "Fuente: Secretaría de Tránsito de Barranquilla · datos.gov.co"
    "</small>",
    unsafe_allow_html=True,
)