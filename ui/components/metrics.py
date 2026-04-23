"""
ui/components/metrics.py

Responsabilidad: renderizar grupos de métricas (KPIs) con st.metric.
Ninguna función aquí toca MongoDB ni settings — solo recibe datos
ya calculados y los muestra.

Funciones públicas:
    render_kpis_principales()   — 4 métricas del home y página MongoDB
    render_kpis_victimas()      — máximos de heridos y muertos (gráficos)
    render_sin_datos()          — aviso cuando la colección está vacía
    render_estado_conexion()    — badge de conexión en sidebar
"""

import streamlit as st


def render_kpis_principales(resumen: dict) -> None:
    """
    Renderiza las 4 métricas globales de la colección.

    Args:
        resumen: dict con claves total_documentos, anios_cubiertos,
                 total_heridos, total_muertos.
                 Viene de accidentes_repo.resumen_coleccion().
    """
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Registros en BD",  f"{resumen['total_documentos']:,}")
    c2.metric("📅 Años cubiertos",   resumen["anios_cubiertos"])
    c3.metric("🤕 Total heridos",    f"{resumen['total_heridos']:,}")
    c4.metric("💀 Total muertos",    f"{resumen['total_muertos']:,}")


def render_kpis_victimas(maximos: dict) -> None:
    """
    Renderiza los máximos de víctimas en un solo accidente.

    Args:
        maximos: dict con claves max_heridos, max_muertos.
                 Viene de analytics_repo.maximos_victimas().
    """
    c1, c2 = st.columns(2)
    c1.metric("🤕 Máx. heridos en un accidente", maximos.get("max_heridos", 0))
    c2.metric("💀 Máx. muertos en un accidente", maximos.get("max_muertos", 0))


def render_kpis_filtrados(total: int, anios: list, label_extra: str = "") -> None:
    """
    Métricas rápidas dentro de una vista filtrada (ej: página MongoDB).

    Args:
        total:       número de documentos tras aplicar filtros.
        anios:       lista de años disponibles en la colección.
        label_extra: texto adicional opcional junto al conteo.
    """
    c1, c2 = st.columns(2)
    label = f"📄 Registros{' ' + label_extra if label_extra else ''}"
    c1.metric(label, f"{total:,}")
    if anios:
        c2.metric("📅 Rango de años", f"{min(anios)} – {max(anios)}")


def render_sin_datos() -> None:
    """
    Muestra un aviso claro cuando la colección está vacía.
    Se usa en el home y en cualquier página que requiera datos cargados.
    """
    st.warning(
        "⚠️ No hay datos aún. "
        "Ve a la página **📡 API** para cargar los datos desde datos.gov.co."
    )


def render_estado_conexion(conectado: bool, total: int = 0) -> None:
    """
    Badge en el sidebar indicando el estado de la conexión a MongoDB.

    Args:
        conectado: True si la conexión fue exitosa.
        total:     número de documentos en la colección (opcional).
    """
    if conectado:
        st.sidebar.success(f"🍃 MongoDB conectado · {total:,} registros")
    else:
        st.sidebar.error("❌ Sin conexión a MongoDB")