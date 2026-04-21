"""
app.py
Página principal (Home). Solo UI.
La navegación multipágina la maneja Streamlit automáticamente
detectando la carpeta pages/.
"""

import streamlit as st
from mongo_dao import MongoDAO

st.set_page_config(
    page_title="Accidentalidad Barranquilla",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  ESTILOS GLOBALES                                                    #
# ------------------------------------------------------------------ #
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1c2128 0%, #21262d 100%);
        border: 1px solid #30363d; border-radius: 12px; padding: 16px 20px;
    }
    div[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.1em; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0883e !important; font-size: 2rem !important; font-weight: 700; }
    h1, h2, h3 { color: #e6edf3 !important; }
    hr { border-color: #30363d; }
    .stButton > button { background: linear-gradient(135deg, #f0883e, #d29922); color: #0d1117; border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1.5rem; }
    .nav-card { background: linear-gradient(135deg, #1c2128, #21262d); border: 1px solid #30363d; border-radius: 16px; padding: 1.5rem 2rem; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center; gap: 0.5rem; }
    .nav-card .icon { font-size: 2.5rem; }
    .nav-card h3 { margin: 0 !important; font-size: 1.1rem !important; }
    .nav-card p { color: #8b949e; margin: 0; font-size: 0.85rem; }
    .hero { background: linear-gradient(135deg, #161b22 0%, #1c2128 60%, #0d1117 100%); border: 1px solid #30363d; border-left: 5px solid #f0883e; border-radius: 16px; padding: 3rem 3rem 2.5rem; margin-bottom: 2.5rem; }
    .hero h1 { font-size: 2.8rem !important; font-weight: 700; background: linear-gradient(90deg, #f0883e, #d29922); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem !important; }
    .hero p { color: #8b949e; font-size: 1rem; max-width: 600px; }
    .badge { display: inline-block; background: #21262d; border: 1px solid #30363d; border-radius: 20px; padding: 0.2rem 0.8rem; font-size: 0.75rem; color: #8b949e; margin-right: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  CONEXIÓN A MONGO                                                    #
# ------------------------------------------------------------------ #
@st.cache_resource(show_spinner=False)
def obtener_dao():
    return MongoDAO()

try:
    dao = obtener_dao()
    resumen = dao.resumen_coleccion()
    mongo_ok = True
except Exception:
    mongo_ok = False
    resumen = {}

# ------------------------------------------------------------------ #
#  HERO                                                                #
# ------------------------------------------------------------------ #
st.markdown("""
<div class="hero">
    <h1>🚦 Accidentalidad en Barranquilla</h1>
    <p>
        Dashboard interactivo de accidentes de tránsito en el Distrito de Barranquilla.
        Datos extraídos desde la API de Datos Abiertos Colombia,
        almacenados en MongoDB Atlas y visualizados con Streamlit y Plotly.
    </p>
    <br>
    <span class="badge">📡 API REST</span>
    <span class="badge">🍃 MongoDB Atlas</span>
    <span class="badge">📊 Plotly</span>
    <span class="badge">🐍 Python</span>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  KPIs                                                                #
# ------------------------------------------------------------------ #
if mongo_ok and resumen.get("total_documentos", 0) > 0:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Registros en BD", f"{resumen['total_documentos']:,}")
    c2.metric("📅 Años cubiertos", resumen["anios_cubiertos"])
    c3.metric("🤕 Total heridos", f"{resumen['total_heridos']:,}")
    c4.metric("💀 Total muertos", f"{resumen['total_muertos']:,}")
else:
    st.warning("⚠️ No hay datos aún. Ve a la página **📡 API** para cargar los datos.")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  TARJETAS DE NAVEGACIÓN                                              #
# ------------------------------------------------------------------ #
st.markdown("### 🗺️ Navega por la aplicación")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""<div class="nav-card"><div class="icon">📡</div><h3>API</h3><p>Consulta la API REST de datos.gov.co y carga los datos en MongoDB</p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="nav-card"><div class="icon">🍃</div><h3>MongoDB</h3><p>Explora los documentos almacenados en MongoDB Atlas</p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="nav-card"><div class="icon">📊</div><h3>Gráficos</h3><p>Visualizaciones interactivas con filtros por año, gravedad y tipo</p></div>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  FLUJO                                                               #
# ------------------------------------------------------------------ #
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### ⚙️ Flujo de datos")
st.markdown("""
<div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:1.5rem 2rem;">
    <p style="color:#8b949e;margin:0;font-size:0.95rem;text-align:center;">
        <span style="color:#f0883e;font-weight:600;">datos.gov.co API REST</span>
        &nbsp;→&nbsp;<span style="color:#e6edf3;">extractor.py</span>
        &nbsp;→&nbsp;<span style="color:#3fb950;font-weight:600;">MongoDB Atlas</span>
        &nbsp;→&nbsp;<span style="color:#e6edf3;">transformers.py</span>
        &nbsp;→&nbsp;<span style="color:#79c0ff;font-weight:600;">Gráficos Plotly</span>
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>")
st.markdown("<small style='color:#8b949e'>Fuente: Secretaría de Tránsito de Barranquilla · datos.gov.co · Actualización automática cada 24h</small>", unsafe_allow_html=True)
