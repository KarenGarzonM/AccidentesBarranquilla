"""
ui/components/charts.py

Responsabilidad: construir figuras Plotly a partir de DataFrames
ya transformados. Ninguna función aquí toca MongoDB ni Streamlit.

Cada función:
  - Recibe un pd.DataFrame con columnas conocidas
  - Devuelve un plotly.graph_objects.Figure
  - Aplica el tema visual del proyecto (COLORS, fuente, fondo)

Uso en una página:
    from ui.components.charts import chart_por_anio
    st.plotly_chart(chart_por_anio(df), use_container_width=True)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.styles import COLORS


# ── Layout base compartido ─────────────────────────────────────────────────

def _layout_base(titulo: str = "") -> dict:
    """Configuración de layout común a todos los gráficos."""
    return dict(
        title=dict(
            text=titulo,
            font=dict(color=COLORS["text_primary"], size=15),
            x=0,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=COLORS["bg_tertiary"],
        font=dict(color=COLORS["text_muted"], family="Space Grotesk, sans-serif"),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"]),
        yaxis=dict(gridcolor=COLORS["border"], linecolor=COLORS["border"]),
        hoverlabel=dict(
            bgcolor=COLORS["bg_card"],
            bordercolor=COLORS["border"],
            font_color=COLORS["text_primary"],
        ),
    )


# ── Gráficos ───────────────────────────────────────────────────────────────

def chart_por_anio(df: pd.DataFrame) -> go.Figure:
    """
    Línea de accidentes totales por año.
    Espera columnas: Año (str), total (int).
    """
    fig = px.line(
        df,
        x="Año",
        y="total",
        markers=True,
        labels={"total": "Accidentes", "Año": "Año"},
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig.update_traces(
        line_width=2.5,
        marker=dict(size=7, color=COLORS["accent_alt"]),
    )
    fig.update_layout(**_layout_base("Accidentes por año"))
    return fig


def chart_por_mes(df: pd.DataFrame) -> go.Figure:
    """
    Barras de accidentes por mes.
    Espera columnas: Mes (str), total (int).
    """
    fig = px.bar(
        df,
        x="Mes",
        y="total",
        labels={"total": "Accidentes", "Mes": "Mes"},
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(**_layout_base("Accidentes por mes"))
    return fig


def chart_por_gravedad(df: pd.DataFrame) -> go.Figure:
    """
    Dona de accidentes por gravedad.
    Espera columnas: Gravedad (str), total (int).
    """
    colores = [
        COLORS["accent"],
        COLORS["accent_alt"],
        COLORS["success"],
        COLORS["info"],
        "#a371f7",
    ]
    fig = px.pie(
        df,
        names="Gravedad",
        values="total",
        hole=0.45,
        color_discrete_sequence=colores,
    )
    fig.update_traces(
        textfont_color=COLORS["text_primary"],
        marker=dict(line=dict(color=COLORS["bg_primary"], width=2)),
    )
    fig.update_layout(
        **_layout_base("Distribución por gravedad"),
        legend=dict(font=dict(color=COLORS["text_muted"])),
    )
    return fig


def chart_por_tipo(df: pd.DataFrame) -> go.Figure:
    """
    Barras horizontales de accidentes por clase/tipo.
    Espera columnas: Tipo (str), total (int).
    """
    df_sorted = df.sort_values("total")
    fig = px.bar(
        df_sorted,
        x="total",
        y="Tipo",
        orientation="h",
        labels={"total": "Accidentes", "Tipo": "Tipo"},
        color_discrete_sequence=[COLORS["info"]],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        **_layout_base("Accidentes por tipo"),
        yaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            tickfont=dict(size=11),
        ),
    )
    return fig


def chart_por_hora(df: pd.DataFrame) -> go.Figure:
    """
    Área de accidentes por hora del día.
    Espera columnas: Hora (int), total (int), Etiqueta (str).
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Etiqueta"],
        y=df["total"],
        mode="lines",
        fill="tozeroy",
        line=dict(color=COLORS["accent"], width=2),
        fillcolor=f"rgba(240,136,62,0.15)",
        hovertemplate="<b>%{x}</b><br>Accidentes: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **_layout_base("Distribución por hora del día"),
        xaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            tickangle=-45,
            tickfont=dict(size=10),
        ),
    )
    return fig


def chart_por_dia(df: pd.DataFrame) -> go.Figure:
    """
    Barras de accidentes por día de la semana.
    Espera columnas: Día (str), total (int).
    """
    fig = px.bar(
        df,
        x="Día",
        y="total",
        labels={"total": "Accidentes", "Día": "Día"},
        color_discrete_sequence=[COLORS["success"]],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(**_layout_base("Accidentes por día de la semana"))
    return fig


def chart_top_sitios(df: pd.DataFrame) -> go.Figure:
    """
    Barras horizontales de los sitios más peligrosos.
    Espera columnas: Sitio (str), total (int).
    """
    df_sorted = df.sort_values("total")
    fig = px.bar(
        df_sorted,
        x="total",
        y="Sitio",
        orientation="h",
        labels={"total": "Accidentes", "Sitio": "Sitio"},
        color_discrete_sequence=[COLORS["accent_alt"]],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        **_layout_base("Top sitios con más accidentes"),
        height=420,
        yaxis=dict(
            gridcolor=COLORS["border"],
            linecolor=COLORS["border"],
            tickfont=dict(size=10),
        ),
    )
    return fig