"""
data/extractors/api_extractor.py

Responsabilidad: consumir la API REST de datos.gov.co,
normalizar los registros y persistirlos en MongoDB.

Funciones públicas:
    extraer_todos_los_datos()   — upsert incremental
    recargar_todos_los_datos()  — borra y recarga todo
"""

import hashlib
from datetime import datetime

import requests

from config.settings import settings
from data.mongo_client import get_collection
from data.repositories.accidentes_repo import (
    upsert_muchos,
    eliminar_todos,
    insertar_muchos,
)


# ── Helpers privados ───────────────────────────────────────────────────────

def _generar_id_unico(registro: dict) -> str:
    clave = (
        f"{registro.get('fecha_accidente', '')}_"
        f"{registro.get('hora_accidente', '')}_"
        f"{registro.get('sitio_exacto_accidente', '')}"
    )
    return hashlib.md5(clave.encode()).hexdigest()


def _normalizar_registro(registro: dict) -> dict:
    """
    Limpia y tipifica los campos numéricos de un registro.
    La API devuelve valores como "1.0" (string con decimal),
    por eso se hace float() antes de int().
    """
    registro["_id"] = _generar_id_unico(registro)
    registro["cargado_en"] = datetime.utcnow()

    for campo in [
        "cant_heridos_en_sitio_accidente",
        "cant_muertos_en_sitio_accidente",
        "cantidad_accidentes",
    ]:
        valor = registro.get(campo)
        try:
            registro[campo] = int(float(valor)) if valor is not None else 0
        except (ValueError, TypeError):
            registro[campo] = 0

    try:
        registro["a_o_accidente"] = int(float(registro.get("a_o_accidente", 0)))
    except (ValueError, TypeError):
        registro["a_o_accidente"] = 0

    return registro


def _descargar_todos(callback=None) -> list:
    """
    Descarga todos los registros de la API con paginación.
    Llama a callback(total_descargados) tras cada página si se provee.
    """
    offset = 0
    todos = []

    while True:
        params = {
            "$limit": settings.api_page_size,
            "$offset": offset,
            "$order": "fecha_accidente ASC",
        }

        try:
            response = requests.get(
                settings.api_url,
                params=params,
                timeout=settings.api_timeout_s,
            )
            response.raise_for_status()
            registros = response.json()
        except requests.RequestException as e:
            print(f"Error al consumir la API en offset {offset}: {e}")
            break

        if not registros:
            break

        todos.extend([_normalizar_registro(r) for r in registros])
        offset += settings.api_page_size

        if callback:
            callback(len(todos))

        print(f" → Descargados {len(todos)} registros...")

        if len(registros) < settings.api_page_size:
            break

    return todos


# ── Funciones públicas ─────────────────────────────────────────────────────

def extraer_todos_los_datos(callback=None) -> int:
    """Modo incremental: upsert sin eliminar datos previos."""
    col = get_collection()
    print(f"[{datetime.now()}] Iniciando extracción incremental...")

    registros = _descargar_todos(callback)
    if registros:
        upsert_muchos(col, registros)

    print(f"[{datetime.now()}] Completado. Total: {len(registros)} registros.")
    return len(registros)


def recargar_todos_los_datos(callback=None) -> int:
    """
    Modo recarga completa: descarga primero, luego borra MongoDB
    e inserta todo de nuevo. Si la descarga falla, no toca la BD.
    """
    col = get_collection()
    print(f"[{datetime.now()}] Iniciando recarga completa...")

    # 1. Descargar antes de tocar la BD
    registros = _descargar_todos(callback)
    if not registros:
        print("No se obtuvieron registros de la API. Abortando recarga.")
        return 0

    # 2. Borrar colección existente
    eliminados = eliminar_todos(col)
    print(f" → {eliminados} documentos eliminados de MongoDB.")

    # 3. Insertar los nuevos
    insertar_muchos(col, registros)
    print(f"[{datetime.now()}] Recarga completada. {len(registros)} registros insertados.")
    return len(registros)


if __name__ == "__main__":
    recargar_todos_los_datos()