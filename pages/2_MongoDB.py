"""
pages/2_MongoDB.py
Página de MongoDB: explora los documentos almacenados en Atlas.
Paginación y filtros reales en el servidor (no sobre la página actual).
"""

import streamlit as st
import pandas as pd
from mongo_dao import MongoDAO

st.set_page_config(page_title="MongoDB · Accidentalidad", page_icon="🍃", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3 { color: #e6edf3 !important; }
    .stButton > button { background: linear-gradient(135deg, #f0883e, #d29922); color: #0d1117; border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1.5rem; }
    div[data-testid="metric-container"] { background: linear-gradient(135deg, #1c2128, #21262d); border: 1px solid #30363d; border-radius: 12px; padding: 16px 20px; }
    div[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem !important; text-transform: uppercase; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #3fb950 !important; font-size: 2rem !important; font-weight: 700; }
    .mongo-badge { display: inline-block; background: #1a3a1a; border: 1px solid #3fb950; border-radius: 20px; padding: 0.2rem 0.8rem; font-size: 0.8rem; color: #3fb950; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  CONEXIÓN                                                            #
# ------------------------------------------------------------------ #
@st.cache_resource(show_spinner=False)
def obtener_dao():
    return MongoDAO()

try:
    dao = obtener_dao()
except Exception as e:
    st.error(f"Error de conexión a MongoDB: {e}")
    st.stop()

# ------------------------------------------------------------------ #
#  ENCABEZADO                                                          #
# ------------------------------------------------------------------ #
st.markdown("## 🍃 MongoDB Atlas — Colección de accidentes")
st.markdown("<span class='mongo-badge'>● Conectado a MongoDB Atlas</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  RESUMEN DE LA COLECCIÓN                                             #
# ------------------------------------------------------------------ #
resumen = dao.resumen_coleccion()

if resumen["total_documentos"] == 0:
    st.warning("⚠️ La colección está vacía. Ve a la página **📡 API** para cargar datos.")
    st.stop()

st.markdown("### 📊 Resumen de la colección")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total documentos", f"{resumen['total_documentos']:,}")
c2.metric("Años cubiertos", resumen["anios_cubiertos"])
c3.metric("Total heridos acum.", f"{resumen['total_heridos']:,}")
c4.metric("Total muertos acum.", f"{resumen['total_muertos']:,}")

st.markdown("---")

# ------------------------------------------------------------------ #
#  FILTROS EN SIDEBAR                                                  #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## 🔍 Filtros MongoDB")
    st.markdown("---")

    anios = dao.obtener_anios_disponibles()
    anio_sel = st.selectbox("Filtrar por año", options=["Todos"] + [str(a) for a in anios])

    gravedades = dao.obtener_gravedades()
    gravedad_sel = st.selectbox("Filtrar por gravedad", options=["Todas"] + gravedades)

    por_pagina = st.select_slider("Registros por página", options=[25, 50, 100, 200], value=50)

# ------------------------------------------------------------------ #
#  EXPLORADOR DE DOCUMENTOS                                            #
# ------------------------------------------------------------------ #
st.markdown("### 🔎 Explorador de documentos")

# Contar con filtros reales en Mongo para calcular la paginación correcta
total_filtrado = dao.contar_con_filtros(
    anio=anio_sel if anio_sel != "Todos" else None,
    gravedad=gravedad_sel if gravedad_sel != "Todas" else None,
)
total_paginas = max(1, (total_filtrado + por_pagina - 1) // por_pagina)

col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
with col_pag2:
    pagina = st.number_input(
        f"Página (1 – {total_paginas:,})",
        min_value=1,
        max_value=total_paginas,
        value=1,
        step=1,
    ) - 1

# Obtener documentos con filtros reales aplicados en Mongo
with st.spinner("Cargando documentos..."):
    documentos = dao.obtener_documentos_paginados(
        pagina=pagina,
        por_pagina=por_pagina,
        anio=anio_sel if anio_sel != "Todos" else None,
        gravedad=gravedad_sel if gravedad_sel != "Todas" else None,
    )

if documentos:
    df = pd.DataFrame(documentos)

    st.markdown(
        f"<small style='color:#8b949e'>Mostrando {len(df)} documentos · "
        f"Página {pagina + 1} de {total_paginas:,} · "
        f"Total con filtros: {total_filtrado:,} · "
        f"Total en colección: {resumen['total_documentos']:,}</small>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    rename_map = {
        "fecha_accidente": "Fecha",
        "hora_accidente": "Hora",
        "gravedad_accidente": "Gravedad",
        "clase_accidente": "Clase",
        "sitio_exacto_accidente": "Sitio",
        "cant_heridos_en_sitio_accidente": "Heridos",
        "cant_muertos_en_sitio_accidente": "Muertos",
        "cantidad_accidentes": "Cantidad",
        "a_o_accidente": "Año",
        "mes_accidente": "Mes",
        "dia_accidente": "Día",
    }
    df_display = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "Fecha" in df_display.columns:
        df_display["Fecha"] = df_display["Fecha"].astype(str).str[:10]

    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        column_config={
            "Heridos": st.column_config.NumberColumn(format="%d"),
            "Muertos": st.column_config.NumberColumn(format="%d"),
            "Cantidad": st.column_config.NumberColumn(format="%d"),
            "Año": st.column_config.NumberColumn(format="%d"),
            "Gravedad": st.column_config.TextColumn(),
        }
    )

    st.markdown("<br>", unsafe_allow_html=True)
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar página como CSV",
        data=csv,
        file_name=f"accidentes_pagina_{pagina + 1}.csv",
        mime="text/csv",
    )
else:
    st.info("No hay documentos que coincidan con los filtros.")

st.markdown(
    "<small style='color:#8b949e'>Base de datos: MongoDB Atlas · Colección: accidentes · "
    "Ordenado por fecha descendente · Filtros aplicados en el servidor</small>",
    unsafe_allow_html=True,
)