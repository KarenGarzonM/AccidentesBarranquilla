"""
ui/styles.py

Responsabilidad: centralizar todos los estilos globales de la app.
Cada página llama a apply_global_styles() al inicio, antes de
renderizar cualquier componente.

Uso:
    from ui.styles import apply_global_styles
    apply_global_styles()
"""

import streamlit as st


# ── Paleta de colores ──────────────────────────────────────────────────────
# Definida aquí como constantes para reutilizar en componentes Python
# que necesiten colores (ej: Plotly charts).

COLORS = {
    "bg_primary":    "#0d1117",
    "bg_secondary":  "#161b22",
    "bg_tertiary":   "#1c2128",
    "bg_card":       "#21262d",
    "border":        "#30363d",
    "text_primary":  "#e6edf3",
    "text_muted":    "#8b949e",
    "accent":        "#f0883e",
    "accent_alt":    "#d29922",
    "success":       "#3fb950",
    "info":          "#79c0ff",
}

# Paleta para gráficos Plotly — importar desde aquí en charts.py
PLOTLY_COLORS = [
    COLORS["accent"],
    COLORS["accent_alt"],
    COLORS["success"],
    COLORS["info"],
    "#a371f7",
    "#f78166",
]


# ── Estilos globales ───────────────────────────────────────────────────────

def apply_global_styles() -> None:
    """
    Inyecta el CSS global de la aplicación vía st.markdown.
    Llamar una vez al inicio de cada página, justo después de
    st.set_page_config().
    """
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif;
}}
.stApp {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {COLORS['bg_secondary']};
    border-right: 1px solid {COLORS['border']};
}}

/* ── Métricas ── */
div[data-testid="metric-container"] {{
    background: linear-gradient(135deg, {COLORS['bg_tertiary']} 0%, {COLORS['bg_card']} 100%);
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px 20px;
}}
div[data-testid="metric-container"] label {{
    color: {COLORS['text_muted']} !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: {COLORS['accent']} !important;
    font-size: 2rem !important;
    font-weight: 700;
}}

/* ── Tipografía ── */
h1, h2, h3 {{
    color: {COLORS['text_primary']} !important;
}}
hr {{
    border-color: {COLORS['border']};
}}

/* ── Botones ── */
.stButton > button {{
    background: linear-gradient(135deg, {COLORS['accent']}, {COLORS['accent_alt']});
    color: {COLORS['bg_primary']};
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
}}

/* ── Tarjetas de navegación ── */
.nav-card {{
    background: linear-gradient(135deg, {COLORS['bg_tertiary']}, {COLORS['bg_card']});
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    padding: 1.125rem 2rem;
    text-align: center;
    height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.25rem;
}}
.nav-card .icon {{ font-size: 2.25rem; }}
.nav-card h3    {{ margin: 0 !important; font-size: 1.1rem !important; }}
.nav-card p     {{ color: {COLORS['text_muted']}; margin: 0; font-size: 0.85rem; }}

/* ── Hero ── */
.hero {{
    background: linear-gradient(135deg, {COLORS['bg_secondary']} 0%, {COLORS['bg_tertiary']} 60%, {COLORS['bg_primary']} 100%);
    border: 1px solid {COLORS['border']};
    border-left: 5px solid {COLORS['accent']};
    border-radius: 16px;
    padding: 3rem 3rem 2.5rem;
    margin-bottom: 2.5rem;
}}
.hero h1 {{
    font-size: 2.8rem !important;
    font-weight: 700;
    background: linear-gradient(90deg, {COLORS['accent']}, {COLORS['accent_alt']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem !important;
}}
.hero p {{
    color: {COLORS['text_muted']};
    font-size: 1rem;
    max-width: 66.66%;
}}

/* ── Badges ── */
.badge {{
    display: inline-block;
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    color: {COLORS['text_muted']};
    margin-right: 0.5rem;
}}
</style>
"""