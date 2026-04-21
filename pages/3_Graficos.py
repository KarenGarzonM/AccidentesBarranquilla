"""
pages/3_Graficos.py
Página de visualizaciones interactivas con Plotly.
"""

import streamlit as st
import plotly.express as px
from mongo_dao import MongoDAO
import transformers as tr

st.set_page_config(page_title="Gráficos · Accidentalidad", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    h1, h2, h3 { color: #e6edf3 !important; }
    div[data-testid="metric-container"] { background: linear-gradient(135deg, #1c2128, #21262d); border: 1px solid #30363d; border-radius: 12px; padding: 16px 20px; }
    div[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.75rem !important; text-transform: uppercase; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0883e !important; font-size: 2rem !important; font-weight: 700; }
    hr { border-color: #30363d; }
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
    st.error(f"Error de conexión: {e}")
    st.stop()

if dao.contar_total() == 0:
    st.warning("⚠️ No hay datos. Ve a la página **📡 API** para cargarlos.")
    st.stop()

# ------------------------------------------------------------------ #
#  SIDEBAR — FILTROS                                                   #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## 🔍 Filtros")
    st.markdown("---")

    anios_disponibles = dao.obtener_anios_disponibles()
    anios_sel = st.multiselect("Año(s)", options=anios_disponibles, default=anios_disponibles)

    gravedades_opciones = dao.obtener_gravedades()
    gravedades_sel = st.multiselect("Gravedad", options=gravedades_opciones, default=gravedades_opciones)

    tipos_opciones = dao.obtener_clases()
    tipos_sel = st.multiselect("Clase de accidente", options=tipos_opciones, default=tipos_opciones)

    st.markdown("---")
    st.markdown(f"<small style='color:#8b949e'>📦 {dao.contar_total():,} registros en BD</small>", unsafe_allow_html=True)

filtros = {
    "anios": anios_sel if anios_sel else None,
    "gravedad": gravedades_sel if gravedades_sel else None,
    "clase": tipos_sel if tipos_sel else None,
}

# Layout base para gráficos
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#8b949e",
    coloraxis_showscale=False,
    margin=dict(t=20, b=20),
    height=320,
)

# ------------------------------------------------------------------ #
#  ENCABEZADO                                                          #
# ------------------------------------------------------------------ #
st.markdown("## 📊 Visualizaciones — Accidentalidad Barranquilla")
st.markdown("---")

# ------------------------------------------------------------------ #
#  KPIs                                                                #
# ------------------------------------------------------------------ #
maximos = dao.maximos_victimas(filtros)
total_acc = sum(r["total"] for r in dao.accidentes_por_anio(filtros))
heridos_data = dao.accidentes_por_gravedad(filtros)
heridos_total = next((r["total"] for r in heridos_data if r["_id"] == "Con heridos"), 0)
muertos_total = next((r["total"] for r in heridos_data if r["_id"] == "Con muertos"), 0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total accidentes", f"{total_acc:,}")
c2.metric("Accidentes con heridos", f"{heridos_total:,}")
c3.metric("Máx. heridos en 1 accidente", maximos["max_heridos"])
c4.metric("Máx. muertos en 1 accidente", maximos["max_muertos"])

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  FILA 1: Por año + Por mes                                           #
# ------------------------------------------------------------------ #
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.markdown("### 📅 Accidentes por Año")
    df = tr.preparar_por_anio(dao.accidentes_por_anio(filtros))
    if not df.empty:
        fig = px.bar(df, x="Año", y="total", color="total",
                     color_continuous_scale=["#21262d", "#f0883e"],
                     labels={"total": "Accidentes"}, text="total")
        fig.update_traces(textposition="outside", textfont_color="#e6edf3")
        fig.update_layout(**LAYOUT,
                          xaxis=dict(showgrid=False, color="#8b949e"),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros seleccionados.")

with r1c2:
    st.markdown("### 📆 Accidentes por Mes")
    df = tr.preparar_por_mes(dao.accidentes_por_mes(filtros))
    if not df.empty:
        fig = px.line(df, x="Mes", y="total", markers=True,
                      labels={"total": "Accidentes"},
                      color_discrete_sequence=["#f0883e"])
        fig.update_traces(line_width=3, marker=dict(size=8, color="#d29922"))
        fig.update_layout(**LAYOUT,
                          xaxis=dict(showgrid=False, color="#8b949e", tickangle=-30),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros seleccionados.")

# ------------------------------------------------------------------ #
#  FILA 2: Por tipo (donut) + Por hora                                 #
# ------------------------------------------------------------------ #
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown("### 🥧 % de Accidentes por Tipo")
    df = tr.preparar_por_tipo(dao.accidentes_por_tipo(filtros))
    if not df.empty:
        fig = px.pie(df, names="Tipo", values="total", hole=0.55,
                     color_discrete_sequence=px.colors.sequential.Oranges_r)
        fig.update_traces(textinfo="percent+label", textfont_color="#e6edf3",
                          marker=dict(line=dict(color="#0d1117", width=2)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#8b949e",
                          showlegend=True, legend=dict(font=dict(color="#8b949e")),
                          margin=dict(t=20, b=20), height=340)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros seleccionados.")

with r2c2:
    st.markdown("### 🕐 Accidentes por Hora del Día")
    df = tr.preparar_por_hora(dao.accidentes_por_hora(filtros))
    if not df.empty:
        fig = px.bar(df, x="Etiqueta", y="total",
                     labels={"total": "Accidentes", "Etiqueta": "Hora"},
                     color="total",
                     color_continuous_scale=["#21262d", "#d29922", "#f0883e"])
        fig.update_layout(**LAYOUT, height=340,
                          xaxis=dict(showgrid=False, color="#8b949e", tickangle=-45),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros seleccionados.")

# ------------------------------------------------------------------ #
#  FILA 3: Gravedad + Día de semana                                    #
# ------------------------------------------------------------------ #
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.markdown("### ⚠️ Distribución por Gravedad")
    df = tr.preparar_por_gravedad(dao.accidentes_por_gravedad(filtros))
    if not df.empty:
        colores_grav = {"Con muertos": "#f85149", "Con heridos": "#f0883e", "Solo daños": "#3fb950"}
        fig = px.bar(df, x="total", y="Gravedad", orientation="h",
                     color="Gravedad", color_discrete_map=colores_grav,
                     labels={"total": "Accidentes"}, text="total")
        fig.update_traces(textposition="outside", textfont_color="#e6edf3")
        fig.update_layout(**LAYOUT, height=280, showlegend=False,
                          xaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"),
                          yaxis=dict(showgrid=False, color="#8b949e"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros seleccionados.")

with r3c2:
    st.markdown("### 📊 Accidentes por Día de Semana")
    df = tr.preparar_por_dia(dao.accidentes_por_dia_semana(filtros))
    if not df.empty:
        fig = px.bar(df, x="Día", y="total", color="total",
                     color_continuous_scale=["#21262d", "#f0883e"],
                     labels={"total": "Accidentes"}, text="total")
        fig.update_traces(textposition="outside", textfont_color="#e6edf3")
        fig.update_layout(**LAYOUT, height=280,
                          xaxis=dict(showgrid=False, color="#8b949e"),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros seleccionados.")

# ------------------------------------------------------------------ #
#  FILA 4: Top sitios                                                  #
# ------------------------------------------------------------------ #
st.markdown("### 📍 Top 10 Sitios con Mayor Accidentalidad")
df = tr.preparar_top_sitios(dao.top_sitios_peligrosos(top_n=10, filtros=filtros))
if not df.empty:
    fig = px.bar(df.sort_values("total"), x="total", y="Sitio", orientation="h",
                 color="total", color_continuous_scale=["#21262d", "#f85149"],
                 labels={"total": "Accidentes", "Sitio": "Lugar"}, text="total")
    fig.update_traces(textposition="outside", textfont_color="#e6edf3")
    fig.update_layout(**LAYOUT, height=420,
                      xaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"),
                      yaxis=dict(showgrid=False, color="#8b949e", tickfont=dict(size=11)))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sin datos para los filtros seleccionados.")

st.markdown("---")
st.markdown(
    "<small style='color:#8b949e'>Datos: Secretaría de Tránsito de Barranquilla · datos.gov.co</small>",
    unsafe_allow_html=True,
)
