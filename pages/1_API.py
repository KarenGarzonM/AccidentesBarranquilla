"""
pages/1_API.py
Página de API: muestra el JSON de datos.gov.co como tabla
y permite recargar los datos en MongoDB (borra todo y vuelve a insertar).
"""

import streamlit as st
import requests
import pandas as pd

from config.settings import settings
from data.extractors.api_extractor import recargar_todos_los_datos
from core.scheduler import iniciar_scheduler
from ui.styles import apply_global_styles

st.set_page_config(page_title="API · Accidentalidad", page_icon="📡", layout="wide")

apply_global_styles()

# Scheduler
if "scheduler_iniciado" not in st.session_state:
    iniciar_scheduler()
    st.session_state["scheduler_iniciado"] = True

API_URL = settings.api_url

st.markdown("## Extraccion de Datos")

st.markdown(f"""
<div class="info-box">
    <p>
        <strong style="color:#e6edf3;">Descripcion:</strong> Consume los datos de la API publica de Datos Abiertos Colombia
        <br>
        <strong style="color:#e6edf3;">Endpoint:</strong>
        <a href="{API_URL}" target="_blank">{API_URL}</a>
        <br>
        <strong style="color:#e6edf3;">Dataset:</strong> Accidentalidad en Barranquilla
        <br>
        <strong style="color:#e6edf3;">Formato:</strong> JSON · Paginación mediante <code>$limit</code> y <code>$offset</code>
        <br><br>
        Este endpoint permite acceder a datos abiertos oficiales relacionados con la accidentalidad vial en Barranquilla.
        <br>
        La estructura paginada facilita la extracción eficiente de grandes volúmenes de información, 
        lo cual es clave para su posterior procesamiento y análisis.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ------------------------------------------------------------------ #
#  PREVISUALIZACIÓN DE LA API                                          #
# ------------------------------------------------------------------ #
st.markdown("### 🔍 Previsualización - Últimos registros de la API")

col_limit, col_btn = st.columns([2, 1])
with col_limit:
    limite = st.slider("Cantidad de registros a previsualizar", min_value=10, max_value=200, value=50, step=10)

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    consultar = st.button("Consultar API", use_container_width=True)

if consultar or "api_preview" in st.session_state:
    if consultar:
        with st.spinner("Consultando la API..."):
            try:
                resp = requests.get(API_URL, params={"$limit": limite, "$order": "fecha_accidente DESC"}, timeout=30)
                resp.raise_for_status()
                datos = resp.json()
                st.session_state["api_preview"] = datos
            except Exception as e:
                st.error(f"Error al consultar la API: {e}")
                datos = []
    else:
        datos = st.session_state.get("api_preview", [])

    if datos:
        df = pd.DataFrame(datos)

        m1, m2, m3 = st.columns(3)
        m1.metric("Registros obtenidos", len(df))
        m2.metric("Columnas", len(df.columns))
        m3.metric("Fuente", "datos.gov.co")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📋 Datos en tabla")

        cols_orden = [
            "fecha_accidente", "hora_accidente", "gravedad_accidente",
            "clase_accidente", "sitio_exacto_accidente",
            "cant_heridos_en_sitio_accidente", "cant_muertos_en_sitio_accidente",
            "cantidad_accidentes", "a_o_accidente", "mes_accidente", "dia_accidente",
        ]
        cols_mostrar = [c for c in cols_orden if c in df.columns]
        cols_extra = [c for c in df.columns if c not in cols_mostrar]
        df_mostrar = df[cols_mostrar + cols_extra]

        st.dataframe(
            df_mostrar,
            use_container_width=True,
            height=450,
            column_config={
                "fecha_accidente": st.column_config.TextColumn("Fecha"),
                "hora_accidente": st.column_config.TextColumn("Hora"),
                "gravedad_accidente": st.column_config.TextColumn("Gravedad"),
                "clase_accidente": st.column_config.TextColumn("Clase"),
                "sitio_exacto_accidente": st.column_config.TextColumn("Sitio"),
                "cant_heridos_en_sitio_accidente": st.column_config.NumberColumn("Heridos"),
                "cant_muertos_en_sitio_accidente": st.column_config.NumberColumn("Muertos"),
                "cantidad_accidentes": st.column_config.NumberColumn("Cantidad"),
                "a_o_accidente": st.column_config.NumberColumn("Año"),
                "mes_accidente": st.column_config.TextColumn("Mes"),
                "dia_accidente": st.column_config.TextColumn("Día"),
            }
        )

st.markdown("---")

# ------------------------------------------------------------------ #
#  RECARGA COMPLETA EN MONGODB                                         #
# ------------------------------------------------------------------ #
st.markdown("### 🍃 Transferencia de datos a MongoDB Atlas")

st.markdown("""
<div class="warning-box">
    <p>
        <strong>⚠️ Este proceso elimina TODOS los documentos existentes</strong> en MongoDB
        <br>
        Re-inserta los datos frescos de la API. Úsalo para sincronizar completamente
        sin duplicados. La operación puede tardar varios minutos.
    </p>
</div>
""", unsafe_allow_html=True)

col_carga1, col_carga2 = st.columns([1, 2])
with col_carga1:
    cargar = st.button("Eliminar y recargar desde API", use_container_width=True)

if cargar:
    barra = st.progress(0, text="Descargando datos de la API...")
    estado = st.empty()

    def actualizar_progreso(total_descargados: int):
        barra.progress(min(int((total_descargados / 20000) * 90), 90),
                       text=f"Descargados {total_descargados:,} registros...")

    try:
        estado.info("⬇️ Paso 1/3 — Descargando todos los registros de la API...")
        total = recargar_todos_los_datos(callback=actualizar_progreso)
        barra.progress(100, text="¡Completado!")
        estado.empty()
        st.success(f"✅ **{total:,} registros** cargados en MongoDB Atlas. Colección actualizada desde cero.")
        st.balloons()
    except Exception as e:
        barra.empty()
        st.error(f"Error durante la recarga: {e}")

st.markdown(
    "<small style='color:#8b949e'>La actualización automática ocurre cada 24 horas via APScheduler.</small>",
    unsafe_allow_html=True,
)