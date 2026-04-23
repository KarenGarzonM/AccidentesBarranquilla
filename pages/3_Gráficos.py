"""
pages/3_Graficos.py
Página de visualizaciones interactivas con Plotly.
"""

import streamlit as st
import plotly.express as px

from data.mongo_client import get_collection
from data.repositories.accidentes_repo import (
    contar_total,
    obtener_anios_disponibles,
    obtener_gravedades,
    obtener_clases,
)
from data.repositories.analytics_repo import (
    accidentes_por_anio,
    accidentes_por_mes,
    accidentes_por_tipo,
    accidentes_por_gravedad,
    accidentes_por_hora,
    accidentes_por_dia_semana,
    top_sitios_peligrosos,
    maximos_victimas,
)
from core.transformers import (
    preparar_por_anio,
    preparar_por_mes,
    preparar_por_tipo,
    preparar_por_gravedad,
    preparar_por_hora,
    preparar_por_dia,
    preparar_top_sitios,
)
from ui.styles import apply_global_styles
from ui.components.metrics import render_sin_datos

st.set_page_config(page_title="Gráficos · Accidentalidad", page_icon="📊", layout="wide")

apply_global_styles()

# ------------------------------------------------------------------ #
#  CONEXIÓN                                                            #
# ------------------------------------------------------------------ #
@st.cache_resource(show_spinner=False)
def obtener_col():
    return get_collection()
try:
    col = obtener_col()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

if contar_total(col) == 0:
    render_sin_datos()
    st.stop()

# ------------------------------------------------------------------ #
#  SIDEBAR — FILTROS                                                   #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("## 🔍 Filtros")
    st.markdown("---")

    anios_disponibles = obtener_anios_disponibles(col)
    anios_sel = st.multiselect("Año(s)", options=anios_disponibles, default=anios_disponibles)

    gravedades_opciones = obtener_gravedades(col)
    gravedades_sel = st.multiselect("Gravedad", options=gravedades_opciones, default=gravedades_opciones)

    tipos_opciones = obtener_clases(col)
    tipos_sel = st.multiselect("Clase de accidente", options=tipos_opciones, default=tipos_opciones)

    st.markdown("---")
    st.markdown(f"<small style='color:#8b949e'>📦 {contar_total(col):,} registros en BD</small>", unsafe_allow_html=True)

filtros = {
    "anios": anios_sel if anios_sel else None,
    "gravedad": gravedades_sel if gravedades_sel else None,
    "clase": tipos_sel if tipos_sel else None,
}

# Layout base para gráficos — sin height para evitar conflictos al sobrescribir
LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#8b949e",
    coloraxis_showscale=False,
    margin=dict(t=20, b=20),
)

# ------------------------------------------------------------------ #
#  ENCABEZADO                                                          #
# ------------------------------------------------------------------ #
st.markdown("## 📊 Visualizaciones — Accidentalidad Barranquilla")
st.markdown("---")

# ------------------------------------------------------------------ #
#  KPIs                                                                #
# ------------------------------------------------------------------ #
maximos = maximos_victimas(col, filtros)
total_acc = sum(r["total"] for r in accidentes_por_anio(col, filtros))
heridos_data = accidentes_por_gravedad(col, filtros)
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
    st.markdown("### 🚨 Accidentes por Año")
    df = preparar_por_anio(accidentes_por_anio(col, filtros))
    if not df.empty:
        fig = px.bar(df, x="Año", y="total", color="total",
                     color_continuous_scale=["#21262d", "#f0883e"],
                     labels={"total": "Accidentes"}, text="total")
        fig.update_traces(textposition="outside", textfont_color="#e6edf3")
        fig.update_layout(**LAYOUT, height=320,
                          xaxis=dict(showgrid=False, color="#8b949e"),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos para los filtros seleccionados.")

with r1c2:
    st.markdown("### 📆 Accidentes por Mes")
    df = preparar_por_mes(accidentes_por_mes(col, filtros))
    if not df.empty:
        fig = px.line(df, x="Mes", y="total", markers=True,
                      labels={"total": "Accidentes"},
                      color_discrete_sequence=["#f0883e"])
        fig.update_traces(line_width=3, marker=dict(size=8, color="#d29922"))
        fig.update_layout(**LAYOUT, height=320,
                          xaxis=dict(showgrid=False, color="#8b949e", tickangle=-30),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos para los filtros seleccionados.")

# ------------------------------------------------------------------ #
#  FILA 2: Por tipo (donut) + Por hora                                 #
# ------------------------------------------------------------------ #
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown("### 📌 % de Accidentes por Tipo")
    df = preparar_por_tipo(accidentes_por_tipo(col, filtros))
    if not df.empty:
        fig = px.pie(df, names="Tipo", values="total", hole=0.55,
                     color_discrete_sequence=px.colors.sequential.Oranges_r)
        fig.update_traces(textinfo="percent+label", textfont_color="#e6edf3",
                          marker=dict(line=dict(color="#0d1117", width=2)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#8b949e",
                          showlegend=True, legend=dict(font=dict(color="#8b949e")),
                          margin=dict(t=20, b=20), height=340)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos para los filtros seleccionados.")

with r2c2:
    st.markdown("### 🕐 Accidentes por Hora del Día")
    df = preparar_por_hora(accidentes_por_hora(col, filtros))
    if not df.empty:
        fig = px.bar(df, x="Etiqueta", y="total",
                     labels={"total": "Accidentes", "Etiqueta": "Hora"},
                     color="total",
                     color_continuous_scale=["#21262d", "#d29922", "#f0883e"])
        fig.update_layout(**LAYOUT, height=340,
                          xaxis=dict(showgrid=False, color="#8b949e", tickangle=-45),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos para los filtros seleccionados.")

# ------------------------------------------------------------------ #
#  FILA 3: Gravedad + Día de semana                                    #
# ------------------------------------------------------------------ #
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.markdown("### ⚠️ Distribución por Gravedad")
    df = preparar_por_gravedad(accidentes_por_gravedad(col, filtros))
    if not df.empty:
        colores_grav = {"Con muertos": "#f85149", "Con heridos": "#f0883e", "Solo daños": "#3fb950"}
        fig = px.bar(df, x="total", y="Gravedad", orientation="h",
                     color="Gravedad", color_discrete_map=colores_grav,
                     labels={"total": "Accidentes"}, text="total")
        fig.update_traces(textposition="outside", textfont_color="#e6edf3")
        fig.update_layout(**LAYOUT, height=280, showlegend=False,
                          xaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"),
                          yaxis=dict(showgrid=False, color="#8b949e"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos para los filtros seleccionados.")

with r3c2:
    st.markdown("### 📊 Accidentes por Día de Semana")
    df = preparar_por_dia(accidentes_por_dia_semana(col, filtros))
    if not df.empty:
        fig = px.bar(df, x="Día", y="total", color="total",
                     color_continuous_scale=["#21262d", "#f0883e"],
                     labels={"total": "Accidentes"}, text="total")
        fig.update_traces(textposition="outside", textfont_color="#e6edf3")
        fig.update_layout(**LAYOUT, height=280,
                          xaxis=dict(showgrid=False, color="#8b949e"),
                          yaxis=dict(showgrid=True, gridcolor="#21262d", color="#8b949e"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos para los filtros seleccionados.")

# ------------------------------------------------------------------ #
#  FILA 4: Top sitios                                                  #
# ------------------------------------------------------------------ #
st.markdown("### 📍 Top 10 Sitios con Mayor Accidentalidad")
df = preparar_top_sitios(top_sitios_peligrosos(col, top_n=10, filtros=filtros))
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